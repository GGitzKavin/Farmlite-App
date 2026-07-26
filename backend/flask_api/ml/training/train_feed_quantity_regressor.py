"""Controlled Design A/B synthetic feed-quantity regression utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.feature_builder import build_features
from ml.training.experiment_types import CandidateEvaluation, TaskSelection
from ml.training.experiment_utils import fit_candidate
from ml.training.metrics import regression_beats_baseline, regression_metrics
from ml.training.model_registry import candidate_configs


TASK_NAME = "feed_quantity"
DESIGN_A_MODEL = "feed_quantity_regressor_design_a"
DESIGN_B_MODEL = "feed_quantity_regressor_design_b"


def add_predicted_feed_type(
    dataframe: pd.DataFrame,
    predictions: np.ndarray | pd.Series,
) -> pd.DataFrame:
    """Add only an explicitly generated predicted feed-category feature."""

    values = np.asarray(predictions, dtype=object)
    if len(values) != len(dataframe):
        raise ValueError("predicted_feed_type row count does not match dataframe")
    result = dataframe.copy()
    result["predicted_feed_type"] = values
    return result


def build_feed_quantity_views(
    training: pd.DataFrame,
    evaluation: pd.DataFrame,
    *,
    design: str,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Build exact Design A or leakage-safe Design B feature views."""

    if design == "A":
        model_name = DESIGN_A_MODEL
        allow_predicted = False
    elif design == "B":
        model_name = DESIGN_B_MODEL
        allow_predicted = True
        if "predicted_feed_type" not in training.columns:
            raise ValueError("Design B training requires predicted_feed_type")
        if "predicted_feed_type" not in evaluation.columns:
            raise ValueError("Design B evaluation requires predicted_feed_type")
    else:
        raise ValueError("design must be 'A' or 'B'")

    train_result = build_features(
        training,
        model_name,
        allow_predicted_feature=allow_predicted,
    )
    evaluation_result = build_features(
        evaluation,
        model_name,
        allow_predicted_feature=allow_predicted,
    )
    if design == "B" and "feed_type" in train_result.X.columns:
        raise ValueError("True feed_type entered Design B features")
    return (
        train_result.X,
        train_result.y,
        evaluation_result.X,
        evaluation_result.y,
    )


def evaluate_feed_quantity_candidates(
    training: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    design: str,
    skip_expensive: bool = False,
) -> list[CandidateEvaluation]:
    """Fit registered regressors on training and score validation only."""

    X_train, y_train, X_validation, y_validation = build_feed_quantity_views(
        training,
        validation,
        design=design,
    )
    model_name = DESIGN_A_MODEL if design == "A" else DESIGN_B_MODEL
    return [
        fit_candidate(
            config,
            model_name,
            X_train,
            y_train,
            X_validation,
            y_validation,
            regression_metrics,
        )
        for config in candidate_configs(
            TASK_NAME, skip_expensive=skip_expensive
        )
    ]


def select_feed_quantity_candidate(
    evaluations: list[CandidateEvaluation],
    *,
    design: str,
) -> tuple[CandidateEvaluation, TaskSelection]:
    """Select by validation MAE, RMSE, R², and then simplicity/cost."""

    baselines = [
        result for result in evaluations if result.configuration.is_baseline
    ]
    candidates = [
        result for result in evaluations if not result.configuration.is_baseline
    ]
    if not baselines or not candidates:
        raise ValueError("Feed-quantity baseline or candidate results are missing")
    baseline = min(
        baselines,
        key=lambda result: (
            result.metrics["mae"],
            result.metrics["rmse"],
        ),
    )
    selected = min(
        candidates,
        key=lambda result: (
            result.metrics["mae"],
            result.metrics["rmse"],
            -result.metrics["r2"],
            result.training_seconds,
        ),
    )
    beats = regression_beats_baseline(selected.metrics, baseline.metrics)
    design_name = f"feed_quantity_design_{design.casefold()}"
    reason = (
        "Lowest validation MAE, then RMSE and higher R² within the controlled "
        f"Design {design} candidate set. "
    )
    if beats:
        reason += "It clears the documented validation baseline rule."
        release_status = "CANDIDATE_ACCEPTED_WITH_LIMITATIONS"
    else:
        reason += (
            "It does not clear the baseline rule and remains research-only."
        )
        release_status = "RESEARCH_ONLY"
    selection = TaskSelection(
        task=design_name,
        selected_configuration_id=selected.configuration.configuration_id,
        selected_algorithm=selected.configuration.algorithm,
        validation_metrics=selected.metrics,
        baseline_configuration_id=baseline.configuration.configuration_id,
        baseline_metrics=baseline.metrics,
        selection_reason=reason,
        beats_baseline_on_validation=beats,
        release_status=release_status,
    )
    return selected, selection


