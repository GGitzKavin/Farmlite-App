"""Controlled orchestration for Bangladesh candidate-only inference."""

from __future__ import annotations

import logging
import math
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd

from config.settings import bangladesh_candidate_models_enabled
from ml.inference.bangladesh_artifact_loader import (
    ArtifactLoadError,
    LoadedCandidate,
    load_candidate,
)
from ml.inference.bangladesh_eligibility import (
    EligibilityResult,
    evaluate_eligibility,
)
from ml.inference.bangladesh_thi import ThiResult, calculate_thi


LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION = "2.0.0-design"

MODEL_SOURCES = {
    "dmi": "BANGLADESH_DMI_CANDIDATE_V1",
    "milk": "BANGLADESH_MILK_CANDIDATE_V1",
}
PREDICTION_FIELDS = {
    "dmi": "dmi_kg_day",
    "milk": "milk_yield_l_day",
}
PREDICTION_UNITS = {
    "dmi_kg_day": "kg dry matter/cow/day",
    "milk_yield_l_day": "L/cow/day",
}
RULE_RECOMMENDATION = {
    "feed_category": None,
    "roughage_kg_day": None,
    "concentrate_kg_day": None,
    "mineral_mix": None,
    "water_advice": None,
}
CANDIDATE_LIMITATION = (
    "Bangladesh outputs are candidate-only prototype results and are not "
    "production, commercial, or veterinary approved."
)
EXTERNAL_VALIDATION_LIMITATION = (
    "The candidates have not received independent external validation "
    "outside the source study population."
)
RANGE_LIMITATION = (
    "Prediction sanity ranges use study-observed targets as integration "
    "guards, not universal biological limits."
)
NO_NUTRITION_LIMITATION = (
    "DMI is dry-matter intake only and is not converted to a ration, "
    "roughage, concentrate, or as-fed quantity."
)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _warning(code: str, message: str, severity: str = "WARNING") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _warning_from_text(message: str) -> dict[str, str]:
    if message.startswith("The study workbooks"):
        code = "BD_ENVIRONMENT_LIMIT"
    elif message.startswith("Local is"):
        code = "BD_LOCAL_LIMITED"
    elif message.startswith("Breed was not used"):
        code = "BREED_NOT_USED_FOR_GENETIC_GROUP"
    else:
        code = "ELIGIBILITY_LIMITATION"
    return _warning(code, message)


def _unique_warnings(
    values: list[dict[str, str]],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        key = (value["code"], value["message"])
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _eligibility_payload(
    status: str,
    scope: str,
    fallback_reason: str | None,
) -> dict[str, str | None]:
    return {
        "status": status,
        "scope": scope,
        "fallback_reason": fallback_reason,
    }


def _base_response() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "prediction_status": "FALLBACK_REQUIRED",
        "eligibility": {
            "dmi": _eligibility_payload(
                "FALLBACK_REQUIRED",
                "UNRESOLVED",
                None,
            ),
            "milk": _eligibility_payload(
                "FALLBACK_REQUIRED",
                "UNRESOLVED",
                None,
            ),
        },
        "environment": {
            "calculated_thi": None,
            "display_thi": None,
            "thi_category": None,
            "mapping_version": None,
            "verification_status": None,
            "source": "UNAVAILABLE",
        },
        "ml_predictions": {
            "dmi_kg_day": None,
            "milk_yield_l_day": None,
        },
        "model_sources": {"dmi": None, "milk": None},
        "model_provenance": {"dmi": None, "milk": None},
        "rule_recommendation": dict(RULE_RECOMMENDATION),
        "prediction_units": dict(PREDICTION_UNITS),
        "value_sources": {
            "environment.calculated_thi": "UNAVAILABLE",
            "environment.display_thi": "UNAVAILABLE",
            "environment.thi_category": "UNAVAILABLE",
            "environment.mapping_version": "UNAVAILABLE",
            "environment.verification_status": "UNAVAILABLE",
            "ml_predictions.dmi_kg_day": "UNAVAILABLE",
            "ml_predictions.milk_yield_l_day": "UNAVAILABLE",
            "rule_recommendation.feed_category": "UNAVAILABLE",
            "rule_recommendation.roughage_kg_day": "UNAVAILABLE",
            "rule_recommendation.concentrate_kg_day": "UNAVAILABLE",
            "rule_recommendation.mineral_mix": "UNAVAILABLE",
            "rule_recommendation.water_advice": "UNAVAILABLE",
        },
        "warnings": [],
        "limitations": [NO_NUTRITION_LIMITATION],
        "fallback_reasons": [],
    }


