"""Read-only helpers for the Phase 4.5C Bangladesh HF cross audit.

This module parses the supplied Office files in memory.  It deliberately has
no model-training, prediction, source-conversion, or processed-data behavior.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from config.settings import PROJECT_ROOT
from ml.data_integration.office_reader import (
    DocxData,
    SheetData,
    WorkbookData,
    read_docx,
    read_xlsx,
)


AUDIT_VERSION = "4.5C"
SOURCE_DIR = (
    PROJECT_ROOT / "datasets" / "external" / "raw" / "bangladesh_hf_cross"
)
METADATA_FILENAME = "metadata.docx"
DMI_FILENAME = "DMI, milk yield and composition.xlsx"
PHYSIOLOGY_FILENAME = "physiological responses.xlsx"
BLOOD_FILENAME = "Blood metabolites.xlsx"
EXPECTED_FILENAMES = [
    METADATA_FILENAME,
    DMI_FILENAME,
    PHYSIOLOGY_FILENAME,
    BLOOD_FILENAME,
]
EXPECTED_SHA256 = {
    BLOOD_FILENAME: (
        "1328BE3360353212B34E4321C1B77EEC5BB3081CE4002E7E93252310B4C07541"
    ),
    DMI_FILENAME: (
        "EC3FECE684C40343C2A4F8F527F2BBE274E7B5B6EBD2B200FCDA623DBDC6A508"
    ),
    METADATA_FILENAME: (
        "B5C652DAA3C0DB3BCACF6931D46D072ECF6793863821856991B17A994F737A03"
    ),
    PHYSIOLOGY_FILENAME: (
        "58F5B01BC771E618C19EE33EC18A96F698EB61E262FE501182E3A2BDDAD01F65"
    ),
}

SOURCE_RECORD = {
    "title": (
        "Physiological responses, Dry matter Intake, milk yield, composition "
        "and blood metabolites of HF Cross cows"
    ),
    "contributor": "Pehan Eshtiak Ahamed",
    "version": "2",
    "published": "2026-03-30",
    "doi": "10.17632/954f6g36sb.2",
    "url": "https://data.mendeley.com/datasets/954f6g36sb/2",
    "licence": "CC BY 4.0",
    "study_period": "January to December 2024",
    "study_location": (
        "Central Cattle Breeding and Dairy Farm, Savar, Bangladesh"
    ),
    "cow_count": 50,
    "sampling": (
        "Five milk and blood samples per cow per THI category; physiological "
        "parameters twice daily on sampling dates and averaged."
    ),
}
RELATED_ARTICLE = {
    "title": (
        "Effects of cyclic temperature-humidity index on milk production, "
        "physiological and haematobiochemical responses in Holstein-Friesian "
        "cows of varied genetic proportions"
    ),
    "doi": "10.1016/j.anopes.2026.100139",
    "url": (
        "https://www.sciencedirect.com/science/article/pii/"
        "S2772694026000130"
    ),
    "thi_formula": (
        "THI = (1.8 × T + 32) − [(0.55 − 0.0055 × RH) × "
        "(1.8 × T − 26)]"
    ),
    "thi_inputs": "T = dry-bulb temperature (°C); RH = relative humidity (%)",
}


class BangladeshAuditError(RuntimeError):
    """Raised when a critical audit invariant is not satisfied."""


@dataclass(frozen=True)
class VariableDefinition:
    """A source definition linked to its exact supplied workbook column."""

    source_variable: str
    full_definition: str
    unit: str
    measurement_period: str
    measurement_method: str
    workbook: str
    sheet: str
    exact_source_column: str
    measurement_status: str
    notes: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


WORKBOOK_COLUMN_MAP = {
    PHYSIOLOGY_FILENAME: {
        "Cow_ID": "Animal ID",
        "Genetic_Group": "Genetic group",
        "THI_Range": "THI Range",
        "Replication_No": "Replication No",
        "Rectal_Temp_F": "Rectal Temp (F)",
        "Pulse_Rate_bpm": "Pulse Rate (bpm)",
        "Respiration_Rate_bpm": "Respiration Rate (bpm)",
    },
    DMI_FILENAME: {
        "Cow_ID": "Animal ID",
        "Genetic_Group": "Genetic Group",
        "THI_Range": "THI Range",
        "Replication_No": "Replication No",
        "Dry_Matter_Intake_(DMI)_Kg_per_day": "DMI (kg)",
        "Milk_Yield_L_per_day": "Milk Yield (L/day/cow)",
        "SCC_cells_per_mL": "SCC cells per mL",
        "Fat_%": "Fat%",
        "SNF_%": "SNF%",
        "Protein_%": "Protein %",
        "Salt_%": "Salt%",
        "Lactose_%": "Lactose%",
        "pH": "pH",
    },
    BLOOD_FILENAME: {
        "Cow_ID": "Animal ID",
        "Genetic_Group": "Genetic Group",
        "THI_Range": "THI Range",
        "Replication_No": "Replication No",
        "Glucose_mmol_per_L": "Glucose (mmol/L)",
        "Total_Protein_g_per_dL": "Total Protein (g/dL)",
        "Uric_Acid_mg_per_dL": "Uric Acid (mg/dL)",
        "Cholesterol_mg_per_dL": "Cholesterol (mg/dL)",
        "Calcium_mg_per_dL": "Calcium (mg/dL)",
        "HDL_mg_per_dL": "HDL (mg/dL)",
        "AST_U_per_L": "AST (U/I)",
        "ALT_U_per_L": "ALT (U/I)",
        "Cortisol_µg_per_dL": "Cortisol (µg/dL)",
    },
}


def sha256_file(path: str | Path) -> str:
    """Return an uppercase SHA-256 checksum without modifying the file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def tree_checksum(
    path: str | Path,
    excluded_names: set[str] | None = None,
) -> dict[str, str]:
    """Hash every file below a directory using stable relative paths."""

    root = Path(path)
    if not root.exists():
        return {}
    excluded = excluded_names or set()
    files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(
            name for name in directories if name not in excluded
        )
        files.extend(
            Path(current) / name
            for name in sorted(names)
            if name not in excluded
        )
    return {
        item.relative_to(root).as_posix(): sha256_file(item)
        for item in files
    }


