"""Primitive request validation for the backend-only prediction API v2."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Any


MAX_REQUEST_BYTES = 16 * 1024
MAX_TEXT_LENGTH = 256

ALLOWED_FIELDS = {
    "breed",
    "genetic_group",
    "age_months",
    "weight_kg",
    "lactation_stage",
    "days_in_milk",
    "previous_week_avg_yield_l",
    "body_condition_score",
    "ambient_temperature_c",
    "humidity_percent",
    "health_status",
}
REQUIRED_GENERAL_FIELDS = {
    "breed",
    "age_months",
    "weight_kg",
    "lactation_stage",
}
OPTIONAL_NUMERIC_FIELDS = {
    "previous_week_avg_yield_l",
    "body_condition_score",
    "ambient_temperature_c",
    "humidity_percent",
}


@dataclass(frozen=True)
class RequestValidationResult:
    """Validated value or controlled field errors."""

    valid: bool
    value: dict[str, Any] | None
    field_errors: dict[str, str]


def _is_number(value: object) -> bool:
    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def validate_v2_request(data: dict[str, Any]) -> RequestValidationResult:
    """Validate primitive JSON types without applying candidate fallbacks."""

    errors: dict[str, str] = {}
    unknown_fields = sorted(set(data) - ALLOWED_FIELDS)
    for field in unknown_fields:
        errors[field] = "Unexpected field."

    for field in REQUIRED_GENERAL_FIELDS:
        if field not in data or data[field] is None:
            errors[field] = "Required field is missing."

    for field in (
        "breed",
        "lactation_stage",
        "genetic_group",
        "health_status",
    ):
        value = data.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            errors[field] = "Must be a string."
        elif not value.strip():
            errors[field] = "Must not be empty."
        elif len(value) > MAX_TEXT_LENGTH:
            errors[field] = "Text value is too long."

    age = data.get("age_months")
    if age is not None:
        if isinstance(age, bool) or not isinstance(age, int):
            errors["age_months"] = "Must be an integer."
        elif age <= 0:
            errors["age_months"] = "Must be greater than zero."

    weight = data.get("weight_kg")
    if weight is not None:
        if not _is_number(weight):
            errors["weight_kg"] = "Must be a finite number."
        elif float(weight) <= 0:
            errors["weight_kg"] = "Must be greater than zero."

    days_in_milk = data.get("days_in_milk")
    if days_in_milk is not None:
        if isinstance(days_in_milk, bool) or not isinstance(days_in_milk, int):
            errors["days_in_milk"] = "Must be an integer or null."
        elif days_in_milk < 0:
            errors["days_in_milk"] = "Must be zero or greater."

    for field in OPTIONAL_NUMERIC_FIELDS:
        value = data.get(field)
        if value is not None and not _is_number(value):
            errors[field] = "Must be a finite number or null."

    non_negative_fields = {
        "previous_week_avg_yield_l",
    }
    for field in non_negative_fields:
        value = data.get(field)
        if _is_number(value) and float(value) < 0:
            errors[field] = "Must be zero or greater."

    body_condition_score = data.get("body_condition_score")
    if _is_number(body_condition_score) and not (
        1 <= float(body_condition_score) <= 5
    ):
        errors["body_condition_score"] = "Must be from 1 through 5."

    if errors:
        return RequestValidationResult(False, None, errors)

    normalized = dict(data)
    for field in ("breed", "lactation_stage", "genetic_group", "health_status"):
        if isinstance(normalized.get(field), str):
            normalized[field] = normalized[field].strip()
    return RequestValidationResult(True, normalized, {})


__all__ = [
    "MAX_REQUEST_BYTES",
    "RequestValidationResult",
    "validate_v2_request",
]
