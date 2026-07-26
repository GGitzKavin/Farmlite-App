"""Controlled, cow-grouped modeling helpers for Bangladesh Phase 4.5D.

The approved primary feature contract is deliberately tiny:
``genetic_group`` and ``thi_category``.  Source identifiers and same-record
outcomes are retained only for lineage, grouping, or evaluation.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import (
    GroupKFold,
    GroupShuffleSplit,
    LeaveOneGroupOut,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor

from config.settings import FLASK_API_DIR, PROJECT_ROOT
from ml.data_integration.bangladesh_audit import (
    DMI_FILENAME,
    EXPECTED_SHA256,
    SOURCE_DIR,
    dataframe_from_sheet,
    sha256_file,
)
from ml.data_integration.office_reader import read_xlsx
from ml.training.metrics import json_safe, regression_metrics


RANDOM_SEED = 42
CONTRACT_PATH = FLASK_API_DIR / "config" / "bangladesh_model_contract.json"
PROCESSED_DIR = (
    PROJECT_ROOT / "datasets" / "external" / "processed"
    / "bangladesh_hf_cross"
)
PRIMARY_FEATURES = ["genetic_group", "thi_category"]
LINEAGE_FIELDS = [
    "source_workbook",
    "source_sheet",
    "source_row_number",
    "cow_id",
    "replication",
    "thi_category",
    "genetic_group",
]
TASKS = {
    "dmi": {
        "model_name": "bangladesh_dmi_regressor",
        "target": "dry_matter_intake_kg_day",
        "source_target": "DMI (kg)",
        "unit": "kg/cow/day",
        "processed_filename": "bangladesh_dmi_model_data_v1.csv",
    },
    "milk": {
        "model_name": "bangladesh_milk_yield_regressor",
        "target": "milk_yield_l_day",
        "source_target": "Milk Yield (L/day/cow)",
        "unit": "L/cow/day",
        "processed_filename": "bangladesh_milk_model_data_v1.csv",
    },
}
MINIMUM_MEANINGFUL_IMPROVEMENT = 0.05
MAXIMUM_FOLD_MAE_CV = 0.35


class BangladeshExperimentError(RuntimeError):
    """Raised when a controlled-experiment invariant fails."""


@dataclass(frozen=True)
class CandidateSpec:
    """One modest, predeclared regression configuration."""

    configuration_id: str
    algorithm: str
    parameters: dict[str, Any]
    is_baseline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    """Return an explicit UTC timestamp."""

    return datetime.now(UTC).isoformat()


def load_contract() -> dict[str, Any]:
    """Load and validate the immutable Phase 4.5D feature contract."""

    if not CONTRACT_PATH.is_file():
        raise BangladeshExperimentError(
            f"Bangladesh model contract is missing: {CONTRACT_PATH}"
        )
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("contract_version") != "bangladesh_hf_model_contract_v1":
        raise BangladeshExperimentError("Unsupported Bangladesh contract version")
    if contract.get("production_approved") is not False:
        raise BangladeshExperimentError("Contract must remain production-false")
    for task in TASKS:
        model_name = TASKS[task]["model_name"]
        model = contract["models"].get(model_name)
        if model is None:
            raise BangladeshExperimentError(
                f"Contract model is missing: {model_name}"
            )
        if model["feature_order"] != PRIMARY_FEATURES:
            raise BangladeshExperimentError(
                f"Feature order changed for {model_name}"
            )
        if model["grouping_field"] != "cow_id":
            raise BangladeshExperimentError(
                f"Grouping field changed for {model_name}"
            )
    return contract


def load_source_frame() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read the approved workbook and verify its exact source checksum."""

    source = SOURCE_DIR / DMI_FILENAME
    checksum = sha256_file(source)
    if checksum != EXPECTED_SHA256[DMI_FILENAME]:
        raise BangladeshExperimentError(
            f"Bangladesh DMI/milk workbook checksum changed: {checksum}"
        )
    workbook = read_xlsx(source)
    if [sheet.name for sheet in workbook.sheets] != ["Sheet1"]:
        raise BangladeshExperimentError("Bangladesh source sheet inventory changed")
    frame = dataframe_from_sheet(workbook.sheets[0])
    expected_columns = [
        "Animal ID",
        "Genetic Group",
        "THI Range",
        "Replication No",
        "DMI (kg)",
        "Milk Yield (L/day/cow)",
        "SCC cells per mL",
        "Fat%",
        "SNF%",
        "Protein %",
        "Salt%",
        "Lactose%",
        "pH",
        "source_row_number",
    ]
    if list(frame.columns) != expected_columns:
        raise BangladeshExperimentError("Bangladesh source columns changed")
    metadata = {
        "source_path": str(source),
        "source_workbook": DMI_FILENAME,
        "source_sheet": "Sheet1",
        "source_sha256": checksum,
        "source_rows": len(frame),
    }
    return frame, metadata