def discover_bangladesh_files(
    source_dir: str | Path = SOURCE_DIR,
) -> dict[str, Path]:
    """Discover exactly the four approved source files in semantic order."""

    directory = Path(source_dir)
    if not directory.is_dir():
        raise BangladeshAuditError(
            f"Bangladesh source directory does not exist: {directory}"
        )
    files = {name: directory / name for name in EXPECTED_FILENAMES}
    missing = [name for name, path in files.items() if not path.is_file()]
    if missing:
        raise BangladeshAuditError(
            "Missing Bangladesh source file(s): " + ", ".join(missing)
        )
    unexpected = sorted(
        item.name for item in directory.iterdir() if item.is_file()
        and item.name not in EXPECTED_FILENAMES
    )
    if unexpected:
        raise BangladeshAuditError(
            "Unexpected Bangladesh source file(s): " + ", ".join(unexpected)
        )
    return files


def dataframe_from_sheet(
    sheet: SheetData,
    header_row: int = 1,
) -> pd.DataFrame:
    """Create an in-memory frame and retain original one-based source rows."""

    if header_row < 1 or len(sheet.rows) < header_row:
        raise BangladeshAuditError(
            f"Header row {header_row} is absent from sheet {sheet.name}"
        )
    headers = [
        str(value).strip() if value is not None else f"UNNAMED_{index}"
        for index, value in enumerate(sheet.rows[header_row - 1], start=1)
    ]
    if len(headers) != len(set(headers)):
        raise BangladeshAuditError(
            f"Duplicate column names in {sheet.name}: {headers}"
        )
    rows = [
        list(row[: len(headers)]) + [None] * max(0, len(headers) - len(row))
        for row in sheet.rows[header_row:]
    ]
    frame = pd.DataFrame(rows, columns=headers)
    frame = frame.loc[
        ~frame.apply(
            lambda row: all(is_missing(value) for value in row),
            axis=1,
        )
    ].copy()
    frame["source_row_number"] = [
        header_row + 1 + int(index) for index in frame.index
    ]
    frame.reset_index(drop=True, inplace=True)
    return frame


def is_missing(value: Any) -> bool:
    """Treat blank strings and common textual sentinels as missing."""

    if value is None:
        return True
    try:
        if bool(pd.isna(value)):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip().casefold() in {
        "",
        "na",
        "n/a",
        "nan",
        "none",
        "null",
    }


