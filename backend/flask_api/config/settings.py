"""Filesystem settings derived from the FarmLite project root."""

import os
from collections.abc import Mapping
from pathlib import Path


FLASK_API_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATASETS_DIR = PROJECT_ROOT / "datasets"
RAW_DATA_DIR = DATASETS_DIR / "raw"
INTERIM_DATA_DIR = DATASETS_DIR / "interim"
PROCESSED_DATA_DIR = DATASETS_DIR / "processed"
EXTERNAL_DATA_DIR = DATASETS_DIR / "external"

ML_DIR = FLASK_API_DIR / "ml"
ML_MODELS_DIR = ML_DIR / "models"
ML_REPORTS_DIR = ML_DIR / "reports"

MILK_YIELD_DATASET_PATH = (
    RAW_DATA_DIR / "global_cattle_milk_yield_prediction_dataset.csv"
)
DISEASE_DATASET_PATH = (
    RAW_DATA_DIR / "global_cattle_disease_detection_dataset.csv"
)
MILK_YIELD_MODEL_PATH = ML_MODELS_DIR / "milk_yield_model.joblib"

BANGLADESH_CANDIDATE_MODELS_ENABLED_ENV = (
    "BANGLADESH_CANDIDATE_MODELS_ENABLED"
)
BANGLADESH_CANDIDATE_MODELS_ENABLED_DEFAULT = False
FEATURE_FLAG_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def parse_feature_flag(value: object) -> bool:
    """Return true only for the explicitly supported environment values."""

    if not isinstance(value, str):
        return BANGLADESH_CANDIDATE_MODELS_ENABLED_DEFAULT
    return value.strip().casefold() in FEATURE_FLAG_TRUE_VALUES


def bangladesh_candidate_models_enabled(
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Read the disabled-by-default Bangladesh candidate feature flag."""

    source = os.environ if environ is None else environ
    return parse_feature_flag(
        source.get(BANGLADESH_CANDIDATE_MODELS_ENABLED_ENV)
    )


def ensure_generated_output_directories() -> None:
    """Create directories used by future preprocessing and training runs."""

    for directory in (
        INTERIM_DATA_DIR,
        PROCESSED_DATA_DIR,
        ML_MODELS_DIR,
        ML_REPORTS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


__all__ = [
    "BANGLADESH_CANDIDATE_MODELS_ENABLED_DEFAULT",
    "BANGLADESH_CANDIDATE_MODELS_ENABLED_ENV",
    "DATASETS_DIR",
    "DISEASE_DATASET_PATH",
    "EXTERNAL_DATA_DIR",
    "FLASK_API_DIR",
    "INTERIM_DATA_DIR",
    "MILK_YIELD_DATASET_PATH",
    "MILK_YIELD_MODEL_PATH",
    "ML_DIR",
    "ML_MODELS_DIR",
    "ML_REPORTS_DIR",
    "PROCESSED_DATA_DIR",
    "PROJECT_ROOT",
    "RAW_DATA_DIR",
    "bangladesh_candidate_models_enabled",
    "ensure_generated_output_directories",
    "parse_feature_flag",
]
