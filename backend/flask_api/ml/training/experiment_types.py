"""Typed records for controlled Phase 4 experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CandidateConfig:
    """One small, documented estimator configuration."""

    configuration_id: str
    task: str
    algorithm: str
    estimator_name: str
    parameters: dict[str, Any]
    preprocessor_kind: str
    is_baseline: bool = False
    resource_class: str = "STANDARD"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""

        return asdict(self)


@dataclass
class CandidateEvaluation:
    """Validation results and the fitted training-only pipeline."""

    configuration: CandidateConfig
    metrics: dict[str, Any]
    training_seconds: float
    prediction_seconds: float
    pipeline: Any = field(repr=False)
    predictions: Any = field(repr=False, default=None)

    def to_record(self) -> dict[str, Any]:
        """Flatten primary metrics for a CSV candidate table."""

        record = {
            "configuration_id": self.configuration.configuration_id,
            "algorithm": self.configuration.algorithm,
            "is_baseline": self.configuration.is_baseline,
            "training_seconds": self.training_seconds,
            "prediction_seconds": self.prediction_seconds,
        }
        for name, value in self.metrics.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                record[name] = value
        return record

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-ready evaluation metadata without the pipeline."""

        return {
            "configuration": self.configuration.to_dict(),
            "metrics": self.metrics,
            "training_seconds": self.training_seconds,
            "prediction_seconds": self.prediction_seconds,
        }


@dataclass
class ExperimentData:
    """Canonical dataset partitions aligned to the locked manifests."""

    full: Any = field(repr=False)
    train: Any = field(repr=False)
    validation: Any = field(repr=False)
    test: Any = field(repr=False)
    split_manifest: Any = field(repr=False)
    fold_manifest: Any = field(repr=False)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSelection:
    """Validation-locked selection for one task."""

    task: str
    selected_configuration_id: str
    selected_algorithm: str
    validation_metrics: dict[str, Any]
    baseline_configuration_id: str
    baseline_metrics: dict[str, Any]
    selection_reason: str
    beats_baseline_on_validation: bool
    release_status: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""

        return asdict(self)


__all__ = [
    "CandidateConfig",
    "CandidateEvaluation",
    "ExperimentData",
    "TaskSelection",
]