def disabled_response() -> dict[str, Any]:
    """Return a complete response without touching THI or candidate artifacts."""

    response = _base_response()
    response["prediction_status"] = "DISABLED"
    for task in ("dmi", "milk"):
        response["eligibility"][task] = _eligibility_payload(
            "FALLBACK_REQUIRED",
            "UNRESOLVED",
            "FEATURE_DISABLED",
        )
    response["warnings"] = [
        _warning(
            "FEATURE_DISABLED",
            "Bangladesh candidate models are disabled by configuration.",
            "INFORMATION",
        )
    ]
    response["limitations"].append(CANDIDATE_LIMITATION)
    response["fallback_reasons"] = ["FEATURE_DISABLED"]
    return response


def validate_prediction_value(
    value: object,
    *,
    minimum: float,
    maximum: float,
) -> tuple[float | None, str | None]:
    """Validate one scalar prediction without clipping it."""

    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        return None, "Prediction was not a finite numeric scalar."
    numeric = float(value)
    if numeric < 0:
        return None, "Prediction was negative."
    if numeric < minimum or numeric > maximum:
        return (
            None,
            "Prediction was outside the documented study-observed sanity "
            "range.",
        )
    return numeric, None


def _predict_candidate(
    loaded: LoadedCandidate,
    genetic_group: str,
    thi_category: str,
) -> tuple[float | None, str | None]:
    frame = pd.DataFrame(
        [[genetic_group, thi_category]],
        columns=list(loaded.spec.feature_order),
    )
    try:
        raw = loaded.model.predict(frame)
        flattened = np.asarray(raw).reshape(-1)
    except Exception:
        LOGGER.exception(
            "phase5_event=prediction_failure task=%s",
            loaded.spec.task,
        )
        return None, "Candidate prediction failed."
    if flattened.size != 1:
        return None, "Candidate returned an unexpected output shape."
    return validate_prediction_value(
        flattened[0],
        minimum=loaded.spec.sanity_minimum,
        maximum=loaded.spec.sanity_maximum,
    )


def _environment_payload(result: ThiResult) -> dict[str, Any]:
    return {
        "calculated_thi": result.calculated_thi,
        "display_thi": result.display_thi,
        "thi_category": result.thi_category,
        "mapping_version": result.mapping_version,
        "verification_status": result.verification_status,
        "source": (
            "SERVER_CALCULATED"
            if result.calculated_thi is not None
            else "UNAVAILABLE"
        ),
    }


def _apply_ineligible(
    response: dict[str, Any],
    eligibility: EligibilityResult,
) -> dict[str, Any]:
    for task in ("dmi", "milk"):
        response["eligibility"][task] = _eligibility_payload(
            eligibility.status,
            eligibility.scope,
            eligibility.fallback_reason,
        )
    response["warnings"] = _unique_warnings(
        list(response["warnings"])
        + [_warning_from_text(value) for value in eligibility.warnings]
    )
    if eligibility.fallback_reason:
        response["fallback_reasons"] = [eligibility.fallback_reason]
    response["prediction_status"] = "FALLBACK_REQUIRED"
    LOGGER.info(
        "phase5_event=eligibility status=%s scope=%s fallback=%s",
        eligibility.status,
        eligibility.scope,
        eligibility.fallback_reason or "none",
    )
    return response


