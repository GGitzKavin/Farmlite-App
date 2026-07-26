"""Deterministic split and training-only fold assignment utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split

from ml.preprocessing.preprocessing_types import (
    FoldAssignmentResult,
    SplitAssignmentResult,
)


DEFAULT_RANDOM_SEED = 42
DEFAULT_TRAIN_FRACTION = 0.70
DEFAULT_VALIDATION_FRACTION = 0.15
DEFAULT_TEST_FRACTION = 0.15
DEFAULT_OOF_FOLDS = 5
SPLIT_VERSION = "phase3_split_v1"
FOLD_VERSION = "phase3_feed_type_oof_v1"
SPLIT_NAMES = ("train", "validation", "test")


class SplitAssignmentError(ValueError):
    """Raised when deterministic partitioning cannot be completed safely."""


def _dataframe_hash(dataframe: pd.DataFrame) -> str:
    rendered = dataframe.to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest().upper()


def _numeric_summary(series: pd.Series) -> dict[str, float | int | None]:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric[np.isfinite(numeric)]
    if valid.empty:
        return {
            "count": 0,
            "missing_count": int(numeric.isna().sum()),
            "mean": None,
            "standard_deviation": None,
            "minimum": None,
            "p25": None,
            "median": None,
            "p75": None,
            "maximum": None,
        }
    return {
        "count": int(valid.count()),
        "missing_count": int(numeric.isna().sum()),
        "mean": round(float(valid.mean()), 6),
        "standard_deviation": round(float(valid.std()), 6),
        "minimum": round(float(valid.min()), 6),
        "p25": round(float(valid.quantile(0.25)), 6),
        "median": round(float(valid.median()), 6),
        "p75": round(float(valid.quantile(0.75)), 6),
        "maximum": round(float(valid.max()), 6),
    }


def _class_distribution(
    labels: pd.Series,
    assignments: pd.Series,
) -> dict[str, dict[str, dict[str, float | int]]]:
    distribution: dict[str, dict[str, dict[str, float | int]]] = {}
    for split in SPLIT_NAMES:
        values = labels.loc[assignments == split]
        counts = values.value_counts(dropna=False).sort_index()
        total = len(values)
        distribution[split] = {
            str(category): {
                "count": int(count),
                "percentage": round(int(count) / total * 100, 6)
                if total
                else 0.0,
            }
            for category, count in counts.items()
        }
    return distribution


def _regression_distribution(
    values: pd.Series,
    assignments: pd.Series,
) -> dict[str, dict[str, float | int | None]]:
    return {
        split: _numeric_summary(values.loc[assignments == split])
        for split in SPLIT_NAMES
    }


def _distribution_difference(
    split_summaries: dict[str, dict[str, float | int | None]],
    overall: dict[str, float | int | None],
) -> dict[str, Any]:
    overall_mean = overall["mean"]
    overall_std = overall["standard_deviation"]
    standardized_differences: dict[str, float] = {}
    for split, summary in split_summaries.items():
        if (
            overall_mean is None
            or overall_std in (None, 0)
            or summary["mean"] is None
        ):
            difference = 0.0
        else:
            difference = abs(
                (float(summary["mean"]) - float(overall_mean))
                / float(overall_std)
            )
        standardized_differences[split] = round(difference, 6)
    maximum = max(standardized_differences.values(), default=0.0)
    return {
        "standardized_mean_difference_by_split": standardized_differences,
        "materiality_threshold": 0.10,
        "maximum_standardized_mean_difference": maximum,
        "material_difference_detected": maximum > 0.10,
        "interpretation": (
            "This is a split-balance diagnostic for the synthetic dataset, "
            "not a biological threshold."
        ),
    }


def create_split_assignments(
    dataframe: pd.DataFrame,
    *,
    stratify_column: str = "feed_type",
    random_seed: int = DEFAULT_RANDOM_SEED,
    split_version: str = SPLIT_VERSION,
) -> SplitAssignmentResult:
    """Create one stable 70/15/15 assignment stratified by feed category."""

    if dataframe.empty:
        raise SplitAssignmentError("Cannot split an empty dataframe")
    if stratify_column not in dataframe.columns:
        raise SplitAssignmentError(
            f"Stratification column is missing: {stratify_column}"
        )
    labels = dataframe[stratify_column]
    if labels.isna().any():
        raise SplitAssignmentError(
            f"Stratification column '{stratify_column}' contains missing values"
        )
    class_counts = labels.value_counts()
    if (class_counts < 4).any():
        too_small = ", ".join(map(str, class_counts[class_counts < 4].index))
        raise SplitAssignmentError(
            "Every stratification class needs at least four records: " + too_small
        )

    positions = np.arange(len(dataframe))
    train_positions, temporary_positions = train_test_split(
        positions,
        train_size=DEFAULT_TRAIN_FRACTION,
        test_size=DEFAULT_VALIDATION_FRACTION + DEFAULT_TEST_FRACTION,
        random_state=random_seed,
        shuffle=True,
        stratify=labels.to_numpy(),
    )
    temporary_labels = labels.iloc[temporary_positions].to_numpy()
    validation_positions, test_positions = train_test_split(
        temporary_positions,
        train_size=0.5,
        test_size=0.5,
        random_state=random_seed,
        shuffle=True,
        stratify=temporary_labels,
    )

    assignments = np.full(len(dataframe), "", dtype=object)
    assignments[train_positions] = "train"
    assignments[validation_positions] = "validation"
    assignments[test_positions] = "test"
    source_rows = (
        pd.to_numeric(dataframe["source_row_number"], errors="raise")
        .astype("int64")
        .to_numpy()
        if "source_row_number" in dataframe.columns
        else np.arange(1, len(dataframe) + 1, dtype=np.int64)
    )
    cattle_ids = (
        dataframe["cattle_id"].astype("string").to_numpy()
        if "cattle_id" in dataframe.columns
        else pd.array([pd.NA] * len(dataframe), dtype="string")
    )
    observation_dates = (
        dataframe["observation_date"].astype("string").to_numpy()
        if "observation_date" in dataframe.columns
        else pd.array([pd.NA] * len(dataframe), dtype="string")
    )
    manifest = pd.DataFrame(
        {
            "source_row_number": source_rows,
            "cattle_id": cattle_ids,
            "observation_date": observation_dates,
            "split": assignments,
            "random_seed": random_seed,
            "split_version": split_version,
        }
    )

    assignment_series = pd.Series(assignments, index=dataframe.index)
    counts = {
        split: int((assignment_series == split).sum()) for split in SPLIT_NAMES
    }
    percentages = {
        split: round(count / len(dataframe) * 100, 6)
        for split, count in counts.items()
    }
    duplicate_source_rows = int(manifest["source_row_number"].duplicated().sum())
    missing_assignments = int((manifest["split"] == "").sum())
    cattle_overlap_count = 0
    if manifest["cattle_id"].notna().any():
        cattle_overlap_count = int(
            (
                manifest.dropna(subset=["cattle_id"])
                .groupby("cattle_id")["split"]
                .nunique()
                .gt(1)
            ).sum()
        )

    feed_distribution = _class_distribution(labels, assignment_series)
    feed_quantity_summary = (
        _regression_distribution(
            dataframe["feed_quantity_kg"], assignment_series
        )
        if "feed_quantity_kg" in dataframe.columns
        else {}
    )
    milk_yield_summary = (
        _regression_distribution(dataframe["milk_yield_l"], assignment_series)
        if "milk_yield_l" in dataframe.columns
        else {}
    )
    overall_feed_quantity = (
        _numeric_summary(dataframe["feed_quantity_kg"])
        if "feed_quantity_kg" in dataframe.columns
        else {}
    )
    overall_milk_yield = (
        _numeric_summary(dataframe["milk_yield_l"])
        if "milk_yield_l" in dataframe.columns
        else {}
    )
    summary: dict[str, Any] = {
        "total_row_count": len(dataframe),
        "row_counts": counts,
        "percentages": percentages,
        "random_seed": random_seed,
        "split_version": split_version,
        "split_algorithm": (
            "Two-stage sklearn train_test_split: 70% train, then equal "
            "validation/test halves of the remaining 30%; Feed_Type stratified"
        ),
        "stratification_column": stratify_column,
        "feed_type_distribution": feed_distribution,
        "feed_quantity_kg_summary": feed_quantity_summary,
        "milk_yield_l_summary": milk_yield_summary,
        "feed_quantity_distribution_difference": (
            _distribution_difference(
                feed_quantity_summary, overall_feed_quantity
            )
            if feed_quantity_summary
            else {}
        ),
        "milk_yield_distribution_difference": (
            _distribution_difference(milk_yield_summary, overall_milk_yield)
            if milk_yield_summary
            else {}
        ),
        "checks": {
            "cattle_id_overlap_count": cattle_overlap_count,
            "duplicate_source_row_count": duplicate_source_rows,
            "missing_assignment_count": missing_assignments,
            "each_row_assigned_once": (
                len(manifest) == len(dataframe)
                and duplicate_source_rows == 0
                and missing_assignments == 0
            ),
            "manifest_columns_are_traceability_only": set(manifest.columns)
            == {
                "source_row_number",
                "cattle_id",
                "observation_date",
                "split",
                "random_seed",
                "split_version",
            },
        },
    }
    summary["reproducibility_hash_sha256"] = _dataframe_hash(manifest)
    return SplitAssignmentResult(manifest=manifest, summary=summary)


def create_training_fold_assignments(
    dataframe: pd.DataFrame,
    split_manifest: pd.DataFrame,
    *,
    stratify_column: str = "feed_type",
    random_seed: int = DEFAULT_RANDOM_SEED,
    number_of_folds: int = DEFAULT_OOF_FOLDS,
    fold_version: str = FOLD_VERSION,
) -> FoldAssignmentResult:
    """Assign every training row to one deterministic stratified OOF fold."""

    required_manifest = {"source_row_number", "cattle_id", "split"}
    missing = sorted(required_manifest - set(split_manifest.columns))
    if missing:
        raise SplitAssignmentError(
            "Split manifest lacks required fields: " + ", ".join(missing)
        )
    if len(split_manifest) != len(dataframe):
        raise SplitAssignmentError(
            "Split manifest row count does not match the dataframe"
        )
    if stratify_column not in dataframe.columns:
        raise SplitAssignmentError(
            f"OOF stratification column is missing: {stratify_column}"
        )

    train_positions = np.flatnonzero(
        split_manifest["split"].to_numpy() == "train"
    )
    train_labels = dataframe.iloc[train_positions][stratify_column]
    minimum_class_count = int(train_labels.value_counts().min())
    if minimum_class_count < number_of_folds:
        raise SplitAssignmentError(
            f"At least {number_of_folds} rows per class are required for OOF folds"
        )

    fold_values = np.full(len(train_positions), -1, dtype=np.int64)
    splitter = StratifiedKFold(
        n_splits=number_of_folds,
        shuffle=True,
        random_state=random_seed,
    )
    local_positions = np.arange(len(train_positions))
    for fold_index, (_, validation_local) in enumerate(
        splitter.split(local_positions, train_labels.to_numpy()),
        start=1,
    ):
        fold_values[validation_local] = fold_index
    if (fold_values < 1).any():
        raise SplitAssignmentError("At least one training row lacks an OOF fold")

    training_manifest = split_manifest.iloc[train_positions]
    fold_manifest = pd.DataFrame(
        {
            "source_row_number": training_manifest[
                "source_row_number"
            ].to_numpy(),
            "cattle_id": training_manifest["cattle_id"].to_numpy(),
            "training_fold": fold_values,
            "random_seed": random_seed,
            "fold_version": fold_version,
        }
    ).sort_values("source_row_number", ignore_index=True)

    fold_counts = {
        str(fold): int((fold_manifest["training_fold"] == fold).sum())
        for fold in range(1, number_of_folds + 1)
    }
    fold_distribution: dict[str, dict[str, dict[str, float | int]]] = {}
    labels_by_source_row = pd.Series(
        dataframe[stratify_column].to_numpy(),
        index=split_manifest["source_row_number"].to_numpy(),
    )
    for fold in range(1, number_of_folds + 1):
        rows = fold_manifest.loc[
            fold_manifest["training_fold"] == fold, "source_row_number"
        ]
        fold_labels = labels_by_source_row.loc[rows.to_numpy()]
        counts = fold_labels.value_counts().sort_index()
        fold_distribution[str(fold)] = {
            str(category): {
                "count": int(count),
                "percentage": round(int(count) / len(fold_labels) * 100, 6),
            }
            for category, count in counts.items()
        }

    non_training_rows = set(
        split_manifest.loc[
            split_manifest["split"] != "train", "source_row_number"
        ].tolist()
    )
    assigned_rows = set(fold_manifest["source_row_number"].tolist())
    summary: dict[str, Any] = {
        "training_row_count": len(fold_manifest),
        "number_of_folds": number_of_folds,
        "fold_counts": fold_counts,
        "random_seed": random_seed,
        "fold_version": fold_version,
        "fold_algorithm": "StratifiedKFold on training rows only",
        "stratification_column": stratify_column,
        "feed_type_distribution_by_fold": fold_distribution,
        "checks": {
            "every_training_row_assigned_once": (
                len(fold_manifest) == len(train_positions)
                and not fold_manifest["source_row_number"].duplicated().any()
            ),
            "validation_and_test_rows_excluded": not bool(
                assigned_rows.intersection(non_training_rows)
            ),
            "duplicate_source_row_count": int(
                fold_manifest["source_row_number"].duplicated().sum()
            ),
            "contains_predictions": any(
                "predict" in str(column).casefold()
                for column in fold_manifest.columns
            ),
        },
    }
    summary["reproducibility_hash_sha256"] = _dataframe_hash(fold_manifest)
    return FoldAssignmentResult(manifest=fold_manifest, summary=summary)


def write_split_artifacts(
    split_result: SplitAssignmentResult,
    *,
    manifest_path: str | Path,
    summary_path: str | Path,
    report_path: str | Path,
) -> None:
    """Write the compact manifest, JSON summary, and human-readable report."""

    manifest_target = Path(manifest_path)
    summary_target = Path(summary_path)
    report_target = Path(report_path)
    for target in (manifest_target, summary_target, report_target):
        target.parent.mkdir(parents=True, exist_ok=True)
    split_result.manifest.to_csv(
        manifest_target,
        index=False,
        lineterminator="\n",
    )
    summary_target.write_text(
        json.dumps(split_result.summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_target.write_text(
        render_split_report(split_result.summary),
        encoding="utf-8",
    )


def write_fold_artifacts(
    fold_result: FoldAssignmentResult,
    *,
    manifest_path: str | Path,
    summary_path: str | Path,
) -> None:
    """Write training-only OOF fold assignments and their summary."""

    manifest_target = Path(manifest_path)
    summary_target = Path(summary_path)
    for target in (manifest_target, summary_target):
        target.parent.mkdir(parents=True, exist_ok=True)
    fold_result.manifest.to_csv(
        manifest_target,
        index=False,
        lineterminator="\n",
    )
    summary_target.write_text(
        json.dumps(fold_result.summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _markdown_distribution(
    distribution: dict[str, dict[str, dict[str, float | int]]],
) -> list[str]:
    lines = ["| Split | Category | Count | Percentage |", "|---|---|---:|---:|"]
    for split, categories in distribution.items():
        for category, values in categories.items():
            lines.append(
                f"| {split} | {category} | {values['count']} | "
                f"{values['percentage']:.6f}% |"
            )
    return lines


def _markdown_numeric_summary(
    summaries: dict[str, dict[str, float | int | None]],
) -> list[str]:
    lines = [
        "| Split | Count | Mean | Std | Min | P25 | Median | P75 | Max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split, item in summaries.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    split,
                    str(item["count"]),
                    str(item["mean"]),
                    str(item["standard_deviation"]),
                    str(item["minimum"]),
                    str(item["p25"]),
                    str(item["median"]),
                    str(item["p75"]),
                    str(item["maximum"]),
                ]
            )
            + " |"
        )
    return lines


def render_split_report(summary: dict[str, Any]) -> str:
    """Render the required deterministic split report."""

    counts = summary["row_counts"]
    percentages = summary["percentages"]
    checks = summary["checks"]
    feed_difference = summary["feed_quantity_distribution_difference"]
    milk_difference = summary["milk_yield_distribution_difference"]
    lines = [
        "# FarmLite Data Split Report",
        "",
        "## Summary",
        "",
        f"- Total rows: {summary['total_row_count']:,}",
        f"- Training: {counts['train']:,} ({percentages['train']:.6f}%)",
        (
            f"- Validation: {counts['validation']:,} "
            f"({percentages['validation']:.6f}%)"
        ),
        f"- Test: {counts['test']:,} ({percentages['test']:.6f}%)",
        f"- Random seed: {summary['random_seed']}",
        f"- Split version: `{summary['split_version']}`",
        f"- Algorithm: {summary['split_algorithm']}",
        "",
        "## Feed_Type Distribution by Split",
        "",
        *_markdown_distribution(summary["feed_type_distribution"]),
        "",
        "## Feed_Quantity_kg Summary by Split",
        "",
        *_markdown_numeric_summary(summary["feed_quantity_kg_summary"]),
        "",
        (
            "Material distribution difference detected: "
            f"**{feed_difference['material_difference_detected']}** "
            f"(maximum standardized mean difference "
            f"{feed_difference['maximum_standardized_mean_difference']}; "
            f"threshold {feed_difference['materiality_threshold']})."
        ),
        "",
        "## Milk_Yield_L Summary by Split",
        "",
        *_markdown_numeric_summary(summary["milk_yield_l_summary"]),
        "",
        (
            "Material distribution difference detected: "
            f"**{milk_difference['material_difference_detected']}** "
            f"(maximum standardized mean difference "
            f"{milk_difference['maximum_standardized_mean_difference']}; "
            f"threshold {milk_difference['materiality_threshold']})."
        ),
        "",
        "## Integrity Checks",
        "",
        f"- Cattle_ID overlap count: {checks['cattle_id_overlap_count']}",
        (
            "- Duplicate source-row count: "
            f"{checks['duplicate_source_row_count']}"
        ),
        f"- Missing assignment count: {checks['missing_assignment_count']}",
        f"- Every row assigned once: {checks['each_row_assigned_once']}",
        (
            "- Manifest fields are traceability-only: "
            f"{checks['manifest_columns_are_traceability_only']}"
        ),
        (
            "- Reproducibility SHA-256: "
            f"`{summary['reproducibility_hash_sha256']}`"
        ),
        "",
        "## Limitations",
        "",
        "- The source is publisher-declared synthetic data.",
        "- Feed quantity basis and measurement period are not independently validated.",
        "- Milk-yield measurement period and zero meaning are not independently validated.",
        "- The random split is not evidence of real-world generalization.",
        "- Cattle_ID is retained only for traceability and never as a predictive feature.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "DEFAULT_OOF_FOLDS",
    "DEFAULT_RANDOM_SEED",
    "DEFAULT_TEST_FRACTION",
    "DEFAULT_TRAIN_FRACTION",
    "DEFAULT_VALIDATION_FRACTION",
    "FOLD_VERSION",
    "SPLIT_NAMES",
    "SPLIT_VERSION",
    "SplitAssignmentError",
    "create_split_assignments",
    "create_training_fold_assignments",
    "render_split_report",
    "write_fold_artifacts",
    "write_split_artifacts",
]
