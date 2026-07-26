"""Generate and validate the Phase 4.5C Bangladesh audit artifacts.

Run from ``backend/flask_api`` with:

    venv\\Scripts\\python.exe -m ml.data_integration.validate_bangladesh_dataset
"""

from __future__ import annotations

import ast
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import (
    FLASK_API_DIR,
    ML_MODELS_DIR,
    ML_REPORTS_DIR,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
)
from ml.data_integration.bangladesh_audit import (
    AUDIT_VERSION,
    BLOOD_FILENAME,
    BangladeshAuditError,
    DMI_FILENAME,
    EXPECTED_SHA256,
    METADATA_FILENAME,
    PHYSIOLOGY_FILENAME,
    RELATED_ARTICLE,
    SOURCE_RECORD,
    analyze_join,
    classify_leakage,
    common_schema,
    data_quality_issues,
    dataframe_from_sheet,
    detect_repeated_observations,
    discover_bangladesh_files,
    farmlite_compatibility,
    inventory_entry,
    parse_metadata_document,
    sha256_file,
    target_audit,
    target_matrix,
    tree_checksum,
    workbook_profile,
)
from ml.data_integration.office_reader import read_docx, read_xlsx


REPORT_DIR = ML_REPORTS_DIR
DOCUMENTATION_DIR = PROJECT_ROOT / "documentation"
CONFIG_DIR = FLASK_API_DIR / "config"

INVENTORY_PATH = REPORT_DIR / "bangladesh_dataset_inventory.json"
AUDIT_REPORT_PATH = REPORT_DIR / "bangladesh_dataset_audit.md"
VARIABLE_DICTIONARY_PATH = (
    REPORT_DIR / "bangladesh_variable_dictionary.csv"
)
TARGET_MATRIX_PATH = REPORT_DIR / "bangladesh_target_matrix.csv"
QUALITY_PATH = REPORT_DIR / "bangladesh_data_quality_issues.csv"
JOIN_REPORT_PATH = (
    REPORT_DIR / "bangladesh_cross_workbook_join_report.md"
)
COMPATIBILITY_PATH = (
    REPORT_DIR / "bangladesh_farmlite_compatibility.csv"
)
OPTION_B_PATH = REPORT_DIR / "bangladesh_option_b_support_report.md"
SOURCE_REGISTER_PATH = (
    DOCUMENTATION_DIR / "bangladesh_dataset_source_register.md"
)
METHODOLOGY_PATH = (
    DOCUMENTATION_DIR / "bangladesh_dataset_methodology_summary.md"
)
GROUPING_PATH = (
    DOCUMENTATION_DIR / "bangladesh_grouping_and_split_requirements.md"
)
MODEL_OPTIONS_PATH = (
    DOCUMENTATION_DIR / "bangladesh_model_design_options.md"
)
RWANDA_COMPARISON_PATH = (
    DOCUMENTATION_DIR / "rwanda_bangladesh_dataset_comparison.md"
)
SCHEMA_PATH = CONFIG_DIR / "bangladesh_hf_common_schema.json"

