"""Metrics used consistently across Phase 4 candidates."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    precision_recall_fscore_support,
    precision_score,
    r2_score,
    recall_score,
)


def json_safe(value: Any) -> Any:
    """Convert NumPy values and non-finite floats to strict JSON values."""

    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, np.ndarray)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def classification_metrics(
    actual: Iterable[Any],
    predicted: Iterable[Any],
    *,
    labels: list[str],
) -> dict[str, Any]:
    """Calculate complete multiclass metrics without hiding undefined classes."""

    actual_array = np.asarray(actual, dtype=object)
    predicted_array = np.asarray(predicted, dtype=object)
    precision, recall, f1, support = precision_recall_fscore_support(
        actual_array,
        predicted_array,
        labels=labels,
        zero_division=0,
    )
    predicted_counts = {
        label: int(np.sum(predicted_array == label)) for label in labels
    }
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
            "predicted_count": predicted_counts[label],
        }
        for index, label in enumerate(labels)
    }
    return json_safe(
        {
            "accuracy": float(accuracy_score(actual_array, predicted_array)),
            "balanced_accuracy": float(
                balanced_accuracy_score(actual_array, predicted_array)
            ),
            "macro_precision": float(
                precision_score(
                    actual_array,
                    predicted_array,
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            ),
            "macro_recall": float(
                recall_score(
                    actual_array,
                    predicted_array,
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            ),
            "macro_f1": float(
                f1_score(
                    actual_array,
                    predicted_array,
                    labels=labels,
                    average="macro",
                    zero_division=0,
                )
            ),
            "weighted_f1": float(
                f1_score(
                    actual_array,
                    predicted_array,
                    labels=labels,
                    average="weighted",
                    zero_division=0,
                )
            ),
            "labels": labels,
            "per_class": per_class,
            "confusion_matrix": confusion_matrix(
                actual_array,
                predicted_array,
                labels=labels,
            ).tolist(),
            "predicted_class_distribution": predicted_counts,
            "predicted_class_count": int(
                sum(count > 0 for count in predicted_counts.values())
            ),
        }
    )


def regression_metrics(
    actual: Iterable[float],
    predicted: Iterable[float],
) -> dict[str, Any]:
    """Calculate regression and residual diagnostics."""

    actual_array = np.asarray(actual, dtype=float)
    predicted_array = np.asarray(predicted, dtype=float)
    residuals = actual_array - predicted_array
    mse = float(mean_squared_error(actual_array, predicted_array))
    return json_safe(
        {
            "mae": float(mean_absolute_error(actual_array, predicted_array)),
            "rmse": math.sqrt(mse),
            "r2": float(r2_score(actual_array, predicted_array)),
            "median_absolute_error": float(
                median_absolute_error(actual_array, predicted_array)
            ),
            "mean_residual": float(np.mean(residuals)),
            "residual_standard_deviation": float(
                np.std(residuals, ddof=1)
            ),
            "minimum_prediction": float(np.min(predicted_array)),
            "maximum_prediction": float(np.max(predicted_array)),
            "negative_prediction_count": int(np.sum(predicted_array < 0)),
        }
    )


def regression_beats_baseline(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    *,
    minimum_relative_improvement: float = 0.01,
) -> bool:
    """Apply the documented validation/test regression acceptance rule."""

    if candidate.get("r2") is None or candidate["r2"] <= 0:
        return False
    mae_improvement = (baseline["mae"] - candidate["mae"]) / baseline["mae"]
    rmse_improvement = (
        baseline["rmse"] - candidate["rmse"]
    ) / baseline["rmse"]
    return (
        candidate["mae"] < baseline["mae"]
        and candidate["rmse"] < baseline["rmse"]
        and mae_improvement >= minimum_relative_improvement
        and rmse_improvement >= minimum_relative_improvement
    )


def classification_beats_baselines(
    candidate: dict[str, Any],
    most_frequent: dict[str, Any],
    stratified: dict[str, Any],
    *,
    minimum_macro_f1_gain: float = 0.01,
) -> bool:
    """Apply a conservative multiclass validation/test acceptance rule."""

    return (
        candidate["macro_f1"]
        >= stratified["macro_f1"] + minimum_macro_f1_gain
        and candidate["balanced_accuracy"]
        > stratified["balanced_accuracy"]
        and candidate["accuracy"] > most_frequent["accuracy"]
        and candidate["predicted_class_count"] > 1
    )


__all__ = [
    "classification_beats_baselines",
    "classification_metrics",
    "json_safe",
    "regression_beats_baseline",
    "regression_metrics",
]
