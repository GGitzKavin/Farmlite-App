"""Hash-verified loading for the Phase 5 Bangladesh candidate pipelines."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import joblib

from config.settings import FLASK_API_DIR


LOGGER = logging.getLogger(__name__)

INVENTORY_PATH = (
    FLASK_API_DIR
    / "ml"
    / "reports"
    / "bangladesh_candidate_integration_inventory.json"
)
MODEL_CONTRACT_PATH = (
    FLASK_API_DIR / "config" / "bangladesh_model_contract.json"
)
CANDIDATE_ROOT = (
    FLASK_API_DIR / "ml" / "models" / "candidates" / "bangladesh"
)

EXPECTED_GENETIC_GROUPS = {
    "Local",
    "HF50",
    "HF62.5",
    "HF75",
    "HF87.5",
}
EXPECTED_THI_CATEGORIES = {"T0", "T1", "T2"}
EXPECTED_TASK_OUTPUTS = {
    "dmi": (
        "dry_matter_intake_kg_day",
        "kg dry matter/cow/day",
    ),
    "milk": (
        "milk_yield_l_day",
        "L/cow/day",
    ),
}


class ArtifactLoadError(RuntimeError):
    """Expected candidate-integrity or deserialization failure."""

    def __init__(self, code: str, message: str, task: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.task = task


@dataclass(frozen=True)
class ArtifactSpec:
    """Trusted inventory values needed to verify one candidate."""

    task: str
    model_name: str
    artifact_path: Path
    metadata_path: Path
    artifact_sha256: str
    metadata_sha256: str
    artifact_status: str
    target: str
    target_definition: str
    output_unit: str
    feature_order: tuple[str, ...]
    dataset_name: str
    dataset_checksum: str
    dataset_doi: str
    sanity_minimum: float
    sanity_maximum: float


@dataclass(frozen=True)
class VerifiedArtifact:
    """Integrity evidence collected before joblib deserialization."""

    spec: ArtifactSpec
    metadata: dict[str, Any]
    artifact_sha256: str
    metadata_sha256: str


@dataclass(frozen=True)
class LoadedCandidate:
    """Successfully verified and deserialized candidate."""

    spec: ArtifactSpec
    metadata: dict[str, Any]
    model: Any


_CACHE: dict[tuple[str, str, str], LoadedCandidate] = {}
_CACHE_LOCK = threading.RLock()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_json(path: Path, task: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{task} candidate metadata is unavailable or invalid.",
            task,
        ) from error
    if not isinstance(value, dict):
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{task} candidate metadata must be a JSON object.",
            task,
        )
    return value


def _trusted_path(path: Path, trusted_root: Path, task: str) -> Path:
    resolved = path.resolve()
    root = trusted_root.resolve()
    if not resolved.is_relative_to(root):
        raise ArtifactLoadError(
            "ARTIFACT_INCOMPATIBLE",
            f"{task} candidate path is outside the repository-controlled root.",
            task,
        )
    return resolved


def get_artifact_spec(task: str) -> ArtifactSpec:
    """Resolve a candidate exclusively from repository-controlled contracts."""

    inventory = _read_json(INVENTORY_PATH, task)
    contract = _read_json(MODEL_CONTRACT_PATH, task)
    candidates = inventory.get("candidates")
    if not isinstance(candidates, dict) or task not in candidates:
        raise ArtifactLoadError(
            "ARTIFACT_UNAVAILABLE",
            f"No reviewed candidate inventory exists for task '{task}'.",
            task,
        )

    candidate = candidates[task]
    contract_key = (
        "bangladesh_dmi_regressor"
        if task == "dmi"
        else "bangladesh_milk_yield_regressor"
    )
    try:
        contract_model = contract["models"][contract_key]
        target_range = inventory["training_dataset"][
            "observed_target_ranges"
        ][candidate["target"]]
        artifact_path = FLASK_API_DIR / candidate["artifact_path"]
        metadata_path = FLASK_API_DIR / candidate["metadata_path"]
        result = ArtifactSpec(
            task=task,
            model_name=candidate["model_name"],
            artifact_path=artifact_path,
            metadata_path=metadata_path,
            artifact_sha256=candidate["artifact_sha256"],
            metadata_sha256=candidate["metadata_sha256"],
            artifact_status=candidate["artifact_status"],
            target=candidate["target"],
            target_definition=contract_model["target_definition"],
            output_unit=candidate["output_unit"],
            feature_order=tuple(candidate["feature_order"]),
            dataset_name=inventory["training_dataset"]["name"],
            dataset_checksum=inventory["training_dataset"]["sha256"],
            dataset_doi=inventory["training_dataset"]["doi"],
            sanity_minimum=float(target_range["minimum"]),
            sanity_maximum=float(target_range["maximum"]),
        )
        if (
            result.target,
            result.output_unit,
        ) != EXPECTED_TASK_OUTPUTS[task]:
            raise ArtifactLoadError(
                "ARTIFACT_INCOMPATIBLE",
                f"The reviewed {task} output contract is incompatible.",
                task,
            )
        return result
    except (KeyError, TypeError, ValueError) as error:
        raise ArtifactLoadError(
            "ARTIFACT_INCOMPATIBLE",
            f"The reviewed {task} candidate inventory is incompatible.",
            task,
        ) from error


def _validate_metadata(
    spec: ArtifactSpec,
    metadata: dict[str, Any],
) -> None:
    exact_values = {
        "artifact_status": spec.artifact_status,
        "model_name": spec.model_name,
        "target": spec.target,
        "target_definition": spec.target_definition,
        "dataset_source": spec.dataset_name,
        "dataset_checksum": spec.dataset_checksum,
        "dataset_doi": spec.dataset_doi,
    }
    for field, expected in exact_values.items():
        if metadata.get(field) != expected:
            raise ArtifactLoadError(
                "ARTIFACT_METADATA_INVALID",
                f"{spec.task} metadata field '{field}' is incompatible.",
                spec.task,
            )

    if metadata.get("feature_order") != list(spec.feature_order):
        raise ArtifactLoadError(
            "ARTIFACT_INCOMPATIBLE",
            f"{spec.task} candidate feature order is incompatible.",
            spec.task,
        )
    if metadata.get("production_approved") is not False:
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{spec.task} candidate must remain production_approved=false.",
            spec.task,
        )
    if metadata.get("commercial_use_approved") is not False:
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{spec.task} candidate commercial approval must remain false.",
            spec.task,
        )
    if metadata.get("veterinary_use_approved") is not False:
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{spec.task} candidate veterinary approval must remain false.",
            spec.task,
        )
    if metadata.get("repeated_measurements") is not True:
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{spec.task} repeated-measure limitation is missing.",
            spec.task,
        )
    if metadata.get("number_of_unique_cows") != 50:
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{spec.task} dataset identity is incompatible.",
            spec.task,
        )

    reload_check = metadata.get("reload_check")
    if (
        not isinstance(reload_check, dict)
        or reload_check.get("artifact_sha256") != spec.artifact_sha256
        or reload_check.get("feature_order") != list(spec.feature_order)
        or reload_check.get("reload_predictions_identical") is not True
    ):
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{spec.task} reload evidence is missing or incompatible.",
            spec.task,
        )


def verify_candidate_integrity(
    task: str,
    *,
    spec: ArtifactSpec | None = None,
    trusted_root: Path = CANDIDATE_ROOT,
) -> VerifiedArtifact:
    """Verify file paths, hashes, and metadata without loading joblib."""

    candidate_spec = get_artifact_spec(task) if spec is None else spec
    artifact_path = _trusted_path(
        candidate_spec.artifact_path,
        trusted_root,
        task,
    )
    metadata_path = _trusted_path(
        candidate_spec.metadata_path,
        trusted_root,
        task,
    )

    if not artifact_path.is_file() or not metadata_path.is_file():
        raise ArtifactLoadError(
            "ARTIFACT_UNAVAILABLE",
            f"{task} candidate artifact or metadata file is missing.",
            task,
        )

    artifact_hash = _sha256(artifact_path)
    if artifact_hash != candidate_spec.artifact_sha256:
        LOGGER.error(
            "phase5_event=artifact_hash_mismatch task=%s",
            task,
        )
        raise ArtifactLoadError(
            "ARTIFACT_HASH_MISMATCH",
            f"{task} candidate artifact failed SHA-256 verification.",
            task,
        )

    metadata_hash = _sha256(metadata_path)
    if metadata_hash != candidate_spec.metadata_sha256:
        LOGGER.error(
            "phase5_event=metadata_hash_mismatch task=%s",
            task,
        )
        raise ArtifactLoadError(
            "ARTIFACT_METADATA_INVALID",
            f"{task} candidate metadata failed SHA-256 verification.",
            task,
        )

    metadata = _read_json(metadata_path, task)
    _validate_metadata(candidate_spec, metadata)
    return VerifiedArtifact(
        spec=replace(
            candidate_spec,
            artifact_path=artifact_path,
            metadata_path=metadata_path,
        ),
        metadata=metadata,
        artifact_sha256=artifact_hash,
        metadata_sha256=metadata_hash,
    )


def _validate_loaded_pipeline(loaded: LoadedCandidate) -> None:
    model = loaded.model
    if not hasattr(model, "predict") or not hasattr(model, "named_steps"):
        raise ArtifactLoadError(
            "ARTIFACT_INCOMPATIBLE",
            f"{loaded.spec.task} artifact is not the expected pipeline.",
            loaded.spec.task,
        )
    try:
        encoder = model.named_steps[
            "preprocessing"
        ].named_transformers_["categorical"]
        categories = [set(values.tolist()) for values in encoder.categories_]
    except (AttributeError, KeyError, TypeError) as error:
        raise ArtifactLoadError(
            "ARTIFACT_INCOMPATIBLE",
            f"{loaded.spec.task} preprocessing pipeline is incompatible.",
            loaded.spec.task,
        ) from error
    if categories != [EXPECTED_GENETIC_GROUPS, EXPECTED_THI_CATEGORIES]:
        raise ArtifactLoadError(
            "ARTIFACT_INCOMPATIBLE",
            f"{loaded.spec.task} encoded categories are incompatible.",
            loaded.spec.task,
        )


def load_candidate(
    task: str,
    *,
    spec: ArtifactSpec | None = None,
    trusted_root: Path = CANDIDATE_ROOT,
) -> LoadedCandidate:
    """Return a cached candidate only after all integrity checks pass."""

    candidate_spec = get_artifact_spec(task) if spec is None else spec
    cache_key = (
        task,
        candidate_spec.artifact_sha256,
        str(candidate_spec.artifact_path.resolve()),
    )
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None:
            return cached

        verified = verify_candidate_integrity(
            task,
            spec=candidate_spec,
            trusted_root=trusted_root,
        )
        try:
            model = joblib.load(verified.spec.artifact_path)
        except Exception as error:
            LOGGER.exception(
                "phase5_event=model_loading_failure task=%s",
                task,
            )
            raise ArtifactLoadError(
                "MODEL_ERROR",
                f"{task} candidate could not be deserialized.",
                task,
            ) from error

        loaded = LoadedCandidate(
            spec=verified.spec,
            metadata=verified.metadata,
            model=model,
        )
        _validate_loaded_pipeline(loaded)
        _CACHE[cache_key] = loaded
        return loaded


def clear_candidate_cache() -> None:
    """Clear the in-process cache for tests and controlled reloads."""

    with _CACHE_LOCK:
        _CACHE.clear()


__all__ = [
    "ArtifactLoadError",
    "ArtifactSpec",
    "LoadedCandidate",
    "VerifiedArtifact",
    "clear_candidate_cache",
    "get_artifact_spec",
    "load_candidate",
    "verify_candidate_integrity",
]
