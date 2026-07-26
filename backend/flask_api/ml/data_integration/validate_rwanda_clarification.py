"""Generate and validate the Phase 4.5B Rwanda clarification package.

Run from ``backend/flask_api``:

    venv\\Scripts\\python.exe -m ml.data_integration.validate_rwanda_clarification

This module performs read-only comparisons. It does not create cleaned data,
fit models, make predictions, or alter any supplied Rwanda workbook.
"""

from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import FLASK_API_DIR, PROJECT_ROOT
from ml.data_integration.office_reader import read_xlsx
from ml.data_integration.rwanda_audit import (
    COW_FILENAME,
    EXPECTED_FILENAMES,
    EXPECTED_SHA256,
    REPORT_DIR,
    SCHEMA_PATH,
    SOURCE_DIR,
    RwandaAuditError,
    dataframe_from_sheet,
    discover_rwanda_files,
    sha256_file,
    write_csv,
)
from ml.data_integration.rwanda_formula_audit import (
    age_column_analysis,
    audit_all_formulas,
    negative_leftover_analysis,
)
from ml.data_integration.validate_rwanda_dataset import _protected_snapshot


DATASET_URL = "https://data.mendeley.com/datasets/6jf28ftxrr/1"
ARTICLE_URL = (
    "https://www.sciencedirect.com/science/article/pii/S2772694025000068"
)

FORMULA_CSV_PATH = REPORT_DIR / "rwanda_formula_reconstruction.csv"
FORMULA_REPORT_PATH = REPORT_DIR / "rwanda_formula_audit.md"
NEGATIVE_REPORT_PATH = REPORT_DIR / "rwanda_negative_leftover_analysis.md"
AGE_REPORT_PATH = REPORT_DIR / "rwanda_age_column_analysis.md"
TARGET_REPAIR_PATH = REPORT_DIR / "rwanda_target_repair_matrix.csv"
OPTION_B_PATH = REPORT_DIR / "rwanda_option_b_support_report.md"

EVIDENCE_REGISTER_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_clarification_evidence_register.md"
)
IDENTIFIER_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_identifier_requirements.md"
)
WATER_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_water_target_definition.md"
)
MILK_PATH = PROJECT_ROOT / "documentation" / "rwanda_milk_target_definition.md"
NUTRIENT_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_nutrient_rule_assessment.md"
)
FODDER_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_fodder_sample_limitations.md"
)
CLEANING_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_interim_cleaning_specification.md"
)
SMALL_DATA_PATH = (
    PROJECT_ROOT
    / "documentation"
    / "rwanda_small_dataset_model_design_options.md"
)
TRAINING_GATE_PATH = (
    PROJECT_ROOT / "documentation" / "rwanda_model_design_approval_gate.md"
)
AUTHOR_QUESTIONS_PATH = (
    PROJECT_ROOT / "notes" / "rwanda_dataset_author_questions.md"
)
AUTHOR_EMAIL_PATH = (
    PROJECT_ROOT / "notes" / "rwanda_dataset_author_email_draft.md"
)

PRIOR_REPORTS = (
    REPORT_DIR / "rwanda_dataset_inventory.json",
    REPORT_DIR / "rwanda_dataset_audit.md",
    REPORT_DIR / "rwanda_variable_dictionary.csv",
    REPORT_DIR / "rwanda_target_matrix.csv",
    REPORT_DIR / "rwanda_data_quality_issues.csv",
    REPORT_DIR / "rwanda_cross_file_join_report.md",
    REPORT_DIR / "rwanda_farmlite_compatibility.csv",
    OPTION_B_PATH,
    SCHEMA_PATH,
)

SYNTHETIC_SOURCE_HASHES = {
    "datasets/raw/global_cattle_disease_detection_dataset.csv": (
        "4CEDFA77234FE45B441E303FF051C33123969E37C3B484A03387094A613DC4B9"
    ),
    "datasets/raw/global_cattle_milk_yield_prediction_dataset.csv": (
        "26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3"
    ),
}

REQUIRED_OUTPUTS = (
    FORMULA_CSV_PATH,
    FORMULA_REPORT_PATH,
    NEGATIVE_REPORT_PATH,
    AGE_REPORT_PATH,
    TARGET_REPAIR_PATH,
    EVIDENCE_REGISTER_PATH,
    IDENTIFIER_PATH,
    WATER_PATH,
    MILK_PATH,
    NUTRIENT_PATH,
    FODDER_PATH,
    CLEANING_PATH,
    SMALL_DATA_PATH,
    TRAINING_GATE_PATH,
    AUTHOR_QUESTIONS_PATH,
    AUTHOR_EMAIL_PATH,
    OPTION_B_PATH,
)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _escape(value: Any) -> str:
    if value is None:
        return "UNCLEAR"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _format(value: Any, digits: int = 6) -> str:
    if value is None:
        return "UNCLEAR"
    if isinstance(value, float):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def _load_prior_reports() -> dict[str, Any]:
    missing = [str(path) for path in PRIOR_REPORTS if not path.is_file()]
    if missing:
        raise RwandaAuditError(
            "Required Phase 4.5A report(s) missing: " + ", ".join(missing)
        )
    inventory = json.loads(PRIOR_REPORTS[0].read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    csv_shapes = {
        path.name: pd.read_csv(path).shape
        for path in PRIOR_REPORTS
        if path.suffix == ".csv"
    }
    if inventory.get("expected_file_count") != 4:
        raise RwandaAuditError("Phase 4.5A inventory no longer reports four files")
    if not schema.get("unsupported_fields_are_omitted"):
        raise RwandaAuditError("Phase 4.5A schema no longer fails closed")
    if "PARTIAL_OPTION_B_SUPPORT" not in OPTION_B_PATH.read_text(
        encoding="utf-8"
    ):
        raise RwandaAuditError("Prior Option B decision is unavailable")
    return {
        "inventory": inventory,
        "schema": schema,
        "csv_shapes": csv_shapes,
    }


def _synthetic_hashes() -> dict[str, str]:
    return {
        relative: sha256_file(PROJECT_ROOT / relative)
        for relative in SYNTHETIC_SOURCE_HASHES
    }


def _prior_report_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(PROJECT_ROOT)): sha256_file(path)
        for path in PRIOR_REPORTS
        if path != OPTION_B_PATH
    }


