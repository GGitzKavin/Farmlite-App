"""Small serializable result types used by FarmLite preprocessing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd


class ValidationMode(str, Enum):
    """Supported schema-validation contexts."""

    TRAINING_DATA = "TRAINING_DATA"
    INFERENCE_INPUT = "INFERENCE_INPUT"
    TEST_FIXTURE = "TEST_FIXTURE"


class ValidationSeverity(str, Enum):
    """Severity attached to a validation or cleaning issue."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass(frozen=True)
class ValidationIssue:
    """One aggregated validation finding."""

    field: str
    issue_type: str
    severity: ValidationSeverity
    message: str
    affected_count: int = 1
    sample_rows: list[int] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    action: str = "PRESERVED"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""

        result = asdict(self)
        result["severity"] = self.severity.value
        return result


@dataclass
class ValidationResult:
    """Structured schema-validation result."""

    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    missing_required_fields: list[str] = field(default_factory=list)
    unexpected_fields: list[str] = field(default_factory=list)
    unknown_categories: dict[str, list[str]] = field(default_factory=dict)
    range_violations: list[dict[str, Any]] = field(default_factory=list)
    leakage_fields: list[str] = field(default_factory=list)
    row_count: int = 0

    @property
    def issues(self) -> list[ValidationIssue]:
        """Return errors followed by warnings."""

        return [*self.errors, *self.warnings]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""

        return {
            "valid": self.valid,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
            "missing_required_fields": self.missing_required_fields,
            "unexpected_fields": self.unexpected_fields,
            "unknown_categories": self.unknown_categories,
            "range_violations": self.range_violations,
            "leakage_fields": self.leakage_fields,
            "row_count": self.row_count,
        }


@dataclass(frozen=True)
class DatasetLoadMetadata:
    """Read-only facts recorded for one dataset load."""

    source_path: Path
    row_count: int
    column_count: int
    loaded_at_utc: str
    source_format: str
    file_size_bytes: int
    selected_columns: list[str] | None = None
    row_limit: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""

        result = asdict(self)
        result["source_path"] = str(self.source_path)
        return result


@dataclass
class DatasetLoadResult:
    """A loaded dataframe and its source metadata."""

    dataframe: pd.DataFrame
    metadata: DatasetLoadMetadata


@dataclass(frozen=True)
class ColumnMappingMetadata:
    """Evidence produced while mapping source names to canonical names."""

    operation: str
    mapped_columns: dict[str, str]
    unmapped_columns: list[str]
    ambiguous_columns: list[str]
    missing_required_columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""

        return asdict(self)


@dataclass
class ColumnMappingResult:
    """A canonicalized dataframe and deterministic mapping evidence."""

    dataframe: pd.DataFrame
    metadata: ColumnMappingMetadata


@dataclass
class DataCleanResult:
    """Cleaned values, row-level issues, and aggregate metadata."""

    dataframe: pd.DataFrame
    issues: pd.DataFrame
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ModelSpec:
    """Resolved feature and target contract for one model design."""

    model_name: str
    feature_names: list[str]
    target_name: str
    contract_version: str
    categorical_features: list[str]
    numeric_features: list[str]


@dataclass
class FeatureBuildResult:
    """A model-ready logical view before learned preprocessing is fitted."""

    X: pd.DataFrame
    y: pd.Series | None
    feature_names: list[str]
    target_name: str
    excluded_fields: list[dict[str, str]]
    model_contract_version: str


@dataclass
class SplitAssignmentResult:
    """One deterministic train/validation/test assignment."""

    manifest: pd.DataFrame
    summary: dict[str, Any]


@dataclass
class FoldAssignmentResult:
    """Deterministic training-only out-of-fold assignments."""

    manifest: pd.DataFrame
    summary: dict[str, Any]


__all__ = [
    "ColumnMappingMetadata",
    "ColumnMappingResult",
    "DataCleanResult",
    "DatasetLoadMetadata",
    "DatasetLoadResult",
    "FeatureBuildResult",
    "FoldAssignmentResult",
    "ModelSpec",
    "SplitAssignmentResult",
    "ValidationIssue",
    "ValidationMode",
    "ValidationResult",
    "ValidationSeverity",
]
