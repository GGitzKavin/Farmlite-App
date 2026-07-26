"""Shared paths for future materialized feature datasets.

Current training scripts build their preprocessing pipelines in memory. When
FarmLite begins persisting validated features, those files must be written
under ``datasets/processed`` through this module.
"""

from pathlib import Path

from config.settings import PROCESSED_DATA_DIR


def processed_dataset_path(filename: str) -> Path:
    """Return a safe path inside ``datasets/processed`` for a filename."""

    normalized_name = Path(filename).name
    if not normalized_name or normalized_name != filename:
        raise ValueError("filename must be a plain file name without directories")
    return PROCESSED_DATA_DIR / normalized_name


__all__ = ["processed_dataset_path"]