def _evidence_rows() -> list[dict[str, str]]:
    cow = COW_FILENAME
    return [
        {
            "issue_id": "RW-DMI-001",
            "file": cow,
            "location": "Raw data",
            "field": "DMIcapacity (kgDM)",
            "metadata": "120/NDF × BW/100; described as intake capacity",
            "observed": (
                "All 96 stored values equal DM served - leftover; the NDF/BW "
                "equation matches 69 within tolerance and conflicts in 27."
            ),
            "conflict": "One field has documented intake and capacity meanings.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-DMI-002",
            "file": cow,
            "location": "Raw data",
            "field": "DMIR kg",
            "metadata": "Dry-matter intake requirement (kg).",
            "observed": (
                "All 96 values equal 3.5% of body weight; repository text prints "
                "DMIR=BW×3.5."
            ),
            "conflict": (
                "Requirement is model-derived and must not be treated as "
                "observed intake; printed scaling needs confirmation."
            ),
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-DMI-003",
            "file": cow,
            "location": "Raw data",
            "field": "leftover",
            "metadata": "Leftovers (kg DM), reportedly weighed next morning.",
            "observed": "28/96 values are negative.",
            "conflict": (
                "Signed values cannot be ordinary positive refused feed without "
                "making calculated intake exceed served DM."
            ),
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-ID-001",
            "file": cow,
            "location": "Raw data",
            "field": "cow_id",
            "metadata": "No definition supplied.",
            "observed": "No cow identifier column exists.",
            "conflict": "Unique cows and grouping cannot be verified.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-ID-002",
            "file": cow,
            "location": "Raw data",
            "field": "farm_id",
            "metadata": "No definition supplied.",
            "observed": "No farm identifier column exists.",
            "conflict": "The reported 96 farms cannot be audited row by row.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-ID-003",
            "file": cow,
            "location": "Raw data",
            "field": "Repeated observations",
            "metadata": "Repository describes cross-sectional collection.",
            "observed": "No cow ID, farm ID, visit ID, or date is supplied.",
            "conflict": "Row independence remains unprovable.",
            "confidence": "UNKNOWN",
        },
        {
            "issue_id": "RW-AGE-001",
            "file": cow,
            "location": "Raw data",
            "field": "cowageinyears",
            "metadata": "Cow age in years.",
            "observed": "64 numeric, 30 breed-text, and 2 missing values.",
            "conflict": "No alternative age field permits deterministic repair.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-WATER-001",
            "file": cow,
            "location": "Raw data",
            "field": "waterday",
            "metadata": "Calls water consumed per day using jerry cans provided.",
            "observed": (
                "Repository methods and gap formula explicitly use water "
                "provided; no remaining/refused water field exists."
            ),
            "conflict": "Provided water is not verified consumed water.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-WATER-002",
            "file": cow,
            "location": "Raw data",
            "field": "waterrequi.",
            "metadata": "12.3 + 2.15×DMIR + 0.73×potential milk.",
            "observed": "66/89 stored values match within tolerance; 23 mismatch.",
            "conflict": "Seven stored values are missing despite available inputs.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-WATER-003",
            "file": cow,
            "location": "Raw data",
            "field": "gapwater",
            "metadata": "Water required - waterday.",
            "observed": "88/89 comparable rows match; source row 77 mismatches.",
            "conflict": "One material stored formula inconsistency.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-NDF-001",
            "file": cow,
            "location": "Raw data",
            "field": "NDF feeds",
            "metadata": "Metadata states kg DM.",
            "observed": (
                "Values range 26.77-77.98; repository/article report mean "
                "58.5% NDF."
            ),
            "conflict": "Metadata unit conflicts with percentage evidence.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-CP-001",
            "file": cow,
            "location": "Raw data",
            "field": "Cpintakeingr",
            "metadata": "CP in feeds × DMI.",
            "observed": "All 87 comparable rows reproduce within tolerance.",
            "conflict": "Intake inherits unresolved DMIcapacity semantics.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-CP-002",
            "file": cow,
            "location": "Raw data",
            "field": "CPmaint; CPmilk; TotalreqCP",
            "metadata": "6.27×MW; 82×potential milk; sum of both.",
            "observed": "CPmilk conflicts with its documented formula in 22 rows.",
            "conflict": "Stored total is internally consistent with stored inputs.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-CP-003",
            "file": cow,
            "location": "Raw data",
            "field": "gapCP",
            "metadata": "Total CP requirement minus maintenance CP.",
            "observed": (
                "Stored values match total CP requirement minus current CP "
                "intake in all 87 comparable rows."
            ),
            "conflict": "Workbook metadata contradicts repository and values.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-ME-001",
            "file": cow,
            "location": "Raw data",
            "field": "MEfeeds",
            "metadata": "2.2 + 0.136G24 + 0.057CP + 0.0029CP².",
            "observed": "78 stored values; no G24 column.",
            "conflict": "Cannot independently reconstruct composition.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-ME-002",
            "file": cow,
            "location": "Raw data",
            "field": "G24",
            "metadata": "Gas volume after 24 hours.",
            "observed": "Required input is absent from every supplied file.",
            "conflict": "MEfeeds reproduction is blocked.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-ME-003",
            "file": cow,
            "location": "Raw data",
            "field": "ME maintenance/milk/total requirement",
            "metadata": "0.589×MW; 5.023×potential milk; sum.",
            "observed": (
                "Maintenance arithmetic matches stored rows; milk requirement "
                "mismatches 20 comparable rows and 16 stored rows are missing."
            ),
            "conflict": "Stored requirement chain is only partially reproducible.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-JOIN-001",
            "file": "Cow and fodder workbooks",
            "location": "Raw data / Composites feeds",
            "field": "LabN° / Lab N°",
            "metadata": "Composite laboratory/sample identifier.",
            "observed": "Cow side has 90 unique keys; fodder side has 97.",
            "conflict": "Sample sharing semantics are not documented.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-JOIN-002",
            "file": cow,
            "location": "Raw data",
            "field": "LabN°",
            "metadata": "Composite sample key, not cow ID.",
            "observed": "Six duplicate occurrences across three repeated keys.",
            "conflict": "Could mean shared diet, duplicated animal, or repeat sample.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-JOIN-003",
            "file": "Different fodders components in the samples.xlsx",
            "location": "Composites feeds",
            "field": "Lab N°",
            "metadata": "Composite sample identifier.",
            "observed": "Seven keys have no cow-workbook row.",
            "conflict": "Reason for unlinked samples is undocumented.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-FEED-001",
            "file": "Fodder workbook and bucket plan",
            "location": "Composites feeds / Table 1",
            "field": "SAMPLE ID / bucket plan",
            "metadata": "Observed fodders and farmer-followed calf practice.",
            "observed": "No expert or optimized ration outcome exists.",
            "conflict": "Observed diets cannot be recommendation labels.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-FEED-002",
            "file": "Different fodders components in the samples.xlsx",
            "location": "Composites feeds",
            "field": "SAMPLE ID",
            "metadata": "Ingredient-list text.",
            "observed": "No ingredient weights, proportions, or inclusion rates.",
            "conflict": "Ration composition and feed quantities cannot be rebuilt.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-MILK-001",
            "file": cow,
            "location": "Raw data",
            "field": "hand-milked yield / Total milk performance",
            "metadata": "Measured hand milk versus hand milk plus assumed calf milk.",
            "observed": "Both fields have 96 values and different provenance.",
            "conflict": "Calculated total must not be relabelled directly measured.",
            "confidence": "HIGH",
        },
        {
            "issue_id": "RW-MILK-002",
            "file": cow,
            "location": "Raw data",
            "field": "Ass.calfmilk",
            "metadata": "Age-band allocation of 6/4/2/1/0 L.",
            "observed": "All stored values reproduce from daysinmilk bands.",
            "conflict": "Calf consumption is estimated rather than measured.",
            "confidence": "HIGH",
        },
    ]


def _render_evidence_register(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Rwanda Clarification Evidence Register",
        "",
        (
            "This register distinguishes observed conflicts from unresolved "
            "interpretations. No source value was corrected."
        ),
        "",
        "| Issue ID | File | Sheet/table | Column/field | Metadata definition | "
        "Observed data evidence | Conflict | Confidence |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape(row[key])
                for key in (
                    "issue_id",
                    "file",
                    "location",
                    "field",
                    "metadata",
                    "observed",
                    "conflict",
                    "confidence",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## External Evidence",
            "",
            f"- Repository reproduction notes: {DATASET_URL}",
            f"- Related research article: {ARTICLE_URL}",
            (
                "- The repository clarifies formulas and water-provided "
                "wording but does not resolve record identity or source-cell "
                "conflicts."
            ),
        ]
    )
    return "\n".join(lines)


