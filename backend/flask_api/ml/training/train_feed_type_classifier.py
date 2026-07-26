"""Controlled training utilities for the synthetic feed-category classifier."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.feature_builder import build_features, load_model_contract
from ml.training.experiment_types import (
    CandidateEvaluation,
    TaskSelection,
)
from ml.training.experiment_utils import fit_candidate
from ml.training.metrics import (
    classification_beats_baselines,
    classification_metrics,
)
from ml.training.model_registry import candidate_configs


MODEL_NAME = "feed_type_classifier"
TASK_NAME = "feed_type"
COMPLEXITY_ORDER = {
    "LogisticRegression": 0,
    "DecisionTreeClassifier": 1,
    "RandomForestClassifier": 2,
    "HistGradientBoostingClassifier": 3,
}


def approved_labels() -> list[str]:
    """Return the contract-ordered synthetic feed categories."""

    return list(
        load_model_contract()["models"]["feed_type_classifier"]["target"][
            "allowed_categories"
        ]
    )


def build_classifier_views(
    training: pd.DataFrame,
    evaluation: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Build leakage-safe classifier X/y views."""

    train_result = build_features(training, MODEL_NAME)
    evaluation_result = build_features(evaluation, MODEL_NAME)
    return (
        train_result.X,
        train_result.y,
        evaluation_result.X,
        evaluation_result.y,
    )


def evaluate_feed_type_candidates(
    training: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    skip_expensive: bool = False,
) -> list[CandidateEvaluation]:
    """Fit registered candidates on training and score validation only."""

    X_train, y_train, X_validation, y_validation = build_classifier_views(
        training, validation
    )
    labels = approved_labels()
    results = []
    for config in candidate_configs(TASK_NAME, skip_expensive=skip_expensive):
        results.append(
            fit_candidate(
                config,
                MODEL_NAME,
                X_train,
                y_train,
                X_validation,
                y_validation,
                classification_metrics,
                metric_kwargs={"labels": labels},
            )
        )
    return results


def select_feed_type_candidate(
    evaluations: list[CandidateEvaluation],
) -> tuple[CandidateEvaluation, TaskSelection]:
    """Lock a validation-only classifier selection with a simplicity tie-break."""

    by_id = {
        result.configuration.configuration_id: result for result in evaluations
    }
    most_frequent = by_id["feed_type_dummy_most_frequent"]
    stratified = by_id["feed_type_dummy_stratified"]
    candidates = [
        result for result in evaluations if not result.configuration.is_baseline
    ]
    if not candidates:
        raise ValueError("No non-baseline feed-type candidates were evaluated")
    best_macro = max(result.metrics["macro_f1"] for result in candidates)
    shortlist = [
        result
        for result in candidates
        if result.metrics["macro_f1"] >= best_macro - 0.002
    ]
    selected = max(
        shortlist,
        key=lambda result: (
            result.metrics["macro_f1"],
            result.metrics["balanced_accuracy"],
            result.metrics["predicted_class_count"],
            -COMPLEXITY_ORDER.get(result.configuration.algorithm, 99),
            -result.training_seconds,
        ),
    )
    beats = classification_beats_baselines(
        selected.metrics,
        most_frequent.metrics,
        stratified.metrics,
    )
    reason = (
        "Highest validation Macro F1 within the controlled candidate set, "
        "then balanced accuracy and class coverage; simplicity breaks "
        "near-ties. "
    )
    if beats:
        reason += "It clears the documented validation baseline margin."
        release_status = "CANDIDATE_ACCEPTED_WITH_LIMITATIONS"
    else:
        reason += (
            "It does not clear the documented baseline margin and remains "
            "research-only despite being the strongest candidate."
        )
        release_status = "RESEARCH_ONLY"
    selection = TaskSelection(
        task=TASK_NAME,
        selected_configuration_id=selected.configuration.configuration_id,
        selected_algorithm=selected.configuration.algorithm,
        validation_metrics=selected.metrics,
        baseline_configuration_id=stratified.configuration.configuration_id,
        baseline_metrics=stratified.metrics,
        selection_reason=reason,
        beats_baseline_on_validation=beats,
        release_status=release_status,
    )
    return selected, selection


