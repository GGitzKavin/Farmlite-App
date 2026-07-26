"""Generate and validate the read-only Rwanda dairy dataset audit.

Run from ``backend/flask_api``:

    venv\\Scripts\\python.exe -m ml.data_integration.validate_rwanda_dataset

No model training, prediction, source conversion, or permanent join occurs.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import (
    FLASK_API_DIR,
    MILK_YIELD_MODEL_PATH,
    PROJECT_ROOT,
)
from ml.data_integration.office_reader import read_docx, read_xlsx
from ml.data_integration.rwanda_audit import (
    AUDIT_VERSION,
    BUCKET_FILENAME,
    COW_FILENAME,
    DATASET_CITATION,
    EXPECTED_FILENAMES,
    EXPECTED_SHA256,
    EXTERNAL_METHOD_EVIDENCE,
    FODDER_FILENAME,
    METADATA_FILENAME,
    REPORT_DIR,
    RwandaAuditError,
    SCHEMA_PATH,
    SOURCE_DIR,
    analyze_join,
    build_inventory,
    candidate_feature_register,
    classify_feed_label,
    column_profile,
    common_schema,
    cow_quality_issues,
    dataframe_from_sheet,
    detect_repeated_cows,
    detect_target_fields,
    discover_rwanda_files,
    farmlite_compatibility,
    fodder_quality_issues,
    formula_consistency_issues,
    parse_metadata_definitions,
    sha256_file,
    target_matrix,
    write_csv,
    write_json,
)


AUDIT_REPORT_PATH = REPORT_DIR / "rwanda_dataset_audit.md"
INVENTORY_PATH = REPORT_DIR / "rwanda_dataset_inventory.json"
VARIABLE_DICTIONARY_PATH = REPORT_DIR / "rwanda_variable_dictionary.csv"
TARGET_MATRIX_PATH = REPORT_DIR / "rwanda_target_matrix.csv"
QUALITY_PATH = REPORT_DIR / "rwanda_data_quality_issues.csv"
JOIN_REPORT_PATH = REPORT_DIR / "rwanda_cross_file_join_report.md"
COMPATIBILITY_PATH = REPORT_DIR / "rwanda_farmlite_compatibility.csv"
OPTION_B_PATH = REPORT_DIR / "rwanda_option_b_support_report.md"
SOURCE_REGISTER_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_dataset_source_register.md"
)
METHODOLOGY_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_dataset_methodology_summary.md"
)
INTEGRATION_OPTIONS_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_dataset_integration_options.md"
)

REQUIRED_AUDIT_HEADINGS = [
    "# Rwanda Dairy Nutrition Dataset Audit",
    "## Executive Summary",
    "## Source Files",
    "## Licence and Citation",
    "## Study Design",
    "## Metadata Workbook",
    "## Individual-Cow Workbook",
    "### Observation Structure",
    "### Cow and Farm Identifiers",
    "### Repeated Measurements",
    "### Candidate Features",
    "### Candidate Targets",
    "### Missing Values",
    "### Data-Quality Issues",
    "## Fodder Components Workbook",
    "### Feed Ingredients",
    "### Dry Matter",
    "### Crude Protein",
    "### Energy",
    "### Fibre",
    "### Nutrient-Lookup Suitability",
    "## Bucket Feeding Plan",
    "### Purpose",
    "### Inputs",
    "### Outputs",
    "### Units and Period",
    "### Recommendation Status",
    "### Rule-Engine Suitability",
    "## Dry-Matter Intake Assessment",
    "## Milk-Yield Assessment",
    "## Water Assessment",
    "## Protein Assessment",
    "## Energy Assessment",
    "## Feed-Category Label Assessment",
    "## Cross-File Join Assessment",
    "## FarmLite Feature Compatibility",
    "## Leakage Risks",
    "## Common Schema",
    "## Option B Support Assessment",
    "## Limitations",
    "## Final Decision",
]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _escape(value: Any) -> str:
    if value is None:
        return "UNCLEAR"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _format_number(value: Any, digits: int = 4) -> str:
    if value is None:
        return "UNCLEAR"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    return str(value)


def _hash_tree(path: Path, *, excluded_parts: set[str] | None = None) -> str:
    excluded = excluded_parts or set()
    records = []
    if path.exists():
        for item in sorted(item for item in path.rglob("*") if item.is_file()):
            if excluded.intersection(item.parts):
                continue
            records.append(
                f"{item.relative_to(PROJECT_ROOT).as_posix()}|{sha256_file(item)}"
            )
    return hashlib.sha256("\n".join(records).encode("utf-8")).hexdigest().upper()


def _protected_snapshot() -> dict[str, Any]:
    candidate_dir = (
        FLASK_API_DIR / "ml" / "models" / "candidates" / "phase4"
    )
    processed_dir = PROJECT_ROOT / "datasets" / "processed"
    pdf_files = sorted(
        path
        for path in PROJECT_ROOT.rglob("*.pdf")
        if "venv" not in path.parts and "node_modules" not in path.parts
    )
    return {
        "routes": sha256_file(FLASK_API_DIR / "api" / "routes.py"),
        "feed_planner": sha256_file(
            FLASK_API_DIR / "ml" / "inference" / "feed_planner.py"
        ),
        "nutrition_rules": sha256_file(
            FLASK_API_DIR / "ml" / "validation" / "nutrition_rules.py"
        ),
        "retained_model": sha256_file(MILK_YIELD_MODEL_PATH),
        "phase4_candidates": {
            path.name: sha256_file(path)
            for path in sorted(candidate_dir.glob("*"))
            if path.is_file()
        },
        "frontend_tree": _hash_tree(
            PROJECT_ROOT / "frontend",
            excluded_parts={"node_modules", "dist"},
        ),
        "pdf_files": {
            path.relative_to(PROJECT_ROOT).as_posix(): sha256_file(path)
            for path in pdf_files
        },
        "processed_files": sorted(
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in processed_dir.rglob("*")
            if path.is_file()
        )
        if processed_dir.exists()
        else [],
    }


def _column_profiles(
    frame: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    return {
        column: column_profile(frame, column)
        for column in frame.columns
        if column != "source_row_number"
    }


def _formula_audit(cow_sheet: Any) -> dict[str, Any]:
    return {
        "formula_count": cow_sheet.formula_count,
        "formula_cells": [
            {
                "cell": cell.reference,
                "formula": cell.formula,
                "cached_value": cell.value,
            }
            for cell in cow_sheet.cells
            if cell.formula is not None
        ],
        "note": (
            "Only eight source cells contain Excel formulas; most calculated "
            "values are stored as constants. Formulas were not recalculated."
        ),
    }


def _ingredient_summary(fodder_frame: pd.DataFrame) -> dict[str, Any]:
    raw_ingredients: list[str] = []
    samples_with_repeated_tokens = 0
    for value in fodder_frame["SAMPLE ID"]:
        if value is None:
            continue
        tokens = [
            token.strip()
            for token in str(value).replace("/", ",").split(",")
            if token.strip()
        ]
        raw_ingredients.extend(tokens)
        lowered = [token.casefold() for token in tokens]
        if len(lowered) != len(set(lowered)):
            samples_with_repeated_tokens += 1
    counts = Counter(raw_ingredients)
    return {
        "sample_count": len(fodder_frame),
        "raw_ingredient_token_count": len(raw_ingredients),
        "case_sensitive_unique_token_count": len(counts),
        "top_raw_tokens": [
            {"source_feed_name": name, "count": count}
            for name, count in counts.most_common(20)
        ],
        "samples_with_repeated_tokens": samples_with_repeated_tokens,
        "standardized_names_created": False,
        "reason": (
            "Spelling and taxonomy were not standardized because no "
            "expert-reviewed mapping is supplied."
        ),
    }


def _feed_component_register(
    fodder_frame: pd.DataFrame,
    join_audit: dict[str, Any],
) -> list[dict[str, Any]]:
    """Register raw composite lists without inventing standardized names."""

    records = []
    for _, row in fodder_frame.iterrows():
        records.append(
            {
                "source_feed_name": row["SAMPLE ID"],
                "standardized_name": "NOT_CREATED",
                "feed_category": "UNCLEAR",
                "dry_matter_percentage": (
                    "AVAILABLE_ONLY_AFTER_LIMITED_LabN_JOIN"
                ),
                "crude_protein_percentage": (
                    "AVAILABLE_ONLY_AFTER_LIMITED_LabN_JOIN"
                ),
                "energy_content": "AVAILABLE_ONLY_AFTER_LIMITED_LabN_JOIN",
                "fibre_content": (
                    "AVAILABLE_ONLY_AFTER_LIMITED_LabN_JOIN_UNIT_UNCLEAR"
                ),
                "mineral_content": "NOT_AVAILABLE",
                "unit": "ingredient-list text",
                "measurement_method": (
                    "Observed daily composite fodder list; nutrient methods "
                    "documented separately for composite laboratory samples."
                ),
                "number_of_samples": 1,
                "missing_fields": (
                    "category; standardized name; direct nutrient columns; minerals"
                ),
                "lab_sample_id": row["Lab N°"],
                "join_safety": join_audit["join_safety"],
            }
        )
    return records


def _metadata_report(
    definitions: list[Any],
    metadata_sheet: Any,
) -> str:
    measured = Counter(item.measurement_status for item in definitions)
    examples = definitions[:8]
    return "\n".join(
        [
            f"- Sheets: `{metadata_sheet.name}`",
            f"- Populated rows: {metadata_sheet.row_count}",
            f"- Populated columns: {metadata_sheet.column_count}",
            "- Definition-table columns: `Number`, `Variables`, `explanations/definitions`",
            f"- Parsed definitions: {len(definitions)}",
            "- Missing-value codes: none documented.",
            "- Category definitions: sites, broad breed, lactation period, and calf age bands are documented.",
            "- Formula descriptions: DMI, water, milk, ME, and CP equations are documented.",
            (
                "- Measurement-status counts: "
                + ", ".join(
                    f"{status}={count}"
                    for status, count in sorted(measured.items())
                )
            ),
            "",
            "| Variable | Exact definition | Unit | Period | Status |",
            "|---|---|---|---|---|",
            *[
                f"| `{_escape(item.source_variable_name)}` | "
                f"{_escape(item.exact_definition)} | {_escape(item.unit)} | "
                f"{_escape(item.period)} | `{item.measurement_status}` |"
                for item in examples
            ],
            "",
            (
                "The complete 48-field register is in "
                "`rwanda_variable_dictionary.csv`."
            ),
        ]
    )


def _cow_column_table(
    profiles: dict[str, dict[str, Any]],
) -> list[str]:
    lines = [
        "| Source column | Missing | Missing % | Unique | Types | Min | Max | Mean |",
        "|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for name, profile in profiles.items():
        numeric = profile["numeric_summary"]
        lines.append(
            f"| `{_escape(name)}` | {profile['missing_count']} | "
            f"{profile['missing_percentage']:.2f} | {profile['unique_count']} | "
            f"{_escape(json.dumps(profile['data_types'], sort_keys=True))} | "
            f"{_format_number(numeric['minimum'])} | "
            f"{_format_number(numeric['maximum'])} | "
            f"{_format_number(numeric['mean'])} |"
        )
    return lines


def _target_summary(
    definitions: list[Any],
    domain: str,
) -> list[str]:
    records = detect_target_fields(definitions, domain)
    return [
        "| Field | Source definition | Unit | Period | Measurement | Status |",
        "|---|---|---|---|---|---|",
        *[
            f"| `{_escape(item['source_variable_name'])}` | "
            f"{_escape(item['exact_definition'])} | {_escape(item['unit'])} | "
            f"{_escape(item['period'])} | "
            f"`{item['measurement_status']}` | `{item['status']}` |"
            for item in records
        ],
    ]


def _render_audit_report(
    *,
    inventory: dict[str, Any],
    metadata_workbook: Any,
    definitions: list[Any],
    cow_frame: pd.DataFrame,
    cow_profiles: dict[str, dict[str, Any]],
    repeated: dict[str, Any],
    feature_register: list[dict[str, Any]],
    fodder_frame: pd.DataFrame,
    ingredient_summary: dict[str, Any],
    document: Any,
    join_audit: dict[str, Any],
    quality_issues: list[dict[str, Any]],
    formula_audit: dict[str, Any],
) -> str:
    severity = Counter(issue["severity"] for issue in quality_issues)
    types = Counter(issue["issue_type"] for issue in quality_issues)
    available_features = [
        item["candidate_feature"]
        for item in feature_register
        if item["exact_source_column"] != "NOT_AVAILABLE"
    ]
    lines = [
        "# Rwanda Dairy Nutrition Dataset Audit",
        "",
        "## Executive Summary",
        "",
        (
            "The source contains 96 cross-sectional lactating-cow observations, "
            "daily measured/recorded feed, milk, and water fields, composite "
            "feed laboratory characteristics, calculated nutrient intake and "
            "requirement fields, and 97 observed fodder-mixture descriptions."
        ),
        (
            "It does not contain cow or farm identifiers, observation dates, "
            "a true feed recommendation label, optimized rations, concentrate "
            "quantities, mineral data, environmental measurements, or a "
            "lactating-cow ration-selection rule."
        ),
        (
            "DMI is documented as served DM minus next-morning leftovers, but "
            "28 negative leftover values block an unqualified DMI target until "
            "the authors clarify the source column. Milk and water fields are "
            "daily, but any model design remains limited by the small "
            "cross-sectional sample and absent grouping identifiers."
        ),
        "",
        "Final audit decision: **PARTIAL_OPTION_B_SUPPORT**. No training occurred.",
        "",
        "## Source Files",
        "",
        "| File | Size bytes | SHA-256 | Opens | Sheets/tables |",
        "|---|---:|---|---|---|",
        *[
            f"| `{item['filename']}` | {item['file_size_bytes']} | "
            f"`{item['sha256']}` | {item['opens_successfully']} | "
            f"{item['excel_sheet_count'] if item['excel_sheet_count'] is not None else item['docx_table_count']} |"
            for item in inventory["files"]
        ],
        "",
        "All source archives remained in place and were read without conversion.",
        "",
        "## Licence and Citation",
        "",
        (
            f"- Dataset: {DATASET_CITATION['title']} "
            f"({DATASET_CITATION['repository']}, V{DATASET_CITATION['version']})."
        ),
        f"- Dataset DOI: `{DATASET_CITATION['doi']}`.",
        f"- Dataset licence: `{DATASET_CITATION['licence']}`.",
        f"- Related article DOI: `{DATASET_CITATION['related_article_doi']}`.",
        (
            "- The supplied files contain authorship/citation text but no "
            "licence statement; licence evidence comes from the Mendeley record."
        ),
        "",
        "## Study Design",
        "",
        f"- {EXTERNAL_METHOD_EVIDENCE['study_design']}",
        f"- {EXTERNAL_METHOD_EVIDENCE['cow_and_farm_count']}",
        "- Sampling was purposive at the cow/farm stage, not a randomized feeding trial.",
        "- Data collection was observational and cross-sectional.",
        "- Feeding system was cut-and-carry fodder based across the study.",
        "",
        "## Metadata Workbook",
        "",
        _metadata_report(definitions, metadata_workbook.sheets[0]),
        "",
        "## Individual-Cow Workbook",
        "",
        f"- Sheet: `Raw data`; rows: {len(cow_frame)}; columns: 43.",
        "- Header row: Excel row 11; source data rows: 12-107.",
        "- Duplicate complete rows: 0.",
        f"- Excel formula cells: {formula_audit['formula_count']}; most calculated values are stored constants.",
        "",
        "### Observation Structure",
        "",
        (
            "The repository describes one cross-sectional lactating-cow "
            "observation from each of 96 farms. The workbook has 96 rows but "
            "does not contain a cow_id or farm_id, so row-level identity and "
            "repeated-cow absence cannot be independently proven from the file."
        ),
        "",
        "### Cow and Farm Identifiers",
        "",
        "- `LabN°` is a composite feed laboratory/sample key, not a cow identifier.",
        "- Workbook cow_id: `NOT_AVAILABLE`.",
        "- Workbook farm_id: `NOT_AVAILABLE`.",
        "- Publication-reported farms: 96; workbook-verifiable farm count: `UNCLEAR`.",
        f"- `LabN°` unique values: {cow_frame['LabN°'].nunique(dropna=True)}.",
        "",
        "### Repeated Measurements",
        "",
        f"- Status: `{repeated['status']}`.",
        f"- Reason: {repeated['reason']}",
        f"- Future splitting rule: {repeated['future_split_rule']}",
        "",
        "### Candidate Features",
        "",
        "- Evidenced fields: " + ", ".join(f"`{name}`" for name in available_features) + ".",
        "- Current milk must be excluded from X when milk yield is the target.",
        "- DMI, water, CP, ME, and gap outcomes must not enter pre-outcome features.",
        "- `LabN°` and source row are identifiers only.",
        "",
        "### Candidate Targets",
        "",
        "- DMI: calculated source field, blocked pending negative-leftover clarification.",
        "- Milk: verified daily hand-milk and calculated total daily milk, ready with limitations.",
        "- Water: daily jerry-can-recorded intake, ready with limitations.",
        "- CP and ME: calculated intakes/requirements, more defensible for rule validation than ML labels.",
        "- Feed/ration category: no expert or optimized label.",
        "",
        "### Missing Values",
        "",
        *(_cow_column_table(cow_profiles)),
        "",
        (
            "In addition to explicit blanks, `cowageinyears` has 30 nonnumeric "
            "highland breed descriptions. Effective usable numeric age is "
            "64/96, not the apparent 94/96 nonblank count."
        ),
        "",
        "### Data-Quality Issues",
        "",
        (
            "- Total issue records: "
            f"{len(quality_issues)} ("
            + ", ".join(
                f"{name}={count}" for name, count in sorted(severity.items())
            )
            + ")."
        ),
        "- Leading issue types: "
        + ", ".join(
            f"{name}={count}" for name, count in types.most_common(10)
        )
        + ".",
        "- No source record was removed, filled, standardized, or corrected.",
        "",
        "## Fodder Components Workbook",
        "",
        "- Sheets: `Composites feeds` (97 data rows) and `Sheet2` (2 definitions).",
        "- Each row is a composite daily fodder-ingredient list keyed by `Lab N°`.",
        "- Duplicate complete rows: 0; duplicate `Lab N°`: 0.",
        "",
        "### Feed Ingredients",
        "",
        (
            f"- Raw ingredient tokens: {ingredient_summary['raw_ingredient_token_count']}; "
            f"case-sensitive unique raw tokens: {ingredient_summary['case_sensitive_unique_token_count']}."
        ),
        "- No standardized feed names or inferred categories were created.",
        "",
        "### Dry Matter",
        "",
        (
            "No DM values are stored in this workbook. Composite-sample DM "
            "percentage is in cow-workbook column `DMfeeds` and requires the "
            "limited `Lab N°` relationship."
        ),
        "",
        "### Crude Protein",
        "",
        (
            "No CP values are stored in this workbook. Composite CP percentage "
            "is in `%Protein` in the cow workbook."
        ),
        "",
        "### Energy",
        "",
        (
            "No energy values are stored in this workbook. Calculated "
            "`MEfeeds` is in the cow workbook."
        ),
        "",
        "### Fibre",
        "",
        (
            "`NDF feeds` is stored in the cow workbook. Its metadata unit "
            "conflicts with the percentage-like values/equation and is UNCLEAR."
        ),
        "",
        "### Nutrient-Lookup Suitability",
        "",
        (
            "Decision: `PARTIALLY_COMPATIBLE`. It supports observed composite "
            "ingredient lookup after the limited Lab N° relationship, but not "
            "ingredient-specific nutrient lookup, direct ration validation, "
            "mineral calculations, or recommendation labels."
        ),
        "",
        "## Bucket Feeding Plan",
        "",
        "### Purpose",
        "",
        (
            "One supplemental table describes a calf milk bucket-feeding "
            "program reported as followed by farmers in Rwanda's highlands and lowlands."
        ),
        "",
        "### Inputs",
        "",
        "- Calf age bands from birth through weaning.",
        "",
        "### Outputs",
        "",
        "- Milk consumption per calf per day and contextual cow milk production per day.",
        "",
        "### Units and Period",
        "",
        "- Litres per day; some cells show morning/evening allocations such as `2L-2L`.",
        "",
        "### Recommendation Status",
        "",
        (
            "Status: `VERIFIED_OBSERVED_PRACTICE`. The document says the plan "
            "was followed by farmers and cites farmer-field-school promoters; "
            "it does not establish an optimized or expert-approved ration."
        ),
        "",
        "### Rule-Engine Suitability",
        "",
        (
            "Supporting calf milk-allocation evidence only. It does not provide "
            "a lactating-cow roughage, concentrate, water, mineral, or ration-selection rule."
        ),
        "",
        "## Dry-Matter Intake Assessment",
        "",
        *(_target_summary(definitions, "dmi")),
        "",
        (
            "The repository verifies daily DMI as served DM minus leftovers. "
            "The source column named `DMIcapacity (kgDM)` matches that equation, "
            "but it also matches a BW/NDF capacity equation and 28 leftover "
            "values are negative. Target status: `CALCULATED_DMI`; model-design "
            "decision: `BLOCKED_UNCLEAR_DEFINITION` until clarified."
        ),
        "",
        "## Milk-Yield Assessment",
        "",
        *(_target_summary(definitions, "milk")),
        "",
        (
            "`hand-milked yield` is the directly measured daily candidate "
            "(96 usable; 1-17 L/day; mean 6.0542). `Total milk performance` "
            "adds model-assumed calf suckling and is calculated. Model decision: "
            "`READY_WITH_LIMITATIONS`, especially due absent grouping keys."
        ),
        "",
        "## Water Assessment",
        "",
        *(_target_summary(definitions, "water")),
        "",
        (
            "`waterday` has 96 usable values, 15-80 L/cow/day, mean 35.1042. "
            "It is container-based daily water provided/recorded, not a precise "
            "metered consumption measurement. Requirement and gaps are calculated. "
            "Model decision: `READY_WITH_LIMITATIONS`."
        ),
        "",
        "## Protein Assessment",
        "",
        *(_target_summary(definitions, "protein")),
        "",
        (
            "CP percentage is laboratory-derived; CP intake, maintenance, milk "
            "requirement, total requirement, and gaps are calculated. A metadata "
            "formula contradiction exists for `gapCP`. Best use: transparent "
            "rule validation after formula confirmation, not a learned requirement target."
        ),
        "",
        "## Energy Assessment",
        "",
        *(_target_summary(definitions, "energy")),
        "",
        (
            "ME composition, intake, maintenance, potential-milk requirement, "
            "and gaps are calculated. `MEfeeds` lacks the row-level gas-volume "
            "input required to independently reproduce it. Best use: rule "
            "validation with documented equations and provenance."
        ),
        "",
        "## Feed-Category Label Assessment",
        "",
        (
            "The fodder workbook records ingredients actually served. It does "
            "not identify a nutritionist recommendation, optimized ration, "
            "treatment optimum, or broad expert label. Status: "
            "`OBSERVED_DIET_ONLY`. A genuine feed recommendation classifier is "
            "not supported; `EXPERT_FEED_LABELS_REQUIRED`."
        ),
        "",
        "## Cross-File Join Assessment",
        "",
        (
            f"Cow workbook to fodder workbook via LabN°/Lab N°: "
            f"{join_audit['matched_left_row_count']}/{join_audit['left_row_count']} "
            f"cow rows match ({join_audit['left_match_percentage']:.2f}%). "
            f"Status: `{join_audit['join_safety']}`."
        ),
        (
            f"The cow table has {join_audit['left_duplicate_key_count']} duplicate "
            "key occurrences; the fodder table has none. There is no many-to-many join."
        ),
        "- Metadata links semantically, not by record key.",
        "- The DOCX has no cow/sample/farm key and cannot be row-joined.",
        "",
        "## FarmLite Feature Compatibility",
        "",
        "- Direct/partial current inputs: breed, age_years, weight, lactation stage, days in milk.",
        "- Missing current inputs: previous-week yield, body-condition score, temperature, humidity.",
        "- Useful future fields: parity, site, daily water, served DM, leftovers, and ingredient list.",
        "- No frontend change was made.",
        "",
        "## Leakage Risks",
        "",
        "- Current/total milk is target leakage for a milk-yield model.",
        "- DMI, water, CP, ME, requirements, and gaps are same-row outcomes.",
        "- Calculated requirements are deterministic equations and poor ML targets.",
        "- `LabN°` and source row can enable memorization and are identifier-only.",
        "- Random row splitting is not defensible without cow/farm grouping evidence.",
        "",
        "## Common Schema",
        "",
        (
            "The evidence-only schema is stored at "
            "`backend/flask_api/config/rwanda_dairy_common_schema.json`. "
            "Unsupported fields were omitted rather than filled with guesses."
        ),
        "",
        "## Option B Support Assessment",
        "",
        "| Component | Decision |",
        "|---|---|",
        "| DMI regression | `BLOCKED_UNCLEAR_DEFINITION` |",
        "| Milk-yield regression | `READY_WITH_LIMITATIONS` |",
        "| Water-intake regression | `READY_WITH_LIMITATIONS` |",
        "| CP intake/requirement | `READY_WITH_LIMITATIONS` for calculations/rules |",
        "| Energy intake/requirement | `READY_WITH_LIMITATIONS` for calculations/rules |",
        "| Feed/ration category | `NOT_SUPPORTED` without expert labels |",
        "| Bucket ration selection | `NOT_SUPPORTED` for lactating cows |",
        "",
        "## Limitations",
        "",
        "- Small cross-sectional sample: 96 cow observations.",
        "- No cow_id, farm_id, observation date, repeated-observation key, or treatment period.",
        "- Purposive cow/farm inclusion limits representativeness.",
        "- Thirty highland age cells contain breed text; two more are blank.",
        "- Twenty-eight negative leftover values conflict with the weighing method.",
        "- NDF unit and CP-gap metadata formula require clarification.",
        "- Composite ingredients lack quantities and expert categories.",
        "- No environmental measurements or historical milk yield.",
        "",
        "## Final Decision",
        "",
        "**PARTIAL_OPTION_B_SUPPORT**",
        "",
        (
            "The source can support a later, separately approved design phase "
            "for daily milk and water models and transparent nutrient rules. "
            "DMI model design is blocked pending source clarification. A genuine "
            "feed classifier and full ration recommendation remain unsupported."
        ),
        "",
        "No model was trained, evaluated, integrated, replaced, or deployed.",
    ]
    return "\n".join(lines)


def _render_join_report(
    join_audit: dict[str, Any],
) -> str:
    return "\n".join(
        [
            "# Rwanda Cross-File Join Audit",
            "",
            "No permanent or processed join was created.",
            "",
            "| Left file | Right file | Keys | Cardinality evidence | Match | Safety |",
            "|---|---|---|---|---:|---|",
            (
                f"| `{COW_FILENAME}` | `{FODDER_FILENAME}` | "
                f"`LabN°` -> `Lab N°` | "
                f"{join_audit['left_unique_key_count']} unique left keys; "
                f"{join_audit['right_unique_key_count']} unique right keys; "
                f"{join_audit['left_duplicate_key_count']} left duplicate occurrences | "
                f"{join_audit['left_match_percentage']:.2f}% | "
                f"`{join_audit['join_safety']}` |"
            ),
            (
                f"| `Metadata.xlsx` | All sources | Semantic definitions only | "
                "No record key | N/A | `NO_VALID_JOIN_KEY` |"
            ),
            (
                f"| `{BUCKET_FILENAME}` | Cow/fodder sources | No shared key | "
                "Separate calf-practice table | 0% | `NO_VALID_JOIN_KEY` |"
            ),
            "",
            "## Lab Sample Relationship",
            "",
            f"- Cow rows: {join_audit['left_row_count']}.",
            f"- Fodder rows: {join_audit['right_row_count']}.",
            f"- Matched cow rows: {join_audit['matched_left_row_count']}.",
            (
                "- Fodder-only keys: "
                + ", ".join(join_audit["unmatched_right_keys"])
                + "."
            ),
            f"- Many-to-many risk: {join_audit['many_to_many_risk']}.",
            f"- Meaning: {join_audit['meaning']}",
            "",
            (
                "Although every cow row finds a fodder record, repeated LabN° "
                "values conflict with a simplistic one-sample-per-cow assumption. "
                "Use only after confirming sample-sharing semantics."
            ),
        ]
    )


def _render_option_b_report() -> str:
    answers = [
        (
            "1. Better feed-quantity or DMI model?",
            (
                "`BLOCKED_UNCLEAR_DEFINITION`. Daily DMI is documented, but "
                "negative leftovers and dual capacity/intake semantics need author correction."
            ),
        ),
        (
            "2. Daily milk-yield model?",
            (
                "`READY_WITH_LIMITATIONS` using measured hand-milked L/day; "
                "small cross-sectional data and missing grouping IDs remain."
            ),
        ),
        (
            "3. Water-intake prediction?",
            (
                "`READY_WITH_LIMITATIONS`; waterday is L/cow/day but based on "
                "jerry cans provided rather than metered drinking."
            ),
        ),
        (
            "4. CP intake/requirement?",
            "Supports documented calculations/rule validation; not a direct learned requirement.",
        ),
        (
            "5. Energy intake/requirement?",
            "Supports documented calculations/rule validation with missing G24 reproduction input.",
        ),
        (
            "6. Roughage/concentrate quantities?",
            "No. Ingredient lists have neither quantities nor validated categories.",
        ),
        (
            "7. True feed recommendation label?",
            "No. Only observed composite fodders and farmer calf practice.",
        ),
        (
            "8. Bucket plan ration-selection rule?",
            "No for lactating cows; it is observed calf milk-allocation practice.",
        ),
        (
            "9. Fodder workbook nutrient calculations?",
            (
                "Partially. It supplies ingredient text; composite nutrient "
                "values are in the cow workbook and require a limited LabN join."
            ),
        ),
        (
            "10. Can files be joined safely?",
            (
                "Cow-to-fodder is `POSSIBLE_WITH_LIMITATIONS`; metadata is "
                "semantic; DOCX has no join key."
            ),
        ),
        (
            "11. Repeated cow observations?",
            "UNCLEAR because cow_id is absent; source methodology says cross-sectional.",
        ),
        (
            "12. Missing FarmLite inputs?",
            (
                "previous-week yield, body-condition score, ambient "
                "temperature, and humidity; numeric age is incomplete."
            ),
        ),
        (
            "13. Potential future inputs?",
            (
                "parity, site, served DM, leftovers, water intake, and observed "
                "ingredient list, subject to timing and quality controls."
            ),
        ),
        (
            "14. Keep synthetic data in training?",
            (
                "Do not merge it with Rwanda records. Retain it only as a "
                "separate historical prototype benchmark."
            ),
        ),
        (
            "15. Phase 4 redesign priorities?",
            (
                "Redesign milk and water candidates separately; investigate "
                "DMI after correction; do not rebuild feed classification "
                "without expert recommendation labels."
            ),
        ),
    ]
    return "\n".join(
        [
            "# Rwanda Option B Support Report",
            "",
            "## Decision: `PARTIAL_OPTION_B_SUPPORT`",
            "",
            *[
                f"### {question}\n\n{answer}\n"
                for question, answer in answers
            ],
            "## Boundary",
            "",
            (
                "This is an audit decision only. It does not authorize model "
                "training, preprocessing, source merging, frontend changes, "
                "nutrition-rule changes, integration, or deployment."
            ),
        ]
    )


def _render_source_register(inventory: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Rwanda Dairy Dataset Source Register",
            "",
            f"- Dataset title: {DATASET_CITATION['title']}",
            "- Contributors: " + ", ".join(DATASET_CITATION["contributors"]),
            f"- Repository: {DATASET_CITATION['repository']}",
            f"- Dataset DOI: `{DATASET_CITATION['doi']}`",
            f"- Dataset URL: {DATASET_CITATION['url']}",
            f"- Version/published: {DATASET_CITATION['version']} / {DATASET_CITATION['published']}",
            f"- Dataset licence: `{DATASET_CITATION['licence']}`",
            f"- Related article DOI: `{DATASET_CITATION['related_article_doi']}`",
            f"- Related article URL: {DATASET_CITATION['related_article_url']}",
            f"- Licence note: {DATASET_CITATION['licence_scope_note']}",
            "",
            "## Supplied Files",
            "",
            "| File | SHA-256 | Size bytes |",
            "|---|---|---:|",
            *[
                f"| `{item['filename']}` | `{item['sha256']}` | "
                f"{item['file_size_bytes']} |"
                for item in inventory["files"]
            ],
            "",
            (
                "The supplied Office files contain title, author, and "
                "affiliation text but no licence statement. Dataset-licence "
                "evidence is taken from the repository record."
            ),
        ]
    )


def _render_methodology() -> str:
    return "\n".join(
        [
            "# Rwanda Dairy Dataset Methodology Summary",
            "",
            "## Design",
            "",
            f"- {EXTERNAL_METHOD_EVIDENCE['study_design']}",
            f"- {EXTERNAL_METHOD_EVIDENCE['cow_and_farm_count']}",
            "- Observational, cross-sectional, and purposively selected at the final cow/farm stage.",
            "",
            "## Measurements",
            "",
            f"- Body weight: {EXTERNAL_METHOD_EVIDENCE['body_weight']}",
            f"- Feed: {EXTERNAL_METHOD_EVIDENCE['feed']}",
            f"- DMI: {EXTERNAL_METHOD_EVIDENCE['dmi']}",
            f"- Milk: {EXTERNAL_METHOD_EVIDENCE['milk']}",
            f"- Water: {EXTERNAL_METHOD_EVIDENCE['water']}",
            f"- Feed samples: {EXTERNAL_METHOD_EVIDENCE['feed_samples']}",
            f"- Laboratory methods: {EXTERNAL_METHOD_EVIDENCE['laboratory_methods']}",
            "",
            "## Calculations",
            "",
            f"- {EXTERNAL_METHOD_EVIDENCE['requirements']}",
            "- Milk, DMI, water, ME, and CP gaps are calculated, not directly measured.",
            "- Potential milk and nutrient requirements are model/equation derived.",
            "",
            "## Audit Caveats",
            "",
            "- Twenty-eight negative leftover values conflict with physical next-morning weighing.",
            "- The highland age column contains breed descriptions.",
            "- NDF unit metadata conflicts with value semantics.",
            "- CP-gap metadata wording conflicts with repository equations and values.",
            "",
            f"Primary methodology record: {EXTERNAL_METHOD_EVIDENCE['source_url']}",
        ]
    )


def _render_integration_options() -> str:
    return "\n".join(
        [
            "# Rwanda Dataset Integration Options",
            "",
            "No integration is authorized in Phase 4.5A.",
            "",
            "| Future option | Current status | Prerequisite |",
            "|---|---|---|",
            (
                "| Daily hand-milk model design | `READY_WITH_LIMITATIONS` | "
                "Approve a grouped-validation strategy or acknowledge that grouping IDs are unavailable. |"
            ),
            (
                "| Water-intake model design | `READY_WITH_LIMITATIONS` | "
                "Clarify provided water versus consumed water and define intended prediction timing. |"
            ),
            (
                "| DMI model design | `BLOCKED_UNCLEAR_DEFINITION` | "
                "Resolve negative leftovers and DMIcapacity naming/semantics with source authors. |"
            ),
            (
                "| CP/ME rule validation | `READY_WITH_LIMITATIONS` | "
                "Confirm NDF unit, CP-gap formula, and model/equation provenance. |"
            ),
            (
                "| Ingredient lookup | `PARTIALLY_COMPATIBLE` | "
                "Create an expert-reviewed ingredient vocabulary and confirm LabN sample sharing. |"
            ),
            (
                "| Feed recommendation classifier | `EXPERT_FEED_LABELS_REQUIRED` | "
                "Collect nutritionist-approved or optimized ration labels. |"
            ),
            (
                "| Calf milk allocation rule | `SUPPORTING_DATA_ONLY` | "
                "Separate calf domain review; outside lactating-cow Option B. |"
            ),
            "",
            "## Synthetic Dataset Boundary",
            "",
            (
                "Do not merge the Phase 4 synthetic records with Rwanda records. "
                "They have different provenance, population, target semantics, "
                "feature availability, and validation limitations."
            ),
        ]
    )


def _validate_outputs(
    inventory: dict[str, Any],
    document: Any,
) -> None:
    required_paths = [
        INVENTORY_PATH,
        AUDIT_REPORT_PATH,
        VARIABLE_DICTIONARY_PATH,
        TARGET_MATRIX_PATH,
        QUALITY_PATH,
        JOIN_REPORT_PATH,
        COMPATIBILITY_PATH,
        OPTION_B_PATH,
        SCHEMA_PATH,
        SOURCE_REGISTER_PATH,
        METHODOLOGY_PATH,
        INTEGRATION_OPTIONS_PATH,
    ]
    missing = [str(path) for path in required_paths if not path.is_file()]
    if missing:
        raise RwandaAuditError(
            "Required audit output(s) missing: " + ", ".join(missing)
        )
    parsed_inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    parsed_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if parsed_inventory["expected_file_count"] != 4:
        raise RwandaAuditError("Inventory JSON does not record four files")
    if not parsed_schema["unsupported_fields_are_omitted"]:
        raise RwandaAuditError("Common schema did not omit unsupported fields")
    for path in (
        VARIABLE_DICTIONARY_PATH,
        TARGET_MATRIX_PATH,
        QUALITY_PATH,
        COMPATIBILITY_PATH,
    ):
        parsed = pd.read_csv(path)
        if parsed.empty:
            raise RwandaAuditError(f"Generated CSV is empty: {path}")
    audit_text = AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    missing_headings = [
        heading for heading in REQUIRED_AUDIT_HEADINGS if heading not in audit_text
    ]
    if missing_headings:
        raise RwandaAuditError(
            "Audit report headings missing: " + ", ".join(missing_headings)
        )
    if len(document.tables) != 1 or len(document.tables[0]) != 11:
        raise RwandaAuditError("DOCX table extraction result changed")
    if len(inventory["files"]) != 4:
        raise RwandaAuditError("File inventory count changed")


def _assert_audit_only_source() -> None:
    source_files = [
        Path(__file__),
        Path(__file__).with_name("rwanda_audit.py"),
        Path(__file__).with_name("office_reader.py"),
    ]
    prohibited_import_roots = {"sklearn", "joblib"}
    prohibited_call_names = {
        "fit",
        "fit_predict",
        "predict",
        "predict_proba",
        "train_test_split",
        "cross_validate",
        "cross_val_score",
        "cross_val_predict",
    }
    for path in source_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        prohibited: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in prohibited_import_roots:
                        prohibited.append(f"import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".", 1)[0]
                if root in prohibited_import_roots:
                    prohibited.append(f"import:{node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                else:
                    continue
                if call_name in prohibited_call_names:
                    prohibited.append(f"call:{call_name}@{node.lineno}")
        if prohibited:
            raise RwandaAuditError(
                f"Training/prediction operation in audit source {path}: "
                f"{sorted(set(prohibited))}"
            )


def run_audit() -> dict[str, Any]:
    """Run the ordered audit, write reports, and verify protected state."""

    _assert_audit_only_source()
    files = discover_rwanda_files()
    raw_before = {name: sha256_file(path) for name, path in files.items()}
    for filename, expected_hash in EXPECTED_SHA256.items():
        if raw_before[filename] != expected_hash:
            raise RwandaAuditError(
                f"Source checksum changed for {filename}: {raw_before[filename]}"
            )
    protected_before = _protected_snapshot()

    # Required semantic audit order.
    metadata_workbook = read_xlsx(files[METADATA_FILENAME])
    definitions = parse_metadata_definitions(metadata_workbook)
    cow_workbook = read_xlsx(files[COW_FILENAME])
    cow_sheet = cow_workbook.sheets[0]
    cow_frame = dataframe_from_sheet(cow_sheet, header_row=11)
    fodder_workbook = read_xlsx(files[FODDER_FILENAME])
    fodder_sheet = next(
        sheet for sheet in fodder_workbook.sheets if sheet.name == "Composites feeds"
    )
    fodder_frame = dataframe_from_sheet(fodder_sheet, header_row=11)
    document = read_docx(files[BUCKET_FILENAME])

    if len(cow_frame) != 96:
        raise RwandaAuditError(f"Expected 96 cow rows, found {len(cow_frame)}")
    if len(fodder_frame) != 97:
        raise RwandaAuditError(
            f"Expected 97 fodder rows, found {len(fodder_frame)}"
        )

    cow_profiles = _column_profiles(cow_frame)
    repeated = detect_repeated_cows(cow_frame, None)
    feature_register = candidate_feature_register(cow_frame, cow_profiles)
    join_audit = analyze_join(
        cow_frame,
        fodder_frame,
        left_key="LabN°",
        right_key="Lab N°",
    )
    ingredient_summary = _ingredient_summary(fodder_frame)
    feed_component_register = _feed_component_register(
        fodder_frame, join_audit
    )
    formula_audit = _formula_audit(cow_sheet)
    quality_issues = [
        *cow_quality_issues(cow_frame),
        *formula_consistency_issues(cow_frame),
        *fodder_quality_issues(fodder_frame),
    ]
    quality_issues.sort(
        key=lambda item: (
            item["file"],
            str(item["sheet"]),
            str(item["row_number"]),
            item["column"],
            item["issue_type"],
        )
    )
    inventory = build_inventory(
        files,
        {
            METADATA_FILENAME: metadata_workbook,
            COW_FILENAME: cow_workbook,
            FODDER_FILENAME: fodder_workbook,
        },
        document,
    )

    write_json(INVENTORY_PATH, inventory)
    write_csv(
        VARIABLE_DICTIONARY_PATH,
        [item.to_dict() for item in definitions],
    )
    write_csv(TARGET_MATRIX_PATH, target_matrix())
    write_csv(QUALITY_PATH, quality_issues)
    write_csv(
        COMPATIBILITY_PATH,
        farmlite_compatibility(cow_profiles),
    )
    write_json(SCHEMA_PATH, common_schema())
    _write_text(
        AUDIT_REPORT_PATH,
        _render_audit_report(
            inventory=inventory,
            metadata_workbook=metadata_workbook,
            definitions=definitions,
            cow_frame=cow_frame,
            cow_profiles=cow_profiles,
            repeated=repeated,
            feature_register=feature_register,
            fodder_frame=fodder_frame,
            ingredient_summary=ingredient_summary,
            document=document,
            join_audit=join_audit,
            quality_issues=quality_issues,
            formula_audit=formula_audit,
        ),
    )
    _write_text(JOIN_REPORT_PATH, _render_join_report(join_audit))
    _write_text(OPTION_B_PATH, _render_option_b_report())
    _write_text(SOURCE_REGISTER_PATH, _render_source_register(inventory))
    _write_text(METHODOLOGY_PATH, _render_methodology())
    _write_text(INTEGRATION_OPTIONS_PATH, _render_integration_options())

    _validate_outputs(inventory, document)

    raw_after = {name: sha256_file(path) for name, path in files.items()}
    protected_after = _protected_snapshot()
    if raw_before != raw_after:
        raise RwandaAuditError("At least one Rwanda raw source changed")
    if protected_before != protected_after:
        raise RwandaAuditError("At least one protected project file changed")
    if protected_before["processed_files"] != protected_after["processed_files"]:
        raise RwandaAuditError("A processed dataset was generated")

    return {
        "audit_version": AUDIT_VERSION,
        "status": "PASSED_AUDIT_ONLY",
        "raw_hashes_before": raw_before,
        "raw_hashes_after": raw_after,
        "raw_files_unchanged": raw_before == raw_after,
        "protected_files_unchanged": protected_before == protected_after,
        "model_training_occurred": False,
        "prediction_occurred": False,
        "processed_dataset_generated": False,
        "permanent_join_created": False,
        "unsupported_unit_conversion_occurred": False,
        "fake_recommendation_label_created": False,
        "metadata_definition_count": len(definitions),
        "cow_row_count": len(cow_frame),
        "source_reported_unique_cows": 96,
        "workbook_verifiable_unique_cows": None,
        "source_reported_farm_count": 96,
        "workbook_verifiable_farm_count": None,
        "observation_structure": "CROSS_SECTIONAL_ONE_REPORTED_COW_PER_FARM",
        "repeated_cow_status": repeated,
        "fodder_row_count": len(fodder_frame),
        "docx_table_count": len(document.tables),
        "docx_table_rows": len(document.tables[0]),
        "quality_issue_count": len(quality_issues),
        "quality_issue_severity_counts": dict(
            Counter(item["severity"] for item in quality_issues)
        ),
        "join_audit": join_audit,
        "ingredient_summary": ingredient_summary,
        "feed_component_register_row_count": len(feed_component_register),
        "option_b_decision": "PARTIAL_OPTION_B_SUPPORT",
        "files_created": [
            str(path.relative_to(PROJECT_ROOT))
            for path in (
                INVENTORY_PATH,
                AUDIT_REPORT_PATH,
                VARIABLE_DICTIONARY_PATH,
                TARGET_MATRIX_PATH,
                QUALITY_PATH,
                JOIN_REPORT_PATH,
                COMPATIBILITY_PATH,
                OPTION_B_PATH,
                SCHEMA_PATH,
                SOURCE_REGISTER_PATH,
                METHODOLOGY_PATH,
                INTEGRATION_OPTIONS_PATH,
            )
        ],
    }


def main() -> int:
    try:
        result = run_audit()
    except Exception as error:
        print(
            f"RWANDA_AUDIT_FAILED: {type(error).__name__}: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    print(
        "RWANDA_AUDIT_PASSED "
        f"cow_rows={result['cow_row_count']} "
        f"fodder_rows={result['fodder_row_count']} "
        f"quality_issues={result['quality_issue_count']} "
        f"decision={result['option_b_decision']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
