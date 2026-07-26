"""Contract-aware schema validation without silently deleting records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.feature_builder import (
    DEFAULT_CONTRACT_PATH,
    get_model_spec,
    load_model_contract,
)
from ml.preprocessing.preprocessing_types import (
    ValidationIssue,
    ValidationMode,
    ValidationResult,
    ValidationSeverity,
)


TARGET_FIELDS = {"feed_type", "feed_quantity_kg", "milk_yield_l"}
TRACEABILITY_FIELDS = {
    "animal_name",
    "animal_type",
    "cattle_id",
    "farm_id",
    "health_status",
    "observation_date",
    "production_stage",
    "source_row_number",
}
HARD_NONNEGATIVE_FIELDS = {
    "age_months",
    "weight_kg",
    "days_in_milk",
    "previous_week_avg_yield_l",
    "body_condition_score",
    "feed_quantity_kg",
    "milk_yield_l",
}
SUSPICIOUS_RANGE_ONLY_FIELDS = {
    "ambient_temperature_c",
    "body_condition_score",
    "days_in_milk",
    "previous_week_avg_yield_l",
}


def _sample_rows(mask: pd.Series, limit: int = 5) -> list[int]:
    positions = np.flatnonzero(mask.to_numpy())[:limit]
    return [int(position + 1) for position in positions]


def _sample_values(series: pd.Series, mask: pd.Series, limit: int = 5) -> list[str]:
    return sorted(map(str, series.loc[mask].drop_duplicates().head(limit).tolist()))


def _append_issue(
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
    issue: ValidationIssue,
) -> None:
    (errors if issue.severity == ValidationSeverity.ERROR else warnings).append(
        issue
    )


def _allowed_categories(
    contract: dict[str, Any],
    field: str,
) -> list[str] | None:
    if field == "feed_type" or field == "predicted_feed_type":
        return list(
            contract["models"]["feed_type_classifier"]["target"][
                "allowed_categories"
            ]
        )
    feature = contract["shared_validation"]["feature_catalog"].get(field)
    if feature is None:
        return None
    allowed = feature.get("allowed_range_or_categories")
    return list(allowed) if isinstance(allowed, list) else None


def _numeric_range(
    contract: dict[str, Any],
    field: str,
) -> dict[str, float] | None:
    feature = contract["shared_validation"]["feature_catalog"].get(field)
    if feature is not None:
        allowed = feature.get("allowed_range_or_categories")
        return dict(allowed) if isinstance(allowed, dict) else None
    if field == "feed_quantity_kg":
        observed = contract["models"]["feed_quantity_regressor"]["target"].get(
            "observed_range"
        )
        if observed:
            return {
                "dataset_observed_minimum": observed["minimum"],
                "dataset_observed_maximum": observed["maximum"],
            }
    if field == "milk_yield_l":
        observed = contract["models"]["milk_yield_regressor"]["target"].get(
            "observed_range"
        )
        if observed:
            return {
                "dataset_observed_minimum": observed["minimum"],
                "dataset_observed_maximum": observed["maximum"],
            }
    return None


def validate_schema(
    dataframe: pd.DataFrame,
    model_name: str,
    *,
    mode: ValidationMode | str,
    require_target: bool | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> ValidationResult:
    """Validate one canonical dataframe and return structured evidence."""

    validation_mode = ValidationMode(mode)
    contract = load_model_contract(contract_path)
    spec = get_model_spec(model_name, contract_path=contract_path)
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    missing_required: list[str] = []
    unknown_categories: dict[str, list[str]] = {}
    range_violations: list[dict[str, Any]] = []
    leakage_fields: list[str] = []

    duplicate_columns = sorted(
        set(
            map(
                str,
                dataframe.columns[dataframe.columns.duplicated(keep=False)],
            )
        )
    )
    if duplicate_columns:
        errors.append(
            ValidationIssue(
                field="__schema__",
                issue_type="DUPLICATE_CANONICAL_COLUMNS",
                severity=ValidationSeverity.ERROR,
                message=(
                    "Duplicate canonical columns: "
                    + ", ".join(duplicate_columns)
                ),
                affected_count=len(duplicate_columns),
                values=duplicate_columns,
                action="REJECTED_BY_SCHEMA",
            )
        )
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            missing_required_fields=[],
            unexpected_fields=[],
            unknown_categories={},
            range_violations=[],
            leakage_fields=[],
            row_count=len(dataframe),
        )

    target_required = (
        validation_mode != ValidationMode.INFERENCE_INPUT
        if require_target is None
        else require_target
    )
    if validation_mode == ValidationMode.INFERENCE_INPUT:
        required_features = [
            feature
            for feature in spec.feature_names
            if feature
            != "predicted_feed_type"
            and contract["shared_validation"]["feature_catalog"]
            .get(feature, {})
            .get("required", False)
        ]
        if model_name == "feed_quantity_regressor_design_b":
            required_features.append("predicted_feed_type")
    else:
        required_features = list(spec.feature_names)

    for field in required_features:
        if field not in dataframe.columns:
            missing_required.append(field)
    if target_required and spec.target_name not in dataframe.columns:
        missing_required.append(spec.target_name)
    if missing_required:
        errors.append(
            ValidationIssue(
                field="__schema__",
                issue_type="MISSING_REQUIRED_FIELDS",
                severity=ValidationSeverity.ERROR,
                message=(
                    "Missing required fields: " + ", ".join(missing_required)
                ),
                affected_count=len(missing_required),
                values=list(missing_required),
                action="REJECTED_BY_SCHEMA",
            )
        )

    if validation_mode == ValidationMode.INFERENCE_INPUT:
        supplied_targets = sorted(TARGET_FIELDS.intersection(dataframe.columns))
        if supplied_targets:
            leakage_fields.extend(supplied_targets)
            errors.append(
                ValidationIssue(
                    field="__schema__",
                    issue_type="TARGET_FIELDS_FORBIDDEN_AT_INFERENCE",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        "Inference input must not contain targets: "
                        + ", ".join(supplied_targets)
                    ),
                    affected_count=len(supplied_targets),
                    values=supplied_targets,
                    action="REJECTED_BY_SCHEMA",
                )
            )

    if spec.target_name in spec.feature_names:
        leakage_fields.append(spec.target_name)
        errors.append(
            ValidationIssue(
                field=spec.target_name,
                issue_type="TARGET_LEAKAGE",
                severity=ValidationSeverity.ERROR,
                message="The model target appears in the selected feature list.",
                action="REJECTED_BY_SCHEMA",
            )
        )

    expected = set(spec.feature_names)
    if target_required:
        expected.add(spec.target_name)
    unexpected = sorted(
        set(map(str, dataframe.columns)) - expected - TRACEABILITY_FIELDS
    )

    catalog = contract["shared_validation"]["feature_catalog"]
    categorical_fields = [
        field
        for field in [*spec.categorical_features, spec.target_name]
        if field in dataframe.columns
        and (_allowed_categories(contract, field) is not None)
    ]
    for field in categorical_fields:
        series = dataframe[field]
        allowed = _allowed_categories(contract, field) or []
        allowed_exact = set(allowed)
        allowed_casefold = {value.casefold(): value for value in allowed}
        observed = series.dropna().astype(str)
        unknown = sorted(
            {
                value
                for value in observed
                if value.strip() not in allowed_exact
                and value.strip().casefold() not in allowed_casefold
            }
        )
        case_or_space_variants = sorted(
            {
                value
                for value in observed
                if value not in allowed_exact
                and value.strip().casefold() in allowed_casefold
            }
        )
        if unknown:
            unknown_categories[field] = unknown
            severity = (
                ValidationSeverity.ERROR
                if field == spec.target_name
                and validation_mode != ValidationMode.INFERENCE_INPUT
                else ValidationSeverity.WARNING
            )
            _append_issue(
                errors,
                warnings,
                ValidationIssue(
                    field=field,
                    issue_type="UNKNOWN_CATEGORY",
                    severity=severity,
                    message=(
                        f"Unseen category values were preserved for '{field}'."
                    ),
                    affected_count=int(series.astype("string").isin(unknown).sum()),
                    values=unknown[:10],
                    action=(
                        "REJECTED_BY_SCHEMA"
                        if severity == ValidationSeverity.ERROR
                        else "PRESERVED"
                    ),
                ),
            )
        if case_or_space_variants:
            warnings.append(
                ValidationIssue(
                    field=field,
                    issue_type="CATEGORY_FORMAT_VARIANT",
                    severity=ValidationSeverity.WARNING,
                    message=(
                        f"Case or surrounding whitespace differs from the "
                        f"approved categories for '{field}'."
                    ),
                    affected_count=int(
                        series.astype("string").isin(case_or_space_variants).sum()
                    ),
                    values=case_or_space_variants[:10],
                    action="NORMALIZED",
                )
            )

    numeric_fields = [
        field
        for field in [*spec.numeric_features, spec.target_name]
        if field in dataframe.columns
        and (
            field in spec.numeric_features
            or field in {"feed_quantity_kg", "milk_yield_l"}
        )
    ]
    required_value_fields = {
        field
        for field in spec.feature_names
        if catalog.get(field, {}).get("required", False)
    }
    if target_required:
        required_value_fields.add(spec.target_name)

    for field in numeric_fields:
        source = dataframe[field]
        numeric = pd.to_numeric(source, errors="coerce")
        invalid_conversion = source.notna() & numeric.isna()
        if invalid_conversion.any():
            errors.append(
                ValidationIssue(
                    field=field,
                    issue_type="INVALID_NUMERIC_VALUE",
                    severity=ValidationSeverity.ERROR,
                    message=f"Non-numeric values were found in '{field}'.",
                    affected_count=int(invalid_conversion.sum()),
                    sample_rows=_sample_rows(invalid_conversion),
                    values=_sample_values(source, invalid_conversion),
                    action="REJECTED_BY_SCHEMA",
                )
            )

        finite_mask = numeric.notna() & ~np.isfinite(numeric)
        if finite_mask.any():
            errors.append(
                ValidationIssue(
                    field=field,
                    issue_type="NON_FINITE_NUMERIC_VALUE",
                    severity=ValidationSeverity.ERROR,
                    message=f"NaN or infinite values were found in '{field}'.",
                    affected_count=int(finite_mask.sum()),
                    sample_rows=_sample_rows(finite_mask),
                    values=_sample_values(source, finite_mask),
                    action="REJECTED_BY_SCHEMA",
                )
            )

        missing_mask = numeric.isna() & ~invalid_conversion
        if missing_mask.any():
            severity = (
                ValidationSeverity.ERROR
                if field in required_value_fields
                else ValidationSeverity.WARNING
            )
            _append_issue(
                errors,
                warnings,
                ValidationIssue(
                    field=field,
                    issue_type="MISSING_NUMERIC_VALUE",
                    severity=severity,
                    message=(
                        f"Missing numeric values found in '{field}'. "
                        + (
                            "Required values cannot be imputed."
                            if severity == ValidationSeverity.ERROR
                            else "They remain for training-only pipeline imputation."
                        )
                    ),
                    affected_count=int(missing_mask.sum()),
                    sample_rows=_sample_rows(missing_mask),
                    action=(
                        "REJECTED_BY_SCHEMA"
                        if severity == ValidationSeverity.ERROR
                        else "PRESERVED"
                    ),
                ),
            )

        if field in HARD_NONNEGATIVE_FIELDS:
            negative = numeric.notna() & (numeric < 0)
            if negative.any():
                errors.append(
                    ValidationIssue(
                        field=field,
                        issue_type="HARD_INVALID_NEGATIVE",
                        severity=ValidationSeverity.ERROR,
                        message=f"Negative values are invalid for '{field}'.",
                        affected_count=int(negative.sum()),
                        sample_rows=_sample_rows(negative),
                        values=_sample_values(source, negative),
                        action="REJECTED_BY_SCHEMA",
                    )
                )
                range_violations.append(
                    {
                        "field": field,
                        "rule": "minimum=0",
                        "affected_count": int(negative.sum()),
                        "severity": "ERROR",
                    }
                )

        if field == "humidity_percent":
            humidity_invalid = numeric.notna() & (
                (numeric < 0) | (numeric > 100)
            )
            if humidity_invalid.any():
                errors.append(
                    ValidationIssue(
                        field=field,
                        issue_type="HARD_INVALID_HUMIDITY",
                        severity=ValidationSeverity.ERROR,
                        message="Humidity must remain between 0 and 100 percent.",
                        affected_count=int(humidity_invalid.sum()),
                        sample_rows=_sample_rows(humidity_invalid),
                        values=_sample_values(source, humidity_invalid),
                        action="REJECTED_BY_SCHEMA",
                    )
                )
                range_violations.append(
                    {
                        "field": field,
                        "rule": "0 <= value <= 100",
                        "affected_count": int(humidity_invalid.sum()),
                        "severity": "ERROR",
                    }
                )

        limits = _numeric_range(contract, field)
        if limits:
            minimum = limits.get("validation_minimum")
            maximum = limits.get("validation_maximum")
            outside = pd.Series(False, index=dataframe.index)
            if minimum is not None:
                outside |= numeric.notna() & (numeric < float(minimum))
            if maximum is not None:
                outside |= numeric.notna() & (numeric > float(maximum))
            if outside.any():
                inference_hard = (
                    validation_mode == ValidationMode.INFERENCE_INPUT
                    and field in {"age_months", "weight_kg", "humidity_percent"}
                )
                severity = (
                    ValidationSeverity.ERROR
                    if inference_hard
                    else ValidationSeverity.WARNING
                )
                _append_issue(
                    errors,
                    warnings,
                    ValidationIssue(
                        field=field,
                        issue_type="CONTRACT_RANGE_VIOLATION",
                        severity=severity,
                        message=(
                            f"Values outside the approved contract range were "
                            f"found for '{field}'. These synthetic-data bounds "
                            "are not biological safety limits."
                        ),
                        affected_count=int(outside.sum()),
                        sample_rows=_sample_rows(outside),
                        values=_sample_values(source, outside),
                        action=(
                            "REJECTED_BY_SCHEMA"
                            if severity == ValidationSeverity.ERROR
                            else "PRESERVED"
                        ),
                    ),
                )
                range_violations.append(
                    {
                        "field": field,
                        "rule": f"{minimum} <= value <= {maximum}",
                        "affected_count": int(outside.sum()),
                        "severity": severity.value,
                    }
                )

        if field == "milk_yield_l":
            zero = numeric.notna() & (numeric == 0)
            if zero.any():
                warnings.append(
                    ValidationIssue(
                        field=field,
                        issue_type="ZERO_SYNTHETIC_MILK_TARGET",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            "Zero synthetic milk-yield targets are preserved; "
                            "their meaning is not documented."
                        ),
                        affected_count=int(zero.sum()),
                        sample_rows=_sample_rows(zero),
                        action="PRESERVED",
                    )
                )

    categorical_required = [
        field
        for field in spec.categorical_features
        if field in dataframe.columns
        and (
            validation_mode != ValidationMode.INFERENCE_INPUT
            or catalog.get(field, {}).get("required", field == "predicted_feed_type")
        )
    ]
    if (
        target_required
        and spec.target_name in dataframe.columns
        and _allowed_categories(contract, spec.target_name) is not None
    ):
        categorical_required.append(spec.target_name)
    for field in categorical_required:
        missing_mask = dataframe[field].isna() | (
            dataframe[field].astype("string").str.strip() == ""
        )
        if missing_mask.any():
            errors.append(
                ValidationIssue(
                    field=field,
                    issue_type="MISSING_REQUIRED_CATEGORY",
                    severity=ValidationSeverity.ERROR,
                    message=f"Required categorical field '{field}' is missing.",
                    affected_count=int(missing_mask.sum()),
                    sample_rows=_sample_rows(missing_mask),
                    action="REJECTED_BY_SCHEMA",
                )
            )

    return ValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        missing_required_fields=missing_required,
        unexpected_fields=unexpected,
        unknown_categories=unknown_categories,
        range_violations=range_violations,
        leakage_fields=sorted(set(leakage_fields)),
        row_count=len(dataframe),
    )


__all__ = [
    "HARD_NONNEGATIVE_FIELDS",
    "TARGET_FIELDS",
    "TRACEABILITY_FIELDS",
    "validate_schema",
]
