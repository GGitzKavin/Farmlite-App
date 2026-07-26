"""Versioned backend-only route for controlled Bangladesh candidates."""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from api.v2_schemas import MAX_REQUEST_BYTES, validate_v2_request
from config.settings import bangladesh_candidate_models_enabled
from ml.inference.bangladesh_model_service import (
    SCHEMA_VERSION,
    disabled_response,
    predict_bangladesh_candidates,
)


LOGGER = logging.getLogger(__name__)
api_v2_blueprint = Blueprint("api_v2", __name__, url_prefix="/api/v2")


def _error_response(
    error_code: str,
    message: str,
    *,
    field_errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "prediction_status": "UNAVAILABLE",
        "error_code": error_code,
        "message": message,
        "field_errors": field_errors or {},
    }


def _validation_error_code(field_errors: dict[str, str]) -> str:
    messages = tuple(field_errors.values())
    if any("Required field" in message for message in messages):
        return "MISSING_REQUIRED_FIELD"
    if any(
        marker in message
        for message in messages
        for marker in ("string", "integer", "finite", "Unexpected")
    ):
        return "INVALID_FIELD_TYPE"
    return "INVALID_FIELD_RANGE"


@api_v2_blueprint.post("/predict")
def predict_v2():
    """Validate v2 JSON and keep candidate execution behind its flag."""

    if (
        request.content_length is not None
        and request.content_length > MAX_REQUEST_BYTES
    ):
        return (
            jsonify(
                _error_response(
                    "REQUEST_TOO_LARGE",
                    "Request body exceeds the 16 KiB limit.",
                )
            ),
            422,
        )

    try:
        data = request.get_json(force=False, silent=False)
    except (BadRequest, UnsupportedMediaType):
        return (
            jsonify(
                _error_response(
                    "INVALID_JSON",
                    "Request body must be valid JSON.",
                )
            ),
            400,
        )

    if not isinstance(data, dict):
        return (
            jsonify(
                _error_response(
                    "INVALID_JSON",
                    "Request body must be a JSON object.",
                )
            ),
            400,
        )

    enabled = bangladesh_candidate_models_enabled()
    if not enabled:
        LOGGER.info(
            "phase5_event=feature_flag enabled=false "
            "fallback=FEATURE_DISABLED"
        )
        return jsonify(disabled_response()), 200

    validation = validate_v2_request(data)
    if not validation.valid:
        return (
            jsonify(
                _error_response(
                    _validation_error_code(validation.field_errors),
                    "Request validation failed.",
                    field_errors=validation.field_errors,
                )
            ),
            422,
        )

    try:
        result = predict_bangladesh_candidates(
            validation.value or {},
            enabled=True,
        )
    except Exception:
        LOGGER.exception("phase5_event=unexpected_v2_failure")
        return (
            jsonify(
                _error_response(
                    "INTERNAL_SERVER_ERROR",
                    "An unexpected prediction service error occurred.",
                )
            ),
            500,
        )
    return jsonify(result), 200


__all__ = ["api_v2_blueprint"]
