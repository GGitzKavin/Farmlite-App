"""Run the Phase 3 preprocessing validation without training any model."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import MILK_YIELD_DATASET_PATH, ML_REPORTS_DIR
from ml.preprocessing.column_mapper import map_dataset_columns
from ml.preprocessing.data_cleaner import clean_data
from ml.preprocessing.data_loader import load_dataset
from ml.preprocessing.feature_builder import (
    BASE_NUMERIC_FEATURES,
    ModelContractError,
    build_features,
    get_model_spec,
    load_model_contract,
)
from ml.preprocessing.preprocessing_factory import (
    build_linear_preprocessor,
    build_preprocessor,
    build_tree_preprocessor,
)
from ml.preprocessing.preprocessing_types import ValidationMode
from ml.preprocessing.schema_validator import validate_schema
from ml.preprocessing.split_data import (
    create_split_assignments,
    create_training_fold_assignments,
    write_fold_artifacts,
    write_split_artifacts,
)


EXPECTED_PRIMARY_SHA256 = (
    "26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3"
)
SPLIT_MANIFEST_PATH = ML_REPORTS_DIR / "data_split_manifest.csv"
SPLIT_SUMMARY_PATH = ML_REPORTS_DIR / "data_split_summary.json"
SPLIT_REPORT_PATH = ML_REPORTS_DIR / "data_split_report.md"
OOF_MANIFEST_PATH = ML_REPORTS_DIR / "feed_type_oof_fold_manifest.csv"
OOF_SUMMARY_PATH = ML_REPORTS_DIR / "feed_type_oof_fold_summary.json"
VALIDATION_REPORT_PATH = ML_REPORTS_DIR / "preprocessing_validation_report.md"

BASE_FEATURES = [
    "breed",
    "age_months",
    "weight_kg",
    "lactation_stage",
    "days_in_milk",
    "previous_week_avg_yield_l",
    "body_condition_score",
    "ambient_temperature_c",
    "humidity_percent",
]
TARGETS = ["feed_type", "feed_quantity_kg", "milk_yield_l"]
REQUIRED_CANONICAL_COLUMNS = [
    "cattle_id",
    "observation_date",
    *BASE_FEATURES,
    *TARGETS,
]


class PreprocessingValidationError(RuntimeError):
    """Raised when a critical Phase 3 validation check fails."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _validate_artifacts(
    split_rows: int,
    fold_rows: int,
) -> dict[str, Any]:
    split_manifest = pd.read_csv(SPLIT_MANIFEST_PATH)
    fold_manifest = pd.read_csv(OOF_MANIFEST_PATH)
    split_summary = json.loads(SPLIT_SUMMARY_PATH.read_text(encoding="utf-8"))
    fold_summary = json.loads(OOF_SUMMARY_PATH.read_text(encoding="utf-8"))

    expected_split_columns = [
        "source_row_number",
        "cattle_id",
        "observation_date",
        "split",
        "random_seed",
        "split_version",
    ]
    expected_fold_columns = [
        "source_row_number",
        "cattle_id",
        "training_fold",
        "random_seed",
        "fold_version",
    ]
    checks = {
        "split_manifest_row_count": len(split_manifest) == split_rows,
        "fold_manifest_row_count": len(fold_manifest) == fold_rows,
        "split_manifest_columns": list(split_manifest.columns)
        == expected_split_columns,
        "fold_manifest_columns": list(fold_manifest.columns)
        == expected_fold_columns,
        "split_manifest_has_no_targets": not bool(
            set(TARGETS).intersection(split_manifest.columns)
        ),
        "fold_manifest_has_no_targets_or_predictions": not any(
            column in TARGETS or "predict" in column.casefold()
            for column in fold_manifest.columns
        ),
        "split_json_parsed": isinstance(split_summary, dict),
        "fold_json_parsed": isinstance(fold_summary, dict),
        "split_report_exists": SPLIT_REPORT_PATH.is_file(),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise PreprocessingValidationError(
            "Generated artifact validation failed: " + ", ".join(failed)
        )
    return checks


def _format_features(features: list[str]) -> str:
    return ", ".join(f"`{feature}`" for feature in features)


def _render_mapping_table(mapping: dict[str, str]) -> list[str]:
    lines = ["| Source column | Canonical column |", "|---|---|"]
    for source, canonical in mapping.items():
        lines.append(f"| `{source}` | `{canonical}` |")
    return lines


def _render_validation_report(evidence: dict[str, Any]) -> str:
    mapping = evidence["mapping"]
    validations = evidence["validations"]
    split = evidence["split"]
    fold = evidence["fold"]
    data_quality = evidence["data_quality"]
    artifact_checks = evidence["artifact_checks"]
    lines = [
        "# FarmLite Preprocessing Validation Report",
        "",
        "## Executive Summary",
        "",
        "**READY_FOR_PHASE_4_WITH_LIMITATIONS**",
        "",
        (
            "Phase 3 preprocessing, deterministic split assignment, and "
            "training-only fold preparation passed their internal checks. "
            "No classifier or regressor was trained, no prediction was "
            "generated, and this status does not authorize Phase 4."
        ),
        "",
        "## Dataset Source",
        "",
        f"- Dataset: Cattle Health and Feeding Data",
        f"- Publisher/account: ShahHet2812",
        f"- Source path: `{evidence['source_path']}`",
        f"- Rows: {evidence['row_count']:,}",
        f"- Columns loaded: {evidence['column_count']}",
        f"- SHA-256: `{evidence['source_sha256']}`",
        f"- Expected checksum matched: {evidence['source_checksum_matched']}",
        "",
        "The disease dataset was not loaded or merged.",
        "",
        "## Synthetic-Data Limitation",
        "",
        (
            "The publisher declares the dataset synthetic and potentially "
            "unrepresentative of real-world cattle. These components support "
            "an undergraduate pipeline demonstration only, not veterinary, "
            "nutritional, commercial, or real-world feeding claims."
        ),
        "",
        "## Canonical Column Mapping",
        "",
        *_render_mapping_table(mapping["mapped_columns"]),
        "",
        (
            f"Unmapped columns were preserved: "
            f"{len(mapping['unmapped_columns'])}. Ambiguous columns: "
            f"{len(mapping['ambiguous_columns'])}."
        ),
        "",
        "## Required Feature Availability",
        "",
        f"Approved base feature order: {_format_features(BASE_FEATURES)}.",
        "",
        (
            "All nine features and all three synthetic targets were present. "
            "Only the approved aliases were applied."
        ),
        "",
        "## Model 1 Feature Validation",
        "",
        f"- Valid schema: {validations['feed_type_classifier']['valid']}",
        f"- Features: {_format_features(evidence['features']['feed_type_classifier'])}",
        "- Target: `feed_type`",
        "- The target was separated from X.",
        "",
        "## Model 2 Design A Feature Validation",
        "",
        (
            f"- Valid schema: "
            f"{validations['feed_quantity_regressor_design_a']['valid']}"
        ),
        (
            "- Features: "
            f"{_format_features(evidence['features']['feed_quantity_regressor_design_a'])}"
        ),
        "- Target: `feed_quantity_kg`",
        "- The target was separated from X.",
        "",
        "## Model 2 Design B Interface Validation",
        "",
        f"- Default gate refused Design B: {evidence['design_b']['default_gate_refused']}",
        (
            "- True same-row feed type substitution refused: "
            f"{evidence['design_b']['true_feed_type_refused']}"
        ),
        "- Required derived feature: `predicted_feed_type`.",
        "- No predicted values or fake labels were generated.",
        "",
        "## Model 3 Feature Validation",
        "",
        f"- Valid schema: {validations['milk_yield_regressor']['valid']}",
        f"- Features: {_format_features(evidence['features']['milk_yield_regressor'])}",
        "- Target: `milk_yield_l`",
        "- Current `milk_yield_l` was excluded from X; prior-week yield remains historical input.",
        "",
        "## Missing-Value Handling",
        "",
        (
            "Numeric medians and categorical modes are defined inside unfitted "
            "sklearn pipelines. Optional numeric missingness indicators are "
            "included. No full-dataset imputation statistics were fitted."
        ),
        "",
        "## Categorical Handling",
        "",
        (
            "`breed` and `lactation_stage` use most-frequent imputation followed "
            "by OneHotEncoder(handle_unknown=\"ignore\"). Design B additionally "
            "defines `predicted_feed_type` as categorical."
        ),
        "",
        "## Numeric Handling",
        "",
        (
            f"Numeric fields are {_format_features(BASE_NUMERIC_FEATURES)}. "
            "Tree preprocessors leave numeric values unscaled; linear "
            "preprocessors add StandardScaler. All objects remained unfitted."
        ),
        "",
        "## Unknown-Category Handling",
        "",
        (
            "Unseen categories are warned about and preserved for the encoder. "
            "`Dry` is never mapped to Early, Mid, or Late, and an unknown breed "
            "is never mapped to Holstein or another breed."
        ),
        "",
        "## Data-Quality Flags",
        "",
        f"- Aggregated validation errors: {data_quality['aggregated_error_findings']}",
        f"- Aggregated validation warnings: {data_quality['aggregated_warning_findings']}",
        f"- Warning-affected rows/events: {data_quality['warning_affected_count']:,}",
        f"- Cleaner row-level issues: {data_quality['cleaner_issue_count']:,}",
        f"- Rows removed: {data_quality['rows_removed']}",
        (
            "- Zero synthetic milk-yield targets preserved and flagged: "
            f"{data_quality['zero_milk_yield_count']:,}"
        ),
        "",
        (
            "Range boundaries describe the synthetic contract/dataset and are "
            "not biological safety thresholds."
        ),
        "",
        "## Train/Validation/Test Split",
        "",
        f"- Train: {split['row_counts']['train']:,}",
        f"- Validation: {split['row_counts']['validation']:,}",
        f"- Test: {split['row_counts']['test']:,}",
        f"- Seed: {split['random_seed']}",
        f"- Reproducibility hash: `{split['reproducibility_hash_sha256']}`",
        (
            "- Feed-quantity material difference: "
            f"{split['feed_quantity_distribution_difference']['material_difference_detected']}"
        ),
        (
            "- Milk-yield material difference: "
            f"{split['milk_yield_distribution_difference']['material_difference_detected']}"
        ),
        "",
        "Full category and numeric summaries are in `data_split_report.md` and "
        "`data_split_summary.json`.",
        "",
        "## Out-of-Fold Assignment Preparation",
        "",
        f"- Training rows assigned: {fold['training_row_count']:,}",
        f"- Folds: {fold['number_of_folds']}",
        (
            "- Fold counts: "
            + ", ".join(
                f"{name}={count:,}" for name, count in fold["fold_counts"].items()
            )
        ),
        f"- Reproducibility hash: `{fold['reproducibility_hash_sha256']}`",
        "- Validation/test rows received no training fold.",
        "- The artifact contains no predictions.",
        "",
        "## Leakage Checks",
        "",
        "- Own targets are absent from every X frame.",
        "- Cattle and farm identifiers and observation dates are absent from X.",
        "- Same-record outcomes and disease fields are absent from X.",
        "- Split and fold manifests contain no predictive target values.",
        "- Design B refuses ground-truth `feed_type` substitution.",
        "",
        "## Determinism Checks",
        "",
        f"- Repeated split assignment identical: {evidence['determinism']['split_identical']}",
        f"- Repeated OOF assignment identical: {evidence['determinism']['fold_identical']}",
        (
            "- Generated artifact structure valid: "
            f"{all(artifact_checks.values())}"
        ),
        "",
        "## Application Mismatches",
        "",
        "- UI `Dry` has no matching dataset lactation category.",
        "- `healthStatus` is application-only and excluded from ML.",
        "- `productionStage` duplicates lactation stage.",
        "- Parity, season, climate zone, and management system are dataset-only.",
        "- `animalType` is not currently sent to the API.",
        "- The current PDF says L/day although the synthetic target period is unverified.",
        "",
        "No mappings were invented to resolve these differences.",
        "",
        "## Test Results",
        "",
        (
            "The validation command's loading, mapping, schema, feature, "
            "leakage, split, fold, pipeline-factory, artifact, and determinism "
            "checks passed. The separate automated test-suite result is "
            "recorded in the Phase 4 approval gate after it is run."
        ),
        "",
        "## Limitations",
        "",
        "- Kaggle license confirmation remains pending.",
        "- Detailed synthetic generation formulas are unavailable.",
        "- Feed-quantity material basis and period are unvalidated.",
        "- Milk-yield period and zero meaning are unvalidated.",
        "- The synthetic cattle data is not verified dairy-only.",
        "- No prediction model has been trained or evaluated in Phase 3.",
        "",
        "## Phase 4 Readiness Decision",
        "",
        "**READY_FOR_PHASE_4_WITH_LIMITATIONS**",
        "",
        (
            "This recommendation means the preprocessing boundary is ready for "
            "owner review. It does not authorize model training."
        ),
        "",
    ]
    return "\n".join(lines)


def run_validation() -> dict[str, Any]:
    """Execute all Phase 3 preprocessing checks and write approved artifacts."""

    contract = load_model_contract()
    if contract.get("contract_status") != "DESIGN_ONLY_NO_TRAINING_AUTHORIZED":
        raise PreprocessingValidationError(
            "The model contract no longer carries the no-training status"
        )

    source_hash = _sha256_file(MILK_YIELD_DATASET_PATH)
    if source_hash != EXPECTED_PRIMARY_SHA256:
        raise PreprocessingValidationError(
            "Primary dataset checksum differs from the approved Phase 2 value"
        )
    loaded = load_dataset(
        MILK_YIELD_DATASET_PATH,
        required_columns=[
            "Cattle_ID",
            "Breed",
            "Age_Months",
            "Weight_kg",
            "Lactation_Stage",
            "Days_in_Milk",
            "Previous_Week_Avg_Yield",
            "Body_Condition_Score",
            "Ambient_Temperature_C",
            "Humidity_percent",
            "Feed_Type",
            "Feed_Quantity_kg",
            "Milk_Yield_L",
            "Date",
        ],
    )
    mapped = map_dataset_columns(
        loaded.dataframe,
        required_columns=REQUIRED_CANONICAL_COLUMNS,
        raise_on_missing=True,
    )

    validation_models = [
        "feed_type_classifier",
        "feed_quantity_regressor_design_a",
        "milk_yield_regressor",
    ]
    validations = {
        name: validate_schema(
            mapped.dataframe,
            name,
            mode=ValidationMode.TRAINING_DATA,
        )
        for name in validation_models
    }
    invalid_models = [name for name, result in validations.items() if not result.valid]
    if invalid_models:
        raise PreprocessingValidationError(
            "Training schema validation failed for: " + ", ".join(invalid_models)
        )

    cleaned = clean_data(mapped.dataframe)
    if not cleaned.issues.empty and (
        cleaned.issues["severity"] == "ERROR"
    ).any():
        raise PreprocessingValidationError(
            "Cleaner detected hard invalid values; see row-level issues"
        )
    if len(cleaned.dataframe) != len(mapped.dataframe):
        raise PreprocessingValidationError("Cleaner changed the dataset row count")

    built = {
        name: build_features(cleaned.dataframe, name)
        for name in validation_models
    }
    for name, result in built.items():
        spec = get_model_spec(name)
        if result.feature_names != spec.feature_names:
            raise PreprocessingValidationError(
                f"Feature order differs from the contract for {name}"
            )
        if result.target_name in result.X.columns:
            raise PreprocessingValidationError(
                f"Own-target leakage found in {name}"
            )

    default_gate_refused = False
    true_feed_type_refused = False
    try:
        build_features(
            cleaned.dataframe.head(2),
            "feed_quantity_regressor_design_b",
        )
    except ModelContractError:
        default_gate_refused = True
    try:
        build_features(
            cleaned.dataframe.head(2),
            "feed_quantity_regressor_design_b",
            allow_predicted_feature=True,
        )
    except ModelContractError as error:
        true_feed_type_refused = "True same-row feed_type" in str(error)
    if not default_gate_refused or not true_feed_type_refused:
        raise PreprocessingValidationError(
            "Design B did not enforce its predicted-feature boundary"
        )

    preprocessors = {
        name: {
            "default": build_preprocessor(name),
            "linear": build_linear_preprocessor(name),
            "tree": build_tree_preprocessor(name),
        }
        for name in [
            "feed_type_classifier",
            "feed_quantity_regressor_design_a",
            "feed_quantity_regressor_design_b",
            "milk_yield_regressor",
        ]
    }
    if any(
        hasattr(preprocessor, "transformers_")
        for group in preprocessors.values()
        for preprocessor in group.values()
    ):
        raise PreprocessingValidationError(
            "A preprocessing factory unexpectedly returned a fitted object"
        )

    split_result = create_split_assignments(cleaned.dataframe)
    split_repeat = create_split_assignments(cleaned.dataframe)
    split_identical = split_result.manifest.equals(split_repeat.manifest)
    if (
        not split_identical
        or split_result.summary["reproducibility_hash_sha256"]
        != split_repeat.summary["reproducibility_hash_sha256"]
    ):
        raise PreprocessingValidationError(
            "Repeated split assignment was not deterministic"
        )

    fold_result = create_training_fold_assignments(
        cleaned.dataframe,
        split_result.manifest,
    )
    fold_repeat = create_training_fold_assignments(
        cleaned.dataframe,
        split_result.manifest,
    )
    fold_identical = fold_result.manifest.equals(fold_repeat.manifest)
    if (
        not fold_identical
        or fold_result.summary["reproducibility_hash_sha256"]
        != fold_repeat.summary["reproducibility_hash_sha256"]
    ):
        raise PreprocessingValidationError(
            "Repeated OOF fold assignment was not deterministic"
        )

    write_split_artifacts(
        split_result,
        manifest_path=SPLIT_MANIFEST_PATH,
        summary_path=SPLIT_SUMMARY_PATH,
        report_path=SPLIT_REPORT_PATH,
    )
    write_fold_artifacts(
        fold_result,
        manifest_path=OOF_MANIFEST_PATH,
        summary_path=OOF_SUMMARY_PATH,
    )
    artifact_checks = _validate_artifacts(
        split_rows=len(cleaned.dataframe),
        fold_rows=split_result.summary["row_counts"]["train"],
    )

    all_errors = [
        issue
        for result in validations.values()
        for issue in result.errors
    ]
    all_warnings = [
        issue
        for result in validations.values()
        for issue in result.warnings
    ]
    zero_milk_count = int(
        (pd.to_numeric(cleaned.dataframe["milk_yield_l"]) == 0).sum()
    )
    evidence: dict[str, Any] = {
        "source_path": str(loaded.metadata.source_path),
        "source_sha256": source_hash,
        "source_checksum_matched": source_hash == EXPECTED_PRIMARY_SHA256,
        "row_count": loaded.metadata.row_count,
        "column_count": loaded.metadata.column_count,
        "contract_version": contract["contract_version"],
        "mapping": mapped.metadata.to_dict(),
        "validations": {
            name: result.to_dict() for name, result in validations.items()
        },
        "features": {
            name: result.feature_names for name, result in built.items()
        },
        "design_b": {
            "default_gate_refused": default_gate_refused,
            "true_feed_type_refused": true_feed_type_refused,
            "predictions_generated": False,
        },
        "data_quality": {
            "aggregated_error_findings": len(all_errors),
            "aggregated_warning_findings": len(all_warnings),
            "warning_affected_count": sum(
                issue.affected_count for issue in all_warnings
            ),
            "cleaner_issue_count": len(cleaned.issues),
            "rows_removed": 0,
            "zero_milk_yield_count": zero_milk_count,
            "cleaner_metadata": cleaned.metadata,
        },
        "split": split_result.summary,
        "fold": fold_result.summary,
        "determinism": {
            "split_identical": split_identical,
            "fold_identical": fold_identical,
        },
        "artifact_checks": artifact_checks,
        "models_trained": False,
        "prediction_estimators_fitted": False,
        "preprocessors_fitted_on_full_data": False,
        "phase_4_readiness": "READY_FOR_PHASE_4_WITH_LIMITATIONS",
    }
    VALIDATION_REPORT_PATH.write_text(
        _render_validation_report(evidence),
        encoding="utf-8",
    )
    return evidence


def main() -> int:
    """CLI entry point used by the Phase 3 validation command."""

    try:
        evidence = run_validation()
    except (
        FileNotFoundError,
        ModelContractError,
        PreprocessingValidationError,
        ValueError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    split = evidence["split"]["row_counts"]
    folds = evidence["fold"]["fold_counts"]
    print("FarmLite Phase 3 preprocessing validation: PASSED WITH LIMITATIONS")
    print(
        f"Rows: train={split['train']:,}, validation={split['validation']:,}, "
        f"test={split['test']:,}"
    )
    print(
        "OOF folds: "
        + ", ".join(f"{fold}={count:,}" for fold, count in folds.items())
    )
    print(
        "No classifier or regressor was trained, evaluated, fitted, or persisted."
    )
    print(f"Report: {VALIDATION_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