def _render_formula_report(records: list[dict[str, Any]]) -> str:
    counts = Counter(item["status"] for item in records)
    lines = [
        "# Rwanda Formula Reconstruction Audit",
        "",
        "## Scope and Method",
        "",
        (
            "Stored values were compared in memory with every documented "
            "formula and with explicitly labelled alternative interpretations. "
            "Exact tolerance is 1e-9; rounding tolerance is 0.01. No result "
            "replaced a source value."
        ),
        "",
        "## Status Summary",
        "",
        "| Status | Formula interpretations |",
        "|---|---:|",
    ]
    for status in (
        "FULLY_REPRODUCIBLE",
        "REPRODUCIBLE_WITH_TOLERANCE",
        "PARTIALLY_REPRODUCIBLE",
        "NOT_REPRODUCIBLE_MISSING_INPUT",
        "NOT_REPRODUCIBLE_CONFLICT",
        "FORMULA_NOT_DOCUMENTED",
        "UNCLEAR",
    ):
        lines.append(f"| `{status}` | {counts.get(status, 0)} |")
    lines.extend(
        [
            "",
            "## Formula Results",
            "",
            "| ID | Domain | Target | Formula | Exact | Tolerance | Mismatch | "
            "Missing inputs | Stored missing | Status | Ambiguous |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for item in records:
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{item['formula_id']}`",
                    item["domain"],
                    f"`{item['target_field']}`",
                    _escape(item["documented_formula"]),
                    str(item["exact_match_count"]),
                    str(item["tolerance_match_count"]),
                    str(item["mismatch_count"]),
                    str(item["missing_input_row_count"]),
                    str(item["stored_missing_with_inputs_count"]),
                    f"`{item['status']}`",
                    item["ambiguity"],
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Key Conflicts",
            "",
            (
                "- `DMIcapacity (kgDM)`: served-minus-leftover reproduces all "
                "96 stored values; the documented NDF/body-weight capacity "
                "equation is only partial. Neither arithmetic result proves "
                "actual consumed DMI."
            ),
            (
                "- `waterrequi.`: the documented equation matches 66 of 89 "
                "stored values within tolerance, conflicts in 23, and has "
                "seven source blanks despite available inputs."
            ),
            (
                "- `gapwater`: 88 of 89 comparable values match; source row "
                "77 is materially inconsistent."
            ),
            (
                "- `CPmilk` and `5.023*peakMilk`: stored source subsets do not "
                "use the current row's potential-milk value."
            ),
            (
                "- `gapCP`: the repository formula reproduces stored values; "
                "the workbook metadata alternative conflicts in all rows."
            ),
            (
                "- `MEfeeds`: G24 is absent, so the composition equation is "
                "not independently reproducible."
            ),
            "",
            "## Decision",
            "",
            (
                "`WAITING_FOR_DATA_CLARIFICATION`. Reproducible arithmetic is "
                "not automatically a measured target or approved rule."
            ),
        ]
    )
    return "\n".join(lines)


def _render_negative_report(analysis: dict[str, Any]) -> str:
    lines = [
        "# Rwanda Negative Leftover Analysis",
        "",
        "## Finding",
        "",
        (
            f"Exactly {analysis['negative_row_count']} source rows contain a "
            "negative `leftover`. Values were analysed as stored and were not "
            "corrected."
        ),
        "",
        "## Affected Rows",
        "",
        "| Source row | Lab/sample | DM served | Leftover | DMfeeds | "
        "Stored DMIcapacity | Hand milk | Total milk | Weight | Stage | "
        "Served - leftover | Served + leftover | NDF capacity |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in analysis["records"]:
        lines.append(
            "| "
            + " | ".join(
                _format(row[key])
                for key in (
                    "source_row_number",
                    "sample_id",
                    "dm_served",
                    "leftover",
                    "dmfeeds",
                    "stored_dmi_capacity",
                    "hand_milked_yield",
                    "total_milk_performance",
                    "weight_kg",
                    "lactation_stage",
                    "served_minus_leftover",
                    "served_plus_leftover",
                    "ndf_capacity",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Alternative Interpretations",
            "",
            "| ID | Interpretation | Candidate calculation | Stored matches | "
            "Physical conflicts | Assessment | Selected |",
            "|---|---|---|---:|---:|---|---|",
        ]
    )
    for item in analysis["interpretations"]:
        lines.append(
            "| "
            + " | ".join(
                (
                    item["interpretation_id"],
                    item["interpretation"],
                    item["candidate_calculation"],
                    _format(item["stored_dmi_capacity_matches"]),
                    _format(item["physical_conflict_count"]),
                    item["assessment"],
                    "NO",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"Final status: `{analysis['status']}`.",
            "",
            (
                "Interpretations A-E remain separate. Arithmetic consistency "
                "does not establish collection meaning, actual consumption, "
                "or whether extra feed was supplied."
            ),
        ]
    )
    return "\n".join(lines)


def _render_age_report(analysis: dict[str, Any]) -> str:
    entries = "; ".join(f"`{item}`" for item in analysis["unique_text_entries"])
    return f"""# Rwanda Age Column Analysis

## Counts

- Cow rows: {analysis['row_count']}
- Numeric ages: {analysis['numeric_age_count']}
- Breed-text entries: {analysis['breed_text_count']}
- Missing entries: {analysis['missing_age_count']}
- Unique text entries: {analysis['unique_text_count']}

## Text Entries

{entries}

## Repair Investigation

- Other age column: `{'NONE' if not analysis['other_age_columns'] else '; '.join(analysis['other_age_columns'])}`
- Displaced age values found elsewhere: `NO`
- Broad row-shift evidence: `{analysis['row_shift_evidence']}`
- Exact duplicates of the existing `cowbreed` categories: `{'YES' if analysis['exactly_duplicates_cowbreed_values'] else 'NO'}`
- Existing `cowbreed` values: `{'; '.join(analysis['cowbreed_values'])}`
- Deterministic repair possible: `NO`
- Values modified: `NO`

The contaminated entries are more detailed cross-breed descriptions than the
broad `Cross/exotic` field. No evidence-supported numeric age can be recovered
from another supplied column.

## Result

Final status: `{analysis['status']}`.
"""


def _target_repair_rows() -> list[dict[str, str]]:
    return [
        {
            "target": "Measured daily milk",
            "current_source_field": "hand-milked yield",
            "current_status": "VERIFIED_MEASURED_MILK_L_COW_DAY",
            "required_clarification": (
                "Confirm all daily milkings and row/cow independence."
            ),
            "possible_repair": "None to target; supply IDs and collection detail.",
            "training_decision": "READY_WITH_LIMITATIONS",
        },
        {
            "target": "Total milk performance",
            "current_source_field": "Total milk performance",
            "current_status": "CALCULATED_TOTAL_MILK_L_COW_DAY",
            "required_clarification": (
                "Confirm whether estimated calf allocation is required."
            ),
            "possible_repair": (
                "Keep measured and calculated targets separate with provenance."
            ),
            "training_decision": "WAITING_FOR_AUTHOR_RESPONSE",
        },
        {
            "target": "Water provided/consumed",
            "current_source_field": "waterday",
            "current_status": "VERIFIED_WATER_PROVIDED_L_COW_DAY",
            "required_clarification": (
                "Confirm no remaining water was measured and scope is per cow."
            ),
            "possible_repair": (
                "Canonicalize only as water_provided_l_cow_day after approval."
            ),
            "training_decision": "WAITING_FOR_AUTHOR_RESPONSE",
        },
        {
            "target": "DMI",
            "current_source_field": "DMIcapacity (kgDM)",
            "current_status": "BLOCKED_UNCLEAR_DEFINITION",
            "required_clarification": (
                "Resolve capacity versus intake and 28 signed leftovers."
            ),
            "possible_repair": (
                "Preserve source and add approved recalculation separately."
            ),
            "training_decision": "WAITING_FOR_CORRECTED_DATA",
        },
        {
            "target": "CP intake",
            "current_source_field": "Cpintakeingr",
            "current_status": "CALCULATED_INTAKE_DMI_DEPENDENT",
            "required_clarification": "Resolve DMI basis and confirm CP units.",
            "possible_repair": "Transparent rule calculation with audit columns.",
            "training_decision": "RULE_ENGINE_ONLY",
        },
        {
            "target": "CP requirement",
            "current_source_field": "TotalreqCP",
            "current_status": "MODEL_DERIVED_REQUIREMENT",
            "required_clarification": (
                "Confirm guideline and 22 inconsistent CPmilk values."
            ),
            "possible_repair": "Recalculate beside source after approval.",
            "training_decision": "RULE_ENGINE_ONLY",
        },
        {
            "target": "CP gap",
            "current_source_field": "gapCP",
            "current_status": "METADATA_FORMULA_CONFLICT",
            "required_clarification": "Approve repository formula over metadata.",
            "possible_repair": "Keep source plus separately versioned rule output.",
            "training_decision": "WAITING_FOR_AUTHOR_RESPONSE",
        },
        {
            "target": "ME intake",
            "current_source_field": "MEIntake",
            "current_status": "CALCULATED_INTAKE_DMI_DEPENDENT",
            "required_clarification": "Resolve DMI and supply G24/ME provenance.",
            "possible_repair": "Rule calculation after inputs are verified.",
            "training_decision": "RULE_ENGINE_ONLY",
        },
        {
            "target": "ME requirement",
            "current_source_field": "MEmaint+peakmilk",
            "current_status": "PARTIALLY_REPRODUCIBLE_REQUIREMENT",
            "required_clarification": (
                "Resolve 20 ME-milk mismatches and 16 missing source rows."
            ),
            "possible_repair": "Recalculate beside source after approval.",
            "training_decision": "WAITING_FOR_CORRECTED_DATA",
        },
        {
            "target": "ME gap",
            "current_source_field": "gapME",
            "current_status": "CALCULATED_GAP",
            "required_clarification": "Resolve upstream intake and requirement.",
            "possible_repair": "Transparent versioned rule after prerequisites.",
            "training_decision": "WAITING_FOR_CORRECTED_DATA",
        },
        {
            "target": "Feed/ration class",
            "current_source_field": "SAMPLE ID",
            "current_status": "OBSERVED_DIET_ONLY",
            "required_clarification": (
                "Obtain nutritionist-approved or optimized ration labels."
            ),
            "possible_repair": "No target repair from existing observed strings.",
            "training_decision": "EXPERT_LABELS_REQUIRED",
        },
    ]


def _render_identifier_requirements() -> str:
    return """# Rwanda Identifier and Grouping Requirements

## Required Future Identifiers

| Identifier | Why it is required | Current availability |
|---|---|---|
| `cow_id` | Detect repeated animals and prevent animal-level leakage. | `NOT_AVAILABLE` |
| `farm_id` | Group shared management, diet and environmental conditions. | `NOT_AVAILABLE` |
| observation/collection date | Establish temporal order, season and repeat visits. | `NOT_AVAILABLE` |
| sample identifier | Trace laboratory and composite-feed evidence. | `LabN°` / `Lab N°` |
| repeated-visit identifier | Distinguish visits when the same animal is sampled again. | `NOT_AVAILABLE` |

## Existing Field Assessment

| Existing field | Permitted role | Prohibited role |
|---|---|---|
| `LabN°` / `Lab N°` | Composite feed/laboratory sample identifier with limitations. | Cow or farm identifier without written confirmation. |
| `sites` | Lowland/highland site category only. | Farm, household or animal identifier. |
| source row number | Traceability within the supplied workbook. | Biological identity. |

The cow workbook contains 90 unique `LabN°` values for 96 rows. Three sample
numbers repeat, producing six duplicate occurrences. The fodder workbook has
97 unique sample keys, including seven without a cow-workbook match. These
patterns cannot establish whether samples are shared diets, duplicated animals,
or repeated collections.

## Consequences if IDs Remain Unavailable

- Row-level random splitting may leak repeated-animal or farm information.
- Grouped validation cannot be guaranteed.
- External-validity and performance claims must be limited.
- The study-reported 96 cows and 96 farms cannot be independently verified.
- Leave-one-out or repeated cross-validation is acceptable only after row
  independence is confirmed; neither method repairs hidden grouping.

## Specific Information Request

Please confirm whether each row is one distinct cow, whether each cow belongs
to a distinct farm, whether any cow appears more than once, whether `LabN°`
identifies a cow/farm/sample/composite feed, and whether the six duplicate
occurrences represent duplicated animals, shared diets, or repeated samples.

## Status

`WAITING_FOR_DATA_CLARIFICATION`
"""


def _render_water_definition(frame: pd.DataFrame) -> str:
    values = pd.to_numeric(frame["waterday"], errors="coerce")
    return f"""# Rwanda Water Target Definition

## Source Evidence

- Field: `waterday`
- Metadata wording: "Water consumed per day measured using the number of jeri
  cans of 20, 10 and 5 litres that a farmer provides to a cow per day."
- Repository method: water was recorded from graduated jerry cans provided to
  cows daily.
- Repository gap equation: water required per day minus water provided per day.
- Unit and period: L/cow/day.
- Usable values: {values.notna().sum()}/{len(frame)}
- Missing values: {values.isna().sum()}
- Range: {_format(float(values.min()))}-{_format(float(values.max()))} L/cow/day.
- Collection status: owner/farmer-reported container count.
- Direct metering of drinking: `NOT_VERIFIED`
- Remaining/refused water measured: `NOT_AVAILABLE`
- Household/herd aggregation: `UNCLEAR`; wording says per cow.

Repository evidence supports **provided water**, not verified physiological
consumption. The metadata's use of "consumed" conflicts with its own collection
description. No conversion or semantic relabelling was applied.

## Formula Relationships

- Requirement: `12.3 + 2.15 × DMIR + 0.73 × potential milk`.
- Gap: requirement minus `waterday`.
- Requirement reconstruction: 66/89 stored values match within tolerance,
  23 mismatch, and seven are missing despite available inputs.
- Gap reconstruction: 88/89 comparable values match; source row 77 conflicts.

## Provisional Status

`VERIFIED_WATER_PROVIDED_L_COW_DAY`

A water-consumption/intake regressor is not approved. A future model of
farmer-provided water would still require row independence and target-timing
confirmation.

Primary reproduction evidence: {DATASET_URL}
"""


def _render_milk_definition(frame: pd.DataFrame) -> str:
    hand = pd.to_numeric(frame["hand-milked yield"], errors="coerce")
    total = pd.to_numeric(frame["Total milk performance"], errors="coerce")
    return f"""# Rwanda Milk Target Definition

## A. Direct Hand-Milked Yield

| Attribute | Evidence |
|---|---|
| Source field | `hand-milked yield` |
| Definition | Milk measured with graduated 1, 2 and 5 L plastic jugs after each milking session. |
| Unit/period | L/cow/day, supported by repository reporting. |
| Directly measured | `YES` |
| Includes calf estimate | `NO` |
| Includes all daily milkings | `UNCLEAR`; "after each milking session" is documented, but completeness needs confirmation. |
| Usable/missing | {hand.notna().sum()} / {hand.isna().sum()} |
| Range | {_format(float(hand.min()))}-{_format(float(hand.max()))} L/cow/day |
| Target status | `VERIFIED_MEASURED_MILK_L_COW_DAY` |
| Design status | `READY_WITH_LIMITATIONS` |

## B. Total Milk Performance

| Attribute | Evidence |
|---|---|
| Source field | `Total milk performance` |
| Definition | `hand-milked yield + Ass.calfmilk` |
| Unit/period | L/cow/day |
| Directly measured | `NO` |
| Includes calf estimate | `YES`; age-band allocation of 6/4/2/1/0 L. |
| Usable/missing | {total.notna().sum()} / {total.isna().sum()} |
| Range | {_format(float(total.min()))}-{_format(float(total.max()))} L/cow/day |
| Target status | `CALCULATED_TOTAL_MILK_L_COW_DAY` |
| Design status | `BLOCKED` unless the research objective explicitly requires estimated calf milk. |

The two fields remain separate. The preferred future target is directly
measured hand-milked yield, subject to confirmation that it covers all daily
milkings and that the 96 rows are independent.
"""


def _render_nutrient_assessment(records: list[dict[str, Any]]) -> str:
    by_id = {item["formula_id"]: item for item in records}
    rows = [
        (
            "%Protein",
            "Laboratory composition",
            "percent of DM",
            "Kjeldahl method in repository",
            "%Protein",
            "YES for 87 rows",
            "READY_AFTER_UNIT_CLARIFICATION",
        ),
        (
            "Protein/content/gr/kg",
            "Calculated composition conversion",
            "g/kg DM",
            "%Protein × 10",
            "%Protein",
            by_id["RW-FORM-CP-001"]["status"],
            "READY_AFTER_UNIT_CLARIFICATION",
        ),
        (
            "Cpintakeingr",
            "Calculated intake",
            "g/cow/day",
            "CP g/kg × DMI",
            "CP composition; DMI",
            by_id["RW-FORM-CP-002"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "CPmaint=6.27*MW",
            "Model-derived requirement",
            "g/cow/day",
            "6.27 × MW",
            "body weight; metabolic weight",
            by_id["RW-FORM-CP-003"]["status"],
            "RESEARCH_REFERENCE_ONLY",
        ),
        (
            "CPmilk",
            "Model-derived requirement",
            "g/cow/day",
            "82 × potential milk",
            "potential milk",
            by_id["RW-FORM-CP-004"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "TotalreqCP",
            "Model-derived requirement",
            "g/cow/day",
            "maintenance CP + milk CP",
            "stored requirement components",
            by_id["RW-FORM-CP-005"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "gapCP",
            "Calculated gap",
            "g/cow/day",
            "total requirement - current CP intake",
            "requirement; intake",
            by_id["RW-FORM-CP-006A"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "MEfeeds",
            "Unreproducible calculated composition",
            "MJ/kg DM",
            "2.2 + 0.136G24 + 0.057CP + 0.0029CP²",
            "G24; CP",
            by_id["RW-FORM-ME-001"]["status"],
            "NOT_REPRODUCIBLE",
        ),
        (
            "MEIntake",
            "Calculated intake",
            "MJ/cow/day",
            "MEfeeds × DMI",
            "ME composition; DMI",
            by_id["RW-FORM-ME-002"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "MW*0.589=Energyformaintenance",
            "Model-derived requirement",
            "MJ/cow/day",
            "MW × 0.589",
            "body weight; MW",
            by_id["RW-FORM-ME-003"]["status"],
            "RESEARCH_REFERENCE_ONLY",
        ),
        (
            "5.023*peakMilk",
            "Model-derived requirement",
            "MJ/cow/day",
            "5.023 × potential milk",
            "potential milk",
            by_id["RW-FORM-ME-004"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "MEmaint+peakmilk",
            "Model-derived requirement",
            "MJ/cow/day",
            "maintenance ME + milk ME",
            "stored requirement components",
            by_id["RW-FORM-ME-005"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
        (
            "gapME",
            "Calculated gap",
            "MJ/cow/day",
            "total ME requirement - ME intake",
            "requirement; intake",
            by_id["RW-FORM-ME-006"]["status"],
            "READY_AFTER_FORMULA_CLARIFICATION",
        ),
    ]
    lines = [
        "# Rwanda Protein and Energy Rule Assessment",
        "",
        "## Field and Equation Register",
        "",
        "| Field | Classification | Unit | Formula/source | Required inputs | "
        "Reproducibility | Decision |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_escape(item) for item in row) + " |")
    lines.extend(
        [
            "",
            "## Equation Detail",
            "",
            "| Field | Formula | Source/citation | Required inputs | Available "
            "inputs | Unit | Reproducibility | Applicable to FarmLite | Safe "
            "for prototype rule use | Remaining limitation |",
            "|---|---|---|---|---|---|---|---|---|---|",
            (
                "| `%Protein` | Laboratory Kjeldahl result | AOAC method named "
                f"in repository ({DATASET_URL}) | Composite feed sample | "
                "Composite sample and 87 stored results | percent of DM | "
                "Laboratory source value; not recalculated | Potentially | "
                "Only after unit/sample linkage review | Nine missing values; "
                "not ingredient-specific |"
            ),
            (
                "| `Protein/content/gr/kg` | `%Protein × 10` | Workbook "
                "metadata/stored arithmetic | `%Protein` | 87 CP-percent "
                "values | g/kg DM | `PARTIALLY_REPRODUCIBLE` | Yes | Only "
                "after unit approval | Nine missing upstream values |"
            ),
            (
                "| `Cpintakeingr` | `CP g/kg × DMI` | Mendeley reproduction "
                f"notes ({DATASET_URL}) | CP composition; DMI | 87 comparable "
                "rows | g/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | "
                "NO currently | DMIcapacity semantics unresolved |"
            ),
            (
                "| `CPmaint=6.27*MW` | `6.27 × BW^0.75` | Van der Linden et "
                f"al. named in repository ({DATASET_URL}) | Body weight | "
                "96 body weights/MW values | g/cow/day | "
                "`REPRODUCIBLE_WITH_TOLERANCE` | Potentially | Only after "
                "guideline applicability review | Equation version and "
                "population applicability need confirmation |"
            ),
            (
                "| `CPmilk` | `82 × potential milk` | Van der Linden et al. "
                f"named in repository ({DATASET_URL}) | Potential milk | "
                "96 potential-milk values | g/cow/day | "
                "`PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | "
                "22 stored mismatches; potential milk is model-derived |"
            ),
            (
                "| `TotalreqCP` | `maintenance CP + milk CP` | Workbook "
                "metadata | Stored CP components | 96 stored components | "
                "g/cow/day | `REPRODUCIBLE_WITH_TOLERANCE` | Potentially | "
                "NO currently | Reproduces internally but inherits CPmilk "
                "conflicts |"
            ),
            (
                "| `gapCP` | `total CP requirement - current CP intake` | "
                f"Mendeley reproduction notes ({DATASET_URL}) | Requirement; "
                "intake | 87 comparable rows | g/cow/day | "
                "`PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | "
                "Metadata gives a conflicting formula |"
            ),
            (
                "| `%CP gap` | `gapCP × 100 / TotalreqCP` | Workbook metadata "
                "| CP gap; total requirement | 87 comparable rows | percent | "
                "`PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | "
                "Nine stored values missing; inherits upstream conflicts |"
            ),
            (
                "| `MEfeeds` | `2.2 + 0.136G24 + 0.057CP + 0.0029CP²` | "
                f"Groot and Oomen named in repository ({DATASET_URL}) | G24; "
                "CP | CP is partial; G24 absent | MJ/kg DM | "
                "`NOT_REPRODUCIBLE_MISSING_INPUT` | Potentially | NO | G24 "
                "and CP equation basis/version must be supplied |"
            ),
            (
                "| `MEIntake` | `MEfeeds × DMI` | Mendeley reproduction notes "
                f"({DATASET_URL}) | ME composition; DMI | 78 comparable rows | "
                "MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO "
                "currently | Inherits missing G24 and DMI ambiguity |"
            ),
            (
                "| `MW*0.589=Energyformaintenance` | `0.589 × BW^0.75` | Van "
                f"der Linden et al. named in repository ({DATASET_URL}) | "
                "Body weight/MW | Inputs available for 96 rows | MJ/cow/day | "
                "`PARTIALLY_REPRODUCIBLE` | Potentially | Only after guideline "
                "review | 16 stored outputs missing |"
            ),
            (
                "| `5.023*peakMilk` | `5.023 × potential milk` | Van der Linden "
                f"et al. named in repository ({DATASET_URL}) | Potential milk "
                "| Input available for 96 rows | MJ/cow/day | "
                "`PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | "
                "20 mismatches and 16 stored outputs missing |"
            ),
            (
                "| `MEmaint+peakmilk` | `maintenance ME + milk ME` | Workbook "
                "metadata | Stored requirement components | Components "
                "available together for 80 rows | MJ/cow/day | "
                "`PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | "
                "Inherits inconsistent/missing component values |"
            ),
            (
                "| `gapME` | `total ME requirement - ME intake` | Mendeley "
                f"reproduction notes ({DATASET_URL}) | Requirement; intake | "
                "78 comparable rows | MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | "
                "Potentially | NO currently | Inherits composition, DMI and "
                "requirement limitations |"
            ),
            (
                "| `%MEgap` | `gapME × 100 / total ME requirement` | Workbook "
                "metadata | ME gap; total requirement | 80 comparable rows | "
                "percent | `PARTIALLY_REPRODUCIBLE` | Potentially | NO "
                "currently | Inherits every upstream ME limitation |"
            ),
            "",
            "## Applicability to FarmLite",
            "",
            (
                "Deterministic equations should be implemented transparently "
                "as versioned rules rather than learned by a model only when "
                "their sources, units, inputs, and target-population "
                "applicability are approved."
            ),
            "",
            "- CP intake is blocked by DMI semantics.",
            "- CP requirements need equation provenance and correction of "
            "inconsistent `CPmilk` rows.",
            "- CP gap needs an explicit owner decision resolving metadata.",
            "- ME composition is not reproducible without G24.",
            "- ME intake inherits both ME composition and DMI limitations.",
            "- ME requirements need correction of inconsistent/missing rows.",
            "",
            "## Overall Decisions",
            "",
            "- CP: `READY_AFTER_FORMULA_CLARIFICATION`",
            "- ME: `NOT_REPRODUCIBLE` for composition; requirements are "
            "`READY_AFTER_FORMULA_CLARIFICATION`",
            "- Current use: `RESEARCH_REFERENCE_ONLY`; no production rule "
            "change is authorized.",
        ]
    )
    return "\n".join(lines)