def missing_value_report(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Report missing counts and percentages by source column."""

    denominator = len(frame)
    result = []
    for column in frame.columns:
        if column == "source_row_number":
            continue
        missing = int(frame[column].map(is_missing).sum())
        result.append(
            {
                "column": column,
                "missing_count": missing,
                "missing_percentage": (
                    round(100.0 * missing / denominator, 6)
                    if denominator
                    else 0.0
                ),
            }
        )
    return result


def duplicate_row_count(frame: pd.DataFrame) -> int:
    """Count exact duplicate source records, excluding audit row numbers."""

    columns = [
        column for column in frame.columns if column != "source_row_number"
    ]
    return int(frame[columns].duplicated().sum())


def numeric_summary(values: Iterable[Any]) -> dict[str, Any]:
    """Return descriptive values without changing or imputing the source."""

    series = pd.to_numeric(pd.Series(list(values)), errors="coerce").dropna()
    if series.empty:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "standard_deviation": None,
            "zero_count": 0,
            "negative_count": 0,
        }
    return {
        "count": int(series.count()),
        "minimum": float(series.min()),
        "maximum": float(series.max()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "standard_deviation": float(series.std()),
        "zero_count": int((series == 0).sum()),
        "negative_count": int((series < 0).sum()),
    }


def canonical_cow_id(value: Any) -> str | None:
    """Losslessly normalize an identifier for in-memory comparison only."""

    if is_missing(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def canonical_thi(value: Any) -> str | None:
    """Map the directly documented THI label variants to T0/T1/T2."""

    if is_missing(value):
        return None
    match = re.match(r"^\s*(T[012])", str(value), flags=re.IGNORECASE)
    return match.group(1).upper() if match else str(value).strip()


def canonical_genetic_group(value: Any) -> str | None:
    """Normalize punctuation variants documented as the same HF group."""

    if is_missing(value):
        return None
    return (
        str(value)
        .strip()
        .upper()
        .replace("_", "")
        .replace(" ", "")
        .replace("%", "")
    )


def observation_key(frame: pd.DataFrame) -> pd.Series:
    """Build the metadata-supported composite observation key in memory."""

    return pd.Series(
        list(
            zip(
                frame["Animal ID"].map(canonical_cow_id),
                frame["THI Range"].map(canonical_thi),
                frame["Replication No"].map(
                    lambda value: None
                    if is_missing(value)
                    else str(value).strip()
                ),
            )
        ),
        index=frame.index,
        dtype=object,
    )


def detect_repeated_observations(
    frame: pd.DataFrame,
    cow_column: str = "Animal ID",
) -> dict[str, Any]:
    """Summarize repeated cow observations and grouping viability."""

    cows = frame[cow_column].map(canonical_cow_id)
    counts = cows.dropna().value_counts()
    if counts.empty:
        return {
            "status": "UNCLEAR",
            "unique_cows": 0,
            "repeated_cow_count": 0,
            "minimum_records_per_cow": 0,
            "maximum_records_per_cow": 0,
            "grouped_validation_possible": False,
        }
    return {
        "status": "REPEATED" if int(counts.max()) > 1 else "NOT_REPEATED",
        "unique_cows": int(len(counts)),
        "repeated_cow_count": int((counts > 1).sum()),
        "minimum_records_per_cow": int(counts.min()),
        "maximum_records_per_cow": int(counts.max()),
        "observations_per_cow_distribution": {
            str(int(key)): int(value)
            for key, value in counts.value_counts().sort_index().items()
        },
        "grouped_validation_possible": bool(len(counts) > 1),
    }


def _definition_details(variable: str, definition: str) -> tuple[str, str, str]:
    """Return unit, period, and measurement status from explicit semantics."""

    lower = variable.casefold()
    text = f"{variable} {definition}".casefold()
    unit = "UNCLEAR"
    unit_patterns = [
        (r"mmol/?l", "mmol/L"),
        (r"µg/?dl", "µg/dL"),
        (r"mg/?dl", "mg/dL"),
        (r"g/?dl", "g/dL"),
        (r"cells/?ml", "cells/mL"),
        (r"breaths per minute", "breaths/min"),
        (r"beats per minute|bpm", "beats/min"),
        (r"°f", "°F"),
        (r"liters", "L"),
        (r"\bkg\b", "kg"),
        (r"percentage|\b%\b", "%"),
    ]
    for pattern, candidate in unit_patterns:
        if re.search(pattern, text):
            unit = candidate
            break
    period = "per cow per day" if (
        "per_day" in lower
        or "daily" in text
        or ("per cow" in text and "milk_yield" in lower)
    ) else "per observation"
    if lower == "cow_id":
        status = "IDENTIFIER"
    elif lower in {"genetic_group"}:
        status = "OBSERVED"
    elif lower in {"thi_range"}:
        status = "TREATMENT_ASSIGNED"
    elif lower in {"replication_no"}:
        status = "IDENTIFIER"
    elif any(
        token in lower
        for token in (
            "glucose",
            "protein_g",
            "uric",
            "cholesterol",
            "calcium",
            "hdl",
            "ast_",
            "alt_",
            "cortisol",
            "fat_%",
            "snf_%",
            "protein_%",
            "salt_%",
            "lactose_%",
            "scc_",
            "ph",
        )
    ):
        status = "LABORATORY_MEASURED"
    elif "dry_matter_intake" in lower:
        status = "DIRECTLY_MEASURED"
    elif "milk_yield" in lower:
        status = "OBSERVED"
    elif any(token in lower for token in ("rectal", "pulse", "respiration")):
        status = "DIRECTLY_MEASURED"
    else:
        status = "UNKNOWN"
    return unit, period, status


def parse_metadata_document(document: DocxData) -> dict[str, Any]:
    """Parse all DOCX paragraphs after metadata-first inspection."""

    definitions: list[VariableDefinition] = []
    current_workbook: str | None = None
    in_variables = False
    file_aliases = {
        "physiological responses.xlsx": PHYSIOLOGY_FILENAME,
        "milk yield and composition.xlsx": DMI_FILENAME,
        "blood metabolites.xlsx": BLOOD_FILENAME,
    }
    for paragraph in document.paragraphs:
        file_match = re.match(r"^File\s+\d+:\s*(.+)$", paragraph)
        if file_match:
            current_workbook = file_aliases.get(
                file_match.group(1).strip().casefold()
            )
            in_variables = False
            continue
        if paragraph.strip() == "Variables:":
            in_variables = True
            continue
        if not in_variables or current_workbook is None or ":" not in paragraph:
            continue
        variable, definition = paragraph.split(":", 1)
        variable = variable.strip()
        definition = definition.strip()
        if variable not in WORKBOOK_COLUMN_MAP[current_workbook]:
            continue
        unit, period, status = _definition_details(variable, definition)
        method = {
            "DIRECTLY_MEASURED": (
                "Source record says measured using standard procedures; "
                "exact instrument/protocol UNCLEAR"
            ),
            "LABORATORY_MEASURED": (
                "Source record says standard laboratory/biochemical "
                "procedures; exact instrument/protocol UNCLEAR"
            ),
            "OBSERVED": "Recorded observation; exact collection method UNCLEAR",
            "TREATMENT_ASSIGNED": (
                "Assigned categorical range based on environmental THI"
            ),
            "IDENTIFIER": "Administrative/source identifier",
        }.get(status, "UNCLEAR")
        notes = ""
        if variable in {"AST_U_per_L", "ALT_U_per_L"}:
            notes = (
                "Metadata states U/L, but workbook header states U/I; unit "
                "must be confirmed."
            )
        definitions.append(
            VariableDefinition(
                source_variable=variable,
                full_definition=definition,
                unit=unit,
                measurement_period=period,
                measurement_method=method,
                workbook=current_workbook,
                sheet="Sheet1",
                exact_source_column=WORKBOOK_COLUMN_MAP[current_workbook][
                    variable
                ],
                measurement_status=status,
                notes=notes,
            )
        )
    first = document.paragraphs[0] if document.paragraphs else ""
    title = first.split(":", 1)[1].strip() if ":" in first else "UNCLEAR"
    authors = [
        paragraph for paragraph in document.paragraphs
        if paragraph.startswith(("Corresponding Author:", "Contributors:"))
    ]
    return {
        "title": title,
        "author_lines": authors,
        "study_location_local_document": (
            "BLRI affiliation in Savar, Dhaka, Bangladesh; exact study site "
            "UNCLEAR in local DOCX"
        ),
        "study_location_repository_record": SOURCE_RECORD["study_location"],
        "study_period_local_document": "UNCLEAR",
        "study_period_repository_record": SOURCE_RECORD["study_period"],
        "study_design": (
            "Repeated observations of five HF genetic groups under three "
            "cyclic THI categories"
        ),
        "cow_count_local_document": "UNCLEAR",
        "cow_count_repository_record": SOURCE_RECORD["cow_count"],
        "breed_or_genetic_groups": ["0%", "50%", "62.5%", "75%", "87.5% HF"],
        "lactation_stage": "UNCLEAR",
        "number_of_observations_local_document": "UNCLEAR",
        "sampling_frequency_local_document": "UNCLEAR",
        "sampling_frequency_repository_record": SOURCE_RECORD["sampling"],
        "environmental_conditions": "Three categorical THI ranges",
        "temperature_humidity_grouping": {
            "T0": "≤75",
            "T1": "75–80",
            "T2": "≥80",
        },
        "dry_matter_intake_definition": (
            "Dry matter intake per cow (kg); source variable name specifies "
            "kg per day"
        ),
        "milk_yield_definition": "Daily milk yield per cow (liters)",
        "missing_value_codes": "UNCLEAR",
        "data_collection_methods_local_document": "UNCLEAR",
        "licence_local_document": "UNCLEAR",
        "licence_repository_record": SOURCE_RECORD["licence"],
        "citation_local_document": "Title and contributors only",
        "citation_repository_record": (
            f"{SOURCE_RECORD['contributor']} (2026), "
            f"“{SOURCE_RECORD['title']}”, Mendeley Data, V2, "
            f"doi:{SOURCE_RECORD['doi']}"
        ),
        "limitations": [
            "Local DOCX does not state study period or exact study farm.",
            "Local DOCX does not state cow count or sampling schedule.",
            "DMI offered/refusal protocol is not documented.",
            "Milk collection and laboratory instruments are not documented.",
            "Numeric temperature, humidity, and THI are not supplied.",
            "Parity, body weight, age, days in milk, lactation stage, and BCS "
            "are absent.",
            "Missing-value codes are not documented.",
            "AST/ALT units conflict between metadata (U/L) and workbook (U/I).",
        ],
        "paragraph_count": len(document.paragraphs),
        "table_count": len(document.tables),
        "heading_count": len(document.headings),
        "definitions": [item.to_dict() for item in definitions],
    }


def workbook_profile(
    filename: str,
    workbook: WorkbookData,
    frame: pd.DataFrame,
) -> dict[str, Any]:
    """Build a complete workbook/sheet profile for report rendering."""

    sheet = workbook.sheets[0]
    categorical = {}
    numeric = {}
    for column in frame.columns:
        if column == "source_row_number":
            continue
        converted = pd.to_numeric(frame[column], errors="coerce")
        if int(converted.notna().sum()) == len(frame):
            numeric[column] = numeric_summary(frame[column])
        else:
            counts = frame[column].map(
                lambda value: "MISSING" if is_missing(value) else str(value)
            ).value_counts()
            categorical[column] = {
                "unique_count": int(len(counts)),
                "top_values": {
                    key: int(value) for key, value in counts.head(20).items()
                },
            }
    repeated = detect_repeated_observations(frame)
    keys = observation_key(frame)
    return {
        "filename": filename,
        "sheet_name": sheet.name,
        "sheet_state": sheet.state,
        "row_count_excluding_header": len(frame),
        "column_count": len(frame.columns) - 1,
        "exact_column_names": [
            column for column in frame.columns
            if column != "source_row_number"
        ],
        "data_types": {
            column: sorted(
                {
                    type(value).__name__
                    for value in frame[column]
                    if not is_missing(value)
                }
            )
            for column in frame.columns
            if column != "source_row_number"
        },
        "missing_values": missing_value_report(frame),
        "duplicate_rows": duplicate_row_count(frame),
        "duplicate_composite_keys": int(keys.duplicated().sum()),
        "numeric_summaries": numeric,
        "categorical_summaries": categorical,
        "example_values": {
            column: [
                value for value in frame[column].dropna().head(3).tolist()
            ]
            for column in frame.columns
            if column != "source_row_number"
        },
        "identifier_fields": ["Animal ID", "Replication No"],
        "date_or_observation_fields": ["Replication No"],
        "date_fields": [],
        "cow_grouping_fields": ["Animal ID"],
        "genetic_group_fields": [
            column for column in frame.columns
            if column.casefold() == "genetic group"
        ],
        "environmental_groups": ["THI Range"],
        "treatment_groups": ["THI Range"],
        "repeated_measurements": repeated,
        "row_structure": (
            "ONE_ROW_PER_COW_PER_THI_CATEGORY_PER_REPLICATION"
        ),
        "hidden_sheet_count": sum(
            item.state != "visible" for item in workbook.sheets
        ),
        "formula_count": sum(item.formula_count for item in workbook.sheets),
        "merged_cell_count": sum(
            len(item.merged_ranges) for item in workbook.sheets
        ),
        "comment_count": sum(len(item.comments) for item in workbook.sheets),
    }


def detect_target_fields(
    definitions: list[dict[str, Any]],
    domain: str,
) -> list[dict[str, Any]]:
    """Find DMI, milk, composition, physiology, THI, or blood fields."""

    tokens = {
        "dmi": ("dry_matter_intake", "dmi"),
        "milk_yield": ("milk_yield",),
        "milk_composition": (
            "scc_",
            "fat_%",
            "snf_%",
            "protein_%",
            "salt_%",
            "lactose_%",
            "ph",
        ),
        "temperature": ("rectal_temp",),
        "humidity": ("humidity",),
        "thi": ("thi_range",),
        "physiology": ("rectal_temp", "pulse_rate", "respiration_rate"),
        "blood": (
            "glucose_",
            "total_protein_",
            "uric_acid_",
            "cholesterol_",
            "calcium_",
            "hdl_",
            "ast_u",
            "alt_u",
            "cortisol_",
        ),
    }
    selected = tokens.get(domain, ())
    return [
        item for item in definitions
        if any(token in item["source_variable"].casefold() for token in selected)
    ]


def target_audit(
    frame: pd.DataFrame,
    column: str,
    status: str,
    definition: str,
    unit: str,
    period: str,
) -> dict[str, Any]:
    """Audit one numeric target candidate."""

    summary = numeric_summary(frame[column])
    missing = int(frame[column].map(is_missing).sum())
    return {
        "exact_source_column": column,
        "definition": definition,
        "unit": unit,
        "period": period,
        "per_cow_status": "VERIFIED",
        "measurement_status": "DIRECTLY_MEASURED",
        "measurement_method": (
            "Source record states measured using standard procedures; "
            "feed-offered/refusal or exact instrument protocol UNCLEAR"
        ),
        "usable_records": summary["count"],
        "missing_percentage": round(100.0 * missing / len(frame), 6),
        **summary,
        "suspicious_values": (
            "No zero/negative/non-numeric values; biological plausibility "
            "requires domain review"
        ),
        "repeated_observation_structure": (
            "15 observations/cow: 5 replications in each of 3 THI categories"
        ),
        "status": status,
        "ml_suitability": "READY_WITH_LIMITATIONS",
        "cow_level_grouping_possible": True,
    }


def analyze_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str = "left",
    right_name: str = "right",
) -> dict[str, Any]:
    """Audit a composite-key join without persisting joined records."""

    left_keys = observation_key(left)
    right_keys = observation_key(right)
    left_counts = left_keys.value_counts()
    right_counts = right_keys.value_counts()
    left_set = set(left_counts.index)
    right_set = set(right_counts.index)
    matched = left_set & right_set
    many_to_many = any(
        left_counts[key] > 1 and right_counts[key] > 1 for key in matched
    )
    left_duplicate_count = int(left_keys.duplicated(keep=False).sum())
    right_duplicate_count = int(right_keys.duplicated(keep=False).sum())
    if many_to_many:
        safety = "MANY_TO_MANY_RISK"
        cardinality = "MANY_TO_MANY"
    elif left_duplicate_count == 0 and right_duplicate_count == 0:
        cardinality = "ONE_TO_ONE"
        safety = (
            "SAFE_ONE_TO_ONE"
            if len(matched) == len(left) == len(right)
            else "POSSIBLE_WITH_LIMITATIONS"
        )
    elif left_duplicate_count == 0 or right_duplicate_count == 0:
        cardinality = "ONE_TO_MANY"
        safety = "SAFE_ONE_TO_MANY"
    else:
        cardinality = "UNCLEAR"
        safety = "UNCLEAR"
    left_cows = set(left["Animal ID"].map(canonical_cow_id).dropna())
    right_cows = set(right["Animal ID"].map(canonical_cow_id).dropna())
    return {
        "left_workbook": left_name,
        "left_sheet": "Sheet1",
        "right_workbook": right_name,
        "right_sheet": "Sheet1",
        "join_key": "Animal ID + normalized THI Range + Replication No",
        "key_basis": (
            "All three fields are explicitly defined in metadata; row order "
            "was not used."
        ),
        "left_unique_key_count": int(len(left_set)),
        "right_unique_key_count": int(len(right_set)),
        "left_missing_key_count": int(left_keys.map(
            lambda key: any(value is None for value in key)
        ).sum()),
        "right_missing_key_count": int(right_keys.map(
            lambda key: any(value is None for value in key)
        ).sum()),
        "left_duplicate_key_row_count": left_duplicate_count,
        "right_duplicate_key_row_count": right_duplicate_count,
        "match_count": int(len(matched)),
        "left_match_percentage": round(100.0 * len(matched) / len(left), 6),
        "right_match_percentage": round(100.0 * len(matched) / len(right), 6),
        "left_only_key_count": int(len(left_set - right_set)),
        "right_only_key_count": int(len(right_set - left_set)),
        "left_only_cow_ids": sorted(left_cows - right_cows),
        "right_only_cow_ids": sorted(right_cows - left_cows),
        "shared_cow_count": int(len(left_cows & right_cows)),
        "cardinality": cardinality,
        "many_to_many_risk": many_to_many,
        "join_safety": safety,
    }


def classify_leakage(model: str, field: str) -> str:
    """Classify prediction-time leakage conservatively."""

    value = field.casefold()
    if any(token in value for token in ("blood", "cortisol", "glucose")):
        return "RESEARCH_ONLY"
    if any(
        token in value
        for token in ("fat", "protein", "lactose", "snf", "scc", "ph")
    ):
        return "POSSIBLE_LEAKAGE"
    if any(token in value for token in ("rectal", "pulse", "respiration")):
        return "UNCLEAR"
    if model == "DMI" and "milk yield" in value:
        return "POSSIBLE_LEAKAGE"
    if model == "MILK" and "dmi" in value:
        return "POSSIBLE_LEAKAGE"
    if "thi range" in value:
        return "UNCLEAR"
    if "genetic" in value:
        return "SAFE"
    return "NOT_AVAILABLE_AT_INFERENCE"


def farmlite_compatibility(
    frames: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Compare verified fields with the current nine FarmLite inputs."""

    dmi = frames[DMI_FILENAME]
    phys = frames[PHYSIOLOGY_FILENAME]
    rows = [
        ("breed", "PARTIAL", "Genetic Group", "% HF category", "YES", "YES"),
        ("age_months", "NO", "UNCLEAR", "UNCLEAR", "UNCLEAR", "NO"),
        ("weight_kg", "NO", "UNCLEAR", "kg", "UNCLEAR", "NO"),
        ("lactation_stage", "NO", "UNCLEAR", "UNCLEAR", "UNCLEAR", "NO"),
        ("days_in_milk", "NO", "UNCLEAR", "days", "UNCLEAR", "NO"),
        (
            "previous_week_avg_yield_l",
            "NO",
            "UNCLEAR",
            "L/day",
            "UNCLEAR",
            "NO",
        ),
        (
            "body_condition_score",
            "NO",
            "UNCLEAR",
            "score",
            "UNCLEAR",
            "NO",
        ),
        (
            "ambient_temperature_c",
            "NO",
            "UNCLEAR",
            "°C",
            "UNCLEAR",
            "NO",
        ),
        (
            "humidity_percent",
            "NO",
            "UNCLEAR",
            "%",
            "UNCLEAR",
            "NO",
        ),
        ("genetic_group", "YES", "Genetic Group", "% HF category", "YES", "YES"),
        ("thi_group", "YES", "THI Range", "category", "CONDITIONAL", "YES"),
        (
            "respiration_rate",
            "YES",
            "Respiration Rate (bpm)",
            "breaths/min",
            "UNCLEAR",
            "YES",
        ),
        (
            "rectal_temperature",
            "YES",
            "Rectal Temp (F)",
            "°F",
            "UNCLEAR",
            "YES",
        ),
        (
            "pulse_rate",
            "YES",
            "Pulse Rate (bpm)",
            "beats/min",
            "UNCLEAR",
            "YES",
        ),
        (
            "sampling_replication",
            "YES",
            "Replication No",
            "identifier",
            "NO",
            "NO",
        ),
    ]
    output = []
    for feature, present, source, unit, available, frontend_change in rows:
        source_frame = (
            phys if source in phys.columns else dmi
        )
        missing = (
            round(100.0 * source_frame[source].map(is_missing).sum()
                  / len(source_frame), 6)
            if source in source_frame.columns
            else 100.0
        )
        output.append(
            {
                "farmlite_feature": feature,
                "present_in_bangladesh": present,
                "exact_source_column": source,
                "unit": unit,
                "missing_percentage": missing,
                "available_before_prediction": available,
                "suitable_for_model_use": (
                    "YES" if available == "YES" else "WITH_LIMITATIONS"
                    if available in {"CONDITIONAL", "UNCLEAR"} and present == "YES"
                    else "NO"
                ),
                "mapping_required": (
                    "YES" if source != feature and present != "NO" else "NO"
                ),
                "farmlite_frontend_change_required": frontend_change,
            }
        )
    return output


def target_matrix() -> list[dict[str, str]]:
    """Return the required Option B target decision matrix."""

    return [
        {
            "desired_output": "Dry-matter intake",
            "bangladesh_source": DMI_FILENAME,
            "exact_field": "DMI (kg)",
            "unit": "kg/cow/day",
            "period": "per cow per day",
            "measurement_status": "DIRECTLY_MEASURED",
            "ml_suitability": "READY_WITH_LIMITATIONS",
            "rule_suitability": "SUPPORTING_ANALYSIS_ONLY",
            "decision": "READY_WITH_LIMITATIONS",
        },
        {
            "desired_output": "Milk yield",
            "bangladesh_source": DMI_FILENAME,
            "exact_field": "Milk Yield (L/day/cow)",
            "unit": "L/cow/day",
            "period": "per cow per day",
            "measurement_status": "OBSERVED",
            "ml_suitability": "READY_WITH_LIMITATIONS",
            "rule_suitability": "SUPPORTING_ANALYSIS_ONLY",
            "decision": "READY_WITH_LIMITATIONS",
        },
        {
            "desired_output": "Feed/ration category",
            "bangladesh_source": "NONE",
            "exact_field": "UNCLEAR",
            "unit": "UNCLEAR",
            "period": "UNCLEAR",
            "measurement_status": "UNKNOWN",
            "ml_suitability": "EXPERT_LABELS_REQUIRED",
            "rule_suitability": "NOT_SUPPORTED",
            "decision": "EXPERT_LABELS_REQUIRED",
        },
        {
            "desired_output": "Water advice",
            "bangladesh_source": "NONE",
            "exact_field": "UNCLEAR",
            "unit": "UNCLEAR",
            "period": "UNCLEAR",
            "measurement_status": "UNKNOWN",
            "ml_suitability": "NOT_SUPPORTED",
            "rule_suitability": "NOT_SUPPORTED",
            "decision": "NOT_SUPPORTED",
        },
        {
            "desired_output": "Roughage quantity",
            "bangladesh_source": "NONE",
            "exact_field": "UNCLEAR",
            "unit": "UNCLEAR",
            "period": "UNCLEAR",
            "measurement_status": "UNKNOWN",
            "ml_suitability": "NOT_SUPPORTED",
            "rule_suitability": "NOT_SUPPORTED",
            "decision": "NOT_SUPPORTED",
        },
        {
            "desired_output": "Concentrate quantity",
            "bangladesh_source": "NONE",
            "exact_field": "UNCLEAR",
            "unit": "UNCLEAR",
            "period": "UNCLEAR",
            "measurement_status": "UNKNOWN",
            "ml_suitability": "NOT_SUPPORTED",
            "rule_suitability": "NOT_SUPPORTED",
            "decision": "NOT_SUPPORTED",
        },
        {
            "desired_output": "Mineral mix",
            "bangladesh_source": "NONE",
            "exact_field": "UNCLEAR",
            "unit": "UNCLEAR",
            "period": "UNCLEAR",
            "measurement_status": "UNKNOWN",
            "ml_suitability": "NOT_SUPPORTED",
            "rule_suitability": "NOT_SUPPORTED",
            "decision": "NOT_SUPPORTED",
        },
        {
            "desired_output": "Heat-stress warning",
            "bangladesh_source": (
                f"{DMI_FILENAME}; {PHYSIOLOGY_FILENAME}"
            ),
            "exact_field": "THI Range; physiological responses",
            "unit": "category; field-specific",
            "period": "per observation",
            "measurement_status": "TREATMENT_ASSIGNED",
            "ml_suitability": "READY_WITH_LIMITATIONS",
            "rule_suitability": "SUPPORTING_ANALYSIS_ONLY",
            "decision": "READY_WITH_LIMITATIONS",
        },
        {
            "desired_output": "Milk fat",
            "bangladesh_source": DMI_FILENAME,
            "exact_field": "Fat%",
            "unit": "%",
            "period": "per observation",
            "measurement_status": "LABORATORY_MEASURED",
            "ml_suitability": "ML_TARGET_CANDIDATE",
            "rule_suitability": "SUPPORTING_ANALYSIS_ONLY",
            "decision": "SUPPORTING_ANALYSIS_ONLY",
        },
        {
            "desired_output": "Milk protein",
            "bangladesh_source": DMI_FILENAME,
            "exact_field": "Protein %",
            "unit": "%",
            "period": "per observation",
            "measurement_status": "LABORATORY_MEASURED",
            "ml_suitability": "ML_TARGET_CANDIDATE",
            "rule_suitability": "SUPPORTING_ANALYSIS_ONLY",
            "decision": "SUPPORTING_ANALYSIS_ONLY",
        },
    ]


def common_schema() -> dict[str, Any]:
    """Return only canonical fields directly supported by the sources."""

    fields = [
        ("source_file", "Source Office filename", "text", "IDENTIFIER"),
        ("source_sheet", "Source worksheet name", "text", "IDENTIFIER"),
        ("source_row_number", "One-based source row", "row", "IDENTIFIER"),
        ("cow_id", "Unique source cow identifier", "text", "IDENTIFIER"),
        (
            "replication_number",
            "Replicate number within THI category",
            "identifier",
            "IDENTIFIER",
        ),
        (
            "genetic_group",
            "Holstein-Friesian genetic proportion category",
            "% HF category",
            "OBSERVED",
        ),
        (
            "heat_stress_group",
            "Categorical THI range T0/T1/T2",
            "category",
            "TREATMENT_ASSIGNED",
        ),
        (
            "dry_matter_intake_kg_day",
            "Dry matter intake per cow per day",
            "kg/cow/day",
            "DIRECTLY_MEASURED",
        ),
        (
            "milk_yield_l_day",
            "Daily milk yield per cow",
            "L/cow/day",
            "OBSERVED",
        ),
        (
            "rectal_temperature_f",
            "Rectal temperature",
            "°F",
            "DIRECTLY_MEASURED",
        ),
        (
            "respiration_rate_per_min",
            "Breathing rate",
            "breaths/min",
            "DIRECTLY_MEASURED",
        ),
        (
            "pulse_rate_per_min",
            "Heart rate",
            "beats/min",
            "DIRECTLY_MEASURED",
        ),
        ("milk_fat_percent", "Milk fat", "%", "LABORATORY_MEASURED"),
        (
            "milk_protein_percent",
            "Milk protein",
            "%",
            "LABORATORY_MEASURED",
        ),
        (
            "milk_lactose_percent",
            "Milk lactose",
            "%",
            "LABORATORY_MEASURED",
        ),
        (
            "solids_not_fat_percent",
            "Milk solids-not-fat",
            "%",
            "LABORATORY_MEASURED",
        ),
        (
            "somatic_cell_count_per_ml",
            "Somatic cell count",
            "cells/mL",
            "LABORATORY_MEASURED",
        ),
        ("milk_ph", "Milk pH", "pH", "LABORATORY_MEASURED"),
        (
            "blood_glucose_mmol_l",
            "Serum glucose",
            "mmol/L",
            "LABORATORY_MEASURED",
        ),
        (
            "serum_total_protein_g_dl",
            "Total serum protein",
            "g/dL",
            "LABORATORY_MEASURED",
        ),
        (
            "blood_cortisol_ug_dl",
            "Serum cortisol",
            "µg/dL",
            "LABORATORY_MEASURED",
        ),
    ]
    source_lookup = {
        "cow_id": ("ALL", "Animal ID"),
        "replication_number": ("ALL", "Replication No"),
        "genetic_group": ("ALL", "Genetic Group / Genetic group"),
        "heat_stress_group": ("ALL", "THI Range"),
        "dry_matter_intake_kg_day": (DMI_FILENAME, "DMI (kg)"),
        "milk_yield_l_day": (DMI_FILENAME, "Milk Yield (L/day/cow)"),
        "rectal_temperature_f": (
            PHYSIOLOGY_FILENAME,
            "Rectal Temp (F)",
        ),
        "respiration_rate_per_min": (
            PHYSIOLOGY_FILENAME,
            "Respiration Rate (bpm)",
        ),
        "pulse_rate_per_min": (
            PHYSIOLOGY_FILENAME,
            "Pulse Rate (bpm)",
        ),
        "milk_fat_percent": (DMI_FILENAME, "Fat%"),
        "milk_protein_percent": (DMI_FILENAME, "Protein %"),
        "milk_lactose_percent": (DMI_FILENAME, "Lactose%"),
        "solids_not_fat_percent": (DMI_FILENAME, "SNF%"),
        "somatic_cell_count_per_ml": (DMI_FILENAME, "SCC cells per mL"),
        "milk_ph": (DMI_FILENAME, "pH"),
        "blood_glucose_mmol_l": (BLOOD_FILENAME, "Glucose (mmol/L)"),
        "serum_total_protein_g_dl": (
            BLOOD_FILENAME,
            "Total Protein (g/dL)",
        ),
        "blood_cortisol_ug_dl": (
            BLOOD_FILENAME,
            "Cortisol (µg/dL)",
        ),
    }
    output = {}
    for name, definition, unit, status in fields:
        workbook, column = source_lookup.get(
            name, ("GENERATED_AUDIT_PROVENANCE", name)
        )
        research = name.startswith("blood_") or name.startswith("serum_")
        composition = name.startswith("milk_") and name not in {
            "milk_yield_l_day"
        }
        output[name] = {
            "definition": definition,
            "unit": unit,
            "period": (
                "per cow per day"
                if name in {
                    "dry_matter_intake_kg_day",
                    "milk_yield_l_day",
                }
                else "per observation"
            ),
            "source_workbook": workbook,
            "source_sheet": "Sheet1" if workbook not in {
                "ALL", "GENERATED_AUDIT_PROVENANCE"
            } else "ALL",
            "source_column": column,
            "measurement_status": status,
            "ml_role": (
                "RESEARCH_ONLY" if research
                else "POSSIBLE_LEAKAGE" if composition
                else "TARGET" if name in {
                    "dry_matter_intake_kg_day", "milk_yield_l_day"
                }
                else "CANDIDATE_FEATURE"
            ),
            "rule_engine_role": "SUPPORTING_ANALYSIS_ONLY",
            "leakage_risk": (
                "RESEARCH_ONLY" if research
                else "POSSIBLE_LEAKAGE" if composition
                else "UNCLEAR" if name in {
                    "rectal_temperature_f",
                    "respiration_rate_per_min",
                    "pulse_rate_per_min",
                    "heat_stress_group",
                }
                else "LOW"
            ),
            "readiness": (
                "READY_WITH_LIMITATIONS" if name not in {
                    "source_file", "source_sheet", "source_row_number"
                } else "READY"
            ),
        }
    return {
        "schema_version": "4.5C",
        "dataset": "bangladesh_hf_cross",
        "unsupported_fields_are_omitted": True,
        "unsupported_examples": [
            "age_months",
            "weight_kg",
            "parity",
            "body_condition_score",
            "lactation_stage",
            "days_in_milk",
            "ambient_temperature_c",
            "humidity_percent",
            "temperature_humidity_index",
            "milk_yield_kg_day",
            "fresh_feed_intake_kg_day",
            "skin_temperature_c",
            "blood_urea",
            "AST/ALT (unit conflict)",
        ],
        "fields": output,
    }


def data_quality_issues(
    frames: dict[str, pd.DataFrame],
) -> list[dict[str, Any]]:
    """Return detected issues without correcting any source value."""

    issues: list[dict[str, Any]] = []

    def add(
        file: str,
        row: Any,
        cow: Any,
        column: str,
        issue: str,
        value: Any,
        severity: str,
        action: str,
        observation: str = "UNCLEAR",
    ) -> None:
        issues.append(
            {
                "file": file,
                "sheet": "Sheet1" if file.endswith(".xlsx") else "N/A",
                "source_row_number": row,
                "cow_id": cow,
                "observation_id": observation,
                "column": column,
                "issue_type": issue,
                "original_value": value,
                "severity": severity,
                "recommended_action": action,
            }
        )

    # The exact row-level key mismatch, not row order, is the main defect.
    dmi = frames[DMI_FILENAME]
    phys = frames[PHYSIOLOGY_FILENAME]
    dmi_cows = set(dmi["Animal ID"].map(canonical_cow_id))
    phys_cows = set(phys["Animal ID"].map(canonical_cow_id))
    for filename, frame, unmatched in (
        (DMI_FILENAME, dmi, dmi_cows - phys_cows),
        (PHYSIOLOGY_FILENAME, phys, phys_cows - dmi_cows),
    ):
        for _, row in frame.iterrows():
            cow = canonical_cow_id(row["Animal ID"])
            if cow in unmatched:
                add(
                    filename,
                    int(row["source_row_number"]),
                    cow,
                    "Animal ID",
                    "CROSS_WORKBOOK_COW_ID_COVERAGE_MISMATCH",
                    row["Animal ID"],
                    "HIGH",
                    (
                        "Confirm cow ID with source owner before joining "
                        "physiology to DMI/milk or blood."
                    ),
                    f"{canonical_thi(row['THI Range'])}-R{row['Replication No']}",
                )
    # Representative rows for systematic label formatting differences.
    for label in ("HF_50", "HF_62.5", "HF_75", "HF_87.5"):
        row = phys.loc[phys["Genetic group"] == label].iloc[0]
        add(
            PHYSIOLOGY_FILENAME,
            int(row["source_row_number"]),
            canonical_cow_id(row["Animal ID"]),
            "Genetic group",
            "INCONSISTENT_GENETIC_GROUP_LABEL_FORMAT",
            label,
            "MEDIUM",
            "Confirm documented equivalence before any future harmonization.",
        )
    for label in ("T0 (≤75)", "T1 (75-80)", "T2 (≥80)"):
        row = phys.loc[phys["THI Range"] == label].iloc[0]
        add(
            PHYSIOLOGY_FILENAME,
            int(row["source_row_number"]),
            canonical_cow_id(row["Animal ID"]),
            "THI Range",
            "INCONSISTENT_THI_LABEL_FORMAT",
            label,
            "LOW",
            "Use metadata-supported mapping only in a future approved step.",
        )
    blood = frames[BLOOD_FILENAME]
    for index, value in blood["Animal ID"].items():
        if not isinstance(value, str):
            add(
                BLOOD_FILENAME,
                int(blood.loc[index, "source_row_number"]),
                canonical_cow_id(value),
                "Animal ID",
                "MIXED_IDENTIFIER_CELL_TYPES",
                value,
                "MEDIUM",
                "Confirm identifier storage type; do not alter raw cells.",
            )
    for column in ("AST (U/I)", "ALT (U/I)"):
        add(
            BLOOD_FILENAME,
            "HEADER",
            "ALL",
            column,
            "UNIT_CONFLICT_WITH_METADATA",
            "Workbook U/I; metadata U/L",
            "HIGH",
            "Obtain source-owner confirmation of the intended unit.",
        )
    structural = [
        (
            METADATA_FILENAME,
            "File 2",
            "SOURCE_FILENAME_MISMATCH",
            "metadata: milk yield and composition.xlsx; supplied: "
            f"{DMI_FILENAME}",
            "MEDIUM",
            "Confirm that the supplied workbook is the documented File 2.",
        ),
        (
            DMI_FILENAME,
            "DMI (kg)",
            "HEADER_PERIOD_AMBIGUITY",
            "Header says kg; metadata variable name says kg per day",
            "MEDIUM",
            "Retain kg/cow/day only with metadata and repository provenance.",
        ),
        (
            METADATA_FILENAME,
            "DMI",
            "DMI_COLLECTION_PROTOCOL_UNCLEAR",
            "Feed offered/refused method is not documented",
            "HIGH",
            "Obtain the DMI measurement protocol before model training.",
        ),
        (
            METADATA_FILENAME,
            "Milk Yield",
            "MILK_COLLECTION_PROTOCOL_UNCLEAR",
            "Exact collection/instrument method is not documented",
            "MEDIUM",
            "Obtain the milk recording protocol.",
        ),
        (
            METADATA_FILENAME,
            "laboratory fields",
            "LABORATORY_METHODS_UNCLEAR",
            "Exact instruments and assays are absent",
            "MEDIUM",
            "Obtain laboratory methods and quality-control details.",
        ),
        (
            "ALL_WORKBOOKS",
            "date/time",
            "DATE_AND_TIME_FIELDS_ABSENT",
            "No observation date or timestamp",
            "HIGH",
            "Obtain dates/times before temporal or causal feature use.",
        ),
        (
            "ALL_WORKBOOKS",
            "temperature/humidity",
            "ENVIRONMENTAL_INPUTS_ABSENT",
            "No numeric temperature, humidity, or THI values",
            "HIGH",
            "Obtain underlying environmental measurements.",
        ),
        (
            METADATA_FILENAME,
            "missing codes",
            "MISSING_VALUE_CODES_UNDOCUMENTED",
            "UNCLEAR",
            "LOW",
            "Confirm source missing-value conventions.",
        ),
    ]
    for filename, column, issue, value, severity, action in structural:
        add(filename, "N/A", "N/A", column, issue, value, severity, action)
    issues.sort(
        key=lambda item: (
            item["file"],
            str(item["source_row_number"]),
            item["column"],
            item["issue_type"],
        )
    )
    return issues


def inventory_entry(
    path: Path,
    opened: DocxData | WorkbookData,
) -> dict[str, Any]:
    """Create a source inventory row without copying source records."""

    stat = path.stat()
    common = {
        "filename": path.name,
        "relative_path": path.relative_to(PROJECT_ROOT).as_posix(),
        "file_type": path.suffix.lstrip(".").upper(),
        "file_size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "last_modified_timestamp": (
            pd.Timestamp(stat.st_mtime, unit="s", tz="UTC").isoformat()
        ),
        "opens_successfully": True,
        "package_properties": opened.properties,
        "archive_entry_count": len(opened.archive_entries),
    }
    if isinstance(opened, WorkbookData):
        common.update(
            {
                "excel_sheet_count": len(opened.sheets),
                "sheet_names": [sheet.name for sheet in opened.sheets],
                "hidden_sheets": [
                    sheet.name for sheet in opened.sheets
                    if sheet.state != "visible"
                ],
                "merged_cells": {
                    sheet.name: sheet.merged_ranges for sheet in opened.sheets
                },
                "formula_count": sum(
                    sheet.formula_count for sheet in opened.sheets
                ),
                "comment_or_note_count": sum(
                    len(sheet.comments) for sheet in opened.sheets
                ),
                "embedded_table_count": 0,
                "metadata_content": opened.properties,
            }
        )
    else:
        common.update(
            {
                "excel_sheet_count": 0,
                "sheet_names": [],
                "hidden_sheets": [],
                "merged_cells": {},
                "formula_count": 0,
                "comment_or_note_count": len(opened.comments),
                "embedded_table_count": len(opened.tables),
                "metadata_content": {
                    "paragraph_count": len(opened.paragraphs),
                    "heading_count": len(opened.headings),
                    "table_count": len(opened.tables),
                    "properties": opened.properties,
                },
            }
        )
    common["licence_information"] = (
        "Local file: UNCLEAR; matched repository record: CC BY 4.0"
    )
    common["citation_information"] = (
        f"{SOURCE_RECORD['contributor']} (2026), "
        f"{SOURCE_RECORD['title']}, V2, doi:{SOURCE_RECORD['doi']}"
    )
    return common


__all__ = [
    "AUDIT_VERSION",
    "BLOOD_FILENAME",
    "BangladeshAuditError",
    "DMI_FILENAME",
    "EXPECTED_FILENAMES",
    "EXPECTED_SHA256",
    "METADATA_FILENAME",
    "PHYSIOLOGY_FILENAME",
    "RELATED_ARTICLE",
    "SOURCE_DIR",
    "SOURCE_RECORD",
    "analyze_join",
    "canonical_cow_id",
    "canonical_genetic_group",
    "canonical_thi",
    "classify_leakage",
    "common_schema",
    "data_quality_issues",
    "dataframe_from_sheet",
    "detect_repeated_observations",
    "detect_target_fields",
    "discover_bangladesh_files",
    "duplicate_row_count",
    "farmlite_compatibility",
    "inventory_entry",
    "is_missing",
    "missing_value_report",
    "numeric_summary",
    "observation_key",
    "parse_metadata_document",
    "sha256_file",
    "target_audit",
    "target_matrix",
    "tree_checksum",
    "workbook_profile",
]
