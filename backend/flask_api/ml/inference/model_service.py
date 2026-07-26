"""Model loading and prediction helpers for FarmLite milk-yield ML."""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

import joblib
import pandas as pd

try:
    from config.settings import MILK_YIELD_MODEL_PATH
except ModuleNotFoundError:
    # Keep direct script execution working outside package/module invocation.
    flask_api_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(flask_api_dir))
    from config.settings import MILK_YIELD_MODEL_PATH


MODEL_USED = "HistGradientBoostingRegressor"
TARGET_COLUMN = "Milk_Yield_L"
MODEL_LIMITATION = (
    "The model predicts milk yield only and does not directly generate optimal "
    "feed recommendations."
)

FEATURE_MAP = {
    "breed": "Breed",
    "ageMonths": "Age_Months",
    "weightKg": "Weight_kg",
    "lactationStage": "Lactation_Stage",
    "daysInMilk": "Days_in_Milk",
    "ambientTemperatureC": "Ambient_Temperature_C",
    "humidityPercent": "Humidity_percent",
    "previousWeekAvgYield": "Previous_Week_Avg_Yield",
    "bodyConditionScore": "Body_Condition_Score",
}

REQUIRED_FIELDS = {
    "breed",
    "ageMonths",
    "weightKg",
    "lactationStage",
}

NUMERIC_FIELDS = {
    "ageMonths",
    "weightKg",
    "daysInMilk",
    "ambientTemperatureC",
    "humidityPercent",
    "previousWeekAvgYield",
    "bodyConditionScore",
}

OPTIONAL_NUMERIC_DEFAULTS = {
    "ambientTemperatureC": 28.0,
    "humidityPercent": 70.0,
    "previousWeekAvgYield": 0.0,
    "bodyConditionScore": 3.0,
    "daysInMilk": 0.0,
}

_milk_yield_model: Any | None = None


class ModelServiceError(Exception):
    """Expected model-service error with an HTTP-friendly status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _load_model() -> Any:
    global _milk_yield_model

    if _milk_yield_model is not None:
        return _milk_yield_model

    if not MILK_YIELD_MODEL_PATH.is_file():
        raise ModelServiceError(
            f"Milk-yield model file is missing at: {MILK_YIELD_MODEL_PATH}",
            status_code=500,
        )

    try:
        _milk_yield_model = joblib.load(MILK_YIELD_MODEL_PATH)
    except Exception as error:
        raise ModelServiceError(
            f"Failed to load milk-yield model: {error}",
            status_code=500,
        ) from error

    return _milk_yield_model


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _to_float(field_name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ModelServiceError(f"Invalid numeric value for '{field_name}'.")

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ModelServiceError(
            f"Invalid numeric value for '{field_name}'."
        ) from error

    if not math.isfinite(numeric_value):
        raise ModelServiceError(f"Invalid numeric value for '{field_name}'.")

    return numeric_value


def _validate_required_fields(input_data: dict[str, Any]) -> None:
    missing_fields = [
        field for field in sorted(REQUIRED_FIELDS) if _is_missing(input_data.get(field))
    ]
    if missing_fields:
        raise ModelServiceError(
            "Missing required field(s): " + ", ".join(missing_fields),
            status_code=400,
        )


def _build_model_row(input_data: dict[str, Any]) -> dict[str, Any]:
    _validate_required_fields(input_data)

    row: dict[str, Any] = {}
    for api_key, model_feature in FEATURE_MAP.items():
        raw_value = input_data.get(api_key)
        if api_key in OPTIONAL_NUMERIC_DEFAULTS and _is_missing(raw_value):
            raw_value = OPTIONAL_NUMERIC_DEFAULTS[api_key]

        if api_key in NUMERIC_FIELDS:
            row[model_feature] = _to_float(api_key, raw_value)
        else:
            row[model_feature] = str(raw_value).strip()

    return row


def predict_milk_yield(input_data: dict[str, Any]) -> dict[str, Any]:
    """Predict daily milk yield from API input data."""

    if not isinstance(input_data, dict):
        raise ModelServiceError("Request body must be a JSON object.")

    model = _load_model()
    model_row = _build_model_row(input_data)
    features_used = list(FEATURE_MAP.values())

    try:
        model_input = pd.DataFrame([model_row], columns=features_used)
        prediction = float(model.predict(model_input)[0])
    except Exception as error:
        raise ModelServiceError(
            f"Milk-yield prediction failed: {error}",
            status_code=500,
        ) from error

    if not math.isfinite(prediction):
        raise ModelServiceError(
            "Milk-yield prediction returned an invalid value.",
            status_code=500,
        )

    return {
        "predictedMilkYieldL": round(max(prediction, 0.0), 2),
        "modelUsed": MODEL_USED,
        "target": TARGET_COLUMN,
        "featuresUsed": features_used,
        "modelLimitation": MODEL_LIMITATION,
    }


__all__ = ["ModelServiceError", "predict_milk_yield"]