def build_task_frame(source: pd.DataFrame, task: str) -> pd.DataFrame:
    """Create an auditable, target-specific model table in memory."""

    if task not in TASKS:
        raise BangladeshExperimentError(f"Unsupported Bangladesh task: {task}")
    definition = TASKS[task]
    target = definition["target"]
    frame = pd.DataFrame(
        {
            "source_workbook": DMI_FILENAME,
            "source_sheet": "Sheet1",
            "source_row_number": pd.to_numeric(
                source["source_row_number"], errors="raise"
            ).astype(int),
            "cow_id": source["Animal ID"].astype(str).str.strip(),
            "replication": pd.to_numeric(
                source["Replication No"], errors="raise"
            ).astype(int),
            "thi_category": source["THI Range"].astype(str).str.strip(),
            "genetic_group": source["Genetic Group"].astype(str).str.strip(),
            target: pd.to_numeric(
                source[definition["source_target"]], errors="raise"
            ).astype(float),
        }
    )
    required = [*LINEAGE_FIELDS, target]
    if frame[required].isna().any().any():
        raise BangladeshExperimentError(
            f"Missing required value in {task} model data"
        )
    if len(frame) != 750:
        raise BangladeshExperimentError(
            f"Expected 750 {task} rows, found {len(frame)}"
        )
    counts = frame.groupby("cow_id", sort=True).size()
    if len(counts) != 50 or not bool((counts == 15).all()):
        raise BangladeshExperimentError(
            f"Expected 50 cows with 15 rows in {task}"
        )
    if set(frame["thi_category"]) != {"T0", "T1", "T2"}:
        raise BangladeshExperimentError(
            f"Unexpected THI categories in {task}: "
            f"{sorted(frame['thi_category'].unique())}"
        )
    if frame[target].le(0).any():
        raise BangladeshExperimentError(
            f"Non-positive approved target in {task}"
        )
    return frame


def write_processed_task_frame(frame: pd.DataFrame, task: str) -> Path:
    """Write only approved lineage, features, and one task target."""

    target = TASKS[task]["target"]
    expected = [*LINEAGE_FIELDS, target]
    if list(frame.columns) != expected:
        raise BangladeshExperimentError(
            f"Unexpected processed columns for {task}: {list(frame.columns)}"
        )
    path = PROCESSED_DIR / TASKS[task]["processed_filename"]
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    reloaded = pd.read_csv(path, dtype={"cow_id": str})
    if list(reloaded.columns) != expected or len(reloaded) != len(frame):
        raise BangladeshExperimentError(
            f"Processed lineage validation failed for {task}"
        )
    return path


def candidate_specs(task: str) -> list[CandidateSpec]:
    """Return the modest, non-exhaustive approved candidate registry."""

    if task not in TASKS:
        raise BangladeshExperimentError(f"Unsupported Bangladesh task: {task}")
    prefix = f"bangladesh_{task}"
    return [
        CandidateSpec(
            f"{prefix}_dummy_mean",
            "DummyRegressor",
            {"strategy": "mean"},
            is_baseline=True,
        ),
        CandidateSpec(
            f"{prefix}_dummy_median",
            "DummyRegressor",
            {"strategy": "median"},
            is_baseline=True,
        ),
        CandidateSpec(
            f"{prefix}_linear",
            "LinearRegression",
            {},
        ),
        CandidateSpec(
            f"{prefix}_ridge_a0_1",
            "Ridge",
            {"alpha": 0.1},
        ),
        CandidateSpec(
            f"{prefix}_ridge_a1",
            "Ridge",
            {"alpha": 1.0},
        ),
        CandidateSpec(
            f"{prefix}_ridge_a10",
            "Ridge",
            {"alpha": 10.0},
        ),
        CandidateSpec(
            f"{prefix}_tree_d2",
            "DecisionTreeRegressor",
            {
                "max_depth": 2,
                "min_samples_leaf": 20,
                "random_state": RANDOM_SEED,
            },
        ),
        CandidateSpec(
            f"{prefix}_tree_d3",
            "DecisionTreeRegressor",
            {
                "max_depth": 3,
                "min_samples_leaf": 20,
                "random_state": RANDOM_SEED,
            },
        ),
        CandidateSpec(
            f"{prefix}_forest_d2",
            "RandomForestRegressor",
            {
                "n_estimators": 100,
                "max_depth": 2,
                "min_samples_leaf": 10,
                "max_features": 1.0,
                "n_jobs": 1,
                "random_state": RANDOM_SEED,
            },
        ),
        CandidateSpec(
            f"{prefix}_forest_d3",
            "RandomForestRegressor",
            {
                "n_estimators": 100,
                "max_depth": 3,
                "min_samples_leaf": 10,
                "max_features": 1.0,
                "n_jobs": 1,
                "random_state": RANDOM_SEED,
            },
        ),
    ]