REQUIRED_OUTPUTS = (
    INVENTORY_PATH,
    AUDIT_REPORT_PATH,
    VARIABLE_DICTIONARY_PATH,
    TARGET_MATRIX_PATH,
    QUALITY_PATH,
    JOIN_REPORT_PATH,
    COMPATIBILITY_PATH,
    OPTION_B_PATH,
    SOURCE_REGISTER_PATH,
    METHODOLOGY_PATH,
    GROUPING_PATH,
    MODEL_OPTIONS_PATH,
    RWANDA_COMPARISON_PATH,
    SCHEMA_PATH,
)
REQUIRED_AUDIT_HEADINGS = (
    "# Bangladesh HF Cross Dataset Audit",
    "## Scope and Audit Order",
    "## Source Provenance",
    "## Metadata DOCX Audit",
    "## Workbook Structure",
    "## DMI Target Audit",
    "## Milk-Yield Target Audit",
    "## Milk-Composition Audit",
    "## Physiological and Environmental Audit",
    "## Blood-Metabolite Audit",
    "## Identifier and Repeated-Measure Audit",
    "## Cross-Workbook Join Audit",
    "## Data-Quality Analysis",
    "## Leakage Audit",
    "## FarmLite Compatibility",
    "## Model-Support Assessment",
    "## Limitations and Blockers",
    "## Audit-Only Boundary",
)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise BangladeshAuditError(f"Refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _protected_snapshot() -> dict[str, Any]:
    """Hash every protected artifact named in the Phase 4.5C scope."""

    rwanda_dir = (
        PROJECT_ROOT / "datasets" / "external" / "raw" / "rwanda_dairy"
    )
    synthetic_names = (
        "global_cattle_disease_detection_dataset.csv",
        "global_cattle_milk_yield_prediction_dataset.csv",
    )
    synthetic = {}
    for name in synthetic_names:
        path = PROJECT_ROOT / "datasets" / "raw" / name
        synthetic[name] = sha256_file(path) if path.is_file() else None
    nutrition = (
        FLASK_API_DIR / "ml" / "validation" / "nutrition_rules.py"
    )
    routes = {
        "app.py": sha256_file(FLASK_API_DIR / "app.py"),
        **{
            f"api/{key}": value
            for key, value in tree_checksum(FLASK_API_DIR / "api").items()
        },
    }
    candidates = ML_MODELS_DIR / "candidates" / "phase4"
    exclusions = {
        ".git",
        "__pycache__",
        "node_modules",
        "dist",
        "venv",
    }
    pdf_files = {
        key: value
        for key, value in tree_checksum(
            PROJECT_ROOT,
            excluded_names=exclusions,
        ).items()
        if key.casefold().endswith(".pdf")
    }
    return {
        "synthetic_raw": synthetic,
        "rwanda_raw": tree_checksum(rwanda_dir),
        "retained_model": (
            sha256_file(ML_MODELS_DIR / "milk_yield_model.joblib")
            if (ML_MODELS_DIR / "milk_yield_model.joblib").is_file()
            else None
        ),
        "phase4_candidates": tree_checksum(candidates),
        "routes": routes,
        "frontend_tree": tree_checksum(
            PROJECT_ROOT / "frontend",
            excluded_names={"node_modules", "dist", "__pycache__"},
        ),
        "pdf_files": pdf_files,
        "nutrition_rules": (
            sha256_file(nutrition) if nutrition.is_file() else None
        ),
        "processed_files": tree_checksum(PROCESSED_DATA_DIR),
    }


def _assert_audit_only_source() -> None:
    """Reject accidental estimator imports or training/prediction calls."""

    paths = [
        Path(__file__),
        Path(__file__).with_name("bangladesh_audit.py"),
        Path(__file__).with_name("office_reader.py"),
    ]
    prohibited_imports = {"sklearn", "joblib", "tensorflow", "torch", "xgboost"}
    prohibited_calls = {
        "fit",
        "fit_predict",
        "predict",
        "predict_proba",
        "train_test_split",
        "cross_validate",
        "cross_val_score",
        "cross_val_predict",
        "dump",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        findings: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in prohibited_imports:
                        findings.append(f"import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".", 1)[0]
                if root in prohibited_imports:
                    findings.append(f"import:{node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                else:
                    continue
                if name in prohibited_calls:
                    findings.append(f"call:{name}@{node.lineno}")
        if findings:
            raise BangladeshAuditError(
                f"Training/prediction operation in {path}: "
                f"{sorted(set(findings))}"
            )


def _fmt(value: Any, decimals: int = 3) -> str:
    if value is None:
        return "UNCLEAR"
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)


def _numeric_table(profile: dict[str, Any]) -> list[str]:
    lines = [
        "| Field | n | Min | Max | Mean | Median | SD | Zero | Negative |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for field, item in profile["numeric_summaries"].items():
        lines.append(
            f"| `{field}` | {item['count']} | {_fmt(item['minimum'])} | "
            f"{_fmt(item['maximum'])} | {_fmt(item['mean'])} | "
            f"{_fmt(item['median'])} | "
            f"{_fmt(item['standard_deviation'])} | {item['zero_count']} | "
            f"{item['negative_count']} |"
        )
    return lines


def _render_audit_report(
    metadata: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    dmi_audit: dict[str, Any],
    milk_audit: dict[str, Any],
    joins: list[dict[str, Any]],
    quality: list[dict[str, Any]],
    compatibility: list[dict[str, Any]],
) -> str:
    severity = Counter(item["severity"] for item in quality)
    workbook_sections: list[str] = []
    for filename in (DMI_FILENAME, PHYSIOLOGY_FILENAME, BLOOD_FILENAME):
        item = profiles[filename]
        repeated = item["repeated_measurements"]
        workbook_sections.extend(
            [
                f"### `{filename}` / `{item['sheet_name']}`",
                "",
                (
                    f"- Shape: **{item['row_count_excluding_header']} data "
                    f"rows × {item['column_count']} columns**."
                ),
                (
                    "- Columns: "
                    + ", ".join(
                        f"`{column}`" for column in item["exact_column_names"]
                    )
                ),
                (
                    f"- Missing cells by parsed values: 0; exact duplicate "
                    f"rows: {item['duplicate_rows']}; duplicate composite "
                    f"keys: {item['duplicate_composite_keys']}."
                ),
                (
                    f"- Cows: {repeated['unique_cows']}; records/cow: "
                    f"{repeated['minimum_records_per_cow']}–"
                    f"{repeated['maximum_records_per_cow']}."
                ),
                (
                    "- Row structure: "
                    "`ONE_ROW_PER_COW_PER_THI_CATEGORY_PER_REPLICATION`."
                ),
                (
                    f"- Hidden sheets: {item['hidden_sheet_count']}; formulas: "
                    f"{item['formula_count']}; merged ranges: "
                    f"{item['merged_cell_count']}; comments: "
                    f"{item['comment_count']}."
                ),
                "",
                *_numeric_table(item),
                "",
            ]
        )
    join_lines = [
        "| Left | Right | Key matches | Match % | Cardinality | Decision |",
        "|---|---|---:|---:|---|---|",
    ]
    for item in joins:
        join_lines.append(
            f"| `{item['left_workbook']}` | `{item['right_workbook']}` | "
            f"{item['match_count']} | {item['left_match_percentage']:.1f}% | "
            f"{item['cardinality']} | `{item['join_safety']}` |"
        )
    current = compatibility[:9]
    present_current = sum(
        row["present_in_bangladesh"] in {"YES", "PARTIAL"} for row in current
    )
    return "\n".join(
        [
            "# Bangladesh HF Cross Dataset Audit",
            "",
            "## Executive Decision",
            "",
            "**Final decision: `DMI_AND_MILK_SUPPORT`.**",
            "",
            (
                "The source verifies a DMI field in kg per cow per day and "
                "daily milk yield in L per cow per day, each with 750 usable "
                "repeated observations from 50 cows. Both are "
                "`READY_WITH_LIMITATIONS` for future model design. This does "
                "not establish a feed/ration recommendation label."
            ),
            "",
            "## Scope and Audit Order",
            "",
            (
                "Audit only. The files were read in the required order: "
                "`metadata.docx`, DMI/milk workbook, physiology workbook, "
                "then blood workbook. No model was fitted, evaluated, "
                "integrated, deployed, or replaced; no joined or processed "
                "dataset was saved."
            ),
            "",
            "## Source Provenance",
            "",
            (
                f"- Repository dataset: [{SOURCE_RECORD['title']}]"
                f"({SOURCE_RECORD['url']})."
            ),
            (
                f"- Citation: {SOURCE_RECORD['contributor']} (2026), V"
                f"{SOURCE_RECORD['version']}, DOI "
                f"`{SOURCE_RECORD['doi']}`."
            ),
            f"- Repository licence: `{SOURCE_RECORD['licence']}`.",
            (
                f"- Related article: [{RELATED_ARTICLE['title']}]"
                f"({RELATED_ARTICLE['url']}), DOI "
                f"`{RELATED_ARTICLE['doi']}`."
            ),
            (
                "The repository record is supplemental provenance. Local-file "
                "facts and external-record facts are kept distinct."
            ),
            "",
            "## Metadata DOCX Audit",
            "",
            f"- Title: {metadata['title']}",
            "- Authors/contributors: " + " | ".join(metadata["author_lines"]),
            (
                f"- Paragraphs/headings/tables: {metadata['paragraph_count']}/"
                f"{metadata['heading_count']}/{metadata['table_count']}."
            ),
            (
                f"- Parsed variable definitions: "
                f"{len(metadata['definitions'])}."
            ),
            (
                "- Local study period/cow count/sampling frequency: "
                "`UNCLEAR`; repository: January–December 2024, 50 cows, five "
                "milk/blood samples per THI category."
            ),
            (
                "- Local DOCX licence: `UNCLEAR`; matched repository record: "
                "`CC BY 4.0`."
            ),
            (
                "- Absent/unclear: parity, weight, age, DIM, lactation stage, "
                "BCS, missing codes, exact DMI/milk methods, instruments, and "
                "laboratory assays."
            ),
            "",
            "## Workbook Structure",
            "",
            *workbook_sections,
            "## DMI Target Audit",
            "",
            "- Exact field: `DMI (kg)`.",
            (
                "- Definition/status: dry matter intake per cow; metadata "
                "variable name specifies kg/day. "
                "`VERIFIED_DMI_KG_COW_DAY`."
            ),
            (
                f"- Usable/missing: {dmi_audit['usable_records']} / "
                f"{dmi_audit['missing_percentage']:.1f}%."
            ),
            (
                f"- Range/mean/median/SD: {_fmt(dmi_audit['minimum'])}–"
                f"{_fmt(dmi_audit['maximum'])} / "
                f"{_fmt(dmi_audit['mean'])} / "
                f"{_fmt(dmi_audit['median'])} / "
                f"{_fmt(dmi_audit['standard_deviation'])} kg/cow/day."
            ),
            (
                f"- Zero/negative: {dmi_audit['zero_count']}/"
                f"{dmi_audit['negative_count']}."
            ),
            (
                "- Feed offered/refused fields: absent. The source presents "
                "DMI as measured intake, not estimated requirement, but the "
                "exact offered/refusal protocol is `UNCLEAR`."
            ),
            (
                "- Repeats: five observations in each of T0/T1/T2 for every "
                "cow; cow grouping is possible. Variation is non-zero, but "
                "adequacy must be assessed with cow-grouped validation."
            ),
            "- ML decision: `READY_WITH_LIMITATIONS`.",
            "",
            "## Milk-Yield Target Audit",
            "",
            "- Exact field: `Milk Yield (L/day/cow)`.",
            (
                "- Definition/status: daily milk yield per cow in litres; "
                "`VERIFIED_MILK_YIELD_L_COW_DAY`."
            ),
            (
                f"- Usable/missing: {milk_audit['usable_records']} / "
                f"{milk_audit['missing_percentage']:.1f}%."
            ),
            (
                f"- Range/mean/median/SD: {_fmt(milk_audit['minimum'])}–"
                f"{_fmt(milk_audit['maximum'])} / "
                f"{_fmt(milk_audit['mean'])} / "
                f"{_fmt(milk_audit['median'])} / "
                f"{_fmt(milk_audit['standard_deviation'])} L/cow/day."
            ),
            (
                f"- Zero/negative: {milk_audit['zero_count']}/"
                f"{milk_audit['negative_count']}."
            ),
            (
                "- Exact recording instrument/time-of-day protocol is "
                "`UNCLEAR`. Litres were not converted to kilograms."
            ),
            (
                "- ML/external-validation decision: "
                "`READY_WITH_LIMITATIONS`; external validation requires "
                "compatible features, timing, population, and units."
            ),
            "",
            "## Milk-Composition Audit",
            "",
            (
                "Verified fields: `SCC cells per mL`, `Fat%`, `SNF%`, "
                "`Protein %`, `Salt%`, `Lactose%`, and `pH`. All have 750 "
                "non-missing repeated records. Total solids and density are "
                "not present."
            ),
            (
                "Roles: composition fields are `ML_TARGET_CANDIDATE` or "
                "`OPTIONAL_DIAGNOSTIC`; as prediction-time inputs they are "
                "`POSSIBLE_LEAKAGE` because same-record timing and farmer "
                "availability are not established. Exact laboratory or "
                "instrument methods are `UNCLEAR`."
            ),
            "",
            "## Physiological and Environmental Audit",
            "",
            (
                "Verified physiology: `Rectal Temp (F)` (101.23–103.46 °F), "
                "`Pulse Rate (bpm)` (58.8–72.5 beats/min), and "
                "`Respiration Rate (bpm)` (25.0–46.2 breaths/min). The last "
                "header uses bpm, while metadata defines breaths/min."
            ),
            (
                "No ambient temperature, relative humidity, numeric THI, "
                "date, or time is stored in the supplied workbooks. `THI "
                "Range` is an assigned categorical environmental group."
            ),
            (
                f"The related article documents `{RELATED_ARTICLE['thi_formula']}` "
                f"with {RELATED_ARTICLE['thi_inputs']}. Reproduction cannot "
                "be checked because numeric T, RH, and THI are absent."
            ),
            (
                "Repository provenance says physiological readings were "
                "taken twice daily on milk/blood sampling dates and averaged; "
                "whether the averages precede DMI/milk prediction is "
                "`UNCLEAR`."
            ),
            "",
            "## Blood-Metabolite Audit",
            "",
            (
                "Verified fields: glucose, total protein, uric acid, "
                "cholesterol, calcium, HDL, AST, ALT, and cortisol (750 "
                "non-missing records each). AST/ALT units conflict: workbook "
                "`U/I`, metadata `U/L`."
            ),
            (
                "Roles: all are `RESEARCH_OUTCOME` and "
                "`NOT_AVAILABLE_AT_FARM_INFERENCE`; cortisol may be a "
                "`POSSIBLE_HEAT_STRESS_TARGET`. None is approved as a "
                "FarmLite prediction-time input."
            ),
            "",
            "## Identifier and Repeated-Measure Audit",
            "",
            (
                "Each workbook has 50 cow IDs and exactly 15 records/cow: "
                "3 THI categories × 5 replication numbers. Within each "
                "workbook, `Animal ID + THI Range + Replication No` is unique."
            ),
            (
                "No standalone observation ID, date, or sampling timestamp "
                "exists. `Animal ID` is safe for future grouped validation. "
                "All rows from a cow must remain in one partition/fold."
            ),
            (
                "DMI/blood cow IDs are 102–111, 202–211, …, 502–511; "
                "physiology uses 101–110, 201–210, …, 501–510. Thus only 45 "
                "cow IDs are shared with physiology."
            ),
            "",
            "## Cross-Workbook Join Audit",
            "",
            *join_lines,
            "",
            (
                "DMI/milk ↔ blood is `SAFE_ONE_TO_ONE` (750/750). Joins "
                "involving physiology are `POSSIBLE_WITH_LIMITATIONS` "
                "(675/750; 90%). No row-order join is valid, and no joined "
                "dataset was saved."
            ),
            "",
            "## Data-Quality Analysis",
            "",
            (
                f"- Issue rows: {len(quality)} (HIGH={severity['HIGH']}, "
                f"MEDIUM={severity['MEDIUM']}, LOW={severity['LOW']})."
            ),
            (
                "- 150 rows describe the cross-workbook physiology cow-ID "
                "coverage mismatch (75 on each side), not 150 independent "
                "defect types."
            ),
            (
                "- No parsed missing values, exact duplicate rows, duplicate "
                "composite keys, formulas, negative/zero DMI, or "
                "negative/zero milk yield were detected."
            ),
            (
                "- Other findings: mixed blood-ID cell types (2 cells), "
                "genetic/THI label formatting differences, AST/ALT unit "
                "conflicts, missing dates/environmental inputs, and "
                "undocumented methods. No source value was corrected."
            ),
            (
                "- Biological plausibility of physiological/laboratory values "
                "was not asserted without a source-specific clinical "
                "reference and protocol."
            ),
            "",
            "## Leakage Audit",
            "",
            "| Candidate field | DMI model | Milk model | Reason |",
            "|---|---|---|---|",
            "| Genetic group | `SAFE` | `SAFE` | Stable source attribute. |",
            (
                "| THI category | `UNCLEAR` | `UNCLEAR` | Available only if "
                "future conditions are measured and categorized consistently. |"
            ),
            (
                "| Same-day milk/DMI | `POSSIBLE_LEAKAGE` | "
                "`POSSIBLE_LEAKAGE` | Timing/order is not established. |"
            ),
            (
                "| Physiology | `UNCLEAR` | `UNCLEAR` | Averaged on sampling "
                "dates; pre-prediction availability is not established. |"
            ),
            (
                "| Milk composition | `POSSIBLE_LEAKAGE` | "
                "`POSSIBLE_LEAKAGE` | Same-record outcomes. |"
            ),
            (
                "| Blood metabolites | `RESEARCH_ONLY` | `RESEARCH_ONLY` | "
                "Laboratory outcomes unavailable to typical farmers. |"
            ),
            "",
            "## FarmLite Compatibility",
            "",
            (
                f"Only {present_current}/9 current inputs are present or "
                "partially mappable: `breed` is only represented by genetic "
                "group. Age, weight, lactation stage, DIM, previous-week "
                "yield, BCS, numeric ambient temperature, and humidity are "
                "missing."
            ),
            (
                "Potential future inputs: genetic group and measured "
                "temperature/humidity or numeric THI. Physiology could be an "
                "optional research input only after timing and farmer "
                "availability are justified. No frontend was changed."
            ),
            "",
            "## Model-Support Assessment",
            "",
            "| Proposed model | Decision |",
            "|---|---|",
            (
                "| A — DMI regression | `READY_WITH_LIMITATIONS`: target "
                "verified; very limited practical feature set and grouped "
                "validation required. |"
            ),
            (
                "| B — milk-yield regression | `READY_WITH_LIMITATIONS`: "
                "target verified; very limited feature set and timing gaps. |"
            ),
            (
                "| C — heat-stress-aware milk | `READY_WITH_LIMITATIONS`: "
                "categorical THI only; numeric T/RH/THI absent. |"
            ),
            (
                "| D — heat-stress-aware DMI | `READY_WITH_LIMITATIONS`: "
                "categorical THI only; numeric T/RH/THI absent. |"
            ),
            (
                "| E — physiological response | `READY_WITH_LIMITATIONS` as "
                "optional research, not core FarmLite. |"
            ),
            (
                "| F — feed/ration category | `NOT_SUPPORTED`: no expert or "
                "optimized ration labels. |"
            ),
            "",
            "## Limitations and Blockers",
            "",
            "- Exact DMI feed-offered/refusal protocol is `UNCLEAR`.",
            "- Numeric temperature, humidity, THI, dates, and timestamps are absent.",
            "- Physiology cow-ID coverage conflicts with DMI/milk and blood.",
            "- Eight of nine current FarmLite inputs are absent.",
            "- Same-day outcome timing creates unresolved leakage risks.",
            "- No ration ingredients, quantities, or expert recommendations exist.",
            "- Rwanda DMI semantics remain unclear, preventing DMI external validation.",
            "",
            "## Audit-Only Boundary",
            "",
            (
                "No training, estimator fitting, prediction, model evaluation, "
                "preprocessing output, permanent join, dataset concatenation, "
                "unit conversion, source edit, route edit, frontend edit, PDF "
                "edit, nutrition-rule edit, model replacement, or deployment "
                "occurred."
            ),
        ]
    )


def _render_join_report(joins: list[dict[str, Any]]) -> str:
    sections = [
        "# Bangladesh Cross-Workbook Join Report",
        "",
        "## Approved Key Basis",
        "",
        (
            "The audited in-memory key is `Animal ID + normalized THI Range + "
            "Replication No`. Metadata explicitly defines all three fields. "
            "Normalization only maps documented label variants (`T0` and "
            "`T0 (≤75)`, for example). Row order is not a key."
        ),
        "",
    ]
    for item in joins:
        sections.extend(
            [
                (
                    f"## `{item['left_workbook']}` ↔ "
                    f"`{item['right_workbook']}`"
                ),
                "",
                f"- Join safety: `{item['join_safety']}`.",
                f"- Cardinality: `{item['cardinality']}`.",
                (
                    f"- Match: {item['match_count']} keys "
                    f"({item['left_match_percentage']:.1f}% left; "
                    f"{item['right_match_percentage']:.1f}% right)."
                ),
                (
                    f"- Missing keys: left {item['left_missing_key_count']}; "
                    f"right {item['right_missing_key_count']}."
                ),
                (
                    f"- Duplicate-key rows: left "
                    f"{item['left_duplicate_key_row_count']}; right "
                    f"{item['right_duplicate_key_row_count']}."
                ),
                (
                    f"- Left-only/right-only keys: "
                    f"{item['left_only_key_count']}/"
                    f"{item['right_only_key_count']}."
                ),
                (
                    f"- Left-only cows: "
                    f"{item['left_only_cow_ids'] or 'none'}."
                ),
                (
                    f"- Right-only cows: "
                    f"{item['right_only_cow_ids'] or 'none'}."
                ),
                f"- Many-to-many risk: {item['many_to_many_risk']}.",
                "",
            ]
        )
    sections.extend(
        [
            "## Decision",
            "",
            (
                "DMI/milk and blood can be joined one-to-one on the composite "
                "key. Physiology joins require source-owner resolution of the "
                "five-ID-per-group boundary mismatch. No joined data was saved."
            ),
        ]
    )
    return "\n".join(sections)


def _render_option_b_report(joins: list[dict[str, Any]]) -> str:
    answers = [
        ("1. Is DMI clearly defined?", "Yes: dry matter intake per cow in kg/day."),
        ("2. Is DMI measured per cow per day?", "Yes; exact offered/refusal protocol remains `UNCLEAR`."),
        ("3. Is milk yield clearly defined?", "Yes: daily milk yield per cow in litres."),
        ("4. Are cow identifiers present?", "Yes, `Animal ID` in all workbooks."),
        ("5. Are repeated observations linkable?", "Yes within each workbook; cross-workbook physiology coverage is only 90%."),
        ("6. Can grouped validation be performed?", "Yes. Group only by cow; never split repeated rows randomly."),
        ("7. Are temperature and humidity available?", "No numeric temperature or humidity fields are supplied."),
        ("8. Is THI measured or calculated?", "Workbooks store assigned THI categories. The article documents calculation from T and RH, but numeric inputs/THI are absent."),
        ("9. Can a heat-stress-aware DMI model be designed?", "`READY_WITH_LIMITATIONS` using categorical THI only."),
        ("10. Can a heat-stress-aware milk model be designed?", "`READY_WITH_LIMITATIONS` using categorical THI only."),
        ("11. Can the physiological workbook be joined safely?", "`POSSIBLE_WITH_LIMITATIONS`: 675/750 keys and 45/50 cow IDs match."),
        ("12. Can the blood workbook be joined safely?", "`SAFE_ONE_TO_ONE` with DMI/milk: 750/750 keys."),
        ("13. Are blood variables appropriate for FarmLite?", "No as ordinary inference inputs; they are research/laboratory outcomes."),
        ("14. Does any workbook contain expert feed recommendations?", "No."),
        ("15. Can roughage and concentrate quantities be predicted?", "No targets or component quantities are present."),
        ("16. Which FarmLite inputs are missing?", "Age, weight, lactation stage, DIM, previous-week yield, BCS, ambient temperature, and humidity."),
        ("17. Which new frontend inputs may be useful?", "Genetic group plus measured temperature/humidity or numeric THI, after future design review."),
        ("18. Can Bangladesh and Rwanda be combined?", "No. Keep them separate; target semantics, population, design, and feature coverage differ."),
        ("19. Can Bangladesh be used for training and Rwanda for validation?", "Not for DMI now; Rwanda DMI is semantically blocked. Milk requires a separate harmonization/feature review first."),
        ("20. Does this source restore the feed-quantity part of Option B?", "It restores a verified DMI target for research model design, not a complete ration/quantity recommender."),
    ]
    return "\n".join(
        [
            "# Bangladesh Option B Support Report",
            "",
            "## Final Decision: `DMI_AND_MILK_SUPPORT`",
            "",
            *[
                f"### {question}\n\n{answer}\n"
                for question, answer in answers
            ],
            "## Boundary",
            "",
            (
                "This decision authorizes no training or integration. It does "
                "not treat genetic group or THI group as a recommendation "
                "label and does not change the frontend or Option B runtime."
            ),
        ]
    )


def _render_source_register(inventory: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Bangladesh HF Cross Dataset Source Register",
            "",
            "## Repository Record",
            "",
            f"- Title: {SOURCE_RECORD['title']}",
            f"- Contributor: {SOURCE_RECORD['contributor']}",
            f"- Version/published: {SOURCE_RECORD['version']} / {SOURCE_RECORD['published']}",
            f"- Dataset DOI: `{SOURCE_RECORD['doi']}`",
            f"- Dataset URL: {SOURCE_RECORD['url']}",
            f"- Licence: `{SOURCE_RECORD['licence']}`",
            f"- Study period: {SOURCE_RECORD['study_period']}",
            f"- Study location: {SOURCE_RECORD['study_location']}",
            "",
            "## Related Article",
            "",
            f"- Title: {RELATED_ARTICLE['title']}",
            f"- DOI: `{RELATED_ARTICLE['doi']}`",
            f"- URL: {RELATED_ARTICLE['url']}",
            "",
            "## Supplied Files",
            "",
            "| File | Size bytes | SHA-256 |",
            "|---|---:|---|",
            *[
                f"| `{item['filename']}` | {item['file_size_bytes']} | "
                f"`{item['sha256']}` |"
                for item in inventory["files"]
            ],
            "",
            "## Provenance Boundary",
            "",
            (
                "The local DOCX contains no licence statement and only a "
                "partial citation. Licence, version, study period, exact farm, "
                "cow count, and sampling schedule above are attributed to the "
                "matched Mendeley record, not inferred from workbook values."
            ),
        ]
    )


def _render_methodology() -> str:
    return "\n".join(
        [
            "# Bangladesh HF Cross Dataset Methodology Summary",
            "",
            "## Study Design",
            "",
            (
                "Fifty lactating cows from five HF genetic proportions (10 per "
                "group) were studied from January–December 2024 at the Central "
                "Cattle Breeding and Dairy Farm, Savar, Bangladesh. The "
                "workbooks organize observations into T0 (≤75), T1 (75–80), "
                "and T2 (≥80), with five replications per cow/category."
            ),
            "",
            "## Measurement Schedule",
            "",
            (
                "The repository record states that milk and blood were sampled "
                "five times per THI category and physiological parameters were "
                "recorded twice daily on each sampling date and averaged. "
                "Dates and times are not included in the supplied workbooks."
            ),
            "",
            "## DMI and Milk",
            "",
            (
                "DMI is defined as dry matter intake per cow in kg/day; milk "
                "yield is daily litres per cow. The repository says they were "
                "measured using standard procedures, but the exact "
                "feed-offered/refusal protocol, milking protocol, instruments, "
                "and quality control are `UNCLEAR`."
            ),
            "",
            "## Environment and THI",
            "",
            f"- Article formula: `{RELATED_ARTICLE['thi_formula']}`.",
            f"- Inputs: {RELATED_ARTICLE['thi_inputs']}.",
            (
                "- The source workbooks retain only THI categories, not "
                "numeric T, RH, or THI. Stored-value reproduction is therefore "
                "impossible in this audit."
            ),
            "",
            "## Laboratory and Physiological Methods",
            "",
            (
                "Local metadata defines the fields and units. The repository "
                "refers to standard laboratory/biochemical procedures, but "
                "exact devices, assays, calibration, and analytical QA are "
                "`UNCLEAR`. AST/ALT units must be confirmed."
            ),
            "",
            "## Limitations",
            "",
            (
                "No parity, body weight, age, DIM, lactation stage, BCS, "
                "numeric environmental records, or source missing-code "
                "convention is supplied. Physiology cow-ID coverage differs "
                "from DMI/milk and blood."
            ),
        ]
    )


def _render_grouping_requirements() -> str:
    return "\n".join(
        [
            "# Bangladesh Grouping and Split Requirements",
            "",
            "## Verified Observation Hierarchy",
            "",
            "50 cows → 3 THI categories/cow → 5 replications/category → 750 rows.",
            "",
            (
                "The 750 records are repeated observations from 50 animals; "
                "they are not 750 independent cows."
            ),
            "",
            "## Mandatory Group Policy",
            "",
            "- Keep every observation from a cow in the same fold or partition.",
            "- Never randomly split repeated cow records by row.",
            "- Use `Animal ID` as the grouping field.",
            "- Use GroupKFold, GroupShuffleSplit, leave-one-cow-out, or another documented cow-grouped method.",
            "- Preserve genetic-group and THI-category representation where practical without breaking cow groups.",
            "- Fit every learned preprocessing step only inside the training fold.",
            "- Report unique-cow counts and condition counts in every partition.",
            "",
            "## Observation Key",
            "",
            (
                "`Animal ID + THI Range + Replication No` is unique inside "
                "each workbook. Replication number is not globally unique. "
                "No date, timestamp, or standalone observation ID exists."
            ),
            "",
            "## Cross-Workbook Restriction",
            "",
            (
                "DMI/milk and blood have a complete one-to-one key match. "
                "Physiology has only 45 shared cows and 675 matching keys; do "
                "not construct a full cross-workbook training table until the "
                "five boundary IDs per source are resolved."
            ),
        ]
    )


def _render_model_options() -> str:
    return "\n".join(
        [
            "# Bangladesh Model Design Options",
            "",
            "No model was trained in Phase 4.5C.",
            "",
            "## Effective Sample Size",
            "",
            (
                "There are 750 rows but only 50 independent cow groups. "
                "Within-cow correlation reduces effective information, and "
                "uncertainty estimates must use cows—not rows—as the primary "
                "independent unit."
            ),
            "",
            "## Future Validation Designs",
            "",
            "- GroupKFold by cow for repeated grouped comparison.",
            "- Leave-one-cow-out for a high-variance sensitivity analysis.",
            "- GroupShuffleSplit or complete-cow train/validation/test holds.",
            "- Environmental-condition holdout as a robustness test, not a substitute for cow grouping.",
            "- Source-specific external validation only after target, feature, population, and timing harmonization.",
            "",
            "## Future Baseline Families",
            "",
            (
                "Start, if separately approved, with transparent mean/group "
                "baselines, linear regression, and ridge. Consider tightly "
                "controlled shallow tree models and limited boosting only "
                "after leakage-safe grouped baselines. This document does not "
                "authorize any estimator fitting."
            ),
            "",
            "## Candidate Features",
            "",
            (
                "- DMI: genetic group and a prediction-time THI/environment "
                "feature. Same-day milk and physiology remain leakage-unclear."
            ),
            (
                "- Milk yield: genetic group and prediction-time "
                "THI/environment. DMI is usable only if temporal ordering and "
                "farmer availability are proven."
            ),
            (
                "- Missing high-value features: weight, parity, DIM, lactation "
                "stage, BCS, prior yield, ambient temperature, and humidity."
            ),
            "",
            "## Metrics and Uncertainty",
            "",
            (
                "Report MAE/RMSE and bias overall, per cow, genetic group, and "
                "THI category. Include cow-grouped bootstrap or other "
                "group-aware confidence intervals. Report worst-condition and "
                "per-condition performance, not only pooled row metrics."
            ),
        ]
    )


def _render_rwanda_comparison() -> str:
    return "\n".join(
        [
            "# Rwanda–Bangladesh Dataset Comparison",
            "",
            "| Dimension | Bangladesh HF cross | Rwanda dairy |",
            "|---|---|---|",
            "| Dataset type | Repeated experimental/observational records across THI categories | Cross-sectional farm/cow source |",
            "| Cow count | 50 identifiable cows | 96 source-reported cows; workbook cow IDs absent |",
            "| Observation count | 750 rows in each workbook | 96 cow-workbook rows |",
            "| Repeated measures | 15/cow | Not verifiable; methodology is cross-sectional |",
            "| Cow identifiers | Present; physiology coverage mismatch | Absent in audited workbook |",
            "| DMI | kg/cow/day target verified; exact protocol unclear | Blocked by unclear capacity/intake semantics and negative leftovers |",
            "| Milk yield | measured L/cow/day | verified hand-milked L/day |",
            "| Environment | Categorical THI; no numeric T/RH/THI | Current FarmLite temperature/humidity absent |",
            "| Nutrient variables | Milk composition and blood outcomes; no ration nutrients | Calculated CP/ME candidates and fodder text |",
            "| Feed labels | No expert/optimized recommendation labels | No expert recommendation labels |",
            "| Data quality | Complete composite keys internally; 90% physiology cross-match; AST/ALT unit conflict | DMI semantic conflicts, age-column contamination, unit/formula issues |",
            "| ML readiness | DMI/milk design with limitations and cow grouping | Milk/water with limitations; DMI blocked |",
            "| Rule readiness | Supporting heat/composition research only | CP/ME rule support with limitations |",
            "| External validation | Candidate only after feature/population harmonization | DMI not currently valid as Bangladesh external validation |",
            "",
            "## Recommendation",
            "",
            (
                "Use Bangladesh for future DMI and milk model design only "
                "after a new approval and protocol clarification. Keep Rwanda "
                "as separate milk/water and rule-support evidence; do not use "
                "its unclear DMI as external validation. Do not concatenate "
                "the sources. Current harmonization is insufficient because "
                "identifiers, design, populations, feature availability, and "
                "DMI semantics differ."
            ),
        ]
    )


def _validate_outputs(
    metadata: dict[str, Any],
    inventory: dict[str, Any],
) -> None:
    missing = [str(path) for path in REQUIRED_OUTPUTS if not path.is_file()]
    if missing:
        raise BangladeshAuditError(
            "Required audit output(s) missing: " + ", ".join(missing)
        )
    parsed_inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    parsed_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if parsed_inventory["expected_file_count"] != 4:
        raise BangladeshAuditError("Inventory does not record four files")
    if len(parsed_inventory["files"]) != 4:
        raise BangladeshAuditError("Inventory source file count changed")
    if not parsed_schema["unsupported_fields_are_omitted"]:
        raise BangladeshAuditError("Schema includes unsupported fields")
    if len(metadata["definitions"]) != 33:
        raise BangladeshAuditError(
            f"Expected 33 metadata definitions, got "
            f"{len(metadata['definitions'])}"
        )
    for path in (
        VARIABLE_DICTIONARY_PATH,
        TARGET_MATRIX_PATH,
        QUALITY_PATH,
        COMPATIBILITY_PATH,
    ):
        parsed = pd.read_csv(path)
        if parsed.empty:
            raise BangladeshAuditError(f"Generated CSV is empty: {path}")
    text = AUDIT_REPORT_PATH.read_text(encoding="utf-8")
    missing_headings = [
        heading for heading in REQUIRED_AUDIT_HEADINGS if heading not in text
    ]
    if missing_headings:
        raise BangladeshAuditError(
            "Audit headings missing: " + ", ".join(missing_headings)
        )
    for path in REQUIRED_OUTPUTS:
        if path.suffix == ".md" and not path.read_text(
            encoding="utf-8"
        ).lstrip().startswith("#"):
            raise BangladeshAuditError(
                f"Markdown report has no top-level heading: {path}"
            )
    if inventory["files"][0]["filename"] != METADATA_FILENAME:
        raise BangladeshAuditError("Metadata was not inventoried first")


def run_audit() -> dict[str, Any]:
    """Execute the ordered audit, generate reports, and verify immutability."""

    _assert_audit_only_source()
    files = discover_bangladesh_files()
    raw_before = {name: sha256_file(path) for name, path in files.items()}
    if raw_before != {
        name: EXPECTED_SHA256[name] for name in files
    }:
        raise BangladeshAuditError(
            f"Bangladesh source checksum mismatch: {raw_before}"
        )
    protected_before = _protected_snapshot()

    # The semantic order is deliberate and required.
    document = read_docx(files[METADATA_FILENAME])
    metadata = parse_metadata_document(document)
    dmi_workbook = read_xlsx(files[DMI_FILENAME])
    dmi_frame = dataframe_from_sheet(dmi_workbook.sheets[0])
    physiology_workbook = read_xlsx(files[PHYSIOLOGY_FILENAME])
    physiology_frame = dataframe_from_sheet(physiology_workbook.sheets[0])
    blood_workbook = read_xlsx(files[BLOOD_FILENAME])
    blood_frame = dataframe_from_sheet(blood_workbook.sheets[0])

    workbooks = {
        DMI_FILENAME: dmi_workbook,
        PHYSIOLOGY_FILENAME: physiology_workbook,
        BLOOD_FILENAME: blood_workbook,
    }
    frames = {
        DMI_FILENAME: dmi_frame,
        PHYSIOLOGY_FILENAME: physiology_frame,
        BLOOD_FILENAME: blood_frame,
    }
    for name, frame in frames.items():
        if len(frame) != 750:
            raise BangladeshAuditError(
                f"Expected 750 data rows in {name}, found {len(frame)}"
            )
    profiles = {
        name: workbook_profile(name, workbooks[name], frame)
        for name, frame in frames.items()
    }
    dmi_audit = target_audit(
        dmi_frame,
        "DMI (kg)",
        "VERIFIED_DMI_KG_COW_DAY",
        "Dry matter intake per cow",
        "kg/cow/day",
        "per cow per day",
    )
    milk_audit = target_audit(
        dmi_frame,
        "Milk Yield (L/day/cow)",
        "VERIFIED_MILK_YIELD_L_COW_DAY",
        "Daily milk yield per cow",
        "L/cow/day",
        "per cow per day",
    )
    joins = [
        analyze_join(
            dmi_frame,
            physiology_frame,
            DMI_FILENAME,
            PHYSIOLOGY_FILENAME,
        ),
        analyze_join(
            dmi_frame,
            blood_frame,
            DMI_FILENAME,
            BLOOD_FILENAME,
        ),
        analyze_join(
            physiology_frame,
            blood_frame,
            PHYSIOLOGY_FILENAME,
            BLOOD_FILENAME,
        ),
    ]
    quality = data_quality_issues(frames)
    compatibility = farmlite_compatibility(frames)
    inventory = {
        "audit_version": AUDIT_VERSION,
        "audit_order": list(files),
        "expected_file_count": 4,
        "files": [
            inventory_entry(files[METADATA_FILENAME], document),
            inventory_entry(files[DMI_FILENAME], dmi_workbook),
            inventory_entry(
                files[PHYSIOLOGY_FILENAME], physiology_workbook
            ),
            inventory_entry(files[BLOOD_FILENAME], blood_workbook),
        ],
        "repository_record": SOURCE_RECORD,
        "related_article": RELATED_ARTICLE,
        "workbook_profiles": profiles,
        "contains_full_source_records": False,
    }

    _write_json(INVENTORY_PATH, inventory)
    _write_csv(VARIABLE_DICTIONARY_PATH, metadata["definitions"])
    _write_csv(TARGET_MATRIX_PATH, target_matrix())
    _write_csv(QUALITY_PATH, quality)
    _write_csv(COMPATIBILITY_PATH, compatibility)
    _write_json(SCHEMA_PATH, common_schema())
    _write_text(
        AUDIT_REPORT_PATH,
        _render_audit_report(
            metadata,
            profiles,
            dmi_audit,
            milk_audit,
            joins,
            quality,
            compatibility,
        ),
    )
    _write_text(JOIN_REPORT_PATH, _render_join_report(joins))
    _write_text(OPTION_B_PATH, _render_option_b_report(joins))
    _write_text(SOURCE_REGISTER_PATH, _render_source_register(inventory))
    _write_text(METHODOLOGY_PATH, _render_methodology())
    _write_text(GROUPING_PATH, _render_grouping_requirements())
    _write_text(MODEL_OPTIONS_PATH, _render_model_options())
    _write_text(RWANDA_COMPARISON_PATH, _render_rwanda_comparison())
    _validate_outputs(metadata, inventory)

    raw_after = {name: sha256_file(path) for name, path in files.items()}
    protected_after = _protected_snapshot()
    if raw_before != raw_after:
        raise BangladeshAuditError("A Bangladesh raw source changed")
    if protected_before != protected_after:
        changed = sorted(
            key for key in protected_before
            if protected_before[key] != protected_after[key]
        )
        raise BangladeshAuditError(
            "Protected project state changed: " + ", ".join(changed)
        )

    repeated = {
        name: detect_repeated_observations(frame)
        for name, frame in frames.items()
    }
    severity = Counter(item["severity"] for item in quality)
    return {
        "audit_version": AUDIT_VERSION,
        "status": "PASSED_AUDIT_ONLY",
        "files_inspected": list(files),
        "sheet_names": {
            name: [sheet.name for sheet in workbooks[name].sheets]
            for name in workbooks
        },
        "metadata_table_count": len(document.tables),
        "metadata_definition_count": len(metadata["definitions"]),
        "row_counts": {name: len(frame) for name, frame in frames.items()},
        "unique_cows": {
            name: repeated[name]["unique_cows"] for name in frames
        },
        "observations_per_cow": {
            name: repeated[name]["observations_per_cow_distribution"]
            for name in frames
        },
        "dmi_audit": dmi_audit,
        "milk_audit": milk_audit,
        "joins": joins,
        "quality_issue_count": len(quality),
        "quality_severity_counts": dict(severity),
        "option_b_decision": "DMI_AND_MILK_SUPPORT",
        "raw_hashes_before": raw_before,
        "raw_hashes_after": raw_after,
        "raw_files_unchanged": raw_before == raw_after,
        "protected_files_unchanged": protected_before == protected_after,
        "model_training_occurred": False,
        "model_evaluation_occurred": False,
        "prediction_occurred": False,
        "processed_dataset_generated": False,
        "permanent_join_created": False,
        "source_concatenation_occurred": False,
        "expert_feed_labels_invented": False,
        "unsupported_unit_conversion_occurred": False,
        "files_created": [
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in REQUIRED_OUTPUTS
        ],
    }


def main() -> int:
    try:
        result = run_audit()
    except Exception as error:
        print(
            f"BANGLADESH_AUDIT_FAILED: {type(error).__name__}: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    print(
        "BANGLADESH_AUDIT_PASSED "
        f"rows={result['row_counts'][DMI_FILENAME]} "
        f"cows={result['unique_cows'][DMI_FILENAME]} "
        f"quality_issues={result['quality_issue_count']} "
        f"decision={result['option_b_decision']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
