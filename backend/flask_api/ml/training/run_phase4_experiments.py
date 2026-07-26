"""Run the approved, manifest-locked FarmLite Phase 4 experiments.

Run from ``backend/flask_api`` with::

    python -m ml.training.run_phase4_experiments

This module deliberately has no runtime-inference or Flask integration.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from config.settings import (
    FLASK_API_DIR,
    MILK_YIELD_MODEL_PATH,
    ML_REPORTS_DIR,
    PROJECT_ROOT,
)
from ml.preprocessing.feature_builder import build_features, load_model_contract
from ml.training.experiment_types import (
    CandidateConfig,
    CandidateEvaluation,
    ExperimentData,
    TaskSelection,
)
from ml.training.experiment_utils import (
    CANDIDATE_DIR,
    EXPECTED_EXISTING_MODEL_SHA256,
    PHASE4_RUNNER_VERSION,
    Phase4ExperimentError,
    build_candidate_pipeline,
    clone_and_fit,
    configuration_hash,
    ensure_valid_predictions,
    fit_candidate,
    load_experiment_data,
    permutation_importance_records,
    reload_prediction_check,
    sha256_file,
    stable_json_hash,
    stratified_smoke_subset,
    utc_now,
    validate_candidate_metadata,
    write_confusion_matrix_png,
    write_csv_records,
    write_json,
    write_locked_selection,
    write_residual_plot_png,
)
from ml.training.generate_feed_type_oof_predictions import (
    generate_oof_feed_type_predictions,
)
from ml.training.metrics import (
    classification_beats_baselines,
    classification_metrics,
    regression_beats_baseline,
    regression_metrics,
)
from ml.training.model_registry import (
    RANDOM_SEED,
    candidate_configs,
    get_candidate,
)
from ml.training.train_feed_quantity_regressor import (
    DESIGN_A_MODEL,
    DESIGN_B_MODEL,
    add_predicted_feed_type,
    build_feed_quantity_views,
    evaluate_feed_quantity_candidates,
    feed_quantity_diagnostics,
    render_feed_quantity_report,
    select_feed_quantity_candidate,
)
from ml.training.train_feed_type_classifier import (
    MODEL_NAME as FEED_TYPE_MODEL,
    approved_labels,
    build_classifier_views,
    confidence_audit,
    evaluate_feed_type_candidates,
    render_classifier_report,
    select_feed_type_candidate,
)
from ml.training.train_milk_yield_regressor import (
    MODEL_NAME as MILK_YIELD_MODEL,
    build_milk_yield_views,
    evaluate_milk_ablation,
    evaluate_milk_yield_candidates,
    milk_yield_diagnostics,
    render_ablation_report,
    render_milk_yield_report,
    select_milk_yield_candidate,
)


LOCK_PATH = ML_REPORTS_DIR / "locked_model_selection.json"
PREFLIGHT_PATH = ML_REPORTS_DIR / "phase4_preflight_report.md"
SMOKE_PATH = ML_REPORTS_DIR / "phase4_smoke_test_report.md"
SUMMARY_PATH = ML_REPORTS_DIR / "phase4_training_summary.json"
SYNTHETIC_WARNING = (
    "FarmLite is an undergraduate prototype using publisher-declared "
    "synthetic cattle data. Predictions demonstrate an ML pipeline and are "
    "not veterinary, nutritional, commercial, or real-world feeding guidance."
)
BASE_FEATURES = [
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


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _find(
    evaluations: Iterable[CandidateEvaluation],
    configuration_id: str,
) -> CandidateEvaluation:
    for evaluation in evaluations:
        if evaluation.configuration.configuration_id == configuration_id:
            return evaluation
    raise Phase4ExperimentError(
        f"Missing evaluation for locked configuration: {configuration_id}"
    )


def _preflight_report(data: ExperimentData) -> str:
    checks = data.metadata["manifest_checks"]
    feature_checks = data.metadata["feature_order_checks"]
    versions = data.metadata["library_versions"]
    return "\n".join(
        [
            "# FarmLite Phase 4 Preflight Report",
            "",
            f"- Status: `PASSED`",
            f"- Checked at: `{utc_now()}`",
            f"- Runner: `{PHASE4_RUNNER_VERSION}`",
            f"- Configuration hash: `{data.metadata['configuration_hash']}`",
            f"- Primary dataset SHA-256: `{data.metadata['dataset_sha256']}`",
            (
                "- Existing retained milk-yield model SHA-256: "
                f"`{data.metadata['existing_model_sha256_before']}`"
            ),
            f"- Split manifest SHA-256: `{data.metadata['split_manifest_sha256']}`",
            f"- OOF fold manifest SHA-256: `{data.metadata['fold_manifest_sha256']}`",
            f"- Contract version: `{data.metadata['contract_version']}`",
            "",
            "## Locked Partition Checks",
            "",
            f"- Source rows: {data.metadata['row_count']:,}",
            f"- Training rows: {checks['split_counts']['train']:,}",
            f"- Validation rows: {checks['split_counts']['validation']:,}",
            f"- Test rows: {checks['split_counts']['test']:,}",
            f"- Duplicate split assignments: {checks['duplicate_split_assignments']}",
            f"- Missing split assignments: {checks['missing_split_assignments']}",
            f"- Cattle_ID overlap count: {checks['cattle_id_overlap_count']}",
            (
                "- OOF fold counts: "
                + ", ".join(
                    f"{fold}={count:,}"
                    for fold, count in checks["fold_counts"].items()
                )
            ),
            (
                "- Every training row has exactly one OOF fold: "
                f"{checks['all_training_rows_have_one_fold']}"
            ),
            "",
            "## Feature and Leakage Checks",
            "",
            *[
                f"- `{model}`: `{', '.join(features)}`; target absent from X."
                for model, features in feature_checks.items()
            ],
            (
                "- Design B is separately gated and accepts only an explicit "
                "`predicted_feed_type` in addition to the nine base features."
            ),
            "",
            "## Installed Runtime",
            "",
            *[f"- {name}: `{value}`" for name, value in versions.items()],
            "",
            "No package was installed. XGBoost, LightGBM, CatBoost, matplotlib, "
            "Pillow, pytest, and psutil are not required by this runner.",
            "",
            "The preflight passed before any estimator fit.",
        ]
    )


def _smoke_oof_predictions(
    training: pd.DataFrame,
    evaluation: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """Create small training-only cross-fit predictions for Design B smoke."""

    built_train = build_features(training, FEED_TYPE_MODEL)
    built_evaluation = build_features(evaluation, FEED_TYPE_MODEL)
    config = get_candidate("feed_type_logistic_c1")
    splitter = StratifiedKFold(
        n_splits=4,
        shuffle=True,
        random_state=RANDOM_SEED,
    )
    oof = np.empty(len(training), dtype=object)
    for fit_positions, heldout_positions in splitter.split(
        built_train.X, built_train.y
    ):
        pipeline = build_candidate_pipeline(config, FEED_TYPE_MODEL)
        pipeline.fit(
            built_train.X.iloc[fit_positions],
            built_train.y.iloc[fit_positions],
        )
        oof[heldout_positions] = pipeline.predict(
            built_train.X.iloc[heldout_positions]
        )
    if pd.isna(oof).any():
        raise Phase4ExperimentError(
            "Smoke OOF generation left a row without a prediction"
        )
    final_pipeline = build_candidate_pipeline(config, FEED_TYPE_MODEL)
    final_pipeline.fit(built_train.X, built_train.y)
    evaluation_predictions = final_pipeline.predict(built_evaluation.X)
    return oof, np.asarray(evaluation_predictions)


def _smoke_candidate(
    config: CandidateConfig,
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_evaluation: pd.DataFrame,
    y_evaluation: pd.Series,
    temporary_directory: Path,
) -> dict[str, Any]:
    metric = (
        classification_metrics
        if config.task == "feed_type"
        else regression_metrics
    )
    kwargs = {"labels": approved_labels()} if config.task == "feed_type" else {}
    evaluation = fit_candidate(
        config,
        model_name,
        X_train,
        y_train,
        X_evaluation,
        y_evaluation,
        metric,
        metric_kwargs=kwargs,
    )
    check = reload_prediction_check(
        evaluation.pipeline,
        temporary_directory / f"{config.configuration_id}.joblib",
        X_evaluation.head(12),
    )
    return {
        "configuration_id": config.configuration_id,
        "model_name": model_name,
        "status": "PASSED",
        "training_seconds": evaluation.training_seconds,
        "prediction_seconds": evaluation.prediction_seconds,
        "prediction_row_count": len(evaluation.predictions),
        "predictions_finite": True,
        "serialization_reload_equal": check["reload_predictions_identical"],
    }


def run_smoke_tests(
    data: ExperimentData,
    *,
    tasks: list[str],
    skip_expensive: bool,
) -> tuple[list[dict[str, Any]], bool]:
    """Run candidate compatibility checks on training-only records."""

    smoke = stratified_smoke_subset(data.train, rows=4_000)
    smoke_train, smoke_evaluation = train_test_split(
        smoke,
        test_size=1_000,
        random_state=RANDOM_SEED,
        stratify=smoke["feed_type"],
    )
    smoke_train = smoke_train.sort_values("source_row_number").copy()
    smoke_evaluation = smoke_evaluation.sort_values(
        "source_row_number"
    ).copy()
    records: list[dict[str, Any]] = []
    passed = True
    with tempfile.TemporaryDirectory(prefix="farmlite_phase4_smoke_") as temp:
        temporary_directory = Path(temp)
        task_specs: list[
            tuple[str, str, pd.DataFrame, pd.DataFrame]
        ] = []
        if "feed_type" in tasks:
            task_specs.append(
                ("feed_type", FEED_TYPE_MODEL, smoke_train, smoke_evaluation)
            )
        if "feed_quantity" in tasks:
            task_specs.append(
                (
                    "feed_quantity",
                    DESIGN_A_MODEL,
                    smoke_train,
                    smoke_evaluation,
                )
            )
            oof, validation_predictions = _smoke_oof_predictions(
                smoke_train, smoke_evaluation
            )
            task_specs.append(
                (
                    "feed_quantity",
                    DESIGN_B_MODEL,
                    add_predicted_feed_type(smoke_train, oof),
                    add_predicted_feed_type(
                        smoke_evaluation, validation_predictions
                    ),
                )
            )
        if "milk_yield" in tasks:
            task_specs.append(
                (
                    "milk_yield",
                    MILK_YIELD_MODEL,
                    smoke_train,
                    smoke_evaluation,
                )
            )

        for task, model_name, training, evaluation in task_specs:
            if model_name == FEED_TYPE_MODEL:
                views = build_classifier_views(training, evaluation)
            elif model_name in {DESIGN_A_MODEL, DESIGN_B_MODEL}:
                views = build_feed_quantity_views(
                    training,
                    evaluation,
                    design="A" if model_name == DESIGN_A_MODEL else "B",
                )
            else:
                views = build_milk_yield_views(training, evaluation)
            for config in candidate_configs(
                task, skip_expensive=skip_expensive
            ):
                try:
                    records.append(
                        _smoke_candidate(
                            config,
                            model_name,
                            *views,
                            temporary_directory,
                        )
                    )
                except MemoryError as error:
                    records.append(
                        {
                            "configuration_id": config.configuration_id,
                            "model_name": model_name,
                            "status": "SKIPPED_RESOURCE_LIMIT",
                            "reason": str(error) or "MemoryError",
                        }
                    )
                except Exception as error:  # report compatibility failures
                    passed = False
                    records.append(
                        {
                            "configuration_id": config.configuration_id,
                            "model_name": model_name,
                            "status": "FAILED",
                            "reason": f"{type(error).__name__}: {error}",
                        }
                    )
    return records, passed


def _smoke_report(
    records: list[dict[str, Any]],
    *,
    passed: bool,
    tasks: list[str],
    skip_expensive: bool,
) -> str:
    lines = [
        "# FarmLite Phase 4 Smoke-Test Report",
        "",
        "# SMOKE_TEST_ONLY",
        "",
        f"- Status: `{'PASSED' if passed else 'FAILED'}`",
        "- Source: deterministic Feed_Type-stratified subset of training only",
        "- Rows sampled: 4,000 (3,000 fit; 1,000 internal smoke evaluation)",
        f"- Tasks: {', '.join(tasks)}",
        f"- Expensive candidates skipped by flag: {skip_expensive}",
        (
            "- Design B smoke input uses cross-fitted classifier predictions; "
            "true same-row Feed_Type is not substituted."
        ),
        "- Temporary joblib files were isolated in an auto-removed temp folder.",
        "- Metrics from this run are not final experimental results.",
        "",
        "| Model view | Configuration | Status | Fit s | Predict s | Rows | Reload equal |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| `{record['model_name']}` | "
            f"`{record['configuration_id']}` | {record['status']} | "
            f"{record.get('training_seconds', 0):.4f} | "
            f"{record.get('prediction_seconds', 0):.4f} | "
            f"{record.get('prediction_row_count', 0)} | "
            f"{record.get('serialization_reload_equal', '')} |"
        )
        if record.get("reason"):
            lines.append(f"\nReason: `{record['reason']}`")
    return "\n".join(lines)


def _design_b_is_meaningful(
    design_a: TaskSelection,
    design_b: TaskSelection,
) -> tuple[bool, str]:
    a = design_a.validation_metrics
    b = design_b.validation_metrics
    mae_gain = (a["mae"] - b["mae"]) / a["mae"]
    rmse_gain = (a["rmse"] - b["rmse"]) / a["rmse"]
    r2_gain = b["r2"] - a["r2"]
    meaningful = (
        design_b.beats_baseline_on_validation
        and mae_gain >= 0.01
        and rmse_gain >= 0.01
        and r2_gain >= 0.01
    )
    reason = (
        f"Design B validation changes versus A: MAE {mae_gain:+.2%}, "
        f"RMSE {rmse_gain:+.2%}, R2 {r2_gain:+.6f}. "
    )
    if meaningful:
        reason += (
            "It clears the predeclared meaningful-improvement rule, so Design "
            "B is locked subject to one-time test stability and dependency checks."
        )
    else:
        reason += (
            "It does not clear all 1% MAE/RMSE and +0.01 R2 requirements; "
            "Design A is locked to avoid unjustified classifier dependency."
        )
    return meaningful, reason


def _confidence_report(
    validation_audit: dict[str, Any],
    test_audit: dict[str, Any],
) -> str:
    def section(name: str, audit: dict[str, Any]) -> list[str]:
        if not audit.get("available"):
            return [f"## {name}", "", f"- Unavailable: {audit['reason']}", ""]
        return [
            f"## {name}",
            "",
            f"- Rows: {audit['row_count']:,}",
            (
                "- Mean maximum class probability: "
                f"{audit['mean_maximum_probability']:.6f}"
            ),
            (
                "- Median maximum class probability: "
                f"{audit['median_maximum_probability']:.6f}"
            ),
            (
                "- Maximum-probability range: "
                f"{audit['minimum_maximum_probability']:.6f} to "
                f"{audit['maximum_maximum_probability']:.6f}"
            ),
            (
                "- Interquartile range: "
                f"{audit['p25_maximum_probability']:.6f} to "
                f"{audit['p75_maximum_probability']:.6f}"
            ),
            (
                f"- Below {audit['low_confidence_threshold']:.2f}: "
                f"{audit['low_confidence_prediction_count']:,}"
            ),
            (
                f"- Incorrect at or above {audit['high_confidence_threshold']:.2f}: "
                f"{audit['incorrect_high_confidence_prediction_count']:,}"
            ),
            f"- Limitation: {audit['calibration_limitation']}",
            "",
        ]

    return "\n".join(
        [
            "# FarmLite Feed-Type Probability and Confidence Audit",
            "",
            (
                "This is an analytical audit only. Scores are uncalibrated "
                "model outputs on synthetic data and must not be shown as "
                "scientific confidence."
            ),
            "",
            *section("Validation", validation_audit),
            *section("One-Time Final Test", test_audit),
        ]
    )


def _status_classification(
    selection: TaskSelection,
    test_candidate: dict[str, Any],
    test_most_frequent: dict[str, Any],
    test_stratified: dict[str, Any],
) -> tuple[str, bool]:
    test_beats = classification_beats_baselines(
        test_candidate,
        test_most_frequent,
        test_stratified,
    )
    stable = (
        abs(
            selection.validation_metrics["macro_f1"]
            - test_candidate["macro_f1"]
        )
        <= 0.02
    )
    if not selection.beats_baseline_on_validation or not test_beats:
        return "DOES_NOT_BEAT_BASELINE", False
    if not stable:
        return "UNSTABLE", False
    gain = test_candidate["macro_f1"] - test_stratified["macro_f1"]
    return (
        ("MARGINALLY_BEATS_BASELINE" if gain < 0.02 else "BEATS_BASELINE"),
        True,
    )


def _status_regression(
    selection: TaskSelection,
    test_candidate: dict[str, Any],
    test_baseline: dict[str, Any],
) -> tuple[str, bool]:
    test_beats = regression_beats_baseline(test_candidate, test_baseline)
    validation_mae = selection.validation_metrics["mae"]
    stable = (
        abs(test_candidate["mae"] - validation_mae)
        / max(validation_mae, 1e-12)
        <= 0.20
    )
    if not selection.beats_baseline_on_validation or not test_beats:
        return "DOES_NOT_BEAT_BASELINE", False
    if not stable:
        return "UNSTABLE", False
    relative_gain = (
        test_baseline["mae"] - test_candidate["mae"]
    ) / test_baseline["mae"]
    return (
        (
            "MARGINALLY_BEATS_BASELINE"
            if relative_gain < 0.05
            else "BEATS_BASELINE"
        ),
        True,
    )


def _candidate_metadata(
    *,
    task: str,
    config: CandidateConfig,
    feature_order: list[str],
    target: str,
    data: ExperimentData,
    validation_metrics: dict[str, Any],
    test_metrics: dict[str, Any],
    baseline_metrics: dict[str, Any],
    duration: float,
    dependency: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        "artifact_status": "CANDIDATE_ONLY",
        "model_task": task,
        "model_algorithm": config.algorithm,
        "configuration_id": config.configuration_id,
        "hyperparameters": config.parameters,
        "feature_order": feature_order,
        "target": target,
        "preprocessing_description": (
            "Complete sklearn pipeline using the Phase 3 contract-driven "
            "training-only imputation, missing indicators, one-hot encoding, "
            "and scaling only for linear estimators."
        ),
        "dataset_source": {
            "name": "Cattle Health and Feeding Data",
            "platform": "Kaggle",
            "publisher_account": "ShahHet2812",
            "generation_status": "SYNTHETIC_PUBLISHER_DECLARED",
        },
        "synthetic_data_declaration": SYNTHETIC_WARNING,
        "dataset_checksum": data.metadata["dataset_sha256"],
        "split_manifest_hash": data.metadata["split_manifest_sha256"],
        "contract_version": data.metadata["contract_version"],
        "configuration_hash": data.metadata["configuration_hash"],
        "random_seed": RANDOM_SEED,
        "training_row_count": len(data.train),
        "validation_row_count": len(data.validation),
        "test_row_count": len(data.test),
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "baseline_metrics": baseline_metrics,
        "library_versions": data.metadata["library_versions"],
        "training_timestamp": utc_now(),
        "training_duration_seconds": duration,
        "known_limitations": [
            "Publisher-declared synthetic data with undocumented formulas.",
            "Dataset population is not verified dairy-only.",
            "No veterinary, nutritional, commercial, or scientific validation.",
            "License status remains unresolved.",
            "Candidate has not been integrated, deployed, or approved for production.",
        ],
        "deployment_approved": False,
    }
    if dependency is not None:
        metadata["dependency"] = dependency
    validate_candidate_metadata(metadata)
    return metadata


def _save_candidate(
    *,
    filename: str,
    pipeline: Any,
    X_sample: pd.DataFrame,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    artifact_path = CANDIDATE_DIR / filename
    metadata_path = artifact_path.with_suffix(".metadata.json")
    if artifact_path.exists() or metadata_path.exists():
        raise Phase4ExperimentError(
            "Refusing to overwrite an existing candidate artifact: "
            f"{artifact_path}"
        )
    check = reload_prediction_check(
        pipeline,
        artifact_path,
        X_sample,
    )
    metadata = {
        **metadata,
        "artifact_path": str(artifact_path),
        "artifact_sha256": check["artifact_sha256"],
        "artifact_size_bytes": check["artifact_size_bytes"],
        "reload_verification": check,
    }
    validate_candidate_metadata(metadata)
    write_json(metadata_path, metadata)
    return {
        "artifact_path": str(artifact_path),
        "metadata_path": str(metadata_path),
        "artifact_sha256": check["artifact_sha256"],
        "reload_predictions_identical": check[
            "reload_predictions_identical"
        ],
    }


def _model_card(
    *,
    title: str,
    purpose: str,
    features: list[str],
    target: str,
    config: CandidateConfig,
    selection: TaskSelection,
    test_metrics: dict[str, Any],
    baseline_test_metrics: dict[str, Any],
    status: str,
    artifact: dict[str, Any] | None,
    next_action: str,
) -> str:
    deployment = (
        "CANDIDATE_ONLY - integration review is not yet approved."
        if artifact
        else "NO ELIGIBLE CANDIDATE - research-only result."
    )
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Model Purpose",
            "",
            purpose,
            "",
            "## Intended Use",
            "",
            "Undergraduate demonstration of a reproducible synthetic tabular ML workflow.",
            "",
            "## Out-of-Scope Use",
            "",
            "Veterinary, nutritional, commercial, farm-control, safety-critical, "
            "or real-world feeding decisions.",
            "",
            "## Synthetic-Data Warning",
            "",
            SYNTHETIC_WARNING,
            "",
            "## Inputs and Target",
            "",
            f"- Features: {', '.join(f'`{item}`' for item in features)}",
            f"- Target: `{target}`",
            "",
            "## Algorithm and Training",
            "",
            f"- Configuration: `{config.configuration_id}`",
            f"- Algorithm: {config.algorithm}",
            f"- Hyperparameters: `{json.dumps(config.parameters, sort_keys=True)}`",
            "- Fit partition: locked 175,000-row training split only.",
            "- Selection partition: locked 37,500-row validation split.",
            "- Final evaluation: one-time locked 37,500-row test split.",
            "- Random seed: 42 where supported.",
            "",
            "## Results and Baseline Comparison",
            "",
            f"- Validation metrics: `{json.dumps(selection.validation_metrics, sort_keys=True)}`",
            f"- Final test metrics: `{json.dumps(test_metrics, sort_keys=True)}`",
            f"- Final baseline metrics: `{json.dumps(baseline_test_metrics, sort_keys=True)}`",
            f"- Status: `{status}`",
            "",
            "## Known and Ethical Limitations",
            "",
            "- Synthetic generation formulas and dependency structure are undocumented.",
            "- Feed and yield labels are not expert-validated recommendations or measurements.",
            "- Feature importance is association, not causation or biological evidence.",
            "- Dataset licensing remains unresolved.",
            "",
            "## Dairy-Scope Limitation",
            "",
            "The interface is scoped to dairy cattle, while the synthetic dataset "
            "contains cattle whose production purpose is not fully documented.",
            "",
            "## Deployment Status",
            "",
            deployment,
            "",
            "## Recommended Next Action",
            "",
            next_action,
        ]
    )


def _final_test_report(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# FarmLite Phase 4 One-Time Final Test Evaluation",
        "",
        (
            "The selected configurations and both predeclared A/B or ablation "
            "variants were written to `locked_model_selection.json` before "
            "these test targets were scored. Test results did not change selection."
        ),
        "",
        "| Task | Baseline | Selected model | Validation metric | Test metric | Status |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['task']} | {row['baseline']} | "
            f"`{row['selected_model']}` | {row['validation_metric']} | "
            f"{row['test_metric']} | `{row['status']}` |"
        )
    return "\n".join(lines)


def _design_comparison(
    *,
    selection_a: TaskSelection,
    selection_b: TaskSelection,
    test_a: dict[str, Any],
    test_b: dict[str, Any],
    locked_design: str,
    lock_reason: str,
    oof_metrics: dict[str, Any],
) -> str:
    validation_improvement = {
        key: selection_a.validation_metrics[key]
        - selection_b.validation_metrics[key]
        for key in ("mae", "rmse")
    }
    validation_r2 = (
        selection_b.validation_metrics["r2"]
        - selection_a.validation_metrics["r2"]
    )
    test_improvement = {
        key: test_a[key] - test_b[key] for key in ("mae", "rmse")
    }
    test_r2 = test_b["r2"] - test_a["r2"]
    same_direction = (
        np.sign(validation_improvement["mae"])
        == np.sign(test_improvement["mae"])
        and np.sign(validation_improvement["rmse"])
        == np.sign(test_improvement["rmse"])
    )
    return "\n".join(
        [
            "# FarmLite Feed-Quantity Design A/B Comparison",
            "",
            "| Split | Design A MAE | Design B MAE | Design A RMSE | Design B RMSE | Design A R2 | Design B R2 |",
            "|---|---:|---:|---:|---:|---:|---:|",
            (
                f"| Validation | {selection_a.validation_metrics['mae']:.6f} | "
                f"{selection_b.validation_metrics['mae']:.6f} | "
                f"{selection_a.validation_metrics['rmse']:.6f} | "
                f"{selection_b.validation_metrics['rmse']:.6f} | "
                f"{selection_a.validation_metrics['r2']:.6f} | "
                f"{selection_b.validation_metrics['r2']:.6f} |"
            ),
            (
                f"| Test | {test_a['mae']:.6f} | {test_b['mae']:.6f} | "
                f"{test_a['rmse']:.6f} | {test_b['rmse']:.6f} | "
                f"{test_a['r2']:.6f} | {test_b['r2']:.6f} |"
            ),
            "",
            "## Decision",
            "",
            f"- Locked design: **Design {locked_design}**.",
            f"- Validation decision: {lock_reason}",
            (
                "- Validation B-minus-A effect: "
                f"MAE improvement {validation_improvement['mae']:+.6f}, "
                f"RMSE improvement {validation_improvement['rmse']:+.6f}, "
                f"R2 improvement {validation_r2:+.6f}."
            ),
            (
                "- Test B-minus-A effect: "
                f"MAE improvement {test_improvement['mae']:+.6f}, "
                f"RMSE improvement {test_improvement['rmse']:+.6f}, "
                f"R2 improvement {test_r2:+.6f}."
            ),
            f"- Validation/test improvement direction consistent: {same_direction}.",
            (
                "- OOF classifier diagnostic Macro F1: "
                f"{oof_metrics['macro_f1']:.6f}. Classifier errors therefore "
                "propagate into Design B's categorical input."
            ),
            (
                "- Design B is not preferred for a tiny metric difference; it "
                "must justify its extra classifier dependency and OOF complexity."
            ),
        ]
    )


def _phase5_gate(
    *,
    classifier_status: str,
    classifier_metrics: dict[str, Any],
    feed_status: str,
    milk_status: str,
    artifacts: dict[str, Any],
    existing_hash_ok: bool,
    ablation_complete: bool,
) -> tuple[str, str]:
    accepted = sum(
        status in {"BEATS_BASELINE", "MARGINALLY_BEATS_BASELINE"}
        for status in (classifier_status, feed_status, milk_status)
    )
    if accepted == 3:
        recommendation = "READY_FOR_PHASE_5_INTEGRATION_REVIEW"
    elif accepted:
        recommendation = "READY_FOR_PARTIAL_INTEGRATION_REVIEW"
    elif milk_status == "DOES_NOT_BEAT_BASELINE":
        recommendation = "DATASET_REPLACEMENT_RECOMMENDED"
    else:
        recommendation = "MODEL_REDESIGN_REQUIRED"
    rows = [
        (
            "Feed classifier beats baseline",
            (
                "PASSED"
                if classifier_status
                in {"BEATS_BASELINE", "MARGINALLY_BEATS_BASELINE"}
                else "FAILED"
            ),
            classifier_status,
            "Review only if candidate artifact exists.",
        ),
        (
            "Feed classifier predicts all relevant classes",
            (
                "PASSED"
                if classifier_metrics["predicted_class_count"]
                == len(approved_labels())
                else "FAILED"
            ),
            f"{classifier_metrics['predicted_class_count']} predicted classes",
            "Replace/redesign data or classifier if collapsed.",
        ),
        (
            "Feed quantity beats baseline",
            (
                "PASSED"
                if feed_status
                in {"BEATS_BASELINE", "MARGINALLY_BEATS_BASELINE"}
                else "FAILED"
            ),
            feed_status,
            "Review only the locked eligible design.",
        ),
        ("Design A/B comparison completed", "PASSED", "Report created", "None."),
        (
            "Milk yield beats baseline",
            (
                "PASSED"
                if milk_status
                in {"BEATS_BASELINE", "MARGINALLY_BEATS_BASELINE"}
                else "FAILED"
            ),
            milk_status,
            "Interpret only as synthetic prototype performance.",
        ),
        (
            "Milk-yield ablation completed",
            "PASSED" if ablation_complete else "FAILED",
            "Validation and test compared",
            "Retain transparency warning.",
        ),
        (
            "Validation/test stability acceptable",
            (
                "PASSED_WITH_LIMITATIONS"
                if all(
                    status != "UNSTABLE"
                    for status in (classifier_status, feed_status, milk_status)
                )
                else "FAILED"
            ),
            f"{classifier_status}; {feed_status}; {milk_status}",
            "Do not tune against test.",
        ),
        (
            "Candidate artifacts reload successfully",
            (
                "NOT_APPLICABLE"
                if not artifacts
                else (
                    "PASSED"
                    if all(
                    item["reload_predictions_identical"]
                    for item in artifacts.values()
                    )
                    else "FAILED"
                )
            ),
            f"{len(artifacts)} eligible artifact(s)",
            "Only integrate separately approved candidates.",
        ),
        (
            "Existing production model preserved",
            "PASSED" if existing_hash_ok else "FAILED",
            f"SHA-256 unchanged: {existing_hash_ok}",
            "Stop immediately if false.",
        ),
        (
            "Synthetic limitation documented",
            "PASSED",
            "Reports, metadata, and model cards",
            "Keep warning visible in any later integration.",
        ),
        (
            "Dairy-scope limitation documented",
            "PASSED_WITH_LIMITATIONS",
            "Dataset is not verified dairy-only",
            "Acquire a scoped dataset before real-world claims.",
        ),
        (
            "Integration not yet performed",
            "PASSED",
            "Phase 4 only",
            "Await explicit Phase 5 approval.",
        ),
    ]
    lines = [
        "# FarmLite Phase 5 Integration Approval Gate",
        "",
        "| Check | Status | Evidence | Required action |",
        "|---|---|---|---|",
        *[
            f"| {check} | `{status}` | {evidence} | {action} |"
            for check, status, evidence, action in rows
        ],
        "",
        f"## Final Recommendation: `{recommendation}`",
        "",
        "Phase 5 has not begun. No Flask or React integration was performed.",
    ]
    return "\n".join(lines), recommendation


def run_full_experiment(
    data: ExperimentData,
    *,
    skip_expensive: bool,
) -> dict[str, Any]:
    """Run validation selection, lock it, and score final test once."""

    if LOCK_PATH.exists():
        raise Phase4ExperimentError(
            "A Phase 4 selection lock already exists. The final test must not "
            "be rerun or used to revise selection. Create an explicit "
            "amendment workflow only for a proven implementation error."
        )
    print("PHASE4: validation candidate evaluation started", flush=True)

    classifier_evaluations = evaluate_feed_type_candidates(
        data.train,
        data.validation,
        skip_expensive=skip_expensive,
    )
    selected_classifier, classifier_selection = select_feed_type_candidate(
        classifier_evaluations
    )
    classifier_views = build_classifier_views(data.train, data.validation)
    classifier_importance = permutation_importance_records(
        selected_classifier.pipeline,
        classifier_views[2],
        classifier_views[3],
        scoring="f1_macro",
    )
    write_csv_records(
        ML_REPORTS_DIR / "feed_type_candidate_metrics.csv",
        [item.to_record() for item in classifier_evaluations],
    )
    write_csv_records(
        ML_REPORTS_DIR / "feed_type_feature_importance.csv",
        classifier_importance,
    )
    _write_text(
        ML_REPORTS_DIR / "feed_type_classifier_report.md",
        render_classifier_report(
            classifier_evaluations,
            classifier_selection,
            importance_records=classifier_importance,
        ),
    )
    write_confusion_matrix_png(
        selected_classifier.metrics["confusion_matrix"],
        ML_REPORTS_DIR / "feed_type_validation_confusion_matrix.png",
    )
    validation_confidence = confidence_audit(
        selected_classifier.pipeline,
        classifier_views[2],
        classifier_views[3],
    )

    print("PHASE4: generating five-fold training-only OOF predictions", flush=True)
    oof = generate_oof_feed_type_predictions(
        data.train,
        data.validation,
        data.fold_manifest,
        selected_classifier.configuration,
    )
    oof.predictions.to_csv(
        ML_REPORTS_DIR / "feed_type_oof_predictions.csv",
        index=False,
        lineterminator="\n",
    )
    write_json(
        ML_REPORTS_DIR / "feed_type_oof_prediction_summary.json",
        oof.summary,
    )
    train_b = add_predicted_feed_type(
        data.train,
        oof.predictions.sort_values(
            "source_row_number"
        )["predicted_feed_type"].to_numpy(),
    )
    validation_b = add_predicted_feed_type(
        data.validation,
        oof.validation_predictions,
    )

    print("PHASE4: evaluating feed-quantity Design A and Design B", flush=True)
    feed_a_evaluations = evaluate_feed_quantity_candidates(
        data.train,
        data.validation,
        design="A",
        skip_expensive=skip_expensive,
    )
    selected_feed_a, feed_a_selection = select_feed_quantity_candidate(
        feed_a_evaluations,
        design="A",
    )
    feed_b_evaluations = evaluate_feed_quantity_candidates(
        train_b,
        validation_b,
        design="B",
        skip_expensive=skip_expensive,
    )
    selected_feed_b, feed_b_selection = select_feed_quantity_candidate(
        feed_b_evaluations,
        design="B",
    )
    choose_b, design_reason = _design_b_is_meaningful(
        feed_a_selection, feed_b_selection
    )
    locked_design = "B" if choose_b else "A"
    selected_feed = selected_feed_b if choose_b else selected_feed_a
    feed_selection = feed_b_selection if choose_b else feed_a_selection

    feed_a_views = build_feed_quantity_views(
        data.train, data.validation, design="A"
    )
    feed_b_views = build_feed_quantity_views(
        train_b, validation_b, design="B"
    )
    feed_a_importance = permutation_importance_records(
        selected_feed_a.pipeline,
        feed_a_views[2],
        feed_a_views[3],
        scoring="neg_mean_absolute_error",
    )
    feed_b_importance = permutation_importance_records(
        selected_feed_b.pipeline,
        feed_b_views[2],
        feed_b_views[3],
        scoring="neg_mean_absolute_error",
    )
    locked_feed_importance = (
        feed_b_importance if choose_b else feed_a_importance
    )
    write_csv_records(
        ML_REPORTS_DIR / "feed_quantity_design_a_candidate_metrics.csv",
        [item.to_record() for item in feed_a_evaluations],
    )
    write_csv_records(
        ML_REPORTS_DIR / "feed_quantity_design_b_candidate_metrics.csv",
        [item.to_record() for item in feed_b_evaluations],
    )
    write_csv_records(
        ML_REPORTS_DIR / "feed_quantity_feature_importance.csv",
        locked_feed_importance,
    )
    _write_text(
        ML_REPORTS_DIR / "feed_quantity_design_a_report.md",
        render_feed_quantity_report(
            feed_a_evaluations,
            feed_a_selection,
            design="A",
            diagnostics=feed_quantity_diagnostics(
                data.validation, selected_feed_a.predictions
            ),
            importance_records=feed_a_importance,
        ),
    )
    _write_text(
        ML_REPORTS_DIR / "feed_quantity_design_b_report.md",
        render_feed_quantity_report(
            feed_b_evaluations,
            feed_b_selection,
            design="B",
            diagnostics=feed_quantity_diagnostics(
                data.validation, selected_feed_b.predictions
            ),
            importance_records=feed_b_importance,
        ),
    )
    write_residual_plot_png(
        feed_a_views[3],
        selected_feed_a.predictions,
        ML_REPORTS_DIR / "feed_quantity_design_a_residuals.png",
    )
    write_residual_plot_png(
        feed_b_views[3],
        selected_feed_b.predictions,
        ML_REPORTS_DIR / "feed_quantity_design_b_residuals.png",
    )

    print("PHASE4: evaluating milk-yield candidates and ablation", flush=True)
    milk_evaluations = evaluate_milk_yield_candidates(
        data.train,
        data.validation,
        skip_expensive=skip_expensive,
    )
    selected_milk, milk_selection = select_milk_yield_candidate(
        milk_evaluations
    )
    milk_ablation = evaluate_milk_ablation(
        selected_milk.configuration,
        data.train,
        data.validation,
    )
    milk_views = build_milk_yield_views(data.train, data.validation)
    milk_importance = permutation_importance_records(
        selected_milk.pipeline,
        milk_views[2],
        milk_views[3],
        scoring="neg_mean_absolute_error",
    )
    write_csv_records(
        ML_REPORTS_DIR / "milk_yield_candidate_metrics.csv",
        [item.to_record() for item in milk_evaluations],
    )
    write_csv_records(
        ML_REPORTS_DIR / "milk_yield_feature_importance.csv",
        milk_importance,
    )
    _write_text(
        ML_REPORTS_DIR / "milk_yield_regressor_report.md",
        render_milk_yield_report(
            milk_evaluations,
            milk_selection,
            diagnostics=milk_yield_diagnostics(
                data.validation, selected_milk.predictions
            ),
            importance_records=milk_importance,
        ),
    )
    write_residual_plot_png(
        milk_views[3],
        selected_milk.predictions,
        ML_REPORTS_DIR / "milk_yield_residuals.png",
    )

    run_configuration_hash = stable_json_hash(
        {
            "base_configuration_hash": configuration_hash(),
            "skip_expensive_models": skip_expensive,
        }
    )
    lock = {
        "lock_version": "phase4_selection_lock_v1",
        "selected_classifier_configuration": (
            selected_classifier.configuration.configuration_id
        ),
        "selected_feed_quantity_design": locked_design,
        "selected_feed_quantity_configuration": (
            selected_feed.configuration.configuration_id
        ),
        "selected_feed_quantity_design_a_configuration": (
            selected_feed_a.configuration.configuration_id
        ),
        "selected_feed_quantity_design_b_configuration": (
            selected_feed_b.configuration.configuration_id
        ),
        "selected_milk_yield_configuration": (
            selected_milk.configuration.configuration_id
        ),
        "selected_milk_yield_feature_version": "FULL_NINE_FEATURES",
        "selected_milk_yield_ablation_configuration": (
            milk_ablation.configuration.configuration_id
        ),
        "validation_selections": {
            "feed_type": classifier_selection.to_dict(),
            "feed_quantity_design_a": feed_a_selection.to_dict(),
            "feed_quantity_design_b": feed_b_selection.to_dict(),
            "milk_yield": milk_selection.to_dict(),
            "milk_yield_ablation_validation_metrics": milk_ablation.metrics,
        },
        "selection_reasons": {
            "feed_type": classifier_selection.selection_reason,
            "feed_quantity_design": design_reason,
            "feed_quantity": feed_selection.selection_reason,
            "milk_yield": milk_selection.selection_reason,
            "milk_yield_feature_version": (
                "The full nine-feature contract remains locked; ablation is "
                "a predeclared transparency comparison, not a selection search."
            ),
        },
        "random_seed": RANDOM_SEED,
        "contract_version": data.metadata["contract_version"],
        "split_manifest_sha256": data.metadata["split_manifest_sha256"],
        "dataset_sha256": data.metadata["dataset_sha256"],
        "configuration_hash": run_configuration_hash,
        "selection_timestamp": utc_now(),
        "test_targets_inspected_before_lock": False,
    }
    write_locked_selection(LOCK_PATH, lock)
    lock_sha256 = sha256_file(LOCK_PATH)
    print(
        f"PHASE4: selections locked ({lock_sha256}); final test begins once",
        flush=True,
    )

    # No test target is referenced above this boundary.
    classifier_test_views = build_classifier_views(data.train, data.test)
    classifier_final, classifier_fit_seconds = clone_and_fit(
        selected_classifier.pipeline,
        classifier_test_views[0],
        classifier_test_views[1],
    )
    classifier_predictions = classifier_final.predict(classifier_test_views[2])
    classifier_test = classification_metrics(
        classifier_test_views[3],
        classifier_predictions,
        labels=approved_labels(),
    )
    most_frequent = _find(
        classifier_evaluations, "feed_type_dummy_most_frequent"
    )
    stratified = _find(
        classifier_evaluations, "feed_type_dummy_stratified"
    )
    most_frequent_final, _ = clone_and_fit(
        most_frequent.pipeline,
        classifier_test_views[0],
        classifier_test_views[1],
    )
    stratified_final, _ = clone_and_fit(
        stratified.pipeline,
        classifier_test_views[0],
        classifier_test_views[1],
    )
    most_frequent_predictions = most_frequent_final.predict(
        classifier_test_views[2]
    )
    stratified_predictions = stratified_final.predict(
        classifier_test_views[2]
    )
    classifier_test_most_frequent = classification_metrics(
        classifier_test_views[3],
        most_frequent_predictions,
        labels=approved_labels(),
    )
    classifier_test_stratified = classification_metrics(
        classifier_test_views[3],
        stratified_predictions,
        labels=approved_labels(),
    )
    classifier_status, classifier_eligible = _status_classification(
        classifier_selection,
        classifier_test,
        classifier_test_most_frequent,
        classifier_test_stratified,
    )
    write_confusion_matrix_png(
        classifier_test["confusion_matrix"],
        ML_REPORTS_DIR / "feed_type_test_confusion_matrix.png",
    )
    test_confidence = confidence_audit(
        classifier_final,
        classifier_test_views[2],
        classifier_test_views[3],
    )
    _write_text(
        ML_REPORTS_DIR / "feed_type_confidence_report.md",
        _confidence_report(validation_confidence, test_confidence),
    )

    test_feed_predictions = classifier_final.predict(
        classifier_test_views[2]
    )
    test_b = add_predicted_feed_type(data.test, test_feed_predictions)
    feed_test_products: dict[str, dict[str, Any]] = {}
    for design, training, testing, evaluations, selected, selection in (
        (
            "A",
            data.train,
            data.test,
            feed_a_evaluations,
            selected_feed_a,
            feed_a_selection,
        ),
        (
            "B",
            train_b,
            test_b,
            feed_b_evaluations,
            selected_feed_b,
            feed_b_selection,
        ),
    ):
        views = build_feed_quantity_views(
            training, testing, design=design
        )
        final_pipeline, final_fit_seconds = clone_and_fit(
            selected.pipeline,
            views[0],
            views[1],
        )
        predictions = final_pipeline.predict(views[2])
        test_metrics = regression_metrics(views[3], predictions)
        baseline = _find(
            evaluations, selection.baseline_configuration_id
        )
        baseline_pipeline, _ = clone_and_fit(
            baseline.pipeline,
            views[0],
            views[1],
        )
        baseline_predictions = baseline_pipeline.predict(views[2])
        baseline_metrics = regression_metrics(views[3], baseline_predictions)
        status, eligible = _status_regression(
            selection, test_metrics, baseline_metrics
        )
        feed_test_products[design] = {
            "views": views,
            "pipeline": final_pipeline,
            "configuration": selected.configuration,
            "selection": selection,
            "test_metrics": test_metrics,
            "baseline_metrics": baseline_metrics,
            "predictions": predictions,
            "status": status,
            "eligible": eligible,
            "fit_seconds": final_fit_seconds,
        }
    locked_feed_product = feed_test_products[locked_design]
    feed_status = locked_feed_product["status"]
    feed_eligible = bool(locked_feed_product["eligible"])
    if locked_design == "B" and not classifier_eligible:
        feed_eligible = False
        feed_status = "FAILED"

    milk_test_views = build_milk_yield_views(data.train, data.test)
    milk_final, milk_fit_seconds = clone_and_fit(
        selected_milk.pipeline,
        milk_test_views[0],
        milk_test_views[1],
    )
    milk_predictions = milk_final.predict(milk_test_views[2])
    milk_test = regression_metrics(milk_test_views[3], milk_predictions)
    milk_baseline = _find(
        milk_evaluations, milk_selection.baseline_configuration_id
    )
    milk_baseline_final, _ = clone_and_fit(
        milk_baseline.pipeline,
        milk_test_views[0],
        milk_test_views[1],
    )
    milk_baseline_predictions = milk_baseline_final.predict(
        milk_test_views[2]
    )
    milk_test_baseline = regression_metrics(
        milk_test_views[3], milk_baseline_predictions
    )
    milk_status, milk_eligible = _status_regression(
        milk_selection,
        milk_test,
        milk_test_baseline,
    )
    ablation_test_views = build_milk_yield_views(
        data.train, data.test, ablation=True
    )
    milk_ablation_final, _ = clone_and_fit(
        milk_ablation.pipeline,
        ablation_test_views[0],
        ablation_test_views[1],
    )
    ablation_predictions = milk_ablation_final.predict(
        ablation_test_views[2]
    )
    milk_ablation_test = regression_metrics(
        ablation_test_views[3],
        ablation_predictions,
    )
    _write_text(
        ML_REPORTS_DIR / "milk_yield_ablation_report.md",
        render_ablation_report(
            selected_milk.metrics,
            milk_ablation.metrics,
            milk_test,
            milk_ablation_test,
        ),
    )

    _write_text(
        ML_REPORTS_DIR / "feed_quantity_design_comparison.md",
        _design_comparison(
            selection_a=feed_a_selection,
            selection_b=feed_b_selection,
            test_a=feed_test_products["A"]["test_metrics"],
            test_b=feed_test_products["B"]["test_metrics"],
            locked_design=locked_design,
            lock_reason=design_reason,
            oof_metrics=oof.summary["oof_metrics"],
        ),
    )

    final_rows = [
        {
            "task": "Feed type",
            "baseline": "Dummy stratified Macro F1",
            "selected_model": (
                selected_classifier.configuration.configuration_id
            ),
            "validation_metric": (
                f"Macro F1 {selected_classifier.metrics['macro_f1']:.6f}"
            ),
            "test_metric": f"Macro F1 {classifier_test['macro_f1']:.6f}",
            "status": classifier_status,
        },
        {
            "task": f"Feed quantity Design {locked_design}",
            "baseline": "Best dummy MAE",
            "selected_model": (
                locked_feed_product["configuration"].configuration_id
            ),
            "validation_metric": (
                f"MAE {feed_selection.validation_metrics['mae']:.6f}"
            ),
            "test_metric": (
                f"MAE {locked_feed_product['test_metrics']['mae']:.6f}"
            ),
            "status": feed_status,
        },
        {
            "task": "Milk yield",
            "baseline": "Best dummy MAE",
            "selected_model": selected_milk.configuration.configuration_id,
            "validation_metric": (
                f"MAE {milk_selection.validation_metrics['mae']:.6f}"
            ),
            "test_metric": f"MAE {milk_test['mae']:.6f}",
            "status": milk_status,
        },
    ]
    _write_text(
        ML_REPORTS_DIR / "final_test_evaluation.md",
        _final_test_report(final_rows),
    )

    artifacts: dict[str, Any] = {}
    if classifier_eligible:
        classifier_metadata = _candidate_metadata(
            task="synthetic_feed_type_classifier",
            config=selected_classifier.configuration,
            feature_order=list(classifier_test_views[0].columns),
            target="feed_type",
            data=data,
            validation_metrics=selected_classifier.metrics,
            test_metrics=classifier_test,
            baseline_metrics={
                "validation_most_frequent": _find(
                    classifier_evaluations,
                    "feed_type_dummy_most_frequent",
                ).metrics,
                "validation_stratified": _find(
                    classifier_evaluations,
                    "feed_type_dummy_stratified",
                ).metrics,
                "test_most_frequent": classifier_test_most_frequent,
                "test_stratified": classifier_test_stratified,
            },
            duration=classifier_fit_seconds,
        )
        artifacts["feed_type"] = _save_candidate(
            filename="feed_type_classifier_candidate_v1.joblib",
            pipeline=classifier_final,
            X_sample=classifier_test_views[2].head(64),
            metadata=classifier_metadata,
        )
    if feed_eligible:
        dependency = None
        if locked_design == "B":
            dependency = {
                "requires_feed_type_classifier": True,
                "classifier_configuration_id": (
                    selected_classifier.configuration.configuration_id
                ),
                "training_feature_source": "five-fold OOF predictions",
                "validation_and_test_feature_source": (
                    "locked classifier fitted on training only"
                ),
            }
        feed_metadata = _candidate_metadata(
            task=f"synthetic_feed_quantity_regressor_design_{locked_design}",
            config=locked_feed_product["configuration"],
            feature_order=list(locked_feed_product["views"][0].columns),
            target="feed_quantity_kg",
            data=data,
            validation_metrics=feed_selection.validation_metrics,
            test_metrics=locked_feed_product["test_metrics"],
            baseline_metrics={
                "validation": feed_selection.baseline_metrics,
                "test": locked_feed_product["baseline_metrics"],
            },
            duration=locked_feed_product["fit_seconds"],
            dependency=dependency,
        )
        artifacts["feed_quantity"] = _save_candidate(
            filename="feed_quantity_regressor_candidate_v1.joblib",
            pipeline=locked_feed_product["pipeline"],
            X_sample=locked_feed_product["views"][2].head(64),
            metadata=feed_metadata,
        )
    if milk_eligible:
        milk_metadata = _candidate_metadata(
            task="synthetic_milk_yield_regressor",
            config=selected_milk.configuration,
            feature_order=list(milk_test_views[0].columns),
            target="milk_yield_l",
            data=data,
            validation_metrics=selected_milk.metrics,
            test_metrics=milk_test,
            baseline_metrics={
                "validation": milk_selection.baseline_metrics,
                "test": milk_test_baseline,
            },
            duration=milk_fit_seconds,
        )
        artifacts["milk_yield"] = _save_candidate(
            filename="milk_yield_regressor_candidate_v1.joblib",
            pipeline=milk_final,
            X_sample=milk_test_views[2].head(64),
            metadata=milk_metadata,
        )

    model_cards_dir = PROJECT_ROOT / "documentation" / "model_cards"
    _write_text(
        model_cards_dir / "feed_type_classifier_candidate.md",
        _model_card(
            title="FarmLite Synthetic Feed-Type Classifier Candidate",
            purpose=(
                "Predict one publisher-declared synthetic feed category from "
                "nine approved cattle and environment features."
            ),
            features=BASE_FEATURES,
            target="feed_type",
            config=selected_classifier.configuration,
            selection=classifier_selection,
            test_metrics=classifier_test,
            baseline_test_metrics=classifier_test_stratified,
            status=classifier_status,
            artifact=artifacts.get("feed_type"),
            next_action=(
                "Use another expert-labelled dataset or redesign the target "
                "if no candidate clears the baseline; otherwise request a "
                "separate Phase 5 integration review."
            ),
        ),
    )
    feed_features = BASE_FEATURES + (
        ["predicted_feed_type"] if locked_design == "B" else []
    )
    _write_text(
        model_cards_dir / "feed_quantity_regressor_candidate.md",
        _model_card(
            title="FarmLite Synthetic Feed-Quantity Regressor Candidate",
            purpose=(
                "Estimate the publisher-declared synthetic feed-quantity "
                "target; this is not validated daily total feed."
            ),
            features=feed_features,
            target="feed_quantity_kg",
            config=locked_feed_product["configuration"],
            selection=feed_selection,
            test_metrics=locked_feed_product["test_metrics"],
            baseline_test_metrics=locked_feed_product["baseline_metrics"],
            status=feed_status,
            artifact=artifacts.get("feed_quantity"),
            next_action=(
                "Review the locked A/B evidence and acquire a validated "
                "quantity definition before any user-facing interpretation."
            ),
        ),
    )
    _write_text(
        model_cards_dir / "milk_yield_regressor_candidate.md",
        _model_card(
            title="FarmLite Synthetic Milk-Yield Regressor Candidate",
            purpose=(
                "Estimate the publisher-declared synthetic milk-yield target "
                "with an unvalidated measurement period."
            ),
            features=BASE_FEATURES,
            target="milk_yield_l",
            config=selected_milk.configuration,
            selection=milk_selection,
            test_metrics=milk_test,
            baseline_test_metrics=milk_test_baseline,
            status=milk_status,
            artifact=artifacts.get("milk_yield"),
            next_action=(
                "Review the ablation dependence and synthetic limitation "
                "before requesting a separate integration decision."
            ),
        ),
    )

    existing_hash_after = sha256_file(MILK_YIELD_MODEL_PATH)
    existing_hash_ok = (
        existing_hash_after
        == data.metadata["existing_model_sha256_before"]
        == EXPECTED_EXISTING_MODEL_SHA256
    )
    if not existing_hash_ok:
        raise Phase4ExperimentError(
            "Existing retained milk-yield model changed during Phase 4"
        )

    gate_report, recommendation = _phase5_gate(
        classifier_status=classifier_status,
        classifier_metrics=classifier_test,
        feed_status=feed_status,
        milk_status=milk_status,
        artifacts=artifacts,
        existing_hash_ok=existing_hash_ok,
        ablation_complete=True,
    )
    _write_text(
        PROJECT_ROOT / "documentation" / "phase_5_integration_approval.md",
        gate_report,
    )

    complete_option_b = bool(
        classifier_eligible
        and feed_eligible
        and milk_eligible
        and locked_design == "B"
    )
    comparison_lines = [
        "# FarmLite Phase 4 Model Comparison",
        "",
        "| Task | Baseline | Best candidate | Validation result | Test result | Release decision |",
        "|---|---|---|---|---|---|",
        (
            f"| Feed type | Stratified dummy | "
            f"`{selected_classifier.configuration.configuration_id}` | "
            f"Macro F1 {selected_classifier.metrics['macro_f1']:.6f} | "
            f"Macro F1 {classifier_test['macro_f1']:.6f} | "
            f"{'CANDIDATE_ACCEPTED_WITH_LIMITATIONS' if classifier_eligible else 'REJECTED_NO_LEARNABLE_SIGNAL'} |"
        ),
        (
            f"| Feed quantity Design {locked_design} | Best dummy | "
            f"`{locked_feed_product['configuration'].configuration_id}` | "
            f"MAE {feed_selection.validation_metrics['mae']:.6f} | "
            f"MAE {locked_feed_product['test_metrics']['mae']:.6f} | "
            f"{'CANDIDATE_ACCEPTED_WITH_LIMITATIONS' if feed_eligible else 'REJECTED_NO_LEARNABLE_SIGNAL'} |"
        ),
        (
            f"| Milk yield | Best dummy | "
            f"`{selected_milk.configuration.configuration_id}` | "
            f"MAE {selected_milk.metrics['mae']:.6f} | "
            f"MAE {milk_test['mae']:.6f} | "
            f"{'CANDIDATE_ACCEPTED_WITH_LIMITATIONS' if milk_eligible else 'REJECTED_NO_LEARNABLE_SIGNAL'} |"
        ),
        "",
        "## Required Conclusions",
        "",
        (
            f"1. Feed_Type meaningfully predictable: **{classifier_eligible}** "
            f"({classifier_status})."
        ),
        (
            f"2. Feed_Quantity_kg meaningfully predictable: **{feed_eligible}** "
            f"({feed_status})."
        ),
        f"3. Predicted feed type selected: **{locked_design == 'B'}**. {design_reason}",
        (
            f"4. Milk_Yield_L meaningfully predictable: **{milk_eligible}** "
            f"({milk_status})."
        ),
        (
            "5. Previous-week dependence: removing it changes test MAE by "
            f"{milk_ablation_test['mae'] - milk_test['mae']:+.6f}; see ablation report."
        ),
        (
            "6. Validation/test stability statuses: "
            f"{classifier_status}; {feed_status}; {milk_status}."
        ),
        "7. Tasks beating baselines: "
        + (
            ", ".join(
                name
                for name, eligible in (
                    ("feed type", classifier_eligible),
                    ("feed quantity", feed_eligible),
                    ("milk yield", milk_eligible),
                )
                if eligible
            )
            or "none"
        )
        + ".",
        (
            "8. Integration-review candidates: "
            + (", ".join(artifacts) if artifacts else "none")
            + ". Integration remains unapproved."
        ),
        (
            "9. Tasks without eligible artifacts require target/data redesign "
            "or a better-scoped, expert-validated dataset."
        ),
        (
            f"10. Complete Option B architecture supported: **{complete_option_b}**. "
            "All dependent components must independently clear their gates."
        ),
    ]
    _write_text(
        ML_REPORTS_DIR / "phase4_model_comparison.md",
        "\n".join(comparison_lines),
    )

    skipped = []
    if skip_expensive:
        for task in ("feed_type", "feed_quantity", "milk_yield"):
            skipped.extend(
                {
                    "configuration_id": config.configuration_id,
                    "reason": "SKIPPED_RESOURCE_LIMIT_BY_COMMAND_FLAG",
                }
                for config in candidate_configs(task)
                if config.resource_class == "EXPENSIVE"
            )
    failed = []
    if not classifier_eligible:
        failed.append(
            {
                "task": "feed_type",
                "reason": classifier_status,
                "artifact_saved": False,
            }
        )
    if not feed_eligible:
        failed.append(
            {
                "task": "feed_quantity",
                "reason": feed_status,
                "artifact_saved": False,
            }
        )
    if not milk_eligible:
        failed.append(
            {
                "task": "milk_yield",
                "reason": milk_status,
                "artifact_saved": False,
            }
        )

    summary = {
        "phase_status": "PHASE_4_COMPLETED_NO_INTEGRATION",
        "runner_version": PHASE4_RUNNER_VERSION,
        "configuration_hash": lock["configuration_hash"],
        "dataset_metadata": data.metadata,
        "split_metadata": data.metadata["manifest_checks"],
        "candidate_configurations": {
            task: [
                config.to_dict()
                for config in candidate_configs(
                    task, skip_expensive=skip_expensive
                )
            ]
            for task in ("feed_type", "feed_quantity", "milk_yield")
        },
        "validation_metrics": {
            "feed_type": [
                item.to_dict() for item in classifier_evaluations
            ],
            "feed_quantity_design_a": [
                item.to_dict() for item in feed_a_evaluations
            ],
            "feed_quantity_design_b": [
                item.to_dict() for item in feed_b_evaluations
            ],
            "milk_yield": [item.to_dict() for item in milk_evaluations],
            "milk_yield_ablation": milk_ablation.to_dict(),
        },
        "locked_selections": lock,
        "locked_selection_sha256": lock_sha256,
        "test_metrics": {
            "feed_type": classifier_test,
            "feed_type_baseline_most_frequent": (
                classifier_test_most_frequent
            ),
            "feed_type_baseline_stratified": classifier_test_stratified,
            "feed_quantity_design_a": feed_test_products["A"]["test_metrics"],
            "feed_quantity_design_b": feed_test_products["B"]["test_metrics"],
            "milk_yield": milk_test,
            "milk_yield_ablation": milk_ablation_test,
        },
        "baseline_comparisons": {
            "feed_type": {
                "status": classifier_status,
                "beats_validation_and_test": classifier_eligible,
            },
            "feed_quantity": {
                "status": feed_status,
                "beats_validation_and_test": feed_eligible,
            },
            "milk_yield": {
                "status": milk_status,
                "beats_validation_and_test": milk_eligible,
            },
        },
        "artifact_paths": artifacts,
        "artifact_checksums": {
            name: item["artifact_sha256"]
            for name, item in artifacts.items()
        },
        "failed_experiments": failed,
        "skipped_experiments": skipped,
        "warnings": [
            SYNTHETIC_WARNING,
            "Test metrics were inspected once after the selection lock.",
            "No task is production-ready or automatically released.",
        ],
        "limitations": load_model_contract()["dataset"]["limitations"],
        "integration_readiness_decisions": {
            "feed_type": classifier_status,
            "feed_quantity": feed_status,
            "milk_yield": milk_status,
            "complete_option_b_supported": complete_option_b,
            "phase_5_recommendation": recommendation,
            "integration_performed": False,
        },
        "existing_model_sha256_before": data.metadata[
            "existing_model_sha256_before"
        ],
        "existing_model_sha256_after": existing_hash_after,
        "existing_model_unchanged": existing_hash_ok,
        "completed_at": utc_now(),
    }
    write_json(SUMMARY_PATH, summary)
    print("PHASE4: reports and eligible candidate artifacts complete", flush=True)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run controlled FarmLite Phase 4 model experiments."
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Stop after preflight and training-only smoke checks.",
    )
    parser.add_argument(
        "--task",
        choices=["feed_type", "feed_quantity", "milk_yield"],
        action="append",
        help="Limit smoke-only checks to one or more tasks.",
    )
    parser.add_argument(
        "--skip-expensive-models",
        action="store_true",
        help="Skip registry entries marked EXPENSIVE and report each skip.",
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help=(
            "Allow replacement of pre-lock generated reports. This never "
            "overrides an existing selection lock or candidate artifact."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.task and not args.smoke_only:
        raise Phase4ExperimentError(
            "--task is supported for isolated smoke checks only. A full Phase "
            "4 run must lock the dependent tasks together."
        )
    if LOCK_PATH.exists() and not args.smoke_only:
        raise Phase4ExperimentError(
            "locked_model_selection.json already exists; final test reruns are "
            "forbidden even with --force-rerun."
        )
    if (
        not args.smoke_only
        and not args.force_rerun
        and SUMMARY_PATH.exists()
    ):
        raise Phase4ExperimentError(
            "A Phase 4 summary already exists. Refusing stale-output reuse."
        )

    print("PHASE4: manifest-locked preflight started", flush=True)
    data = load_experiment_data()
    _write_text(PREFLIGHT_PATH, _preflight_report(data))
    print("PHASE4: preflight passed; smoke tests started", flush=True)
    tasks = args.task or ["feed_type", "feed_quantity", "milk_yield"]
    smoke_records, smoke_passed = run_smoke_tests(
        data,
        tasks=tasks,
        skip_expensive=args.skip_expensive_models,
    )
    _write_text(
        SMOKE_PATH,
        _smoke_report(
            smoke_records,
            passed=smoke_passed,
            tasks=tasks,
            skip_expensive=args.skip_expensive_models,
        ),
    )
    if not smoke_passed:
        raise Phase4ExperimentError(
            "Phase 4 smoke tests failed; full training was not started"
        )
    print("PHASE4: smoke tests passed", flush=True)
    if args.smoke_only:
        print("PHASE4: SMOKE_TEST_ONLY complete", flush=True)
        return 0
    run_full_experiment(
        data,
        skip_expensive=args.skip_expensive_models,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
