"""Safe, read-only dataset loading for FarmLite preprocessing."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from config.settings import FLASK_API_DIR, PROJECT_ROOT
from ml.preprocessing.preprocessing_types import (
    DatasetLoadMetadata,
    DatasetLoadResult,
)


class DatasetLoadError(RuntimeError):
    """Base error for a dataset that cannot be safely loaded."""


class UnsupportedDatasetFormatError(DatasetLoadError):
    """Raised when a loader for the file extension is not implemented."""


class EmptyDatasetError(DatasetLoadError):
    """Raised when a source has no columns or no data records."""


class UnreadableDatasetError(DatasetLoadError):
    """Raised when pandas cannot parse or read a source file."""


class MissingRequiredColumnsError(DatasetLoadError):
    """Raised when requested required source columns are absent."""


SUPPORTED_FORMATS = {".csv"}


def resolve_project_path(source: str | Path) -> Path:
    """Resolve absolute or project-relative data paths without using CWD alone."""

    path = Path(source).expanduser()
    if path.is_absolute():
        return path.resolve()

    project_candidate = (PROJECT_ROOT / path).resolve()
    if project_candidate.exists():
        return project_candidate

    backend_candidate = (FLASK_API_DIR / path).resolve()
    if backend_candidate.exists():
        return backend_candidate

    return project_candidate


def load_dataset(
    source: str | Path,
    *,
    selected_columns: Iterable[str] | None = None,
    required_columns: Iterable[str] | None = None,
    row_limit: int | None = None,
) -> DatasetLoadResult:
    """Load a CSV without changing it and return the dataframe plus metadata."""

    path = resolve_project_path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file was not found: {path}")
    if path.suffix.casefold() not in SUPPORTED_FORMATS:
        raise UnsupportedDatasetFormatError(
            f"Unsupported dataset format '{path.suffix or '<none>'}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}."
        )
    if row_limit is not None and row_limit < 1:
        raise ValueError("row_limit must be a positive integer when supplied")

    selected = list(selected_columns) if selected_columns is not None else None
    required = list(required_columns or ())
    if selected is not None:
        duplicate_selected = sorted(
            {name for name in selected if selected.count(name) > 1}
        )
        if duplicate_selected:
            raise ValueError(
                "selected_columns contains duplicates: "
                + ", ".join(duplicate_selected)
            )

    try:
        dataframe = pd.read_csv(
            path,
            usecols=selected,
            nrows=row_limit,
            low_memory=False,
        )
    except pd.errors.EmptyDataError as error:
        raise EmptyDatasetError(f"Dataset is empty: {path}") from error
    except ValueError as error:
        if "Usecols do not match columns" in str(error):
            raise MissingRequiredColumnsError(
                f"Selected columns were not found in {path}: {error}"
            ) from error
        raise
    except (OSError, UnicodeError, pd.errors.ParserError) as error:
        raise UnreadableDatasetError(
            f"Dataset could not be read as CSV: {path}: {error}"
        ) from error

    if dataframe.empty or len(dataframe.columns) == 0:
        raise EmptyDatasetError(f"Dataset contains no data records: {path}")

    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise MissingRequiredColumnsError(
            f"Dataset is missing required columns: {', '.join(missing)}"
        )

    metadata = DatasetLoadMetadata(
        source_path=path,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        loaded_at_utc=datetime.now(UTC).isoformat(),
        source_format="CSV",
        file_size_bytes=path.stat().st_size,
        selected_columns=selected,
        row_limit=row_limit,
    )
    return DatasetLoadResult(dataframe=dataframe, metadata=metadata)


def load_dataframe(
    source: str | Path,
    *,
    selected_columns: Iterable[str] | None = None,
    required_columns: Iterable[str] | None = None,
    row_limit: int | None = None,
) -> pd.DataFrame:
    """Return only the dataframe for callers that do not need load metadata."""

    return load_dataset(
        source,
        selected_columns=selected_columns,
        required_columns=required_columns,
        row_limit=row_limit,
    ).dataframe


__all__ = [
    "DatasetLoadError",
    "EmptyDatasetError",
    "MissingRequiredColumnsError",
    "UnsupportedDatasetFormatError",
    "UnreadableDatasetError",
    "load_dataframe",
    "load_dataset",
    "resolve_project_path",
]