def _render_fodder_limitations() -> str:
    return """# Rwanda Fodder Sample Limitations

## What the Workbook Contains

- 97 rows with unique `Lab N°` keys.
- One raw text field listing fodder ingredients in each composite sample.
- Seven sample keys without a matching cow-workbook row.
- Ingredient spelling, case, and repeated-token inconsistencies.

## What It Does Not Contain

- Ingredient weights, proportions, inclusion percentages or offered quantity.
- Ingredient-specific DM, CP, ME, NDF or mineral values.
- Validated roughage/concentrate categories.
- Farm IDs, cow IDs, dates or collection periods.
- Nutritionist-approved or optimized ration labels.

Ingredient strings can be tokenized for traceability only. Ingredient presence
does not establish amount, and a composite diet cannot be reconstructed without
proportions. Mineral-mix quantity, roughage percentage and concentrate
percentage therefore cannot be derived.

## Cross-File Nutrient Relationship

`Lab N°` can link ingredient-list text to composite nutrient values stored in
the cow workbook. This remains `POSSIBLE_WITH_LIMITATIONS`: all 96 cow rows
match a fodder key, but three cow-side keys repeat and sample-sharing semantics
are unknown. Nutrient values must not be created from ingredient names.

## Status

`PARTIALLY_COMPATIBLE` for observed composite-sample lookup only.
`NOT_COMPATIBLE` for ration reconstruction or recommendation labels.
"""