def predict_bangladesh_candidates(
    request_data: dict[str, Any],
    *,
    enabled: bool | None = None,
) -> dict[str, Any]:
    """Predict independently with the two hash-verified candidates."""

    flag_enabled = (
        bangladesh_candidate_models_enabled()
        if enabled is None
        else bool(enabled)
    )
    LOGGER.info(
        "phase5_event=feature_flag enabled=%s",
        str(flag_enabled).lower(),
    )
    if not flag_enabled:
        return disabled_response()

    response = _base_response()
    thi_result = calculate_thi(
        request_data.get("ambient_temperature_c"),
        request_data.get("humidity_percent"),
    )
    response["environment"] = _environment_payload(thi_result)
    response["value_sources"][
        "environment.mapping_version"
    ] = "DERIVED"
    response["value_sources"][
        "environment.verification_status"
    ] = "DERIVED"
    if thi_result.calculated_thi is not None:
        response["value_sources"][
            "environment.calculated_thi"
        ] = "DERIVED"
        response["value_sources"]["environment.display_thi"] = "DERIVED"
    if thi_result.thi_category is not None:
        response["value_sources"]["environment.thi_category"] = "DERIVED"
    response["warnings"] = [
        _warning_from_text(value) for value in thi_result.warnings
    ]
    LOGGER.info(
        "phase5_event=thi_mapping status=%s category=%s",
        thi_result.status,
        thi_result.thi_category or "none",
    )

    eligibility = evaluate_eligibility(request_data, thi_result)
    if eligibility.status != "ELIGIBLE":
        return _apply_ineligible(response, eligibility)

    response["limitations"].extend(
        [
            CANDIDATE_LIMITATION,
            EXTERNAL_VALIDATION_LIMITATION,
            RANGE_LIMITATION,
        ]
    )
    response["warnings"] = _unique_warnings(
        response["warnings"]
        + [_warning_from_text(value) for value in eligibility.warnings]
        + [
            _warning("BD_CANDIDATE_ONLY", CANDIDATE_LIMITATION),
            _warning(
                "BD_EXTERNAL_VALIDATION_MISSING",
                EXTERNAL_VALIDATION_LIMITATION,
            ),
        ]
    )
    fallback_reasons: list[str] = []
    predicted_tasks: list[str] = []

    for task in ("dmi", "milk"):
        response["eligibility"][task] = _eligibility_payload(
            "ELIGIBLE",
            eligibility.scope,
            None,
        )
        try:
            loaded = load_candidate(task)
        except ArtifactLoadError as error:
            public_status = (
                error.code
                if error.code
                in {
                    "ARTIFACT_UNAVAILABLE",
                    "ARTIFACT_HASH_MISMATCH",
                    "MODEL_ERROR",
                }
                else "ARTIFACT_UNAVAILABLE"
            )
            response["eligibility"][task] = _eligibility_payload(
                public_status,
                eligibility.scope,
                error.code,
            )
            fallback_reasons.append(error.code)
            response["warnings"].append(
                _warning(error.code, error.message, "ERROR")
            )
            LOGGER.warning(
                "phase5_event=candidate_fallback task=%s reason=%s",
                task,
                error.code,
            )
            continue

        prediction, validation_error = _predict_candidate(
            loaded,
            str(request_data["genetic_group"]),
            str(thi_result.thi_category),
        )
        if validation_error is not None:
            response["eligibility"][task] = _eligibility_payload(
                "MODEL_ERROR",
                eligibility.scope,
                "MODEL_ERROR",
            )
            fallback_reasons.append("MODEL_ERROR")
            response["warnings"].append(
                _warning(
                    "MODEL_ERROR",
                    f"{task.upper()} candidate rejected: {validation_error}",
                    "ERROR",
                )
            )
            LOGGER.warning(
                "phase5_event=prediction_validation_failure task=%s",
                task,
            )
            continue

        prediction_field = PREDICTION_FIELDS[task]
        response["ml_predictions"][prediction_field] = prediction
        response["model_sources"][task] = MODEL_SOURCES[task]
        response["model_provenance"][task] = {
            "source": MODEL_SOURCES[task],
            "model_name": loaded.spec.model_name,
            "artifact_status": loaded.spec.artifact_status,
            "artifact_sha256": loaded.spec.artifact_sha256,
            "metadata_sha256": loaded.spec.metadata_sha256,
            "contract_version": loaded.metadata.get("contract_version"),
            "feature_order": list(loaded.spec.feature_order),
            "target": loaded.spec.target,
            "unit": loaded.spec.output_unit,
            "dataset_doi": loaded.spec.dataset_doi,
            "dataset_licence": loaded.metadata.get("dataset_licence"),
        }
        response["value_sources"][
            f"ml_predictions.{prediction_field}"
        ] = "ML_PREDICTED"
        predicted_tasks.append(task)

    response["value_sources"]["environment.calculated_thi"] = "DERIVED"
    response["value_sources"]["environment.thi_category"] = "DERIVED"
    response["warnings"] = _unique_warnings(response["warnings"])
    response["fallback_reasons"] = _unique(fallback_reasons)
    if len(predicted_tasks) == 2:
        response["prediction_status"] = "ELIGIBLE"
    elif predicted_tasks:
        response["prediction_status"] = "PARTIAL"
    else:
        response["prediction_status"] = "FALLBACK_REQUIRED"

    LOGGER.info(
        "phase5_event=eligibility status=%s scope=%s predicted=%s",
        response["prediction_status"],
        eligibility.scope,
        ",".join(predicted_tasks) or "none",
    )
    return response


__all__ = [
    "SCHEMA_VERSION",
    "disabled_response",
    "predict_bangladesh_candidates",
    "validate_prediction_value",
]
