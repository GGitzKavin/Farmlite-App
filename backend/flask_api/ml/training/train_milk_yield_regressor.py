"""Controlled synthetic milk-yield training and ablation utilities."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.feature_builder import build_features
from ml.training.experiment_types import (
    CandidateConfig,
    CandidateEvaluation,
    TaskSelection,
)
from ml.training.experiment_utils import fit_candidate
from ml.training.metrics import regression_beats_baseline, regression_metrics
from ml.training.model_registry import candidate_configs
from ml.training.train_feed_quantity_regressor import (
    regression_subgroup_diagnostics,
)


TASK_NAME = "milk_yield"
MODEL_NAME = "milk_yield_regressor"
ABLATION_FEATURE = "previous_week_avg_yield_l"


def build_milk_yield_views(
    training: pd.DataFrame,
    evaluation: pd.DataFrame,
    *,
    ablation: bool = False,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Build full or previous-week-yield ablation feature views."""

    train_result = build_features(training, MODEL_NAME)
    evaluation_result = build_features(evaluation, MODEL_NAME)
    X_train = train_result.X
    X_evaluation = evaluation_result.X
    if ablation:
        X_train = X_train.drop(columns=[ABLATION_FEATURE])
        X_evaluation = X_evaluation.drop(columns=[ABLATION_FEATURE])
    return X_train, train_result.y, X_evaluation, evaluation_result.y