def _estimator(spec: CandidateSpec) -> Any:
    factories = {
        "DummyRegressor": DummyRegressor,
        "LinearRegression": LinearRegression,
        "Ridge": Ridge,
        "DecisionTreeRegressor": DecisionTreeRegressor,
        "RandomForestRegressor": RandomForestRegressor,
    }
    factory = factories.get(spec.algorithm)
    if factory is None:
        raise BangladeshExperimentError(
            f"Unsupported Bangladesh estimator: {spec.algorithm}"
        )
    return factory(**spec.parameters)


def build_pipeline(
    spec: CandidateSpec,
    feature_order: list[str] | None = None,
) -> Pipeline:
    """Build a leakage-safe pipeline with unknown-category handling."""

    features = feature_order or PRIMARY_FEATURES
    allowed = {
        "genetic_group",
        "thi_category",
        "rectal_temperature_f",
        "pulse_rate_per_min",
        "respiration_rate_per_min",
    }
    if not features or len(features) != len(set(features)):
        raise BangladeshExperimentError("Feature order is empty or duplicated")
    forbidden = sorted(set(features) - allowed)
    if forbidden:
        raise BangladeshExperimentError(
            "Forbidden Bangladesh model feature(s): " + ", ".join(forbidden)
        )
    categorical = [
        feature for feature in features
        if feature in {"genetic_group", "thi_category"}
    ]
    numeric = [feature for feature in features if feature not in categorical]
    transformers: list[tuple[str, Any, list[str]]] = []
    if categorical:
        transformers.append(
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical,
            )
        )
    if numeric:
        transformers.append(("numeric", "passthrough", numeric))
    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline(
        [
            ("preprocessing", preprocessor),
            ("estimator", _estimator(spec)),
        ]
    )


def create_group_assignments(frame: pd.DataFrame) -> dict[str, Any]:
    """Create the complete-cow holdout and development-only CV folds."""

    groups = frame["cow_id"].astype(str)
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=RANDOM_SEED,
    )
    development_indices, holdout_indices = next(
        splitter.split(frame, groups=groups)
    )
    development = frame.iloc[development_indices].copy()
    holdout = frame.iloc[holdout_indices].copy()
    development_groups = development["cow_id"].astype(str)
    folds = np.full(len(frame), -1, dtype=int)
    group_kfold = GroupKFold(n_splits=5)
    cv_splits: list[tuple[np.ndarray, np.ndarray]] = []
    development_positions = np.asarray(development_indices)
    for fold, (train_local, validation_local) in enumerate(
        group_kfold.split(
            development,
            groups=development_groups,
        ),
        start=1,
    ):
        train_global = development_positions[train_local]
        validation_global = development_positions[validation_local]
        folds[validation_global] = fold
        cv_splits.append((train_global, validation_global))
    partitions = np.full(len(frame), "development", dtype=object)
    partitions[holdout_indices] = "holdout"
    manifest = frame[LINEAGE_FIELDS].copy()
    manifest["partition"] = partitions
    manifest["group_cv_fold"] = pd.Series(folds).replace(-1, pd.NA)
    manifest["random_seed"] = RANDOM_SEED
    manifest["split_version"] = "bangladesh_group_split_v1"
    validation = validate_group_assignments(frame, manifest)
    return {
        "development_indices": np.asarray(development_indices),
        "holdout_indices": np.asarray(holdout_indices),
        "cv_splits": cv_splits,
        "manifest": manifest,
        "validation": validation,
    }