def regression_subgroup_diagnostics(
    dataframe: pd.DataFrame,
    actual: pd.Series,
    predictions: np.ndarray,
    *,
    group_column: str,
    maximum_groups: int | None = None,
    minimum_rows: int = 100,
) -> list[dict[str, Any]]:
    """Calculate validation-only subgroup diagnostics for reporting."""

    if group_column not in dataframe.columns:
        return []
    working = pd.DataFrame(
        {
            "group": dataframe[group_column].astype("string"),
            "actual": np.asarray(actual, dtype=float),
            "predicted": np.asarray(predictions, dtype=float),
        },
        index=dataframe.index,
    )
    counts = working["group"].value_counts()
    groups = counts.index.tolist()
    if maximum_groups is not None:
        groups = groups[:maximum_groups]
    results = []
    for group in groups:
        subset = working.loc[working["group"] == group]
        if len(subset) < minimum_rows:
            continue
        metrics = regression_metrics(subset["actual"], subset["predicted"])
        results.append(
            {
                "group_column": group_column,
                "group": str(group),
                "row_count": len(subset),
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "r2": metrics["r2"],
            }
        )
    return results


def feed_quantity_diagnostics(
    validation: pd.DataFrame,
    predictions: np.ndarray,
) -> dict[str, list[dict[str, Any]]]:
    """Produce the approved validation-only subgroup views."""

    target = validation["feed_quantity_kg"]
    range_labels = pd.cut(
        target,
        bins=[-np.inf, 7.0, 11.0, 15.0, 19.0, np.inf],
        labels=["<=7", "7-11", "11-15", "15-19", ">19"],
    )
    ranged = validation.assign(feed_quantity_range=range_labels.astype("string"))
    return {
        "feed_type": regression_subgroup_diagnostics(
            validation,
            target,
            predictions,
            group_column="feed_type",
        ),
        "lactation_stage": regression_subgroup_diagnostics(
            validation,
            target,
            predictions,
            group_column="lactation_stage",
        ),
        "largest_breeds": regression_subgroup_diagnostics(
            validation,
            target,
            predictions,
            group_column="breed",
            maximum_groups=10,
        ),
        "feed_quantity_ranges": regression_subgroup_diagnostics(
            ranged,
            target,
            predictions,
            group_column="feed_quantity_range",
        ),
    }


def render_feed_quantity_report(
    evaluations: list[CandidateEvaluation],
    selection: TaskSelection,
    *,
    design: str,
    diagnostics: dict[str, list[dict[str, Any]]],
    importance_records: list[dict[str, Any]] | None = None,
) -> str:
    """Render one validation-only feed-quantity design report."""

    lines = [
        f"# FarmLite Synthetic Feed-Quantity Regressor — Design {design}",
        "",
        "## Scope",
        "",
        (
            "Feed_Quantity_kg is a synthetic regression target whose material "
            "basis and measurement period are not independently validated. "
            "It must not be described as validated daily total feed."
        ),
        "",
        "## Candidate Validation Metrics",
        "",
        "| Configuration | Algorithm | Baseline | MAE | RMSE | R² | Median AE | Mean residual | Residual std | Negative | Train s | Predict s |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in evaluations:
        metric = result.metrics
        lines.append(
            f"| `{result.configuration.configuration_id}` | "
            f"{result.configuration.algorithm} | "
            f"{result.configuration.is_baseline} | "
            f"{metric['mae']:.6f} | {metric['rmse']:.6f} | "
            f"{metric['r2']:.6f} | "
            f"{metric['median_absolute_error']:.6f} | "
            f"{metric['mean_residual']:.6f} | "
            f"{metric['residual_standard_deviation']:.6f} | "
            f"{metric['negative_prediction_count']} | "
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
            f"- Beats baseline: {selection.beats_baseline_on_validation}",
            f"- Release status before test: `{selection.release_status}`",
            f"- Reason: {selection.selection_reason}",
            "",
            "## Subgroup Diagnostics",
            "",
        ]
    )
    for name, records in diagnostics.items():
        if not records:
            continue
        worst = max(records, key=lambda row: row["mae"])
        lines.append(
            f"- {name}: {len(records)} groups; highest validation MAE "
            f"`{worst['group']}` = {worst['mae']:.6f}."
        )
    lines.extend(["", "## Feature Importance", ""])
    if importance_records:
        for row in importance_records[:10]:
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
                "Ground-truth Feed_Type is used only for subgroup reporting. "
                "It is not a Design A input and is never substituted for "
                "predicted_feed_type in Design B."
            ),
            "",
            (
                "Feature importance is synthetic-data association, not causal "
                "or nutritional evidence."
            ),
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "DESIGN_A_MODEL",
    "DESIGN_B_MODEL",
    "TASK_NAME",
    "add_predicted_feed_type",
    "build_feed_quantity_views",
    "evaluate_feed_quantity_candidates",
    "feed_quantity_diagnostics",
    "regression_subgroup_diagnostics",
    "render_feed_quantity_report",
    "select_feed_quantity_candidate",
]