def _render_cleaning_specification() -> str:
    rows = [
        (
            "cowageinyears",
            "30 breed-text values; 2 missing",
            (
                "Preserve original. Set cleaned numeric value missing only "
                "after approval if corrected ages cannot be supplied."
            ),
            "Corrected workbook or author response",
            "YES",
            "MEDIUM",
            "YES",
        ),
        (
            "leftover",
            "28 negative values",
            "Preserve signed source value; do not transform.",
            "Author-defined sign and collection convention",
            "YES",
            "HIGH",
            "YES",
        ),
        (
            "LabN°",
            "Three repeated keys; six duplicate occurrences",
            (
                "Preserve. Add occurrence index only after record/sample "
                "meaning is confirmed."
            ),
            "Sample-sharing and row-identity clarification",
            "YES",
            "MEDIUM",
            "YES",
        ),
        (
            "DMIcapacity (kgDM)",
            "Conflicting capacity/intake formulas",
            (
                "Preserve source. Add separately named recalculated fields and "
                "formula-validation status only after approval."
            ),
            "Approved target definition and formula",
            "YES",
            "HIGH",
            "YES",
        ),
        (
            "waterday",
            "Consumed versus provided wording",
            (
                "Preserve source; provisional canonical mapping only to "
                "water_provided_l_cow_day."
            ),
            "Owner confirmation of collection scope",
            "YES",
            "MEDIUM",
            "YES",
        ),
        (
            "waterrequi.; gapwater",
            "Missing and inconsistent calculated values",
            (
                "Preserve source and add recalculated value plus validation "
                "status separately."
            ),
            "Formula approval and corrected rows",
            "YES",
            "LOW",
            "YES",
        ),
        (
            "NDF feeds",
            "Unit conflict",
            "Do not convert or rename until unit is approved.",
            "Author/data dictionary confirmation",
            "YES",
            "HIGH",
            "YES",
        ),
        (
            "CPmilk; gapCP",
            "Formula mismatches and metadata contradiction",
            "Preserve source; version any future recalculation.",
            "Approved CP equations and corrected values",
            "YES",
            "MEDIUM",
            "YES",
        ),
        (
            "MEfeeds; ME requirement fields",
            "Missing G24 plus inconsistent/missing calculated values",
            "Preserve source; do not impute or recompute as final.",
            "G24 data, formula provenance and corrected workbook",
            "YES",
            "HIGH",
            "YES",
        ),
        (
            "SAMPLE ID",
            "Raw ingredient spelling and no quantities",
            (
                "Preserve text. Create expert-reviewed vocabulary only in a "
                "later approved phase."
            ),
            "Expert mapping and ingredient quantities",
            "YES",
            "MEDIUM",
            "YES",
        ),
    ]
    lines = [
        "# Rwanda Interim Data-Cleaning Specification",
        "",
        (
            "This is a proposal only. No cleaned dataset, corrected cell, "
            "imputed value, normalized label, or processed Rwanda file was "
            "created."
        ),
        "",
        "| Field | Issue | Proposed action | Evidence required | Reversible | "
        "Data-loss risk | Approval required |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_escape(item) for item in row) + " |")
    lines.extend(
        [
            "",
            "## Required Future Audit Columns",
            "",
            "- `source_file`",
            "- `source_sheet`",
            "- `source_row_number`",
            "- `original_value`",
            "- `cleaned_value`",
            "- `cleaning_reason`",
            "- `approval_reference`",
            "",
            (
                "Source values must remain immutable, and recalculated fields "
                "must never overwrite them."
            ),
        ]
    )
    return "\n".join(lines)


def _render_small_data_options() -> str:
    return """# Rwanda Small-Dataset Model Design Options

## Boundary

This document compares future design options only. It does not approve or run
training. Row independence and the selected target must be confirmed first.

## Dataset Implications

There are only 96 rows. A 15% held-out test partition would contain about 14
records, making metrics highly sensitive to individual observations. Missing
age, parity, CP and ME values further reduce usable samples for some designs.
Feature count must remain low, uncertainty must be reported, and external
validation remains necessary because the sample is cross-sectional and
purposively selected at the final farm/cow stage.

## Candidate Algorithms

| Option | Future role | Main control |
|---|---|---|
| Simple linear regression | Transparent baseline for measured milk or verified water-provided target. | Few pre-outcome features; residual diagnostics. |
| Ridge regression | Preferred regularized linear comparison when correlated features are retained. | Tune only inside validation folds. |
| Lasso | Exploratory only when sparse selection has a clear scientific rationale. | Stability analysis across resamples. |
| Small decision tree | Nonlinear benchmark. | Strict depth and minimum-leaf limits. |
| Random forest | High-overfit-risk sensitivity comparison only. | Very shallow trees, restricted features, nested tuning. |
| Gradient boosting | High-overfit-risk comparison only. | Very limited depth, learning rate and iterations. |

Complex ensembles can memorize 96 rows, especially with identifiers, detailed
ingredient strings, calculated targets or leakage fields.

## Validation Options

| Method | Use condition | Limitation |
|---|---|---|
| Leave-one-out CV | Only after all 96 rows are confirmed independent. | High variance; no protection from hidden farm/cow groups. |
| Repeated K-fold CV | Preferred uncertainty assessment after independence confirmation. | Repeated animals/farms would leak across folds. |
| Grouped CV | Required when cow or farm identifiers become available. | Currently impossible because IDs are absent. |
| Bootstrap confidence intervals | Report metric uncertainty and coefficient stability. | Resampling unit must match cow/farm grouping. |
| Small held-out test | Optional only with sufficient independent external data. | About 14 records at 15%; unstable for current dataset. |

## Recommendation

`WAITING_FOR_DATA_CLARIFICATION`. If independence and target definitions are
confirmed, begin with low-feature linear and ridge baselines using repeated or
grouped validation. Do not approve a final design before that evidence exists.
"""


def _render_author_questions() -> str:
    return """# Rwanda Dairy Dataset Clarification Request

## Dataset identity

1. Does each row in the cow workbook represent one unique cow?
2. Does each row represent one unique farm?
3. Can cow and farm identifiers be provided?
4. Is `LabN°` a cow ID, farm ID, composite-feed sample ID, or another ID?
5. Why do six `LabN°` duplicate occurrences appear across three numbers?
6. What do the seven fodder-only sample keys represent?

## Age

7. Why do 30 entries in the age column contain breed names?
8. Is there a corrected age column or corrected workbook?
9. Can the numeric ages for these records be recovered?

## Feed and DMI

10. What does `DM served` represent exactly?
11. What does `leftover` represent exactly?
12. Why are 28 leftover values negative?
13. Does a negative leftover mean shortage, extra feed supplied, or an error?
14. What is the exact DMI calculation formula?
15. What does `DMIcapacity` represent?
16. Is `DMIcapacity` measured intake, predicted intake capacity, or requirement?
17. What are the units and period for every DMI field?
18. Which DMI field should be used as actual consumed dry-matter intake?

## Water

19. Does `waterday` mean water offered, provided, available, reported, or consumed?
20. Was remaining or refused water measured?
21. Is `waterday` per cow per day?
22. How was water requirement calculated, including equation version?
23. How was water gap calculated, and can inconsistent rows be corrected?

## Milk

24. Does `hand-milked yield` include all daily milkings?
25. Is its unit litres per cow per day?
26. How was calf milk consumption estimated?
27. Should `Total milk performance` be treated as observed or calculated?

## Protein

28. What are the units of CP intake and requirement fields?
29. What is the exact CP-gap formula?
30. Why does the metadata definition conflict with stored values?
31. Which CP equation or guideline and version was used?

## Energy

32. What are the units of ME composition, intake and requirements?
33. What is the exact `MEfeeds` equation and CP basis?
34. Which gas-volume or laboratory input was used?
35. Can the missing G24 gas-volume data be supplied?
36. Which energy-requirement guideline and version was used?

## NDF

37. What is the exact NDF unit?
38. Is it percentage of dry matter, g/kg DM, or another basis?

## Feeding plan

39. Does the bucket plan describe farmer practice or a researcher recommendation?
40. Was the ration nutritionally optimized?
41. Were ingredient quantities or inclusion percentages recorded?
42. Is there an additional workbook containing ration quantities?

## Corrected data

43. Is a corrected or newer dataset version available?
44. Can a data dictionary with formulas, units, row identifiers and collection periods be provided?
"""


def _render_author_email() -> str:
    return """# Rwanda Dataset Author Email Draft

**Subject:** Clarification request for Rwanda dairy nutrition dataset (DOI 10.17632/6jf28ftxrr.1)

Dear Dr. Umunezero, Dr. Gachuiri, and Dr. Mutimura,

I am an undergraduate student developing FarmLite, a research prototype
exploring dairy-cattle milk and nutrition modelling. Thank you for publishing
the dataset *Energy, protein, dry matter and water gap analysis in dairy cows
kept under cut and carry fodder-based feeding system* and its supporting
documentation.

Before using any fields for model or transparent nutrition-rule design, I would
be grateful for clarification on a few points:

- whether each cow-workbook row is a distinct cow and farm, and whether cow or
  farm identifiers can be supplied;
- the meaning of repeated `LabN°` values and the seven fodder-only samples;
- the 30 breed descriptions in `cowageinyears`;
- the sign convention for the 28 negative `leftover` values and the intended
  distinction between DMI, DMI requirement and `DMIcapacity`;
- whether `waterday` records water provided or water actually consumed;
- the NDF unit and the intended CP-gap formula;
- the missing G24 input and the exact CP/ME requirement equation versions; and
- whether corrected workbooks, ingredient quantities, or additional
  supplementary material are available.

Could you also confirm whether `hand-milked yield` includes every daily milking
and is expressed in litres per cow per day?

If you provide clarification, may I cite your response in my undergraduate
dissertation with appropriate attribution? I will not share private project
files, and this request does not claim commercial use.

Thank you for your time and for making the data available.

Kind regards,

[Student name]
FarmLite undergraduate project
[University and contact email]

---

Draft only. This email has not been sent.
"""


def _training_gate_rows() -> list[dict[str, str]]:
    return [
        {
            "gate": "Source licence verified",
            "status": "PASSED",
            "evidence": "Mendeley Data version 1 declares CC BY 4.0.",
            "blocking_issue": "None for audit/design use with attribution.",
            "required_action": "Retain DOI and licence attribution.",
        },
        {
            "gate": "Measured milk target verified",
            "status": "PASSED_WITH_LIMITATIONS",
            "evidence": "96 directly measured hand-milked values, 1-17 L/day.",
            "blocking_issue": "Completeness across all daily milkings is unclear.",
            "required_action": "Obtain author confirmation.",
        },
        {
            "gate": "Row independence verified",
            "status": "BLOCKED",
            "evidence": "No cow, farm, visit, or date fields.",
            "blocking_issue": "The 96 rows cannot be proven independent.",
            "required_action": "Obtain identity/collection documentation.",
        },
        {
            "gate": "Cow grouping available",
            "status": "BLOCKED",
            "evidence": "`LabN°` is a composite sample key.",
            "blocking_issue": "No cow_id is supplied.",
            "required_action": "Obtain cow/farm grouping identifiers.",
        },
        {
            "gate": "Water target verified",
            "status": "PASSED_WITH_LIMITATIONS",
            "evidence": "Repository identifies daily water provided.",
            "blocking_issue": "Consumption and remaining water are unmeasured.",
            "required_action": "Limit any future target to water provided.",
        },
        {
            "gate": "DMI target verified",
            "status": "BLOCKED",
            "evidence": "Two meanings for DMIcapacity; 28 negative leftovers.",
            "blocking_issue": "Consumed DMI cannot be defended.",
            "required_action": "Obtain correction and explicit target definition.",
        },
        {
            "gate": "Age data repair approved",
            "status": "BLOCKED",
            "evidence": "30 breed-text and 2 missing age values.",
            "blocking_issue": "No deterministic numeric recovery.",
            "required_action": "Obtain corrected ages or owner missing-value decision.",
        },
        {
            "gate": "Negative leftovers resolved",
            "status": "BLOCKED",
            "evidence": "Five interpretations remain unselected.",
            "blocking_issue": "Sign/collection convention is unknown.",
            "required_action": "Obtain written author clarification.",
        },
        {
            "gate": "CP formulas reproducible",
            "status": "BLOCKED",
            "evidence": "CPmilk mismatches 22 rows; gap metadata conflicts.",
            "blocking_issue": "Requirement and gap definitions need correction.",
            "required_action": "Approve formula version and corrected values.",
        },
        {
            "gate": "ME formulas reproducible",
            "status": "BLOCKED",
            "evidence": "G24 absent; ME-milk mismatch and missing rows.",
            "blocking_issue": "Composition and requirement chain are incomplete.",
            "required_action": "Supply G24, equation version and corrected values.",
        },
        {
            "gate": "NDF unit verified",
            "status": "BLOCKED",
            "evidence": "Metadata says kg DM; values/repository indicate percent.",
            "blocking_issue": "Canonical unit is not owner-confirmed.",
            "required_action": "Obtain explicit unit and basis.",
        },
        {
            "gate": "Feed recommendation labels available",
            "status": "BLOCKED",
            "evidence": "Only observed diets and farmer calf practice.",
            "blocking_issue": "No expert/optimized target labels.",
            "required_action": "Collect nutritionist-approved ration labels.",
        },
        {
            "gate": "Model training not executed",
            "status": "PASSED",
            "evidence": "Clarification validator contains no estimator operations.",
            "blocking_issue": "None.",
            "required_action": "Keep training disabled until a new approval.",
        },
    ]


def _render_training_gate(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Rwanda Model Design Approval Gate",
        "",
        "| Gate | Status | Evidence | Blocking issue | Required action |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                _escape(row[key])
                for key in (
                    "gate",
                    "status",
                    "evidence",
                    "blocking_issue",
                    "required_action",
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Final Recommendation",
            "",
            "`WAITING_FOR_DATA_CLARIFICATION`",
            "",
            (
                "No model design is approved as final, and no training is "
                "authorized or started."
            ),
        ]
    )
    return "\n".join(lines)


CLARIFICATION_SECTION = """## Clarification Requirements Before Training

- Milk model design may proceed only after row independence, grouping, daily
  milking completeness and target definition are confirmed.
- Water is provisionally defined as **water provided**, not verified consumed
  water; consumption modelling remains blocked.
- DMI remains blocked by dual `DMIcapacity` semantics and 28 negative leftovers.
- CP and ME are currently transparent rule-engine candidates only after formula,
  unit, provenance and input clarification.
- Feed-category classification requires nutritionist-approved or optimized
  ration labels.
- Roughage, concentrate and mineral quantities remain unsupported.

Phase 4.5B formula reconstruction did not change the final decision:
`PARTIAL_OPTION_B_SUPPORT`. No training, cleaned-data generation, integration,
or deployment is authorized.
"""


def _update_option_b_report() -> None:
    text = OPTION_B_PATH.read_text(encoding="utf-8")
    if "PARTIAL_OPTION_B_SUPPORT" not in text:
        raise RwandaAuditError("Option B report lost the approved decision")
    marker = "## Clarification Requirements Before Training"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    _write_text(OPTION_B_PATH, text + "\n\n" + CLARIFICATION_SECTION)


def _assert_audit_only_source() -> None:
    source_files = (
        Path(__file__),
        Path(__file__).with_name("rwanda_formula_audit.py"),
    )
    prohibited_import_roots = {"sklearn", "joblib"}
    prohibited_calls = {
        "fit",
        "fit_predict",
        "predict",
        "predict_proba",
        "train_test_split",
        "cross_validate",
        "cross_val_score",
    }
    for path in source_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in prohibited_import_roots:
                        violations.append(f"import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".", 1)[0] in prohibited_import_roots:
                    violations.append(f"import:{node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                else:
                    continue
                if name in prohibited_calls:
                    violations.append(f"call:{name}@{node.lineno}")
        if violations:
            raise RwandaAuditError(
                f"Prohibited model operation in {path}: {sorted(violations)}"
            )


def _validate_outputs(
    *,
    formula_records: list[dict[str, Any]],
    negative: dict[str, Any],
    age: dict[str, Any],
    evidence_rows: list[dict[str, str]],
    repair_rows: list[dict[str, str]],
    gate_rows: list[dict[str, str]],
) -> None:
    missing = [str(path) for path in REQUIRED_OUTPUTS if not path.is_file()]
    if missing:
        raise RwandaAuditError("Clarification output(s) missing: " + ", ".join(missing))
    parsed_formula = pd.read_csv(FORMULA_CSV_PATH)
    parsed_repair = pd.read_csv(TARGET_REPAIR_PATH)
    if len(parsed_formula) != len(formula_records):
        raise RwandaAuditError("Formula CSV row count changed")
    if len(parsed_repair) != 11:
        raise RwandaAuditError("Target repair matrix must contain 11 rows")
    allowed_decisions = {
        "READY_FOR_MODEL_DESIGN",
        "READY_WITH_LIMITATIONS",
        "RULE_ENGINE_ONLY",
        "WAITING_FOR_AUTHOR_RESPONSE",
        "WAITING_FOR_CORRECTED_DATA",
        "EXPERT_LABELS_REQUIRED",
        "NOT_SUPPORTED",
    }
    if not set(parsed_repair["training_decision"]).issubset(allowed_decisions):
        raise RwandaAuditError("Target repair matrix has an invalid decision")
    if negative["negative_row_count"] != 28:
        raise RwandaAuditError("Negative leftover count changed")
    if negative["selected_interpretation"] is not None:
        raise RwandaAuditError("A leftover interpretation was improperly selected")
    if age["breed_text_count"] != 30 or age["values_modified"]:
        raise RwandaAuditError("Age contamination invariant changed")
    required_issue_ids = {
        "RW-DMI-001",
        "RW-DMI-002",
        "RW-DMI-003",
        "RW-ID-001",
        "RW-ID-002",
        "RW-ID-003",
        "RW-AGE-001",
        "RW-WATER-001",
        "RW-WATER-002",
        "RW-WATER-003",
        "RW-NDF-001",
        "RW-CP-001",
        "RW-CP-002",
        "RW-CP-003",
        "RW-ME-001",
        "RW-ME-002",
        "RW-ME-003",
        "RW-JOIN-001",
        "RW-JOIN-002",
        "RW-JOIN-003",
        "RW-FEED-001",
        "RW-FEED-002",
        "RW-MILK-001",
        "RW-MILK-002",
    }
    if {row["issue_id"] for row in evidence_rows} != required_issue_ids:
        raise RwandaAuditError("Evidence register issue IDs are incomplete")
    if len(repair_rows) != 11 or len(gate_rows) != 13:
        raise RwandaAuditError("Decision matrix or gate row count changed")
    required_headings = {
        FORMULA_REPORT_PATH: (
            "# Rwanda Formula Reconstruction Audit",
            "## Formula Results",
            "## Key Conflicts",
        ),
        NEGATIVE_REPORT_PATH: (
            "# Rwanda Negative Leftover Analysis",
            "## Alternative Interpretations",
            "## Result",
        ),
        AGE_REPORT_PATH: (
            "# Rwanda Age Column Analysis",
            "## Repair Investigation",
        ),
        AUTHOR_QUESTIONS_PATH: (
            "# Rwanda Dairy Dataset Clarification Request",
            "## Dataset identity",
            "## Corrected data",
        ),
        TRAINING_GATE_PATH: (
            "# Rwanda Model Design Approval Gate",
            "## Final Recommendation",
        ),
    }
    for path, headings in required_headings.items():
        text = path.read_text(encoding="utf-8")
        if any(heading not in text for heading in headings):
            raise RwandaAuditError(f"Required heading missing from {path}")
    if "LabN°" not in AUTHOR_QUESTIONS_PATH.read_text(encoding="utf-8"):
        raise RwandaAuditError("Author questionnaire lost the sample-ID question")
    if "Draft only. This email has not been sent." not in AUTHOR_EMAIL_PATH.read_text(
        encoding="utf-8"
    ):
        raise RwandaAuditError("Author email draft boundary is missing")
    if "PARTIAL_OPTION_B_SUPPORT" not in OPTION_B_PATH.read_text(encoding="utf-8"):
        raise RwandaAuditError("Option B status changed")


def run_clarification() -> dict[str, Any]:
    """Generate all Phase 4.5B outputs and verify protected state."""

    _assert_audit_only_source()
    prior = _load_prior_reports()
    files = discover_rwanda_files()
    raw_before = {name: sha256_file(path) for name, path in files.items()}
    if raw_before != EXPECTED_SHA256:
        raise RwandaAuditError("A Rwanda source hash differs from Phase 4.5A")
    synthetic_before = _synthetic_hashes()
    if synthetic_before != SYNTHETIC_SOURCE_HASHES:
        raise RwandaAuditError("A synthetic source hash changed")
    prior_hashes_before = _prior_report_hashes()
    protected_before = _protected_snapshot()

    cow_workbook = read_xlsx(files[COW_FILENAME])
    cow_frame = dataframe_from_sheet(cow_workbook.sheets[0], header_row=11)
    if len(cow_frame) != 96:
        raise RwandaAuditError(f"Expected 96 cow rows, found {len(cow_frame)}")

    formula_records = audit_all_formulas(cow_frame)
    negative = negative_leftover_analysis(cow_frame)
    age = age_column_analysis(cow_frame)
    evidence_rows = _evidence_rows()
    repair_rows = _target_repair_rows()
    gate_rows = _training_gate_rows()

    write_csv(FORMULA_CSV_PATH, formula_records)
    write_csv(TARGET_REPAIR_PATH, repair_rows)
    _write_text(FORMULA_REPORT_PATH, _render_formula_report(formula_records))
    _write_text(NEGATIVE_REPORT_PATH, _render_negative_report(negative))
    _write_text(AGE_REPORT_PATH, _render_age_report(age))
    _write_text(EVIDENCE_REGISTER_PATH, _render_evidence_register(evidence_rows))
    _write_text(IDENTIFIER_PATH, _render_identifier_requirements())
    _write_text(WATER_PATH, _render_water_definition(cow_frame))
    _write_text(MILK_PATH, _render_milk_definition(cow_frame))
    _write_text(NUTRIENT_PATH, _render_nutrient_assessment(formula_records))
    _write_text(FODDER_PATH, _render_fodder_limitations())
    _write_text(CLEANING_PATH, _render_cleaning_specification())
    _write_text(SMALL_DATA_PATH, _render_small_data_options())
    _write_text(AUTHOR_QUESTIONS_PATH, _render_author_questions())
    _write_text(AUTHOR_EMAIL_PATH, _render_author_email())
    _write_text(TRAINING_GATE_PATH, _render_training_gate(gate_rows))
    _update_option_b_report()

    _validate_outputs(
        formula_records=formula_records,
        negative=negative,
        age=age,
        evidence_rows=evidence_rows,
        repair_rows=repair_rows,
        gate_rows=gate_rows,
    )

    raw_after = {name: sha256_file(path) for name, path in files.items()}
    synthetic_after = _synthetic_hashes()
    prior_hashes_after = _prior_report_hashes()
    protected_after = _protected_snapshot()
    if raw_before != raw_after:
        raise RwandaAuditError("At least one Rwanda raw file changed")
    if synthetic_before != synthetic_after:
        raise RwandaAuditError("At least one synthetic raw file changed")
    if prior_hashes_before != prior_hashes_after:
        raise RwandaAuditError("A Phase 4.5A audit artifact changed unexpectedly")
    if protected_before != protected_after:
        raise RwandaAuditError("At least one protected project file changed")

    formula_counts = dict(Counter(item["status"] for item in formula_records))
    return {
        "phase": "4.5B",
        "status": "PASSED_CLARIFICATION_ONLY",
        "prior_reports_loaded": True,
        "prior_csv_shapes": prior["csv_shapes"],
        "formula_count": len(formula_records),
        "formula_status_counts": formula_counts,
        "negative_leftover_status": negative["status"],
        "negative_leftover_count": negative["negative_row_count"],
        "age_status": age["status"],
        "water_status": "VERIFIED_WATER_PROVIDED_L_COW_DAY",
        "milk_status": "READY_WITH_LIMITATIONS",
        "training_gate_result": "WAITING_FOR_DATA_CLARIFICATION",
        "option_b_decision": "PARTIAL_OPTION_B_SUPPORT",
        "raw_files_unchanged": raw_before == raw_after,
        "synthetic_files_unchanged": synthetic_before == synthetic_after,
        "prior_reports_unchanged": prior_hashes_before == prior_hashes_after,
        "protected_files_unchanged": protected_before == protected_after,
        "model_training_occurred": False,
        "prediction_occurred": False,
        "processed_rwanda_dataset_created": False,
        "source_value_replaced": False,
        "unsupported_unit_conversion_occurred": False,
        "expert_label_generated": False,
        "files_created_or_updated": [
            str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_OUTPUTS
        ],
    }


def main() -> int:
    try:
        result = run_clarification()
    except Exception as error:
        print(
            f"RWANDA_CLARIFICATION_FAILED: {type(error).__name__}: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    print(
        "RWANDA_CLARIFICATION_PASSED "
        f"formulas={result['formula_count']} "
        f"negative_leftovers={result['negative_leftover_count']} "
        f"gate={result['training_gate_result']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
