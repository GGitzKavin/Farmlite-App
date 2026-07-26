"""Explainable, advisory feed-planning rules for FarmLite."""

from __future__ import annotations

import math
import re
from typing import Any


DEFAULT_WEIGHT_KG = 400.0
WEIGHT_BASED_FALLBACK_RATE = 0.025
SMALL_CATTLE_THRESHOLD_KG = 350.0

ADVISORY_DISCLAIMER = (
    "This recommendation is advisory only and should not replace guidance "
    "from a veterinarian or qualified animal nutritionist."
)

HEALTH_STATUSES_REQUIRING_REVIEW = {
    "sick",
    "critical",
    "under treatment",
    "in treatment",
    "recovering",
}


def _to_finite_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numeric_value):
        return None

    return numeric_value


def _normalize_status(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"
    normalized = re.sub(r"[_-]+", " ", value).strip().lower()
    return re.sub(r"\s+", " ", normalized) or "unknown"


def generate_feed_plan(
    predicted_feed_kg: float,
    weight_kg: float,
    milk_yield_l: float,
    health_status: str,
    production_stage: str | None = None,
) -> dict:
    """Return a conservative, explainable advisory cattle feed plan.

    The planner normalizes invalid inputs, bounds the model prediction using
    body weight, and applies transparent allocation rules. It is not a
    veterinary or animal-nutrition prescription.
    """

    explanation: list[str] = []
    warnings: list[str] = []
    used_fallback = False
    was_clamped = False

    parsed_weight = _to_finite_float(weight_kg)
    if parsed_weight is None or parsed_weight <= 0:
        parsed_weight = DEFAULT_WEIGHT_KG
        used_fallback = True
        warnings.append(
            "Body weight was missing or invalid; a temporary 400 kg fallback "
            "was used. Confirm the animal's weight before using this plan."
        )

    parsed_milk_yield = _to_finite_float(milk_yield_l)
    if parsed_milk_yield is None or parsed_milk_yield < 0:
        parsed_milk_yield = 0.0
        used_fallback = True
        warnings.append(
            "Milk yield was missing or invalid and was treated as 0 L/day."
        )

    minimum_feed = parsed_weight * 0.015
    maximum_feed = parsed_weight * 0.04

    parsed_prediction = _to_finite_float(predicted_feed_kg)
    if parsed_prediction is None or parsed_prediction <= 0:
        parsed_prediction = parsed_weight * WEIGHT_BASED_FALLBACK_RATE
        used_fallback = True
        warnings.append(
            "The model prediction was missing or invalid; a weight-based "
            "fallback of 2.5% of body weight was used."
        )

    bounded_feed = parsed_prediction
    if bounded_feed < minimum_feed:
        bounded_feed = minimum_feed
        was_clamped = True
        warnings.append(
            "The predicted feed quantity was below 1.5% of body weight and "
            "was raised to the advisory minimum."
        )
    elif bounded_feed > maximum_feed:
        bounded_feed = maximum_feed
        was_clamped = True
        warnings.append(
            "The predicted feed quantity exceeded 4.0% of body weight and "
            "was reduced to the advisory maximum."
        )

    if parsed_milk_yield < 5:
        roughage_ratio, concentrate_ratio = 0.75, 0.25
        yield_band = "below 5 L/day"
    elif parsed_milk_yield <= 15:
        roughage_ratio, concentrate_ratio = 0.65, 0.35
        yield_band = "between 5 and 15 L/day"
    elif parsed_milk_yield <= 25:
        roughage_ratio, concentrate_ratio = 0.60, 0.40
        yield_band = "between 15 and 25 L/day"
    else:
        roughage_ratio, concentrate_ratio = 0.55, 0.45
        yield_band = "above 25 L/day"

    roughage_kg = bounded_feed * roughage_ratio
    concentrate_kg = bounded_feed * concentrate_ratio

    normalized_health_status = _normalize_status(health_status)
    if normalized_health_status in HEALTH_STATUSES_REQUIRING_REVIEW:
        concentrate_reduction = concentrate_kg * 0.10
        concentrate_kg -= concentrate_reduction
        roughage_kg += concentrate_reduction
        warnings.append(
            "The animal's health status requires veterinary review; concentrate "
            "was reduced by 10% and the amount was reassigned to roughage."
        )
    elif normalized_health_status == "unknown":
        used_fallback = True
        warnings.append(
            "Health status was missing or invalid; no health-specific feed "
            "adjustment was applied."
        )

    mineral_mix_kg = (
        0.05 if parsed_weight < SMALL_CATTLE_THRESHOLD_KG else 0.10
    )
    feeding_frequency = (
        "3 feedings per day"
        if parsed_milk_yield > 25
        else "2 feedings per day"
    )

    explanation.append(
        f"The model supplied an estimated feed quantity of {parsed_prediction:.2f} kg/day."
    )
    explanation.append(
        f"For a {parsed_weight:.2f} kg animal, the advisory body-weight range is "
        f"{minimum_feed:.2f}-{maximum_feed:.2f} kg/day."
    )
    explanation.append(
        f"Milk yield is {parsed_milk_yield:.2f} L/day ({yield_band}), producing a "
        f"{roughage_ratio * 100:.0f}% roughage and {concentrate_ratio * 100:.0f}% "
        "concentrate starting split."
    )
    explanation.append(
        f"Health status was interpreted as '{normalized_health_status}'."
    )

    if normalized_health_status in HEALTH_STATUSES_REQUIRING_REVIEW:
        explanation.append(
            "The concentrate portion was reduced by 10% because the animal is "
            "sick, recovering, critical, or undergoing treatment."
        )

    if production_stage and str(production_stage).strip():
        explanation.append(
            f"Production stage was recorded as '{str(production_stage).strip()}'; "
            "this version reports the stage but does not apply an additional stage-specific rule."
        )
    else:
        explanation.append(
            "No production stage was supplied, so no stage-specific adjustment was applied."
        )

    confidence_level = (
        "Low"
        if used_fallback
        or was_clamped
        or normalized_health_status in HEALTH_STATUSES_REQUIRING_REVIEW
        else "Moderate"
    )

    return {
        "total_feed_kg": round(bounded_feed, 2),
        "roughage_kg": round(roughage_kg, 2),
        "concentrate_kg": round(concentrate_kg, 2),
        "mineral_mix_kg": round(mineral_mix_kg, 2),
        "water_advice": "Provide clean water with free access throughout the day.",
        "feeding_frequency": feeding_frequency,
        "confidence_level": confidence_level,
        "explanation": explanation,
        "warnings": warnings,
        "disclaimer": ADVISORY_DISCLAIMER,
    }


__all__ = ["generate_feed_plan"]
