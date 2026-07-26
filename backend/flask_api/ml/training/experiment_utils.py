"""Shared manifest-locked Phase 4 experiment utilities."""

from __future__ import annotations

import hashlib
import json
import platform
import struct
import time
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config.settings import (
    FLASK_API_DIR,
    MILK_YIELD_DATASET_PATH,
    MILK_YIELD_MODEL_PATH,
    ML_REPORTS_DIR,
    PROJECT_ROOT,
)
from ml.preprocessing.column_mapper import map_dataset_columns
from ml.preprocessing.data_cleaner import clean_data
from ml.preprocessing.data_loader import load_dataset
from ml.preprocessing.feature_builder import (
    BASE_NUMERIC_FEATURES,
    build_features,
    get_model_spec,
    load_model_contract,
)
from ml.preprocessing.preprocessing_factory import (
    build_linear_preprocessor,
    build_tree_preprocessor,
)
from ml.training.experiment_types import (
    CandidateConfig,
    CandidateEvaluation,
    ExperimentData,
)
from ml.training.metrics import json_safe
from ml.training.model_registry import create_estimator, registry_snapshot


RANDOM_SEED = 42
EXPECTED_PRIMARY_SHA256 = (
    "26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3"
)
EXPECTED_EXISTING_MODEL_SHA256 = (
    "B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA"
)
SPLIT_MANIFEST_PATH = ML_REPORTS_DIR / "data_split_manifest.csv"
SPLIT_SUMMARY_PATH = ML_REPORTS_DIR / "data_split_summary.json"
FOLD_MANIFEST_PATH = ML_REPORTS_DIR / "feed_type_oof_fold_manifest.csv"
FOLD_SUMMARY_PATH = ML_REPORTS_DIR / "feed_type_oof_fold_summary.json"
CANDIDATE_DIR = FLASK_API_DIR / "ml" / "models" / "candidates" / "phase4"
FAILED_EXPERIMENT_DIR = (
    FLASK_API_DIR / "ml" / "models" / "experiments" / "failed" / "phase4"
)
PHASE4_RUNNER_VERSION = "phase4_runner_v1"


class Phase4ExperimentError(RuntimeError):
    """Raised when a critical controlled-experiment rule fails."""


def utc_now() -> str:
    """Return an explicit UTC timestamp."""

    return datetime.now(UTC).isoformat()