def confidence_audit(
    pipeline: Any,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    low_confidence_threshold: float = 0.50,
    high_confidence_threshold: float = 0.80,
) -> dict[str, Any]:
    """Audit model probabilities without interpreting them as certainty."""

    if not hasattr(pipeline, "predict_proba"):
        return {
            "available": False,
            "reason": "Selected classifier does not support predict_proba.",
        }
    probabilities = np.asarray(pipeline.predict_proba(X), dtype=float)
    predictions = np.asarray(pipeline.predict(X), dtype=object)
    maximum = probabilities.max(axis=1)
    actual = np.asarray(y, dtype=object)
    incorrect = predictions != actual
    return {
        "available": True,
        "row_count": len(maximum),
        "mean_maximum_probability": float(maximum.mean()),
        "median_maximum_probability": float(np.median(maximum)),
        "minimum_maximum_probability": float(maximum.min()),
        "p25_maximum_probability": float(np.quantile(maximum, 0.25)),
        "p75_maximum_probability": float(np.quantile(maximum, 0.75)),
        "maximum_maximum_probability": float(maximum.max()),
        "low_confidence_threshold": low_confidence_threshold,
        "low_confidence_prediction_count": int(
            np.sum(maximum < low_confidence_threshold)
        ),
        "high_confidence_threshold": high_confidence_threshold,
        "incorrect_high_confidence_prediction_count": int(
            np.sum(incorrect & (maximum >= high_confidence_threshold))
        ),
        "calibration_limitation": (
            "Maximum class probability is an uncalibrated model score on "
            "publisher-declared synthetic data, not scientific certainty."
        ),
    }


def render_classifier_report(
    evaluations: list[CandidateEvaluation],
    selection: TaskSelection,
    *,
    importance_records: list[dict[str, Any]] | None = None,
) -> str:
    """Render validation-only classifier selection evidence."""

    lines = [
        "# FarmLite Synthetic Feed-Category Classifier Report",
        "",
        "## Scope",
        "",
        (
            "Controlled candidate comparison on the locked training and "
            "validation partitions. Feed_Type is a synthetic category, not a "
            "veterinarian-selected or nutritionally optimal recommendation."
        ),
        "",
        "## Candidate Validation Metrics",
        "",
        "| Configuration | Algorithm | Baseline | Accuracy | Balanced accuracy | Macro F1 | Weighted F1 | Predicted classes | Train s | Predict s |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in evaluations:
        metric = result.metrics
        lines.append(
            f"| `{result.configuration.configuration_id}` | "
            f"{result.configuration.algorithm} | "
            f"{result.configuration.is_baseline} | "
            f"{metric['accuracy']:.6f} | "
            f"{metric['balanced_accuracy']:.6f} | "
            f"{metric['macro_f1']:.6f} | "
            f"{metric['weighted_f1']:.6f} | "
            f"{metric['predicted_class_count']} | "
            f"{result.training_seconds:.3f} | "
            f"{result.prediction_seconds:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Locked Validation Selection",
            "",
            f"- Configuration: `{selection.selected_configuration_id}`",
            f"- Algorithm: {selection.selected_algorithm}",
            f"- Beats baselines on validation: {selection.beats_baseline_on_validation}",
            f"- Release status before test: `{selection.release_status}`",
            f"- Reason: {selection.selection_reason}",
            "",
            "## Interpretability",
            "",
        ]
    )
    if importance_records:
        for row in importance_records[:9]:
            lines.append(
                f"- `{row['canonical_feature']}`: "
                f"{row['importance_mean']:.6f} ± "
                f"{row['importance_standard_deviation']:.6f}"
            )
    else:
        lines.append("- Generated after validation selection.")
    lines.extend(
        [
            "",
            (
                "Permutation importance describes validation association in a "
                "synthetic dataset. It is not causal or biological evidence."
            ),
            "",
            "## Limitations",
            "",
            "- Eight classes are approximately balanced, so near-0.125 accuracy is near random.",
            "- A highest-scoring candidate is not automatically useful or deployable.",
            "- Probability output is not scientific confidence.",
            "- The source population is not verified dairy-only.",
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "MODEL_NAME",
    "TASK_NAME",
    "approved_labels",
    "build_classifier_views",
    "confidence_audit",
    "evaluate_feed_type_candidates",
    "render_classifier_report",
    "select_feed_type_candidate",
]
