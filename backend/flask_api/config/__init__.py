"""Configuration package for FarmLite backend paths and settings."""

from .settings import (
    DATASETS_DIR,
    EXTERNAL_DATA_DIR,
    FLASK_API_DIR,
    INTERIM_DATA_DIR,
    ML_MODELS_DIR,
    ML_REPORTS_DIR,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
)

__all__ = [
    "DATASETS_DIR",
    "EXTERNAL_DATA_DIR",
    "FLASK_API_DIR",
    "INTERIM_DATA_DIR",
    "ML_MODELS_DIR",
    "ML_REPORTS_DIR",
    "PROCESSED_DATA_DIR",
    "PROJECT_ROOT",
    "RAW_DATA_DIR",
]