def validate_group_assignments(
    frame: pd.DataFrame,
    manifest: pd.DataFrame,
) -> dict[str, Any]:
    """Prove that repeated cows never cross a partition or CV fold."""

    if len(frame) != len(manifest):
        raise BangladeshExperimentError("Split manifest row count mismatch")
    if manifest["source_row_number"].duplicated().any():
        raise BangladeshExperimentError("Duplicate source-row assignment")
    if manifest["partition"].isna().any():
        raise BangladeshExperimentError("Missing partition assignment")
    partition_counts = (
        manifest.groupby("cow_id")["partition"].nunique()
    )
    if int((partition_counts > 1).sum()):
        raise BangladeshExperimentError("Cow overlap across holdout boundary")
    development = manifest["partition"] == "development"
    holdout = manifest["partition"] == "holdout"
    if manifest.loc[development, "group_cv_fold"].isna().any():
        raise BangladeshExperimentError("Development row missing CV fold")
    if manifest.loc[holdout, "group_cv_fold"].notna().any():
        raise BangladeshExperimentError("Holdout row assigned to CV fold")
    fold_counts_per_cow = (
        manifest.loc[development].groupby("cow_id")["group_cv_fold"].nunique()
    )
    if int((fold_counts_per_cow != 1).sum()):
        raise BangladeshExperimentError("Repeated cow rows cross CV folds")
    development_cows = set(
        manifest.loc[development, "cow_id"].astype(str)
    )
    holdout_cows = set(manifest.loc[holdout, "cow_id"].astype(str))
    overlap = development_cows & holdout_cows
    if overlap:
        raise BangladeshExperimentError(
            f"Holdout cow overlap: {sorted(overlap)}"
        )
    fold_rows = (
        manifest.loc[development, "group_cv_fold"]
        .astype(int)
        .value_counts()
        .sort_index()
    )
    fold_cows = (
        manifest.loc[development]
        .groupby("group_cv_fold")["cow_id"]
        .nunique()
        .sort_index()
    )
    return {
        "row_count": len(manifest),
        "development_row_count": int(development.sum()),
        "holdout_row_count": int(holdout.sum()),
        "development_cow_count": len(development_cows),
        "holdout_cow_count": len(holdout_cows),
        "cow_overlap_count": len(overlap),
        "missing_partition_assignments": int(
            manifest["partition"].isna().sum()
        ),
        "missing_development_fold_assignments": int(
            manifest.loc[development, "group_cv_fold"].isna().sum()
        ),
        "fold_row_counts": {
            str(int(key)): int(value) for key, value in fold_rows.items()
        },
        "fold_cow_counts": {
            str(int(key)): int(value) for key, value in fold_cows.items()
        },
        "holdout_cow_ids": sorted(holdout_cows),
        "grouping_field": "cow_id",
        "holdout_method": "GroupShuffleSplit",
        "cross_validation_method": "GroupKFold(n_splits=5)",
        "random_seed": RANDOM_SEED,
    }


def _ensure_predictions(predictions: Iterable[float], rows: int) -> np.ndarray:
    values = np.asarray(predictions, dtype=float)
    if len(values) != rows:
        raise BangladeshExperimentError("Prediction row count changed")
    if not np.isfinite(values).all():
        raise BangladeshExperimentError("Non-finite prediction generated")
    return values