def evaluate_milk_yield_candidates(
    training: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    skip_expensive: bool = False,
) -> list[CandidateEvaluation]:
    """Fit registered candidates on training and score validation only."""

    X_train, y_train, X_validation, y_validation = build_milk_yield_views(
        training, validation
    )
    return [
        fit_candidate(
            config,
            MODEL_NAME,
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


def evaluate_milk_ablation(
    config: CandidateConfig,
    training: pd.DataFrame,
    validation: pd.DataFrame,
) -> CandidateEvaluation:
    """Evaluate the selected model family without previous-week yield."""

    X_train, y_train, X_validation, y_validation = build_milk_yield_views(
        training,
        validation,
        ablation=True,
    )
    return fit_candidate(
        config,
        MODEL_NAME,
        X_train,
        y_train,
        X_validation,
        y_validation,
        regression_metrics,
    )


def select_milk_yield_candidate(
    evaluations: list[CandidateEvaluation],
) -> tuple[CandidateEvaluation, TaskSelection]:
    """Select the strongest validation candidate without using test data."""

    baselines = [
        result for result in evaluations if result.configuration.is_baseline
    ]
    candidates = [
        result for result in evaluations if not result.configuration.is_baseline
    ]
    if not baselines or not candidates:
        raise ValueError("Milk-yield baseline or candidate results are missing")
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
    reason = (
        "Lowest validation MAE, then RMSE and higher R² within the controlled "
        "candidate set. The full nine-feature contract remains selected; the "
        "previous-week-yield removal is a transparency ablation only. "
    )
    if beats:
        reason += "The candidate clears the validation baseline rule."
        release_status = "CANDIDATE_ACCEPTED_WITH_LIMITATIONS"
    else:
        reason += "The candidate does not clear the validation baseline rule."
        release_status = "RESEARCH_ONLY"
    selection = TaskSelection(
        task=TASK_NAME,
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


def milk_yield_diagnostics(
    validation: pd.DataFrame,
    predictions: np.ndarray,
) -> dict[str, list[dict[str, Any]]]:
    """Produce approved validation-only milk-yield subgroup diagnostics."""

    target = validation["milk_yield_l"]
    yield_ranges = pd.cut(
        validation["previous_week_avg_yield_l"],
        bins=[-np.inf, 5.0, 10.0, 15.0, 20.0, np.inf],
        labels=["<=5", "5-10", "10-15", "15-20", ">20"],
    )
    zero_status = np.where(target == 0, "zero_target", "positive_target")
    ranged = validation.assign(
        previous_week_yield_range=yield_ranges.astype("string"),
        zero_target_status=zero_status,
    )
    return {
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
        "previous_week_yield_ranges": regression_subgroup_diagnostics(
            ranged,
            target,
            predictions,
            group_column="previous_week_yield_range",
        ),
        "zero_vs_positive_target": regression_subgroup_diagnostics(
            ranged,
            target,
            predictions,
            group_column="zero_target_status",
        ),
    }


def render_milk_yield_report(
    evaluations: list[CandidateEvaluation],
    selection: TaskSelection,
    *,
    diagnostics: dict[str, list[dict[str, Any]]],
    importance_records: list[dict[str, Any]] | None = None,
) -> str:
    """Render validation candidate and interpretability evidence."""

    lines = [
        "# FarmLite Synthetic Milk-Yield Regressor Report",
        "",
        "## Scope",
        "",
        (
            "Milk_Yield_L is a publisher-declared synthetic target whose "
            "measurement period and zero meaning are not independently "
            "validated. It must not be described as verified litres per day."
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
                "Permutation importance describes association in synthetic "
                "validation records. It is not causal or biological evidence."
            ),
            "",
            "## Limitations",
            "",
            "- Strong performance may reflect an undocumented synthetic generation formula.",
            "- Previous-week yield is historical input, not current target leakage.",
            "- The ablation report quantifies dependence on that historical feature.",
            "- The source population is not verified dairy-only.",
            "",
        ]
    )
    return "\n".join(lines)


def render_ablation_report(
    full_validation: dict[str, Any],
    ablation_validation: dict[str, Any],
    full_test: dict[str, Any],
    ablation_test: dict[str, Any],
) -> str:
    """Render the locked full-versus-ablation comparison."""

    validation_mae_change = (
        ablation_validation["mae"] - full_validation["mae"]
    )
    test_mae_change = ablation_test["mae"] - full_test["mae"]
    lines = [
        "# FarmLite Milk-Yield Previous-Week-Yield Ablation",
        "",
        "## Controlled Comparison",
        "",
        "| Version | Validation MAE | Validation RMSE | Validation R² | Test MAE | Test RMSE | Test R² |",
        "|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| Full nine features | {full_validation['mae']:.6f} | "
            f"{full_validation['rmse']:.6f} | {full_validation['r2']:.6f} | "
            f"{full_test['mae']:.6f} | {full_test['rmse']:.6f} | "
            f"{full_test['r2']:.6f} |"
        ),
        (
            f"| Without `previous_week_avg_yield_l` | "
            f"{ablation_validation['mae']:.6f} | "
            f"{ablation_validation['rmse']:.6f} | "
            f"{ablation_validation['r2']:.6f} | "
            f"{ablation_test['mae']:.6f} | {ablation_test['rmse']:.6f} | "
            f"{ablation_test['r2']:.6f} |"
        ),
        "",
        "## Interpretation",
        "",
        f"- Validation MAE increases by {validation_mae_change:.6f} without the historical feature.",
        f"- Test MAE increases by {test_mae_change:.6f} without the historical feature.",
        (
            "- The difference shows how much predictive performance depends "
            "on previous-week yield within this synthetic dataset."
        ),
        (
            "- A large difference is consistent with possible formula linkage "
            "in the undocumented synthetic generator; it does not prove "
            "leakage because the feature is temporally historical."
        ),
        (
            "- Remaining ablation performance indicates how much signal the "
            "other eight features contain in these synthetic records."
        ),
        (
            "- Strong full-model results do not establish real-world dairy, "
            "veterinary, or nutritional validity."
        ),
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "ABLATION_FEATURE",
    "MODEL_NAME",
    "TASK_NAME",
    "build_milk_yield_views",
    "evaluate_milk_ablation",
    "evaluate_milk_yield_candidates",
    "milk_yield_diagnostics",
    "render_ablation_report",
    "render_milk_yield_report",
    "select_milk_yield_candidate",
]
