"""Deterministic approved-alias mapping for dataset and API columns."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Iterable

import pandas as pd

from config.settings import FLASK_API_DIR
from ml.preprocessing.preprocessing_types import (
    ColumnMappingMetadata,
    ColumnMappingResult,
)


DEFAULT_ALIAS_PATH = FLASK_API_DIR / "config" / "column_aliases.json"


class MappingOperation(str, Enum):
    """Mapping contexts kept separate in result metadata."""

    DATASET = "DATASET"
    API = "API"


class ColumnMappingError(ValueError):
    """Raised when approved aliases cannot produce a unique mapping."""


class AliasConfigurationError(ColumnMappingError):
    """Raised when the approved alias configuration is itself ambiguous."""


def _normalized_alias(value: object) -> str:
    return str(value).strip().casefold()


def load_aliases(path: str | Path = DEFAULT_ALIAS_PATH) -> dict[str, list[str]]:
    """Load and validate the approved canonical-to-alias mapping."""

    alias_path = Path(path)
    try:
        raw = json.loads(alias_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as error:
        raise AliasConfigurationError(
            f"Alias configuration is not valid JSON: {alias_path}: {error}"
        ) from error

    if not isinstance(raw, dict):
        raise AliasConfigurationError("Alias configuration must be a JSON object")

    aliases: dict[str, list[str]] = {}
    owner_by_alias: dict[str, str] = {}
    for canonical, values in raw.items():
        if not isinstance(canonical, str) or not isinstance(values, list):
            raise AliasConfigurationError(
                "Every alias entry must map a canonical string to a list"
            )
        approved_values = [canonical, *values]
        aliases[canonical] = []
        for value in approved_values:
            if not isinstance(value, str) or not value.strip():
                raise AliasConfigurationError(
                    f"Invalid alias configured for '{canonical}'"
                )
            key = _normalized_alias(value)
            owner = owner_by_alias.get(key)
            if owner is not None and owner != canonical:
                raise AliasConfigurationError(
                    f"Alias '{value}' ambiguously maps to '{owner}' and "
                    f"'{canonical}'"
                )
            owner_by_alias[key] = canonical
            if value not in aliases[canonical]:
                aliases[canonical].append(value)
    return aliases


def map_columns(
    dataframe: pd.DataFrame,
    *,
    operation: MappingOperation | str,
    aliases_path: str | Path = DEFAULT_ALIAS_PATH,
    required_columns: Iterable[str] = (),
    only_selected_columns: Iterable[str] | None = None,
    preserve_unmapped: bool = True,
    raise_on_missing: bool = False,
) -> ColumnMappingResult:
    """Rename only approved aliases and return deterministic mapping evidence."""

    operation_value = MappingOperation(operation).value
    aliases = load_aliases(aliases_path)
    lookup = {
        _normalized_alias(alias): canonical
        for canonical, values in aliases.items()
        for alias in values
    }

    duplicate_source_names = dataframe.columns[
        dataframe.columns.duplicated(keep=False)
    ].tolist()
    if duplicate_source_names:
        rendered = ", ".join(map(str, duplicate_source_names))
        raise ColumnMappingError(
            f"Duplicate source column names cannot be mapped safely: {rendered}"
        )

    mapped_columns: dict[str, str] = {}
    unmapped_columns: list[str] = []
    canonical_sources: dict[str, str] = {}
    for source in map(str, dataframe.columns):
        canonical = lookup.get(_normalized_alias(source))
        if canonical is None:
            unmapped_columns.append(source)
            continue
        previous_source = canonical_sources.get(canonical)
        if previous_source is not None and previous_source != source:
            raise ColumnMappingError(
                f"Columns '{previous_source}' and '{source}' both map to "
                f"canonical field '{canonical}'. No priority rule is approved."
            )
        canonical_sources[canonical] = source
        mapped_columns[source] = canonical

    required = list(required_columns)
    available_canonical = set(mapped_columns.values())
    missing_required = [
        canonical for canonical in required if canonical not in available_canonical
    ]
    if raise_on_missing and missing_required:
        raise ColumnMappingError(
            "Missing required canonical columns: " + ", ".join(missing_required)
        )

    renamed = dataframe.rename(columns=mapped_columns)
    selected = list(only_selected_columns or ())
    if only_selected_columns is not None:
        missing_selected = [
            column for column in selected if column not in renamed.columns
        ]
        if missing_selected:
            raise ColumnMappingError(
                "Selected canonical columns are missing: "
                + ", ".join(missing_selected)
            )
        renamed = renamed.loc[:, selected]
    elif not preserve_unmapped:
        canonical_order = [
            canonical
            for canonical in aliases
            if canonical in renamed.columns
        ]
        renamed = renamed.loc[:, canonical_order]

    metadata = ColumnMappingMetadata(
        operation=operation_value,
        mapped_columns=mapped_columns,
        unmapped_columns=unmapped_columns,
        ambiguous_columns=[],
        missing_required_columns=missing_required,
    )
    return ColumnMappingResult(dataframe=renamed, metadata=metadata)


def map_dataset_columns(
    dataframe: pd.DataFrame,
    **kwargs: object,
) -> ColumnMappingResult:
    """Map approved dataset source names to canonical names."""

    return map_columns(dataframe, operation=MappingOperation.DATASET, **kwargs)


def map_api_fields(
    dataframe: pd.DataFrame,
    **kwargs: object,
) -> ColumnMappingResult:
    """Map approved API field aliases to canonical names."""

    return map_columns(dataframe, operation=MappingOperation.API, **kwargs)


__all__ = [
    "AliasConfigurationError",
    "ColumnMappingError",
    "DEFAULT_ALIAS_PATH",
    "MappingOperation",
    "load_aliases",
    "map_api_fields",
    "map_columns",
    "map_dataset_columns",
]