def evaluate_grouped_candidate(
    frame: pd.DataFrame,
    task: str,
    spec: CandidateSpec,
    cv_splits: list[tuple[np.ndarray, np.ndarray]],
    feature_order: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate one configuration using development-only grouped OOF rows."""

    target = TASKS[task]["target"]
    features = feature_order or PRIMARY_FEATURES
    predictions = pd.Series(np.nan, index=frame.index, dtype=float)
    fold_records = []
    validation_indices: list[int] = []
    for fold, (train_indices, validation_indices_array) in enumerate(
        cv_splits,
        start=1,
    ):
        train = frame.iloc[train_indices]
        validation = frame.iloc[validation_indices_array]
        train_cows = set(train["cow_id"])
        validation_cows = set(validation["cow_id"])
        if train_cows & validation_cows:
            raise BangladeshExperimentError(
                f"Cow leakage in grouped fold {fold}"
            )
        pipeline = build_pipeline(spec, features)
        pipeline.fit(train[features], train[target])
        fold_predictions = _ensure_predictions(
            pipeline.predict(validation[features]),
            len(validation),
        )
        predictions.iloc[validation_indices_array] = fold_predictions
        validation_indices.extend(validation_indices_array.tolist())
        metrics = regression_metrics(validation[target], fold_predictions)
        fold_records.append(
            {
                "fold": fold,
                "training_rows": len(train),
                "validation_rows": len(validation),
                "training_cows": len(train_cows),
                "validation_cows": len(validation_cows),
                "cow_overlap_count": 0,
                **metrics,
            }
        )
    if len(validation_indices) != len(set(validation_indices)):
        raise BangladeshExperimentError("Grouped validation row assigned twice")
    if predictions.iloc[validation_indices].isna().any():
        raise BangladeshExperimentError("Missing grouped prediction")
    actual = frame.iloc[validation_indices][target]
    predicted = predictions.iloc[validation_indices]
    aggregate = regression_metrics(actual, predicted)
    fold_mae = np.asarray([item["mae"] for item in fold_records], dtype=float)
    fold_r2 = np.asarray([item["r2"] for item in fold_records], dtype=float)
    stability = {
        "fold_mae_mean": float(fold_mae.mean()),
        "fold_mae_standard_deviation": float(fold_mae.std(ddof=1)),
        "fold_mae_coefficient_of_variation": (
            float(fold_mae.std(ddof=1) / fold_mae.mean())
            if fold_mae.mean() else None
        ),
        "fold_r2_mean": float(fold_r2.mean()),
        "fold_r2_standard_deviation": float(fold_r2.std(ddof=1)),
        "all_fold_r2_positive": bool(np.all(fold_r2 > 0)),
    }
    return json_safe(
        {
            "configuration": spec.to_dict(),
            "feature_order": features,
            "aggregate_metrics": aggregate,
            "fold_metrics": fold_records,
            "stability": stability,
            "selection_rows": len(validation_indices),
            "selection_cows": int(
                frame.iloc[validation_indices]["cow_id"].nunique()
            ),
            "predictions": [
                float(value) for value in predicted.to_numpy()
            ],
            "prediction_indices": validation_indices,
        }
    )


def classify_candidate(
    evaluation: dict[str, Any],
    baselines: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply the documented grouped-selection status policy."""

    metrics = evaluation["aggregate_metrics"]
    best_baseline_mae = min(
        item["aggregate_metrics"]["mae"] for item in baselines
    )
    best_baseline_rmse = min(
        item["aggregate_metrics"]["rmse"] for item in baselines
    )
    mae_improvement = (
        (best_baseline_mae - metrics["mae"]) / best_baseline_mae
    )
    rmse_improvement = (
        (best_baseline_rmse - metrics["rmse"]) / best_baseline_rmse
    )
    stability_cv = evaluation["stability"][
        "fold_mae_coefficient_of_variation"
    ]
    stable = (
        stability_cv is not None
        and stability_cv <= MAXIMUM_FOLD_MAE_CV
        and evaluation["stability"]["all_fold_r2_positive"]
    )
    finite = all(
        value is not None and math.isfinite(float(value))
        for value in (
            metrics["mae"],
            metrics["rmse"],
            metrics["r2"],
            metrics["median_absolute_error"],
            metrics["mean_residual"],
        )
    )
    if not finite or metrics["negative_prediction_count"] > 0:
        status = "FAILED"
    elif mae_improvement >= MINIMUM_MEANINGFUL_IMPROVEMENT and (
        rmse_improvement >= MINIMUM_MEANINGFUL_IMPROVEMENT
    ) and metrics["r2"] > 0 and stable:
        status = "BEATS_BASELINE"
    elif mae_improvement > 0 and rmse_improvement > 0 and metrics["r2"] > 0:
        status = "MARGINALLY_BEATS_BASELINE"
    elif not stable and metrics["r2"] > 0:
        status = "UNSTABLE"
    else:
        status = "DOES_NOT_BEAT_BASELINE"
    return {
        "status": status,
        "relative_mae_improvement_vs_best_baseline": float(mae_improvement),
        "relative_rmse_improvement_vs_best_baseline": float(rmse_improvement),
        "stable_across_grouped_folds": stable,
        "finite_predictions": finite,
    }


def select_grouped_candidate(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select using grouped CV only; the final holdout is not accepted here."""

    baselines = [
        item for item in evaluations
        if item["configuration"]["is_baseline"]
    ]
    candidates = [
        item for item in evaluations
        if not item["configuration"]["is_baseline"]
    ]
    if len(baselines) != 2:
        raise BangladeshExperimentError("Mean and median baselines are required")
    for item in candidates:
        item["selection_gate"] = classify_candidate(item, baselines)
    eligible = [
        item for item in candidates
        if item["selection_gate"]["status"] == "BEATS_BASELINE"
    ]
    if not eligible:
        ranked = sorted(
            candidates,
            key=lambda item: (
                item["aggregate_metrics"]["rmse"],
                item["aggregate_metrics"]["mae"],
            ),
        )
        return {
            "selected": None,
            "best_research_configuration": (
                ranked[0]["configuration"]["configuration_id"]
                if ranked else None
            ),
            "selection_status": "NO_CONFIGURATION_PASSED_GROUPED_GATE",
            "selection_reason": (
                "No candidate meaningfully beat both baselines with stable "
                "positive grouped-fold R²."
            ),
        }
    selected = min(
        eligible,
        key=lambda item: (
            item["aggregate_metrics"]["rmse"],
            item["aggregate_metrics"]["mae"],
            item["configuration"]["configuration_id"],
        ),
    )
    return {
        "selected": selected,
        "best_research_configuration": selected["configuration"][
            "configuration_id"
        ],
        "selection_status": "GROUPED_GATE_PASSED",
        "selection_reason": (
            "Lowest grouped-CV RMSE among candidates that meaningfully beat "
            "both baselines, had positive R² in every fold, finite "
            "predictions, no negative predictions, and stable fold MAE."
        ),
    }


def find_spec(task: str, configuration_id: str) -> CandidateSpec:
    """Look up one predeclared configuration."""

    for spec in candidate_specs(task):
        if spec.configuration_id == configuration_id:
            return spec
    raise BangladeshExperimentError(
        f"Unknown {task} configuration: {configuration_id}"
    )


def evaluate_final_holdout(
    frame: pd.DataFrame,
    task: str,
    development_indices: np.ndarray,
    holdout_indices: np.ndarray,
    selected_spec: CandidateSpec,
) -> dict[str, Any]:
    """Fit on development cows and inspect the untouched holdout once."""

    target = TASKS[task]["target"]
    development = frame.iloc[development_indices]
    holdout = frame.iloc[holdout_indices]
    if set(development["cow_id"]) & set(holdout["cow_id"]):
        raise BangladeshExperimentError("Final holdout cow leakage")
    evaluations = {}
    fitted = {}
    for spec in [
        candidate_specs(task)[0],
        candidate_specs(task)[1],
        selected_spec,
    ]:
        pipeline = build_pipeline(spec)
        pipeline.fit(development[PRIMARY_FEATURES], development[target])
        predictions = _ensure_predictions(
            pipeline.predict(holdout[PRIMARY_FEATURES]),
            len(holdout),
        )
        evaluations[spec.configuration_id] = {
            "metrics": regression_metrics(holdout[target], predictions),
            "predictions": predictions.tolist(),
        }
        fitted[spec.configuration_id] = pipeline
    candidate = evaluations[selected_spec.configuration_id]["metrics"]
    baselines = [
        evaluations[candidate_specs(task)[0].configuration_id]["metrics"],
        evaluations[candidate_specs(task)[1].configuration_id]["metrics"],
    ]
    best_mae = min(item["mae"] for item in baselines)
    best_rmse = min(item["rmse"] for item in baselines)
    mae_improvement = (best_mae - candidate["mae"]) / best_mae
    rmse_improvement = (best_rmse - candidate["rmse"]) / best_rmse
    passed = (
        candidate["r2"] > 0
        and mae_improvement >= MINIMUM_MEANINGFUL_IMPROVEMENT
        and rmse_improvement >= MINIMUM_MEANINGFUL_IMPROVEMENT
        and candidate["negative_prediction_count"] == 0
    )
    return {
        "selected_configuration": selected_spec.configuration_id,
        "development_row_count": len(development),
        "development_cow_count": int(development["cow_id"].nunique()),
        "holdout_row_count": len(holdout),
        "holdout_cow_count": int(holdout["cow_id"].nunique()),
        "holdout_cow_ids": sorted(holdout["cow_id"].unique().tolist()),
        "evaluations": evaluations,
        "candidate_relative_mae_improvement": float(mae_improvement),
        "candidate_relative_rmse_improvement": float(rmse_improvement),
        "holdout_gate_passed": bool(passed),
        "decision": "BEATS_BASELINE" if passed else "DOES_NOT_BEAT_BASELINE",
        "selected_pipeline": fitted[selected_spec.configuration_id],
        "holdout_actual": holdout[target].to_numpy(dtype=float),
        "holdout_predictions": np.asarray(
            evaluations[selected_spec.configuration_id]["predictions"],
            dtype=float,
        ),
        "holdout_frame": holdout,
    }


def leave_one_cow_out_analysis(
    frame: pd.DataFrame,
    task: str,
    development_indices: np.ndarray,
    spec: CandidateSpec,
) -> dict[str, Any]:
    """Run a controlled selected-model LOCO analysis on development cows."""

    target = TASKS[task]["target"]
    development = frame.iloc[development_indices].reset_index(drop=True)
    groups = development["cow_id"].astype(str)
    splitter = LeaveOneGroupOut()
    actual_parts = []
    prediction_parts = []
    cow_records = []
    for train_indices, validation_indices in splitter.split(
        development, groups=groups
    ):
        train = development.iloc[train_indices]
        validation = development.iloc[validation_indices]
        pipeline = build_pipeline(spec)
        pipeline.fit(train[PRIMARY_FEATURES], train[target])
        predictions = _ensure_predictions(
            pipeline.predict(validation[PRIMARY_FEATURES]),
            len(validation),
        )
        metrics = regression_metrics(validation[target], predictions)
        cow_records.append(
            {
                "cow_id": str(validation["cow_id"].iloc[0]),
                "rows": len(validation),
                **metrics,
            }
        )
        actual_parts.append(validation[target].to_numpy(dtype=float))
        prediction_parts.append(predictions)
    actual = np.concatenate(actual_parts)
    predictions = np.concatenate(prediction_parts)
    return {
        "method": "LeaveOneGroupOut(cow_id)",
        "fold_count": len(cow_records),
        "aggregate_metrics": regression_metrics(actual, predictions),
        "per_cow_metrics": cow_records,
    }


def grouped_breakdown(
    frame: pd.DataFrame,
    actual: np.ndarray,
    predictions: np.ndarray,
    field: str,
) -> list[dict[str, Any]]:
    """Calculate holdout metrics by THI, genetic group, or cow."""

    records = []
    for value, positions in frame.groupby(field, sort=True).indices.items():
        position_array = np.asarray(list(positions), dtype=int)
        subset_actual = actual[position_array]
        subset_predictions = predictions[position_array]
        metrics = regression_metrics(subset_actual, subset_predictions)
        records.append(
            {
                field: str(value),
                "rows": len(position_array),
                **metrics,
            }
        )
    return records


def feature_analysis(
    pipeline: Pipeline,
    holdout: pd.DataFrame,
    task: str,
) -> dict[str, Any]:
    """Compute post-holdout descriptive permutation importance."""

    target = TASKS[task]["target"]
    result = permutation_importance(
        pipeline,
        holdout[PRIMARY_FEATURES],
        holdout[target],
        scoring="neg_mean_absolute_error",
        n_repeats=30,
        random_state=RANDOM_SEED,
        n_jobs=1,
    )
    importance = [
        {
            "feature": feature,
            "importance_mean_mae_increase": float(
                result.importances_mean[index]
            ),
            "importance_standard_deviation": float(
                result.importances_std[index]
            ),
        }
        for index, feature in enumerate(PRIMARY_FEATURES)
    ]
    predicted = pipeline.predict(holdout[PRIMARY_FEATURES])
    summary = (
        holdout.assign(prediction=predicted)
        .groupby(PRIMARY_FEATURES, sort=True)
        .agg(
            rows=(target, "size"),
            actual_mean=(target, "mean"),
            prediction_mean=("prediction", "mean"),
        )
        .reset_index()
        .to_dict(orient="records")
    )
    return {
        "method": (
            "Permutation importance on the final complete-cow holdout using "
            "negative MAE; descriptive, not causal."
        ),
        "importance": sorted(
            importance,
            key=lambda item: item["importance_mean_mae_increase"],
            reverse=True,
        ),
        "category_prediction_summary": summary,
    }


def save_and_reload_candidate(
    pipeline: Pipeline,
    artifact_path: Path,
    X_sample: pd.DataFrame,
) -> dict[str, Any]:
    """Persist a candidate and verify exact controlled-sample predictions."""

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    before = _ensure_predictions(pipeline.predict(X_sample), len(X_sample))
    joblib.dump(pipeline, artifact_path, compress=3)
    loaded = joblib.load(artifact_path)
    after = _ensure_predictions(loaded.predict(X_sample), len(X_sample))
    identical = bool(np.allclose(before, after, rtol=0.0, atol=1e-12))
    if not identical:
        raise BangladeshExperimentError(
            f"Reloaded predictions differ: {artifact_path}"
        )
    return {
        "artifact_path": str(artifact_path),
        "artifact_sha256": sha256_file(artifact_path),
        "artifact_size_bytes": artifact_path.stat().st_size,
        "reload_predictions_identical": identical,
        "controlled_sample_rows": len(X_sample),
        "feature_order": list(X_sample.columns),
    }


def flatten_candidate_metrics(
    evaluations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flatten grouped evaluation rows for the required CSV reports."""

    rows = []
    for item in evaluations:
        gate = item.get("selection_gate", {})
        metrics = item["aggregate_metrics"]
        stability = item["stability"]
        rows.append(
            {
                "configuration_id": item["configuration"]["configuration_id"],
                "algorithm": item["configuration"]["algorithm"],
                "parameters_json": json.dumps(
                    item["configuration"]["parameters"],
                    sort_keys=True,
                ),
                "is_baseline": item["configuration"]["is_baseline"],
                "group_cv_mae": metrics["mae"],
                "group_cv_rmse": metrics["rmse"],
                "group_cv_r2": metrics["r2"],
                "group_cv_median_absolute_error": metrics[
                    "median_absolute_error"
                ],
                "group_cv_mean_residual": metrics["mean_residual"],
                "minimum_prediction": metrics["minimum_prediction"],
                "maximum_prediction": metrics["maximum_prediction"],
                "negative_prediction_count": metrics[
                    "negative_prediction_count"
                ],
                "fold_mae_standard_deviation": stability[
                    "fold_mae_standard_deviation"
                ],
                "fold_mae_coefficient_of_variation": stability[
                    "fold_mae_coefficient_of_variation"
                ],
                "all_fold_r2_positive": stability[
                    "all_fold_r2_positive"
                ],
                "status": (
                    "BASELINE"
                    if item["configuration"]["is_baseline"]
                    else gate.get("status", "FAILED")
                ),
                "relative_mae_improvement_vs_best_baseline": gate.get(
                    "relative_mae_improvement_vs_best_baseline"
                ),
                "relative_rmse_improvement_vs_best_baseline": gate.get(
                    "relative_rmse_improvement_vs_best_baseline"
                ),
            }
        )
    return rows


def smoke_validate() -> dict[str, Any]:
    """Fit tiny grouped development-only samples before a full experiment."""

    contract = load_contract()
    source, source_metadata = load_source_frame()
    results = {}
    for task in TASKS:
        frame = build_task_frame(source, task)
        assignments = create_group_assignments(frame)
        train_indices, validation_indices = assignments["cv_splits"][0]
        # Use only the first grouped fold; no holdout target is inspected.
        train = frame.iloc[train_indices]
        validation = frame.iloc[validation_indices]
        spec = next(
            item for item in candidate_specs(task)
            if item.algorithm == "Ridge" and item.parameters == {"alpha": 1.0}
        )
        pipeline = build_pipeline(spec)
        pipeline.fit(train[PRIMARY_FEATURES], train[TASKS[task]["target"]])
        predictions = _ensure_predictions(
            pipeline.predict(validation[PRIMARY_FEATURES]),
            len(validation),
        )
        unknown = pd.DataFrame(
            {
                "genetic_group": ["UNKNOWN_HF_GROUP"],
                "thi_category": ["UNKNOWN_THI"],
            }
        )
        unknown_prediction = _ensure_predictions(
            pipeline.predict(unknown), 1
        )
        results[task] = {
            "status": "PASSED",
            "training_rows": len(train),
            "training_cows": int(train["cow_id"].nunique()),
            "validation_rows": len(validation),
            "validation_cows": int(validation["cow_id"].nunique()),
            "cow_overlap_count": len(
                set(train["cow_id"]) & set(validation["cow_id"])
            ),
            "predictions_finite": bool(np.isfinite(predictions).all()),
            "unknown_categories_transform_safely": bool(
                np.isfinite(unknown_prediction).all()
            ),
        }
    return {
        "status": "PASSED",
        "contract_version": contract["contract_version"],
        "source_sha256": source_metadata["source_sha256"],
        "holdout_targets_inspected": False,
        "tasks": results,
    }


__all__ = [
    "BangladeshExperimentError",
    "CONTRACT_PATH",
    "CandidateSpec",
    "LINEAGE_FIELDS",
    "MINIMUM_MEANINGFUL_IMPROVEMENT",
    "PRIMARY_FEATURES",
    "PROCESSED_DIR",
    "RANDOM_SEED",
    "TASKS",
    "build_pipeline",
    "build_task_frame",
    "candidate_specs",
    "classify_candidate",
    "create_group_assignments",
    "evaluate_final_holdout",
    "evaluate_grouped_candidate",
    "feature_analysis",
    "find_spec",
    "flatten_candidate_metrics",
    "grouped_breakdown",
    "leave_one_cow_out_analysis",
    "load_contract",
    "load_source_frame",
    "save_and_reload_candidate",
    "select_grouped_candidate",
    "smoke_validate",
    "utc_now",
    "validate_group_assignments",
    "write_processed_task_frame",
]
