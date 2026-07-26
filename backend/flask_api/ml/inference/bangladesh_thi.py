"""Validated THI calculation for the Bangladesh candidate contract."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Any

from config.settings import FLASK_API_DIR


CONTRACT_PATH = (
    FLASK_API_DIR / "config" / "bangladesh_thi_mapping_contract.json"
)
EXPECTED_EXPRESSION = (
    "(1.8 * T + 32) - ((0.55 - 0.0055 * RH) * (1.8 * T - 26))"
)
ENVIRONMENT_LIMITATION = (
    "The study workbooks do not contain numeric temperature, humidity, or "
    "THI values, so numeric environmental-range overlap is unresolved."
)


@dataclass(frozen=True)
class ThiResult:
    """Structured THI mapping success or failure."""

    status: str
    calculated_thi: float | None
    display_thi: float | None
    thi_category: str | None
    mapping_version: str
    verification_status: str
    error_code: str | None
    warnings: tuple[str, ...]


def _load_contract() -> dict[str, Any]:
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Bangladesh THI mapping contract must be an object.")
    formula = value.get("formula")
    if (
        not isinstance(formula, dict)
        or formula.get("expression") != EXPECTED_EXPRESSION
        or formula.get("verified") is not True
    ):
        raise RuntimeError("Bangladesh THI formula contract is incompatible.")
    return value


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def categorize_thi(
    calculated_thi: float,
    *,
    contract: dict[str, Any] | None = None,
) -> str | None:
    """Apply the exact unrounded T0/T1/T2 boundary contract."""

    mapping = _load_contract() if contract is None else contract
    if not _is_finite_number(calculated_thi):
        return None

    value = float(calculated_thi)
    categories = mapping["categories"]
    for category in categories:
        minimum = category["minimum"]
        maximum = category["maximum"]
        above_minimum = (
            True
            if minimum is None
            else value >= minimum
            if category["minimum_inclusive"]
            else value > minimum
        )
        below_maximum = (
            True
            if maximum is None
            else value <= maximum
            if category["maximum_inclusive"]
            else value < maximum
        )
        if above_minimum and below_maximum:
            return str(category["label"])
    return None


def calculate_thi(
    ambient_temperature_c: object,
    humidity_percent: object,
) -> ThiResult:
    """Validate measured inputs, calculate THI, and derive its category."""

    contract = _load_contract()
    version = str(contract["contract_version"])
    verification = str(contract["verification_status"])

    if ambient_temperature_c is None:
        return ThiResult(
            "MISSING_REQUIRED_INPUT",
            None,
            None,
            None,
            version,
            verification,
            "TEMPERATURE_MISSING",
            (),
        )
    if humidity_percent is None:
        return ThiResult(
            "MISSING_REQUIRED_INPUT",
            None,
            None,
            None,
            version,
            verification,
            "HUMIDITY_MISSING",
            (),
        )
    if not _is_finite_number(ambient_temperature_c):
        return ThiResult(
            "INVALID_ENVIRONMENT_INPUT",
            None,
            None,
            None,
            version,
            verification,
            "TEMPERATURE_INVALID",
            (),
        )
    if not _is_finite_number(humidity_percent):
        return ThiResult(
            "INVALID_ENVIRONMENT_INPUT",
            None,
            None,
            None,
            version,
            verification,
            "HUMIDITY_INVALID",
            (),
        )

    temperature = float(ambient_temperature_c)
    humidity = float(humidity_percent)
    humidity_policy = contract["input_policy"]["humidity_percent"]
    if (
        humidity < float(humidity_policy["minimum"])
        or humidity > float(humidity_policy["maximum"])
    ):
        return ThiResult(
            "INVALID_ENVIRONMENT_INPUT",
            None,
            None,
            None,
            version,
            verification,
            "HUMIDITY_OUT_OF_RANGE",
            (),
        )

    calculated = (1.8 * temperature + 32) - (
        (0.55 - 0.0055 * humidity) * (1.8 * temperature - 26)
    )
    if not math.isfinite(calculated):
        return ThiResult(
            "INVALID_ENVIRONMENT_INPUT",
            None,
            None,
            None,
            version,
            verification,
            "THI_CALCULATION_FAILED",
            (),
        )

    category = categorize_thi(calculated, contract=contract)
    if category not in set(contract["pipeline_category_labels_verified"]):
        return ThiResult(
            "UNKNOWN_THI_CATEGORY",
            calculated,
            round(calculated, 2),
            None,
            version,
            verification,
            "THI_CATEGORY_UNSUPPORTED",
            (ENVIRONMENT_LIMITATION,),
        )

    return ThiResult(
        "ELIGIBLE",
        calculated,
        round(calculated, 2),
        category,
        version,
        verification,
        None,
        (ENVIRONMENT_LIMITATION,),
    )


__all__ = ["ThiResult", "calculate_thi", "categorize_thi"]
