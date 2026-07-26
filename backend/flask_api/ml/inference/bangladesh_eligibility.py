"""Fail-closed eligibility decisions for Bangladesh candidate inference."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ml.inference.bangladesh_thi import ThiResult


SUPPORTED_GENETIC_GROUPS = {
    "Local",
    "HF50",
    "HF62.5",
    "HF75",
    "HF87.5",
}
SUPPORTED_THI_CATEGORIES = {"T0", "T1", "T2"}
IN_SCOPE_LACTATION_STAGES = {
    "early lactation",
    "mid lactation",
    "late lactation",
}
OUT_OF_SCOPE_STAGES = {
    "dry",
    "dry cow",
    "non lactating",
    "non lactating cow",
    "calf",
    "bull",
}
LOCAL_LIMITATION = (
    "Local is a known training category but had no cow in the locked final "
    "holdout; model support is limited."
)


@dataclass(frozen=True)
class EligibilityResult:
    """One deterministic eligibility and population-scope result."""

    status: str
    scope: str
    fallback_reason: str | None
    warnings: tuple[str, ...]


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = re.sub(r"[_-]+", " ", value).strip().casefold()
    return re.sub(r"\s+", " ", normalized)


def evaluate_eligibility(
    request_data: dict[str, Any],
    thi_result: ThiResult,
) -> EligibilityResult:
    """Return eligibility without inferring genetic group from breed."""

    lactation_stage = _normalize_text(request_data.get("lactation_stage"))
    if (
        lactation_stage in OUT_OF_SCOPE_STAGES
        or lactation_stage not in IN_SCOPE_LACTATION_STAGES
    ):
        return EligibilityResult(
            "OUT_OF_SCOPE_POPULATION",
            "OUT_OF_SCOPE",
            "POPULATION_OUT_OF_SCOPE",
            (
                "Bangladesh candidates are limited to supported lactating-cow "
                "scope.",
            ),
        )

    genetic_group = request_data.get("genetic_group")
    if genetic_group is None or (
        isinstance(genetic_group, str) and not genetic_group.strip()
    ):
        return EligibilityResult(
            "MISSING_REQUIRED_INPUT",
            "UNRESOLVED",
            "GENETIC_GROUP_MISSING",
            ("Breed was not used to infer genetic group.",),
        )

    if thi_result.status != "ELIGIBLE":
        fallback_reason = (
            "ENVIRONMENT_MISSING"
            if thi_result.status == "MISSING_REQUIRED_INPUT"
            else "ENVIRONMENT_INVALID"
            if thi_result.status == "INVALID_ENVIRONMENT_INPUT"
            else "THI_CATEGORY_UNKNOWN"
        )
        return EligibilityResult(
            thi_result.status,
            "UNRESOLVED",
            fallback_reason,
            thi_result.warnings,
        )

    if genetic_group not in SUPPORTED_GENETIC_GROUPS:
        return EligibilityResult(
            "UNKNOWN_GENETIC_GROUP",
            "OUT_OF_SCOPE",
            "GENETIC_GROUP_UNKNOWN",
            ("Breed was not used to infer genetic group.",),
        )

    if thi_result.thi_category not in SUPPORTED_THI_CATEGORIES:
        return EligibilityResult(
            "UNKNOWN_THI_CATEGORY",
            "UNRESOLVED",
            "THI_CATEGORY_UNKNOWN",
            (),
        )

    if genetic_group == "Local":
        return EligibilityResult(
            "ELIGIBLE",
            "LIMITED_SUPPORT",
            None,
            (LOCAL_LIMITATION,),
        )

    return EligibilityResult("ELIGIBLE", "IN_SCOPE", None, ())


__all__ = [
    "EligibilityResult",
    "SUPPORTED_GENETIC_GROUPS",
    "SUPPORTED_THI_CATEGORIES",
    "evaluate_eligibility",
]
