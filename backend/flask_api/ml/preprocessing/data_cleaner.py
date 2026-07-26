"""Transparent value cleaning that preserves rows and records every action."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.feature_builder import (
    BASE_CATEGORICAL_FEATURES,
    BASE_NUMERIC_FEATURES,
    DEFAULT_CONTRACT_PATH,
    load_model_contract,
)
from ml.preprocessing.preprocessing_types import DataCleanResult


ISSUE_COLUMNS = [
    "source_row_number",
    "cattle_id",
    "field",
    "issue_type",
    "original_value",
    "normalized_value",
    "severity",
    "action",
]
NUMERIC_COLUMNS = [
    *BASE_NUMERIC_FEATURES,
    "feed_quantity_kg",
    "milk_yield_l",
]
CATEGORICAL_COLUMNS = [
    *BASE_CATEGORICAL_FEATURES,
    "feed_type",
    "predicted_feed_type",
]


def _row_identity(dataframe: pd.DataFrame, position: int) -> tuple[int, Any]:
    source_row = (
        int(dataframe.iloc[position]["source_row_number"])
        if "source_row_number" in dataframe.columns
        and pd.notna(dataframe.iloc[position]["source_row_number"])
        else position + 1
    )
    cattle_id = (
        dataframe.iloc[position]["cattle_id"]
        if "cattle_id" in dataframe.columns
        else None
    )
    return source_row, cattle_id


def _issue(
    dataframe: pd.DataFrame,
    position: int,
    field: str,
    issue_type: str,
    original_value: Any,
    normalized_value: Any,
    severity: str,
    action: str,
) -> dict[str, Any]:
    source_row, cattle_id = _row_identity(dataframe, position)
    return {
        "source_row_number": source_row,
        "cattle_id": cattle_id,
        "field": field,
        "issue_type": issue_type,
        "original_value": original_value,
        "normalized_value": normalized_value,
        "severity": severity,
        "action": action,
    }


def clean_data(
    dataframe: pd.DataFrame,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> DataCleanResult:
    """Normalize approved formatting and numeric parsing without dropping rows."""

    contract = load_model_contract(contract_path)
    cleaned = dataframe.copy()
    issues: list[dict[str, Any]] = []
    feature_catalog = contract["shared_validation"]["feature_catalog"]
    feed_categories = contract["models"]["feed_type_classifier"]["target"][
        "allowed_categories"
    ]

    category_sets: dict[str, list[str]] = {
        "breed": list(
            feature_catalog["breed"]["allowed_range_or_categories"]
        ),
        "lactation_stage": list(
            feature_catalog["lactation_stage"]["allowed_range_or_categories"]
        ),
        "feed_type": list(feed_categories),
        "predicted_feed_type": list(feed_categories),
    }
    lactation_mapping = feature_catalog["lactation_stage"].get(
        "application_to_dataset_mapping", {}
    )
    approved_value_mappings = {
        key.casefold(): value
        for key, value in lactation_mapping.items()
        if value != "NOT_SUPPORTED_BY_DATASET"
    }

    for field in CATEGORICAL_COLUMNS:
        if field not in cleaned.columns:
            continue
        allowed = category_sets[field]
        allowed_casefold = {value.casefold(): value for value in allowed}
        source = cleaned[field]
        rendered = source.astype("string")
        stripped = rendered.str.strip()
        empty_mask = source.notna() & stripped.eq("").fillna(False)
        normalized = stripped.copy()
        if field == "lactation_stage":
            approved = stripped.str.casefold().map(approved_value_mappings)
            normalized = approved.fillna(normalized)
        approved_case = normalized.str.casefold().map(allowed_casefold)
        normalized = approved_case.fillna(normalized)
        normalized = normalized.mask(empty_mask, pd.NA)

        changed_mask = (
            source.notna()
            & ~empty_mask
            & normalized.ne(rendered).fillna(False)
        )
        unknown_mask = (
            source.notna()
            & ~empty_mask
            & ~normalized.isin(allowed).fillna(False)
        )
        cleaned[field] = normalized

        for position in np.flatnonzero(empty_mask.to_numpy()):
            issues.append(
                _issue(
                    dataframe,
                    int(position),
                    field,
                    "EMPTY_STRING",
                    source.iloc[position],
                    None,
                    "WARNING",
                    "SET_TO_MISSING",
                )
            )
        for position in np.flatnonzero(changed_mask.to_numpy()):
            original = source.iloc[position]
            normalized_value = normalized.iloc[position]
            issue_type = (
                "SURROUNDING_WHITESPACE"
                if str(original).strip() != str(original)
                and str(original).strip() == normalized_value
                else "APPROVED_CATEGORY_NORMALIZATION"
            )
            issues.append(
                _issue(
                    dataframe,
                    int(position),
                    field,
                    issue_type,
                    original,
                    normalized_value,
                    "INFO",
                    "NORMALIZED",
                )
            )
        for position in np.flatnonzero(unknown_mask.to_numpy()):
            issues.append(
                _issue(
                    dataframe,
                    int(position),
                    field,
                    "UNKNOWN_CATEGORY",
                    source.iloc[position],
                    normalized.iloc[position],
                    "WARNING",
                    "PRESERVED",
                )
            )

    for field in NUMERIC_COLUMNS:
        if field not in cleaned.columns:
            continue
        source = cleaned[field]
        numeric = pd.to_numeric(source, errors="coerce")
        invalid_mask = source.notna() & numeric.isna()
        infinite_mask = numeric.notna() & ~np.isfinite(numeric)
        string_mask = source.map(lambda value: isinstance(value, str))
        numeric_string_mask = (
            string_mask & numeric.notna() & np.isfinite(numeric)
        )
        numeric = numeric.mask(infinite_mask, np.nan)
        for position in np.flatnonzero(invalid_mask.to_numpy()):
            issues.append(
                _issue(
                    dataframe,
                    int(position),
                    field,
                    "INVALID_NUMERIC_VALUE",
                    source.iloc[position],
                    None,
                    "ERROR",
                    "SET_TO_MISSING",
                )
            )
        for position in np.flatnonzero(infinite_mask.to_numpy()):
            issues.append(
                _issue(
                    dataframe,
                    int(position),
                    field,
                    "NON_FINITE_NUMERIC_VALUE",
                    source.iloc[position],
                    None,
                    "ERROR",
                    "SET_TO_MISSING",
                )
            )
        for position in np.flatnonzero(numeric_string_mask.to_numpy()):
            issues.append(
                _issue(
                    dataframe,
                    int(position),
                    field,
                    "NUMERIC_STRING",
                    source.iloc[position],
                    numeric.iloc[position],
                    "INFO",
                    "NORMALIZED",
                )
            )
        cleaned[field] = numeric

    issue_frame = pd.DataFrame(issues, columns=ISSUE_COLUMNS)
    action_counts = (
        issue_frame["action"].value_counts().sort_index().to_dict()
        if not issue_frame.empty
        else {}
    )
    issue_type_counts = (
        issue_frame["issue_type"].value_counts().sort_index().to_dict()
        if not issue_frame.empty
        else {}
    )
    metadata = {
        "input_row_count": len(dataframe),
        "output_row_count": len(cleaned),
        "row_order_preserved": bool(cleaned.index.equals(dataframe.index)),
        "rows_dropped": 0,
        "issue_count": len(issue_frame),
        "action_counts": {str(key): int(value) for key, value in action_counts.items()},
        "issue_type_counts": {
            str(key): int(value) for key, value in issue_type_counts.items()
        },
    }
    return DataCleanResult(
        dataframe=cleaned,
        issues=issue_frame,
        metadata=metadata,
    )


__all__ = [
    "CATEGORICAL_COLUMNS",
    "ISSUE_COLUMNS",
    "NUMERIC_COLUMNS",
    "clean_data",
]