def sha256_file(path: str | Path) -> str:
    """Return an uppercase SHA-256 for a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def stable_json_hash(value: Any) -> str:
    """Hash a deterministic strict-JSON representation."""

    rendered = json.dumps(
        json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()


def write_json(path: str | Path, value: Any) -> None:
    """Write strict JSON with no NaN or Infinity values."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            json_safe(value),
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_locked_selection(path: str | Path, value: dict[str, Any]) -> None:
    """Create the model-selection lock exactly once.

    The final test stage must never silently replace this file. A later
    correction requires a separate amendment record.
    """

    required = {
        "selected_classifier_configuration",
        "selected_feed_quantity_design",
        "selected_feed_quantity_configuration",
        "selected_milk_yield_configuration",
        "selected_milk_yield_feature_version",
        "validation_selections",
        "random_seed",
        "contract_version",
        "split_manifest_sha256",
        "dataset_sha256",
        "selection_timestamp",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise Phase4ExperimentError(
            "Selection lock is missing required field(s): "
            + ", ".join(missing)
        )
    target = Path(path)
    if target.exists():
        raise Phase4ExperimentError(
            "Selection lock already exists and must not be silently edited: "
            f"{target}"
        )
    write_json(target, value)


def validate_candidate_metadata(value: dict[str, Any]) -> None:
    """Validate the required candidate-only metadata safety fields."""

    required = {
        "artifact_status",
        "model_task",
        "model_algorithm",
        "hyperparameters",
        "feature_order",
        "target",
        "preprocessing_description",
        "dataset_source",
        "synthetic_data_declaration",
        "dataset_checksum",
        "split_manifest_hash",
        "contract_version",
        "random_seed",
        "training_row_count",
        "validation_row_count",
        "test_row_count",
        "validation_metrics",
        "test_metrics",
        "baseline_metrics",
        "library_versions",
        "training_timestamp",
        "training_duration_seconds",
        "known_limitations",
        "deployment_approved",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise Phase4ExperimentError(
            "Candidate metadata is missing required field(s): "
            + ", ".join(missing)
        )
    if value["artifact_status"] != "CANDIDATE_ONLY":
        raise Phase4ExperimentError(
            "Eligible metadata must use artifact_status CANDIDATE_ONLY"
        )
    if value["deployment_approved"] is not False:
        raise Phase4ExperimentError(
            "Candidate metadata must set deployment_approved to false"
        )
    warning = str(value["synthetic_data_declaration"]).casefold()
    if "synthetic" not in warning or "prototype" not in warning:
        raise Phase4ExperimentError(
            "Candidate metadata lacks a clear synthetic prototype warning"
        )


def write_csv_records(
    path: str | Path,
    records: list[dict[str, Any]],
) -> None:
    """Write deterministic candidate or feature-importance records."""

    if not records:
        raise ValueError(f"Refusing to write an empty CSV report: {path}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(target, index=False, lineterminator="\n")


def library_versions() -> dict[str, str]:
    """Record relevant runtime versions without optional packages."""

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }


def configuration_hash() -> str:
    """Hash the registry and approved immutable experiment inputs."""

    contract = load_model_contract()
    payload = {
        "runner_version": PHASE4_RUNNER_VERSION,
        "random_seed": RANDOM_SEED,
        "contract_version": contract["contract_version"],
        "registry": registry_snapshot(),
        "dataset_sha256": EXPECTED_PRIMARY_SHA256,
        "split_manifest_sha256": sha256_file(SPLIT_MANIFEST_PATH),
        "fold_manifest_sha256": sha256_file(FOLD_MANIFEST_PATH),
    }
    return stable_json_hash(payload)


def _validate_manifest_integrity(
    split_manifest: pd.DataFrame,
    fold_manifest: pd.DataFrame,
) -> dict[str, Any]:
    expected_split_columns = {
        "source_row_number",
        "cattle_id",
        "observation_date",
        "split",
        "random_seed",
        "split_version",
    }
    expected_fold_columns = {
        "source_row_number",
        "cattle_id",
        "training_fold",
        "random_seed",
        "fold_version",
    }
    if set(split_manifest.columns) != expected_split_columns:
        raise Phase4ExperimentError("Split manifest columns changed after Phase 3")
    if set(fold_manifest.columns) != expected_fold_columns:
        raise Phase4ExperimentError("OOF fold manifest columns changed after Phase 3")
    if len(split_manifest) != 250_000:
        raise Phase4ExperimentError("Split manifest must contain 250,000 rows")
    if split_manifest["source_row_number"].duplicated().any():
        raise Phase4ExperimentError("Split manifest has duplicate assignments")
    if split_manifest["split"].isna().any():
        raise Phase4ExperimentError("Split manifest has missing assignments")
    counts = split_manifest["split"].value_counts().to_dict()
    expected_counts = {"train": 175_000, "validation": 37_500, "test": 37_500}
    if counts != expected_counts:
        raise Phase4ExperimentError(
            f"Split counts differ from Phase 3: {counts}"
        )
    cattle_overlap = int(
        (
            split_manifest.groupby("cattle_id")["split"]
            .nunique()
            .gt(1)
        ).sum()
    )
    if cattle_overlap:
        raise Phase4ExperimentError("Cattle_ID overlaps across split partitions")
    if len(fold_manifest) != 175_000:
        raise Phase4ExperimentError("OOF fold manifest must contain 175,000 rows")
    if fold_manifest["source_row_number"].duplicated().any():
        raise Phase4ExperimentError("A training row has multiple OOF folds")
    fold_counts = fold_manifest["training_fold"].value_counts().sort_index().to_dict()
    if fold_counts != {1: 35_000, 2: 35_000, 3: 35_000, 4: 35_000, 5: 35_000}:
        raise Phase4ExperimentError(f"OOF fold counts changed: {fold_counts}")
    training_rows = set(
        split_manifest.loc[
            split_manifest["split"] == "train", "source_row_number"
        ]
    )
    if training_rows != set(fold_manifest["source_row_number"]):
        raise Phase4ExperimentError(
            "OOF fold rows do not exactly match the training partition"
        )
    return {
        "split_counts": expected_counts,
        "fold_counts": {str(key): int(value) for key, value in fold_counts.items()},
        "duplicate_split_assignments": 0,
        "missing_split_assignments": 0,
        "cattle_id_overlap_count": cattle_overlap,
        "all_training_rows_have_one_fold": True,
    }


def load_experiment_data() -> ExperimentData:
    """Load, validate, clean, and partition data by the locked manifests."""

    required_paths = [
        MILK_YIELD_DATASET_PATH,
        MILK_YIELD_MODEL_PATH,
        FLASK_API_DIR / "config" / "model_contract.json",
        FLASK_API_DIR / "config" / "column_aliases.json",
        SPLIT_MANIFEST_PATH,
        SPLIT_SUMMARY_PATH,
        FOLD_MANIFEST_PATH,
        FOLD_SUMMARY_PATH,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise Phase4ExperimentError(
            "Required Phase 4 input is missing: " + ", ".join(missing)
        )

    dataset_hash = sha256_file(MILK_YIELD_DATASET_PATH)
    if dataset_hash != EXPECTED_PRIMARY_SHA256:
        raise Phase4ExperimentError("Primary dataset checksum changed")
    existing_model_hash = sha256_file(MILK_YIELD_MODEL_PATH)
    if existing_model_hash != EXPECTED_EXISTING_MODEL_SHA256:
        raise Phase4ExperimentError("Existing production model checksum changed")

    split_summary = json.loads(SPLIT_SUMMARY_PATH.read_text(encoding="utf-8"))
    fold_summary = json.loads(FOLD_SUMMARY_PATH.read_text(encoding="utf-8"))
    split_manifest = pd.read_csv(SPLIT_MANIFEST_PATH)
    fold_manifest = pd.read_csv(FOLD_MANIFEST_PATH)
    manifest_checks = _validate_manifest_integrity(
        split_manifest, fold_manifest
    )
    if (
        sha256_file(SPLIT_MANIFEST_PATH)
        != split_summary["reproducibility_hash_sha256"]
    ):
        raise Phase4ExperimentError("Split manifest hash differs from its summary")
    if (
        sha256_file(FOLD_MANIFEST_PATH)
        != fold_summary["reproducibility_hash_sha256"]
    ):
        raise Phase4ExperimentError("Fold manifest hash differs from its summary")

    loaded = load_dataset(MILK_YIELD_DATASET_PATH)
    mapped = map_dataset_columns(
        loaded.dataframe,
        required_columns=[
            "cattle_id",
            "breed",
            "age_months",
            "weight_kg",
            "lactation_stage",
            "days_in_milk",
            "previous_week_avg_yield_l",
            "body_condition_score",
            "ambient_temperature_c",
            "humidity_percent",
            "feed_type",
            "feed_quantity_kg",
            "milk_yield_l",
        ],
        raise_on_missing=True,
    )
    canonical = mapped.dataframe.assign(
        source_row_number=np.arange(1, len(mapped.dataframe) + 1)
    )
    cleaned = clean_data(canonical)
    if not cleaned.issues.empty and (
        cleaned.issues["severity"] == "ERROR"
    ).any():
        raise Phase4ExperimentError(
            "Hard-invalid cleaning issues appeared after Phase 3"
        )
    canonical = cleaned.dataframe

    if not np.array_equal(
        canonical["source_row_number"].to_numpy(),
        split_manifest["source_row_number"].to_numpy(),
    ):
        raise Phase4ExperimentError("Source-row order does not match split manifest")
    if not np.array_equal(
        canonical["cattle_id"].astype(str).to_numpy(),
        split_manifest["cattle_id"].astype(str).to_numpy(),
    ):
        raise Phase4ExperimentError("Cattle_ID order does not match split manifest")

    split_values = split_manifest["split"].to_numpy()
    train = canonical.loc[split_values == "train"].copy()
    validation = canonical.loc[split_values == "validation"].copy()
    test = canonical.loc[split_values == "test"].copy()
    contract = load_model_contract()

    expected_features = [
        "breed",
        "age_months",
        "weight_kg",
        "lactation_stage",
        "days_in_milk",
        "previous_week_avg_yield_l",
        "body_condition_score",
        "ambient_temperature_c",
        "humidity_percent",
    ]
    feature_checks = {}
    for model_name in (
        "feed_type_classifier",
        "feed_quantity_regressor_design_a",
        "milk_yield_regressor",
    ):
        built = build_features(train.head(20), model_name)
        if built.feature_names != expected_features:
            raise Phase4ExperimentError(
                f"Feature order changed for {model_name}"
            )
        if built.target_name in built.X.columns:
            raise Phase4ExperimentError(f"Target leakage in {model_name}")
        feature_checks[model_name] = built.feature_names

    metadata = {
        "dataset_path": str(MILK_YIELD_DATASET_PATH),
        "dataset_sha256": dataset_hash,
        "existing_model_path": str(MILK_YIELD_MODEL_PATH),
        "existing_model_sha256_before": existing_model_hash,
        "row_count": len(canonical),
        "column_count": loaded.metadata.column_count,
        "contract_version": contract["contract_version"],
        "split_manifest_sha256": sha256_file(SPLIT_MANIFEST_PATH),
        "fold_manifest_sha256": sha256_file(FOLD_MANIFEST_PATH),
        "manifest_checks": manifest_checks,
        "feature_order_checks": feature_checks,
        "library_versions": library_versions(),
        "random_seed": RANDOM_SEED,
        "configuration_hash": configuration_hash(),
        "cleaning_issue_count": len(cleaned.issues),
    }
    return ExperimentData(
        full=canonical,
        train=train,
        validation=validation,
        test=test,
        split_manifest=split_manifest,
        fold_manifest=fold_manifest,
        metadata=metadata,
    )


def build_candidate_pipeline(
    config: CandidateConfig,
    model_name: str,
    *,
    feature_names: list[str] | None = None,
) -> Pipeline:
    """Build a fresh preprocessing-plus-estimator pipeline."""

    spec = get_model_spec(model_name)
    selected_features = feature_names or spec.feature_names
    if len(selected_features) != len(set(selected_features)):
        raise Phase4ExperimentError("Duplicate model features are not allowed")
    forbidden = {
        spec.target_name,
        "cattle_id",
        "farm_id",
        "observation_date",
        "feed_type" if model_name != "feed_type_classifier" else spec.target_name,
        "feed_quantity_kg",
        "milk_yield_l",
    }
    leaked = sorted(set(selected_features).intersection(forbidden))
    if leaked:
        raise Phase4ExperimentError(
            "Forbidden feature(s) in training pipeline: " + ", ".join(leaked)
        )

    factory = (
        build_linear_preprocessor
        if config.preprocessor_kind == "linear"
        else build_tree_preprocessor
    )
    preprocessor = factory(model_name)
    filtered_transformers = []
    for name, transformer, columns in preprocessor.transformers:
        retained = [column for column in columns if column in selected_features]
        if retained:
            filtered_transformers.append((name, transformer, retained))
    preprocessor.set_params(transformers=filtered_transformers)
    if config.preprocessor_kind == "dense_tree":
        preprocessor.set_params(sparse_threshold=0.0)

    return Pipeline(
        steps=[
            ("preprocessing", preprocessor),
            ("estimator", create_estimator(config)),
        ]
    )


def fit_candidate(
    config: CandidateConfig,
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_evaluation: pd.DataFrame,
    y_evaluation: pd.Series,
    metric_function: Callable[..., dict[str, Any]],
    *,
    metric_kwargs: dict[str, Any] | None = None,
) -> CandidateEvaluation:
    """Fit on training rows and evaluate on a separate partition."""

    if not X_train.columns.equals(X_evaluation.columns):
        raise Phase4ExperimentError("Training/evaluation feature order differs")
    pipeline = build_candidate_pipeline(
        config,
        model_name,
        feature_names=list(X_train.columns),
    )
    started = time.perf_counter()
    pipeline.fit(X_train, y_train)
    training_seconds = time.perf_counter() - started
    predict_started = time.perf_counter()
    predictions = pipeline.predict(X_evaluation)
    prediction_seconds = time.perf_counter() - predict_started
    ensure_valid_predictions(predictions, expected_rows=len(X_evaluation))
    metrics = metric_function(
        y_evaluation,
        predictions,
        **(metric_kwargs or {}),
    )
    return CandidateEvaluation(
        configuration=config,
        metrics=metrics,
        training_seconds=round(training_seconds, 6),
        prediction_seconds=round(prediction_seconds, 6),
        pipeline=pipeline,
        predictions=predictions,
    )


def ensure_valid_predictions(
    predictions: Iterable[Any],
    *,
    expected_rows: int,
) -> None:
    """Reject wrong-sized or non-finite numeric prediction output."""

    values = np.asarray(predictions)
    if values.shape[0] != expected_rows:
        raise Phase4ExperimentError(
            f"Prediction row count {values.shape[0]} != {expected_rows}"
        )
    if np.issubdtype(values.dtype, np.number) and not np.isfinite(values).all():
        raise Phase4ExperimentError("Predictions contain NaN or infinity")


def stratified_smoke_subset(
    training: pd.DataFrame,
    *,
    rows: int = 4_000,
) -> pd.DataFrame:
    """Select a deterministic Feed_Type-stratified training-only smoke sample."""

    if rows >= len(training):
        return training.copy()
    subset, _ = train_test_split(
        training,
        train_size=rows,
        random_state=RANDOM_SEED,
        stratify=training["feed_type"],
    )
    return subset.sort_values("source_row_number").copy()


def reload_prediction_check(
    pipeline: Pipeline,
    artifact_path: str | Path,
    X_sample: pd.DataFrame,
) -> dict[str, Any]:
    """Persist, reload, and verify identical controlled-sample predictions."""

    target = Path(artifact_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    before = pipeline.predict(X_sample)
    ensure_valid_predictions(before, expected_rows=len(X_sample))
    joblib.dump(pipeline, target, compress=3)
    loaded = joblib.load(target)
    after = loaded.predict(X_sample)
    ensure_valid_predictions(after, expected_rows=len(X_sample))
    if np.issubdtype(np.asarray(before).dtype, np.number):
        identical = bool(np.allclose(before, after, rtol=0.0, atol=1e-12))
    else:
        identical = bool(np.array_equal(before, after))
    if not identical:
        raise Phase4ExperimentError(
            f"Reloaded predictions differ for candidate artifact: {target}"
        )
    feature_names = list(X_sample.columns)
    return {
        "artifact_path": str(target),
        "artifact_sha256": sha256_file(target),
        "artifact_size_bytes": target.stat().st_size,
        "reload_predictions_identical": identical,
        "controlled_sample_rows": len(X_sample),
        "feature_order": feature_names,
        "predictions_finite": True,
    }


def permutation_importance_records(
    pipeline: Pipeline,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
    *,
    scoring: str,
    sample_rows: int = 5_000,
    n_repeats: int = 3,
) -> list[dict[str, Any]]:
    """Calculate canonical-feature permutation importance on validation only."""

    if len(X_validation) > sample_rows:
        sample = X_validation.sample(n=sample_rows, random_state=RANDOM_SEED)
        target = y_validation.loc[sample.index]
    else:
        sample = X_validation
        target = y_validation
    result = permutation_importance(
        pipeline,
        sample,
        target,
        scoring=scoring,
        n_repeats=n_repeats,
        random_state=RANDOM_SEED,
        n_jobs=1,
    )
    records = [
        {
            "canonical_feature": feature,
            "importance_mean": float(result.importances_mean[index]),
            "importance_standard_deviation": float(
                result.importances_std[index]
            ),
            "scoring": scoring,
            "validation_sample_rows": len(sample),
            "n_repeats": n_repeats,
        }
        for index, feature in enumerate(sample.columns)
    ]
    return sorted(
        records,
        key=lambda item: item["importance_mean"],
        reverse=True,
    )


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    payload = chunk_type + data
    return (
        struct.pack(">I", len(data))
        + payload
        + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    )


def write_rgb_png(
    path: str | Path,
    width: int,
    height: int,
    pixels: bytearray,
) -> None:
    """Write an RGB PNG using only the Python standard library."""

    if len(pixels) != width * height * 3:
        raise ValueError("RGB pixel buffer has the wrong length")
    rows = bytearray()
    row_bytes = width * 3
    for row in range(height):
        rows.append(0)
        start = row * row_bytes
        rows.extend(pixels[start : start + row_bytes])
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
        )
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + _png_chunk(b"IEND", b"")
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def write_confusion_matrix_png(
    matrix: list[list[int]] | np.ndarray,
    path: str | Path,
) -> None:
    """Write a simple normalized confusion-matrix heatmap PNG."""

    values = np.asarray(matrix, dtype=float)
    rows, columns = values.shape
    cell = 56
    margin = 24
    width = columns * cell + margin * 2
    height = rows * cell + margin * 2
    pixels = bytearray([255] * width * height * 3)
    row_totals = values.sum(axis=1, keepdims=True)
    normalized = np.divide(
        values,
        row_totals,
        out=np.zeros_like(values),
        where=row_totals != 0,
    )
    for row in range(rows):
        for column in range(columns):
            intensity = float(normalized[row, column])
            color = (
                int(245 - 190 * intensity),
                int(250 - 130 * intensity),
                int(255 - 35 * intensity),
            )
            for y in range(margin + row * cell, margin + (row + 1) * cell):
                for x in range(
                    margin + column * cell, margin + (column + 1) * cell
                ):
                    index = (y * width + x) * 3
                    pixels[index : index + 3] = bytes(color)
    write_rgb_png(path, width, height, pixels)


def write_residual_plot_png(
    actual: Iterable[float],
    predicted: Iterable[float],
    path: str | Path,
    *,
    sample_rows: int = 6_000,
) -> None:
    """Write a small predicted-versus-residual diagnostic PNG."""

    actual_values = np.asarray(actual, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    if len(actual_values) > sample_rows:
        positions = np.linspace(
            0, len(actual_values) - 1, sample_rows, dtype=int
        )
        actual_values = actual_values[positions]
        predicted_values = predicted_values[positions]
    residuals = actual_values - predicted_values
    width, height, margin = 640, 420, 28
    pixels = bytearray([255] * width * height * 3)
    for x in range(margin, width - margin):
        index = ((height // 2) * width + x) * 3
        pixels[index : index + 3] = bytes((205, 205, 205))
    min_x, max_x = float(predicted_values.min()), float(predicted_values.max())
    min_y, max_y = float(residuals.min()), float(residuals.max())
    x_span = max(max_x - min_x, 1e-12)
    y_span = max(max_y - min_y, 1e-12)
    for x_value, y_value in zip(predicted_values, residuals, strict=True):
        x = margin + int((x_value - min_x) / x_span * (width - 2 * margin - 1))
        y = height - margin - int(
            (y_value - min_y) / y_span * (height - 2 * margin - 1)
        )
        for offset_y in (-1, 0, 1):
            for offset_x in (-1, 0, 1):
                px, py = x + offset_x, y + offset_y
                if 0 <= px < width and 0 <= py < height:
                    index = (py * width + px) * 3
                    pixels[index : index + 3] = bytes((35, 105, 180))
    write_rgb_png(path, width, height, pixels)


def clone_and_fit(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> tuple[Pipeline, float]:
    """Clone and refit one locked pipeline on approved training rows only."""

    final_pipeline = clone(pipeline)
    started = time.perf_counter()
    final_pipeline.fit(X_train, y_train)
    return final_pipeline, round(time.perf_counter() - started, 6)


__all__ = [
    "CANDIDATE_DIR",
    "EXPECTED_EXISTING_MODEL_SHA256",
    "EXPECTED_PRIMARY_SHA256",
    "FAILED_EXPERIMENT_DIR",
    "FOLD_MANIFEST_PATH",
    "FOLD_SUMMARY_PATH",
    "PHASE4_RUNNER_VERSION",
    "Phase4ExperimentError",
    "RANDOM_SEED",
    "SPLIT_MANIFEST_PATH",
    "SPLIT_SUMMARY_PATH",
    "build_candidate_pipeline",
    "clone_and_fit",
    "configuration_hash",
    "ensure_valid_predictions",
    "fit_candidate",
    "library_versions",
    "load_experiment_data",
    "permutation_importance_records",
    "reload_prediction_check",
    "sha256_file",
    "stable_json_hash",
    "stratified_smoke_subset",
    "utc_now",
    "validate_candidate_metadata",
    "write_confusion_matrix_png",
    "write_csv_records",
    "write_json",
    "write_locked_selection",
    "write_residual_plot_png",
]
