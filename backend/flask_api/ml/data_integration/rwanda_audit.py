"""Evidence-bound analysis for the Rwanda dairy nutrition source files.

This module performs descriptive auditing only. It contains no estimator,
prediction, train/test split, or model-persistence operation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Iterable

import pandas as pd

from config.settings import FLASK_API_DIR, PROJECT_ROOT
from ml.data_integration.office_reader import (
    DocxData,
    SheetData,
    WorkbookData,
    read_docx,
    read_xlsx,
)


AUDIT_VERSION = "rwanda_phase_4_5a_audit_v1"
SOURCE_DIR = (
    PROJECT_ROOT / "datasets" / "external" / "raw" / "rwanda_dairy_nutrition"
)
REPORT_DIR = FLASK_API_DIR / "ml" / "reports"
SCHEMA_PATH = FLASK_API_DIR / "config" / "rwanda_dairy_common_schema.json"

METADATA_FILENAME = "Metadata.xlsx"
COW_FILENAME = (
    "Specific data recorded on individual cows under lactation in Rwanda "
    "2020-2021.xlsx"
)
FODDER_FILENAME = "Different fodders components in the samples.xlsx"
BUCKET_FILENAME = "Bucket feeding plan (Supplemental Table).docx"
EXPECTED_FILENAMES = [
    METADATA_FILENAME,
    COW_FILENAME,
    FODDER_FILENAME,
    BUCKET_FILENAME,
]
EXPECTED_SHA256 = {
    METADATA_FILENAME: (
        "DD3001D696D217C19A6C3198A46F262BFD849BBCD061B62CDF974FE4E778E068"
    ),
    COW_FILENAME: (
        "4DADD19810DEA87E1EC2CAE915369E59AB71BF396893496151D8B2F50CF6C876"
    ),
    FODDER_FILENAME: (
        "BA5F9180494FDE7DBC58B95EA4018A08915AE023719D4D453F09D18C25F79D0A"
    ),
    BUCKET_FILENAME: (
        "B3192EEC974B2599C8607B4458825DA19C7919C87E2FEF263821A584D587493B"
    ),
}

DATASET_CITATION = {
    "title": (
        "Energy, protein, dry matter and water gap analysis in dairy cows "
        "kept under cut and carry fodder-based feeding system."
    ),
    "contributors": [
        "Olive Umunezero",
        "Charles Gachuiri",
        "Mupenzi Mutimura",
    ],
    "repository": "Mendeley Data",
    "version": "1",
    "published": "2025-03-17",
    "doi": "10.17632/6jf28ftxrr.1",
    "url": "https://data.mendeley.com/datasets/6jf28ftxrr/1",
    "licence": "CC BY 4.0",
    "licence_scope_note": (
        "The Mendeley dataset record declares CC BY 4.0. The related journal "
        "article has a separate CC BY-NC-ND 4.0 licence."
    ),
    "related_article_doi": "10.1016/j.anopes.2025.100097",
    "related_article_url": (
        "https://www.sciencedirect.com/science/article/pii/"
        "S2772694025000068"
    ),
    "retrieved": "2026-07-25",
}

EXTERNAL_METHOD_EVIDENCE = {
    "study_design": (
        "Cross-sectional; 66 lowland and 30 highland smallholder farms were "
        "purposively selected for having at least one lactating dairy cow."
    ),
    "cow_and_farm_count": (
        "The related publication reports 96 dairy cows from 96 smallholder farms."
    ),
    "body_weight": (
        "Estimated using a tape measure before morning feeding."
    ),
    "milk": (
        "Recorded using graduated plastic jars after each milking session; "
        "the repository describes reported results in litres per day."
    ),
    "water": (
        "Recorded from the number of graduated jerry cans provided to cows daily."
    ),
    "feed": (
        "Feeds were bagged and weighed with a hanging balance before offering; "
        "leftovers were weighed the following morning."
    ),
    "dmi": (
        "Daily DMI was calculated as dry matter served minus leftovers."
    ),
    "feed_samples": (
        "Composite 250 g feed samples were analysed for DM, CP, NDF, and ME."
    ),
    "laboratory_methods": (
        "DM: oven-dried at 60 C for three days; protein: Kjeldahl; NDF: "
        "ANKOM F57 fibre bags; ME: documented equation using gas volume and CP."
    ),
    "requirements": (
        "Feed characterisation used FarmDESIGN methods and cow production "
        "requirements used LIGAPS dairy models/equations."
    ),
    "source_url": DATASET_CITATION["url"],
}

MEASUREMENT_STATUSES = {
    "DIRECTLY_MEASURED",
    "OBSERVED",
    "OWNER_REPORTED",
    "CALCULATED",
    "MODEL_DERIVED",
    "TREATMENT_ASSIGNED",
    "IDENTIFIER",
    "UNKNOWN",
}

UNIT_OVERRIDES: dict[str, str] = {
    "sites": "category code",
    "LabN°": "identifier",
    "Lab N°": "identifier",
    "SAMPLE ID": "ingredient-list text",
    "cowbreed": "category",
    "cowageinyears": "years",
    "parity": "birth count",
    "Bodyweight": "kg",
    "MW": "kg^0.75",
    "DMIR kg": "kg DM/cow/day",
    "DM served": "kg DM/cow/day",
    "leftover": "kg DM/cow/day",
    "daysinmilk": "days",
    "lactationperiod": "category",
    "Ass.calfmilk": "L/cow/day",
    "hand-milked yield": "L/cow/day",
    "Total milk performance": "L/cow/day",
    "gapmilk": "L/cow/day",
    "potentialmilk": "L/cow/day",
    "%gapmilk": "percent",
    "waterday": "L/cow/day",
    "waterrequi.": "L/cow/day",
    "gapwater": "L/cow/day",
    "%watergap": "percent",
    "DMfeeds": "percent",
    "MEfeeds": "MJ/kg DM",
    "NDF feeds": "UNCLEAR",
    "DMIindex": "percent of body weight",
    "DMIcapacity (kgDM)": "kg DM/cow/day",
    "DMI gap": "kg DM/cow/day",
    "%gapDMI": "percent",
    "MEIntake": "MJ/cow/day",
    "MW*0.589=Energyformaintenance": "MJ/cow/day",
    "5.023*peakMilk": "MJ/cow/day",
    "MEmaint+peakmilk": "MJ/cow/day",
    "gapME": "MJ/cow/day",
    "%MEgap": "percent",
    "%Protein": "percent",
    "Protein/content/gr/kg": "g/kg DM",
    "Cpintakeingr": "g/cow/day",
    "CPmaint=6.27*MW": "g/cow/day",
    "CPmilk": "g/cow/day",
    "TotalreqCP": "g/cow/day",
    "gapCP": "g/cow/day",
    "%CP gap": "percent",
    "Age": "calf age band",
    "Milk consumption/day": "L/calf/day",
    "Milk production/day": "L/cow/day",
}

PERIOD_OVERRIDES: dict[str, str] = {
    name: "per cow per day"
    for name in (
        "DMIR kg",
        "DM served",
        "leftover",
        "Ass.calfmilk",
        "hand-milked yield",
        "Total milk performance",
        "gapmilk",
        "potentialmilk",
        "waterday",
        "waterrequi.",
        "gapwater",
        "DMIcapacity (kgDM)",
        "DMI gap",
        "MEIntake",
        "MW*0.589=Energyformaintenance",
        "5.023*peakMilk",
        "MEmaint+peakmilk",
        "gapME",
        "Cpintakeingr",
        "CPmaint=6.27*MW",
        "CPmilk",
        "TotalreqCP",
        "gapCP",
    )
}
PERIOD_OVERRIDES.update(
    {
        "Milk consumption/day": "per calf per day",
        "Milk production/day": "per cow per day",
        "daysinmilk": "lactation-to-observation interval",
        "SAMPLE ID": "fodders served to a selected cow per day",
    }
)

MEASUREMENT_OVERRIDES: dict[str, str] = {
    "sites": "OBSERVED",
    "LabN°": "IDENTIFIER",
    "Lab N°": "IDENTIFIER",
    "SAMPLE ID": "OBSERVED",
    "cowbreed": "OBSERVED",
    "cowageinyears": "OBSERVED",
    "parity": "OBSERVED",
    "Bodyweight": "DIRECTLY_MEASURED",
    "MW": "CALCULATED",
    "DMIR kg": "MODEL_DERIVED",
    "DM served": "DIRECTLY_MEASURED",
    "leftover": "DIRECTLY_MEASURED",
    "daysinmilk": "OBSERVED",
    "lactationperiod": "CALCULATED",
    "Ass.calfmilk": "MODEL_DERIVED",
    "hand-milked yield": "DIRECTLY_MEASURED",
    "Total milk performance": "CALCULATED",
    "gapmilk": "CALCULATED",
    "potentialmilk": "MODEL_DERIVED",
    "%gapmilk": "CALCULATED",
    "waterday": "OWNER_REPORTED",
    "waterrequi.": "MODEL_DERIVED",
    "gapwater": "CALCULATED",
    "%watergap": "CALCULATED",
    "DMfeeds": "DIRECTLY_MEASURED",
    "MEfeeds": "CALCULATED",
    "NDF feeds": "DIRECTLY_MEASURED",
    "DMIindex": "CALCULATED",
    "DMIcapacity (kgDM)": "CALCULATED",
    "DMI gap": "CALCULATED",
    "%gapDMI": "CALCULATED",
    "MEIntake": "CALCULATED",
    "MW*0.589=Energyformaintenance": "CALCULATED",
    "5.023*peakMilk": "CALCULATED",
    "MEmaint+peakmilk": "CALCULATED",
    "gapME": "CALCULATED",
    "%MEgap": "CALCULATED",
    "%Protein": "DIRECTLY_MEASURED",
    "Protein/content/gr/kg": "CALCULATED",
    "Cpintakeingr": "CALCULATED",
    "CPmaint=6.27*MW": "MODEL_DERIVED",
    "CPmilk": "MODEL_DERIVED",
    "TotalreqCP": "MODEL_DERIVED",
    "gapCP": "CALCULATED",
    "%CP gap": "CALCULATED",
    "Age": "OBSERVED",
    "Milk consumption/day": "OBSERVED",
    "Milk production/day": "OBSERVED",
}

TARGET_KEYWORDS = {
    "dmi": (
        "dry matter",
        "dmi",
        "dm served",
        "leftover",
    ),
    "milk": ("milk",),
    "water": ("water",),
    "protein": ("protein", "cp"),
    "energy": ("energy", "me"),
    "feed_category": (
        "sample id",
        "feed type",
        "feed category",
        "ration",
        "fodder",
        "feeding plan",
    ),
}

TARGET_FIELD_NAMES = {
    "dmi": {
        "DMIR kg",
        "DM served",
        "leftover",
        "DMfeeds",
        "DMIindex",
        "DMIcapacity (kgDM)",
        "DMI gap",
        "%gapDMI",
    },
    "milk": {
        "Ass.calfmilk",
        "hand-milked yield",
        "Total milk performance",
        "gapmilk",
        "potentialmilk",
        "%gapmilk",
        "Milk consumption/day",
        "Milk production/day",
    },
    "water": {
        "waterday",
        "waterrequi.",
        "gapwater",
        "%watergap",
    },
    "protein": {
        "%Protein",
        "Protein/content/gr/kg",
        "Cpintakeingr",
        "CPmaint=6.27*MW",
        "CPmilk",
        "TotalreqCP",
        "gapCP",
        "%CP gap",
    },
    "energy": {
        "MEfeeds",
        "MEIntake",
        "MW*0.589=Energyformaintenance",
        "5.023*peakMilk",
        "MEmaint+peakmilk",
        "gapME",
        "%MEgap",
    },
    "feed_category": {"SAMPLE ID"},
}

TARGET_CLASSIFICATIONS: dict[str, tuple[str, str, str]] = {
    "DMIR kg": ("dmi", "UNSUITABLE", "RULE_VALIDATION_ONLY"),
    "DM served": ("dmi", "PARTIALLY_DEFINED", "READY_WITH_LIMITATIONS"),
    "leftover": ("dmi", "PARTIALLY_DEFINED", "BLOCKED_NEGATIVE_VALUES"),
    "DMfeeds": ("dmi", "UNSUITABLE", "SUPPORTING_DATA_ONLY"),
    "DMIindex": ("dmi", "UNSUITABLE", "RULE_VALIDATION_ONLY"),
    "DMIcapacity (kgDM)": (
        "dmi",
        "CALCULATED_DMI",
        "READY_WITH_LIMITATIONS",
    ),
    "DMI gap": ("dmi", "PARTIALLY_DEFINED", "RULE_VALIDATION_ONLY"),
    "%gapDMI": ("dmi", "PARTIALLY_DEFINED", "RULE_VALIDATION_ONLY"),
    "Ass.calfmilk": ("milk", "PARTIALLY_DEFINED", "SUPPORTING_DATA_ONLY"),
    "hand-milked yield": (
        "milk",
        "VERIFIED_MILK_YIELD_L_DAY",
        "READY_WITH_LIMITATIONS",
    ),
    "Total milk performance": (
        "milk",
        "VERIFIED_MILK_YIELD_L_DAY",
        "READY_WITH_LIMITATIONS",
    ),
    "gapmilk": ("milk", "PARTIALLY_DEFINED", "RULE_VALIDATION_ONLY"),
    "potentialmilk": ("milk", "PARTIALLY_DEFINED", "SUPPORTING_DATA_ONLY"),
    "%gapmilk": ("milk", "PARTIALLY_DEFINED", "RULE_VALIDATION_ONLY"),
    "Milk consumption/day": (
        "milk",
        "PARTIALLY_DEFINED",
        "SUPPORTING_DATA_ONLY",
    ),
    "Milk production/day": (
        "milk",
        "PARTIALLY_DEFINED",
        "SUPPORTING_DATA_ONLY",
    ),
    "waterday": (
        "water",
        "VERIFIED_WATER_INTAKE_L_COW_DAY",
        "READY_WITH_LIMITATIONS",
    ),
    "waterrequi.": (
        "water",
        "VERIFIED_WATER_REQUIREMENT",
        "RULE_VALIDATION_ONLY",
    ),
    "gapwater": (
        "water",
        "CALCULATED_WATER_GAP",
        "RULE_VALIDATION_ONLY",
    ),
    "%watergap": (
        "water",
        "PARTIALLY_DEFINED",
        "RULE_VALIDATION_ONLY",
    ),
    "%Protein": (
        "protein",
        "VERIFIED_FEED_CP_PERCENT",
        "NUTRIENT_LOOKUP",
    ),
    "Protein/content/gr/kg": (
        "protein",
        "PARTIALLY_DEFINED",
        "RULE_VALIDATION_ONLY",
    ),
    "Cpintakeingr": (
        "protein",
        "VERIFIED_CP_INTAKE_G_DAY",
        "CALCULATED_TARGET_WITH_LIMITATIONS",
    ),
    "CPmaint=6.27*MW": (
        "protein",
        "VERIFIED_CP_REQUIREMENT_G_DAY",
        "RULE_VALIDATION_ONLY",
    ),
    "CPmilk": (
        "protein",
        "VERIFIED_CP_REQUIREMENT_G_DAY",
        "RULE_VALIDATION_ONLY",
    ),
    "TotalreqCP": (
        "protein",
        "VERIFIED_CP_REQUIREMENT_G_DAY",
        "RULE_VALIDATION_ONLY",
    ),
    "gapCP": (
        "protein",
        "CALCULATED_CP_GAP",
        "RULE_VALIDATION_ONLY",
    ),
    "%CP gap": (
        "protein",
        "PARTIALLY_DEFINED",
        "RULE_VALIDATION_ONLY",
    ),
    "MEfeeds": (
        "energy",
        "FEED_ENERGY_COMPOSITION",
        "NUTRIENT_LOOKUP",
    ),
    "MEIntake": (
        "energy",
        "VERIFIED_ME_INTAKE_MJ_DAY",
        "CALCULATED_TARGET_WITH_LIMITATIONS",
    ),
    "MW*0.589=Energyformaintenance": (
        "energy",
        "VERIFIED_ME_REQUIREMENT_MJ_DAY",
        "RULE_VALIDATION_ONLY",
    ),
    "5.023*peakMilk": (
        "energy",
        "VERIFIED_ME_REQUIREMENT_MJ_DAY",
        "RULE_VALIDATION_ONLY",
    ),
    "MEmaint+peakmilk": (
        "energy",
        "VERIFIED_ME_REQUIREMENT_MJ_DAY",
        "RULE_VALIDATION_ONLY",
    ),
    "gapME": (
        "energy",
        "CALCULATED_ENERGY_GAP",
        "RULE_VALIDATION_ONLY",
    ),
    "%MEgap": (
        "energy",
        "PARTIALLY_DEFINED",
        "RULE_VALIDATION_ONLY",
    ),
    "SAMPLE ID": (
        "feed_category",
        "OBSERVED_DIET_ONLY",
        "NOT_RECOMMENDATION_LABEL",
    ),
}


class RwandaAuditError(RuntimeError):
    """Raised when a critical audit prerequisite or invariant fails."""


@dataclass(frozen=True)
class VariableDefinition:
    source_variable_name: str
    exact_definition: str
    unit: str
    period: str
    measurement_status: str
    source_file: str
    source_sheet: str
    source_column: str
    notes: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def discover_rwanda_files(
    source_dir: str | Path = SOURCE_DIR,
) -> dict[str, Path]:
    """Discover exactly the four required source files."""

    directory = Path(source_dir)
    if not directory.is_dir():
        raise RwandaAuditError(f"Rwanda source directory is missing: {directory}")
    discovered = {
        path.name: path
        for path in directory.iterdir()
        if path.is_file()
    }
    missing = [
        filename for filename in EXPECTED_FILENAMES if filename not in discovered
    ]
    if missing:
        raise RwandaAuditError(
            "Required Rwanda source file(s) missing: " + ", ".join(missing)
        )
    return {filename: discovered[filename] for filename in EXPECTED_FILENAMES}


def extract_unit_period(
    variable: str,
    definition: str,
) -> tuple[str, str]:
    """Return only explicitly supported unit and period descriptions."""

    unit = UNIT_OVERRIDES.get(variable, "UNCLEAR")
    period = PERIOD_OVERRIDES.get(variable, "UNCLEAR")
    return unit, period


def classify_measurement_status(
    variable: str,
    definition: str,
) -> str:
    """Classify measurement status using explicit source evidence."""

    status = MEASUREMENT_OVERRIDES.get(variable, "UNKNOWN")
    if status not in MEASUREMENT_STATUSES:
        raise RwandaAuditError(f"Invalid measurement status: {status}")
    return status


def parse_metadata_definitions(
    workbook: WorkbookData,
) -> list[VariableDefinition]:
    """Parse all three definition sections after Metadata was read first."""

    if len(workbook.sheets) != 1 or workbook.sheets[0].name != "Metadata":
        raise RwandaAuditError("Metadata.xlsx has an unexpected sheet layout")
    rows = workbook.sheets[0].rows
    sections = [
        (16, 59, COW_FILENAME, "Raw data"),
        (64, 66, FODDER_FILENAME, "Composites feeds"),
        (70, 73, BUCKET_FILENAME, "Table 1"),
    ]
    definitions: list[VariableDefinition] = []
    for start, end, source_file, source_sheet in sections:
        for excel_row in range(start + 1, end + 1):
            row = rows[excel_row - 1] if excel_row <= len(rows) else []
            variable = row[1] if len(row) > 1 else None
            definition = row[2] if len(row) > 2 else None
            if not variable or not definition:
                continue
            variable_text = str(variable).strip()
            definition_text = str(definition).strip()
            unit, period = extract_unit_period(
                variable_text, definition_text
            )
            status = classify_measurement_status(
                variable_text, definition_text
            )
            notes = ""
            if variable_text == "NDF feeds":
                notes = (
                    "Metadata states kgDM, but values and the documented "
                    "120/NDF equation behave like percentage; unit is UNCLEAR."
                )
            elif variable_text == "cowageinyears":
                notes = (
                    "The 30 highland rows contain detailed breed text in this "
                    "column; numeric age is usable only for 64 rows."
                )
            elif variable_text == "leftover":
                notes = (
                    "External methodology says next-morning leftovers were "
                    "weighed, but 28 source values are negative."
                )
            elif variable_text == "gapCP":
                notes = (
                    "Metadata definition conflicts with the repository formula "
                    "and row values; rows use total CP requirement minus CP intake."
                )
            definitions.append(
                VariableDefinition(
                    source_variable_name=variable_text,
                    exact_definition=definition_text,
                    unit=unit,
                    period=period,
                    measurement_status=status,
                    source_file=source_file,
                    source_sheet=source_sheet,
                    source_column=variable_text,
                    notes=notes,
                )
            )
    if len(definitions) != 48:
        raise RwandaAuditError(
            f"Expected 48 metadata definitions, found {len(definitions)}"
        )
    return definitions


def dataframe_from_sheet(
    sheet: SheetData,
    *,
    header_row: int,
    first_data_row: int | None = None,
) -> pd.DataFrame:
    """Create an in-memory table without writing or altering the workbook."""

    if header_row < 1 or header_row > len(sheet.rows):
        raise RwandaAuditError(
            f"Header row {header_row} not available in {sheet.name}"
        )
    headers = [
        str(value).strip() if value is not None else f"__blank_{index + 1}"
        for index, value in enumerate(sheet.rows[header_row - 1])
    ]
    if len(headers) != len(set(headers)):
        raise RwandaAuditError(f"Duplicate headers in sheet {sheet.name}")
    start = first_data_row or header_row + 1
    data = sheet.rows[start - 1 :]
    frame = pd.DataFrame(data, columns=headers)
    frame.insert(0, "source_row_number", range(start, start + len(frame)))
    entirely_empty = frame[headers].isna().all(axis=1)
    return frame.loc[~entirely_empty].reset_index(drop=True)


def _is_missing(value: Any) -> bool:
    return value is None or (
        isinstance(value, float) and math.isnan(value)
    ) or (isinstance(value, str) and not value.strip())


def _numeric_values(values: Iterable[Any]) -> list[float]:
    result = []
    for value in values:
        if _is_missing(value) or isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            result.append(number)
    return result


def numeric_summary(values: Iterable[Any]) -> dict[str, Any]:
    """Summarise finite numeric values without imputing invalid entries."""

    numbers = _numeric_values(values)
    if not numbers:
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
        "count": len(numbers),
        "minimum": min(numbers),
        "maximum": max(numbers),
        "mean": mean(numbers),
        "median": median(numbers),
        "standard_deviation": stdev(numbers) if len(numbers) > 1 else None,
        "zero_count": sum(value == 0 for value in numbers),
        "negative_count": sum(value < 0 for value in numbers),
    }


def column_profile(
    frame: pd.DataFrame,
    column: str,
) -> dict[str, Any]:
    """Return missingness, types, examples, and descriptive summaries."""

    values = frame[column].tolist()
    missing_count = sum(_is_missing(value) for value in values)
    nonmissing = [value for value in values if not _is_missing(value)]
    types = Counter(
        "boolean"
        if isinstance(value, bool)
        else "integer"
        if isinstance(value, int)
        else "number"
        if isinstance(value, float)
        else "string"
        for value in nonmissing
    )
    unique_values = list(dict.fromkeys(map(str, nonmissing)))
    numeric = numeric_summary(nonmissing)
    categorical_counts = Counter(map(str, nonmissing)).most_common(10)
    return {
        "column": column,
        "row_count": len(frame),
        "missing_count": missing_count,
        "missing_percentage": (
            100.0 * missing_count / len(frame) if len(frame) else 0.0
        ),
        "data_types": dict(types),
        "unique_count": len(unique_values),
        "example_values": unique_values[:5],
        "numeric_summary": numeric,
        "top_values": [
            {"value": value, "count": count}
            for value, count in categorical_counts
        ],
    }


def missing_value_report(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "column": column,
            "missing_count": profile["missing_count"],
            "missing_percentage": profile["missing_percentage"],
        }
        for column in frame.columns
        if column != "source_row_number"
        for profile in [column_profile(frame, column)]
    ]


def detect_repeated_cows(
    frame: pd.DataFrame,
    cow_id_column: str | None,
) -> dict[str, Any]:
    """Report repeated cows, or UNCLEAR when no cow identifier exists."""

    if not cow_id_column or cow_id_column not in frame:
        return {
            "status": "UNCLEAR",
            "cow_id_column": None,
            "unique_cows": None,
            "repeated_cow_count": None,
            "maximum_records_per_cow": None,
            "reason": (
                "No cow identifier is present. LabN° is a composite feed "
                "sample identifier and must not be treated as cow_id."
            ),
            "future_split_rule": (
                "If a future source supplies repeated cow IDs, split by cow, "
                "never randomly by row."
            ),
        }
    counts = frame[cow_id_column].value_counts(dropna=True)
    return {
        "status": "REPEATED" if (counts > 1).any() else "NOT_REPEATED",
        "cow_id_column": cow_id_column,
        "unique_cows": int(len(counts)),
        "repeated_cow_count": int((counts > 1).sum()),
        "maximum_records_per_cow": int(counts.max()) if len(counts) else 0,
    }


def classify_target(
    variable: str,
    definition: str = "",
) -> dict[str, str]:
    """Classify source fields without inventing recommendation labels."""

    if variable in TARGET_CLASSIFICATIONS:
        domain, status, suitability = TARGET_CLASSIFICATIONS[variable]
        return {
            "domain": domain,
            "status": status,
            "ml_suitability": suitability,
        }
    text = f"{variable} {definition}".casefold()
    if "sample id" in text or "fodder" in text:
        return {
            "domain": "feed_category",
            "status": "INGREDIENT_INFORMATION_ONLY",
            "ml_suitability": "NOT_RECOMMENDATION_LABEL",
        }
    return {
        "domain": "other",
        "status": "UNCLEAR",
        "ml_suitability": "UNCLEAR",
    }


def detect_target_fields(
    definitions: list[VariableDefinition],
    domain: str,
) -> list[dict[str, str]]:
    if domain not in TARGET_FIELD_NAMES:
        raise RwandaAuditError(f"Unsupported target domain: {domain}")
    field_names = TARGET_FIELD_NAMES[domain]
    results = []
    for item in definitions:
        if item.source_variable_name in field_names:
            results.append(
                {
                    **item.to_dict(),
                    **classify_target(
                        item.source_variable_name,
                        item.exact_definition,
                    ),
                }
            )
    return results


def classify_feed_label(
    variable: str,
    definition: str,
) -> str:
    """Reject observed ingredients or plans as recommendation labels."""

    text = f"{variable} {definition}".casefold()
    if "different fodder ingredients" in text or "served" in text:
        return "OBSERVED_DIET_ONLY"
    if "feeding program" in text and "followed by farmers" in text:
        return "VERIFIED_OBSERVED_PRACTICE"
    if "recommend" in text and "expert" in text:
        return "VERIFIED_EXPERT_RECOMMENDATION_LABEL"
    return "UNCLEAR"


def analyze_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_key: str,
    right_key: str,
) -> dict[str, Any]:
    """Profile keys only; no permanent merged table is created."""

    left_values = [
        str(value) for value in left[left_key] if not _is_missing(value)
    ]
    right_values = [
        str(value) for value in right[right_key] if not _is_missing(value)
    ]
    left_counts = Counter(left_values)
    right_counts = Counter(right_values)
    matched_rows = sum(
        count for key, count in left_counts.items() if key in right_counts
    )
    duplicate_left_keys = sum(count - 1 for count in left_counts.values() if count > 1)
    duplicate_right_keys = sum(
        count - 1 for count in right_counts.values() if count > 1
    )
    many_to_many = any(
        left_counts[key] > 1 and right_counts.get(key, 0) > 1
        for key in left_counts
    )
    if many_to_many:
        safety = "MANY_TO_MANY_RISK"
    elif duplicate_left_keys and not duplicate_right_keys:
        safety = "POSSIBLE_WITH_LIMITATIONS"
    elif not duplicate_left_keys and not duplicate_right_keys:
        safety = "SAFE_ONE_TO_ONE"
    else:
        safety = "POSSIBLE_WITH_LIMITATIONS"
    return {
        "left_key": left_key,
        "right_key": right_key,
        "left_row_count": len(left),
        "right_row_count": len(right),
        "left_unique_key_count": len(left_counts),
        "right_unique_key_count": len(right_counts),
        "left_duplicate_key_count": duplicate_left_keys,
        "right_duplicate_key_count": duplicate_right_keys,
        "left_missing_key_count": len(left) - len(left_values),
        "right_missing_key_count": len(right) - len(right_values),
        "matched_left_row_count": matched_rows,
        "left_match_percentage": (
            100.0 * matched_rows / len(left) if len(left) else 0.0
        ),
        "unmatched_left_keys": sorted(
            key for key in left_counts if key not in right_counts
        ),
        "unmatched_right_keys": sorted(
            key for key in right_counts if key not in left_counts
        ),
        "many_to_many_risk": many_to_many,
        "join_safety": safety,
        "meaning": (
            "Links a cow-level observation to the text list of fodder "
            "ingredients for its composite laboratory sample. Repeated LabN° "
            "values mean multiple cow rows may share one fodder record."
        ),
    }


def _issue(
    file: str,
    sheet: str,
    row_number: int | str,
    identifier: Any,
    column: str,
    issue_type: str,
    original_value: Any,
    severity: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "file": file,
        "sheet": sheet,
        "row_number": row_number,
        "identifier": "" if identifier is None else identifier,
        "column": column,
        "issue_type": issue_type,
        "original_value": "" if original_value is None else original_value,
        "severity": severity,
        "recommended_action": recommended_action,
    }


def cow_quality_issues(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Detect source-quality issues without correcting any record."""

    issues: list[dict[str, Any]] = []
    identifier_column = "LabN°"
    for _, row in frame.iterrows():
        source_row = int(row["source_row_number"])
        identifier = row[identifier_column]
        for column in frame.columns:
            if column == "source_row_number":
                continue
            value = row[column]
            if _is_missing(value):
                issues.append(
                    _issue(
                        COW_FILENAME,
                        "Raw data",
                        source_row,
                        identifier,
                        column,
                        "MISSING_VALUE",
                        value,
                        "WARNING",
                        "Clarify from source; do not impute during audit.",
                    )
                )
        age_value = row["cowageinyears"]
        if not _is_missing(age_value):
            try:
                age = float(age_value)
                if age < 0:
                    raise ValueError
            except (TypeError, ValueError):
                issues.append(
                    _issue(
                        COW_FILENAME,
                        "Raw data",
                        source_row,
                        identifier,
                        "cowageinyears",
                        "TEXT_IN_NUMERIC_AGE_COLUMN",
                        age_value,
                        "ERROR",
                        (
                            "Source correction required; values are detailed "
                            "breed descriptions in all highland rows."
                        ),
                    )
                )
        for column in ("Bodyweight", "daysinmilk", "waterday", "DM served"):
            value = row[column]
            if not _is_missing(value) and float(value) < 0:
                issues.append(
                    _issue(
                        COW_FILENAME,
                        "Raw data",
                        source_row,
                        identifier,
                        column,
                        "NEGATIVE_PHYSICAL_VALUE",
                        value,
                        "ERROR",
                        "Verify against collection records; do not auto-correct.",
                    )
                )
        leftover = row["leftover"]
        if not _is_missing(leftover) and float(leftover) < 0:
            issues.append(
                _issue(
                    COW_FILENAME,
                    "Raw data",
                    source_row,
                    identifier,
                    "leftover",
                    "NEGATIVE_LEFTOVER",
                    leftover,
                    "ERROR",
                    (
                        "Physical next-morning leftovers cannot be negative; "
                        "clarify whether this column was back-calculated."
                    ),
                )
            )
        milk = row["hand-milked yield"]
        if not _is_missing(milk) and float(milk) == 0:
            issues.append(
                _issue(
                    COW_FILENAME,
                    "Raw data",
                    source_row,
                    identifier,
                    "hand-milked yield",
                    "ZERO_MILK_YIELD",
                    milk,
                    "WARNING",
                    "Verify whether zero is genuine or a missing-value code.",
                )
            )
    counts = frame["LabN°"].value_counts(dropna=True)
    for lab_number, count in counts[counts > 1].items():
        issues.append(
            _issue(
                COW_FILENAME,
                "Raw data",
                "MULTIPLE",
                lab_number,
                "LabN°",
                "DUPLICATE_SAMPLE_IDENTIFIER",
                count,
                "WARNING",
                (
                    "Treat LabN° as a composite sample key, not cow_id; verify "
                    "why multiple cow records share one sample."
                ),
            )
        )
    issues.extend(
        [
            _issue(
                COW_FILENAME,
                "Raw data",
                "DATASET",
                "",
                "cow_id",
                "MISSING_COW_IDENTIFIER",
                "",
                "ERROR",
                "Obtain a stable cow identifier before grouped ML splitting.",
            ),
            _issue(
                COW_FILENAME,
                "Raw data",
                "DATASET",
                "",
                "farm_id",
                "MISSING_FARM_IDENTIFIER",
                "",
                "ERROR",
                (
                    "The publication reports 96 farms, but the workbook has no "
                    "farm key; obtain it before farm-grouped validation."
                ),
            ),
            _issue(
                COW_FILENAME,
                "Raw data",
                "DATASET",
                "",
                "observation_date",
                "MISSING_OBSERVATION_DATE",
                "",
                "WARNING",
                "Only the 2020-2021 study window is known.",
            ),
            _issue(
                COW_FILENAME,
                "Raw data",
                "DATASET",
                "",
                "NDF feeds",
                "INCONSISTENT_UNIT_DEFINITION",
                "Metadata: kgDM; values/formula: percentage-like",
                "ERROR",
                "Confirm the intended NDF unit from the authors.",
            ),
            _issue(
                COW_FILENAME,
                "Raw data",
                "DATASET",
                "",
                "gapCP",
                "METADATA_FORMULA_CONTRADICTION",
                (
                    "Metadata subtracts maintenance requirement; repository "
                    "and values subtract CP intake from total requirement."
                ),
                "ERROR",
                "Use the repository formula only after author confirmation.",
            ),
            _issue(
                COW_FILENAME,
                "Raw data",
                "DATASET",
                "",
                "%gapmilk",
                "MISLEADING_PERCENT_NAME",
                (
                    "Values equal milk gap / potential milk x 100, despite "
                    "metadata wording referencing total milk performance."
                ),
                "WARNING",
                "Clarify the definition and rename only in a later approved phase.",
            ),
        ]
    )
    return issues


def _split_ingredients(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[,/]", value)
        if item and item.strip()
    ]


def fodder_quality_issues(frame: pd.DataFrame) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        source_row = int(row["source_row_number"])
        sample_id = row["Lab N°"]
        value = row["SAMPLE ID"]
        if _is_missing(value):
            issues.append(
                _issue(
                    FODDER_FILENAME,
                    "Composites feeds",
                    source_row,
                    sample_id,
                    "SAMPLE ID",
                    "MISSING_INGREDIENT_LIST",
                    value,
                    "ERROR",
                    "Obtain the source ingredient list; do not infer it.",
                )
            )
            continue
        ingredients = _split_ingredients(str(value))
        normalized = [ingredient.casefold() for ingredient in ingredients]
        repeated = sorted(
            ingredient
            for ingredient, count in Counter(normalized).items()
            if count > 1
        )
        if repeated:
            issues.append(
                _issue(
                    FODDER_FILENAME,
                    "Composites feeds",
                    source_row,
                    sample_id,
                    "SAMPLE ID",
                    "REPEATED_INGREDIENT_IN_SAMPLE",
                    ", ".join(repeated),
                    "WARNING",
                    "Verify the raw entry; do not silently deduplicate.",
                )
            )
    issues.extend(
        [
            _issue(
                FODDER_FILENAME,
                "Composites feeds",
                "DATASET",
                "",
                "SAMPLE ID",
                "INCONSISTENT_INGREDIENT_SPELLING",
                "Examples include digitalia/digitaria and sugarcanne/sugarcane",
                "WARNING",
                "Create an expert-reviewed vocabulary before standardisation.",
            ),
            _issue(
                FODDER_FILENAME,
                "Composites feeds",
                "DATASET",
                "",
                "nutrient columns",
                "NO_COMPONENT_NUTRIENT_COLUMNS",
                (
                    "Workbook contains composite ingredient text only; DM, CP, "
                    "NDF, and ME values are stored in the cow workbook."
                ),
                "INFO",
                "Use the Lab N° relationship with documented limitations.",
            ),
        ]
    )
    return issues


def formula_consistency_issues(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Compare documented calculated fields without changing source values."""

    formulas: list[tuple[str, Any, list[str]]] = [
        (
            "Total milk performance",
            lambda row: float(row["Ass.calfmilk"])
            + float(row["hand-milked yield"]),
            ["Ass.calfmilk", "hand-milked yield"],
        ),
        (
            "gapmilk",
            lambda row: float(row["potentialmilk"])
            - float(row["Total milk performance"]),
            ["potentialmilk", "Total milk performance"],
        ),
        (
            "DMIcapacity (kgDM)",
            lambda row: float(row["DM served"]) - float(row["leftover"]),
            ["DM served", "leftover"],
        ),
        (
            "DMI gap",
            lambda row: float(row["DMIR kg"])
            - float(row["DMIcapacity (kgDM)"]),
            ["DMIR kg", "DMIcapacity (kgDM)"],
        ),
        (
            "gapwater",
            lambda row: float(row["waterrequi."]) - float(row["waterday"]),
            ["waterrequi.", "waterday"],
        ),
        (
            "MEIntake",
            lambda row: float(row["MEfeeds"])
            * float(row["DMIcapacity (kgDM)"]),
            ["MEfeeds", "DMIcapacity (kgDM)"],
        ),
        (
            "MEmaint+peakmilk",
            lambda row: float(row["MW*0.589=Energyformaintenance"])
            + float(row["5.023*peakMilk"]),
            [
                "MW*0.589=Energyformaintenance",
                "5.023*peakMilk",
            ],
        ),
        (
            "gapME",
            lambda row: float(row["MEmaint+peakmilk"])
            - float(row["MEIntake"]),
            ["MEmaint+peakmilk", "MEIntake"],
        ),
        (
            "Protein/content/gr/kg",
            lambda row: float(row["%Protein"]) * 10.0,
            ["%Protein"],
        ),
        (
            "Cpintakeingr",
            lambda row: float(row["Protein/content/gr/kg"])
            * float(row["DMIcapacity (kgDM)"]),
            ["Protein/content/gr/kg", "DMIcapacity (kgDM)"],
        ),
        (
            "TotalreqCP",
            lambda row: float(row["CPmaint=6.27*MW"])
            + float(row["CPmilk"]),
            ["CPmaint=6.27*MW", "CPmilk"],
        ),
        (
            "gapCP",
            lambda row: float(row["TotalreqCP"])
            - float(row["Cpintakeingr"]),
            ["TotalreqCP", "Cpintakeingr"],
        ),
    ]
    issues: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        for target, calculator, inputs in formulas:
            values = [row[target], *[row[name] for name in inputs]]
            if any(_is_missing(value) for value in values):
                continue
            expected = calculator(row)
            actual = float(row[target])
            # Several calculated source columns are rounded to two or three
            # decimal places even when their inputs retain more precision.
            # Treat sub-centesimal differences as display rounding, not errors.
            tolerance = max(0.01, abs(expected) * 1e-6)
            if abs(actual - expected) > tolerance:
                issues.append(
                    _issue(
                        COW_FILENAME,
                        "Raw data",
                        int(row["source_row_number"]),
                        row["LabN°"],
                        target,
                        "DOCUMENTED_FORMULA_MISMATCH",
                        actual,
                        "ERROR",
                        (
                            f"Expected approximately {expected:.8g} from "
                            f"{', '.join(inputs)}; verify source formula."
                        ),
                    )
                )
    return issues


def candidate_feature_register(
    frame: pd.DataFrame,
    profiles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map only evidenced cow fields to requested candidate concepts."""

    mappings = [
        (
            "cow_id",
            None,
            "NOT_AVAILABLE",
            "No stable cow identifier.",
        ),
        (
            "farm_id",
            None,
            "NOT_AVAILABLE",
            "Publication reports farms, workbook has no farm key.",
        ),
        (
            "breed",
            "cowbreed",
            "INCLUDE_CANDIDATE",
            "Broad Cross/exotic category; detailed breed text contaminates age.",
        ),
        (
            "age_years",
            "cowageinyears",
            "UNCLEAR",
            "Only 64 numeric values; 30 highland rows contain breed text.",
        ),
        ("weight_kg", "Bodyweight", "INCLUDE_CANDIDATE", "Tape-estimated."),
        ("parity", "parity", "OPTIONAL_CANDIDATE", "Three missing values."),
        (
            "body_condition_score",
            None,
            "NOT_AVAILABLE",
            "No BCS field.",
        ),
        (
            "lactation_stage",
            "lactationperiod",
            "INCLUDE_CANDIDATE",
            "Peak/Mid/Late derived from days in milk.",
        ),
        (
            "days_in_milk",
            "daysinmilk",
            "INCLUDE_CANDIDATE",
            "Observed days in milk.",
        ),
        (
            "current_milk_yield",
            "hand-milked yield",
            "POSSIBLE_LEAKAGE",
            "Target for milk model; possible feature only for intake models.",
        ),
        (
            "previous_milk_yield",
            None,
            "NOT_AVAILABLE",
            "No historical-lagged yield.",
        ),
        (
            "ambient_temperature_c",
            None,
            "NOT_AVAILABLE",
            "No environment measurement.",
        ),
        (
            "humidity_percent",
            None,
            "NOT_AVAILABLE",
            "No humidity measurement.",
        ),
        (
            "temperature_humidity_index",
            None,
            "NOT_AVAILABLE",
            "No temperature/humidity source.",
        ),
        (
            "season",
            None,
            "NOT_AVAILABLE",
            "No row-level season/date.",
        ),
        (
            "location",
            "sites",
            "OPTIONAL_CANDIDATE",
            "Only coded lowlands/highlands.",
        ),
        (
            "feeding_system",
            None,
            "NOT_AVAILABLE",
            "Cut-and-carry is study-level constant, not a row column.",
        ),
        (
            "water_access",
            "waterday",
            "POSSIBLE_LEAKAGE",
            "Daily water is a target/outcome, not pre-target access metadata.",
        ),
        (
            "roughage_use",
            None,
            "UNCLEAR",
            "Composite ingredients exist but lack expert categories/quantities.",
        ),
        (
            "concentrate_use",
            None,
            "NOT_AVAILABLE",
            "No verified concentrate indicator.",
        ),
    ]
    records = []
    for canonical, source, decision, notes in mappings:
        profile = profiles.get(source) if source else None
        definition_status = (
            MEASUREMENT_OVERRIDES.get(source, "UNKNOWN") if source else "UNKNOWN"
        )
        records.append(
            {
                "candidate_feature": canonical,
                "exact_source_column": source or "NOT_AVAILABLE",
                "source_sheet": "Raw data" if source else "NOT_AVAILABLE",
                "definition": (
                    next(
                        (
                            item
                            for item in (
                                "See rwanda_variable_dictionary.csv",
                            )
                        ),
                        "UNCLEAR",
                    )
                    if source
                    else "NOT_AVAILABLE"
                ),
                "unit": UNIT_OVERRIDES.get(source, "NOT_AVAILABLE"),
                "missing_percentage": (
                    profile["missing_percentage"] if profile else None
                ),
                "unique_values": profile["unique_count"] if profile else None,
                "example_values": (
                    "|".join(profile["example_values"])
                    if profile
                    else "NOT_AVAILABLE"
                ),
                "available_before_prediction": (
                    "NO"
                    if decision
                    in {"POSSIBLE_LEAKAGE", "DEFINITE_LEAKAGE"}
                    else "YES"
                    if source
                    else "NO"
                ),
                "suitable_as_ml_feature": decision,
                "potential_leakage_risk": (
                    "HIGH"
                    if decision
                    in {"POSSIBLE_LEAKAGE", "DEFINITE_LEAKAGE"}
                    else "NONE_IDENTIFIED"
                    if source
                    else "NOT_AVAILABLE"
                ),
                "measurement_status": definition_status,
                "notes": notes,
            }
        )
    return records


def farmlite_compatibility(
    profiles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare the current nine app inputs with the supplied workbook."""

    rows = [
        (
            "breed",
            "YES",
            "cowbreed",
            "category compatible only after vocabulary mapping",
            "0",
            "YES",
            "YES_WITH_LIMITATIONS",
            "YES",
            "NO",
            "Cross/exotic only; detailed breeds are misplaced in age column.",
        ),
        (
            "age_months",
            "PARTIAL",
            "cowageinyears",
            "years, not months",
            "33.333333",
            "YES",
            "UNCLEAR",
            "YES",
            "NO",
            "30 text breed values and 2 missing; no conversion applied.",
        ),
        (
            "weight_kg",
            "YES",
            "Bodyweight",
            "kg",
            "0",
            "YES",
            "YES",
            "NO",
            "NO",
            "Tape-estimated before morning feeding.",
        ),
        (
            "lactation_stage",
            "YES",
            "lactationperiod",
            "Peak/Mid/Late; mapping required",
            "0",
            "YES",
            "YES",
            "YES",
            "NO",
            "FarmLite Early differs from Rwanda Peak.",
        ),
        (
            "days_in_milk",
            "YES",
            "daysinmilk",
            "days",
            "0",
            "YES",
            "YES",
            "NO",
            "NO",
            "Range 1-540.",
        ),
        (
            "previous_week_avg_yield_l",
            "NO",
            "NOT_AVAILABLE",
            "NOT_AVAILABLE",
            "100",
            "NO",
            "NO",
            "NO",
            "NO",
            "Only current daily milk fields are present.",
        ),
        (
            "body_condition_score",
            "NO",
            "NOT_AVAILABLE",
            "NOT_AVAILABLE",
            "100",
            "NO",
            "NO",
            "NO",
            "NO",
            "Not collected.",
        ),
        (
            "ambient_temperature_c",
            "NO",
            "NOT_AVAILABLE",
            "NOT_AVAILABLE",
            "100",
            "NO",
            "NO",
            "NO",
            "NO",
            "Not collected.",
        ),
        (
            "humidity_percent",
            "NO",
            "NOT_AVAILABLE",
            "NOT_AVAILABLE",
            "100",
            "NO",
            "NO",
            "NO",
            "NO",
            "Not collected.",
        ),
        (
            "NEW: parity",
            "YES",
            "parity",
            "birth count",
            "3.125",
            "YES",
            "YES_WITH_LIMITATIONS",
            "NO",
            "YES",
            "Useful Rwanda feature not currently collected by FarmLite.",
        ),
        (
            "NEW: site_category",
            "YES",
            "sites",
            "1=lowlands; 2=highlands",
            "0",
            "YES",
            "YES",
            "YES",
            "YES",
            "Study region category; not a farm identifier.",
        ),
        (
            "NEW: water_intake_l_day",
            "YES",
            "waterday",
            "L/cow/day",
            "0",
            "NO_FOR_PRE_INTAKE_PREDICTION",
            "TARGET_ONLY",
            "NO",
            "YES",
            "Candidate target and rule input, not a pre-target feature.",
        ),
        (
            "NEW: dry_matter_served_kg_day",
            "YES",
            "DM served",
            "kg DM/cow/day",
            "0",
            "NO_FOR_RECOMMENDATION_TIME",
            "TARGET_OR_RULE_INPUT",
            "NO",
            "YES",
            "Observed feed offering, not optimized recommendation.",
        ),
        (
            "NEW: dry_matter_leftover_kg_day",
            "YES",
            "leftover",
            "kg DM/cow/day",
            "0",
            "NO",
            "BLOCKED_NEGATIVE_VALUES",
            "NO",
            "YES",
            "Twenty-eight negative values require clarification.",
        ),
        (
            "NEW: feed_ingredient_list",
            "YES",
            "SAMPLE ID (fodder workbook)",
            "ingredient-list text",
            "0",
            "NO_FOR_RECOMMENDATION_TIME",
            "SUPPORTING_ONLY",
            "YES",
            "YES",
            "Observed composite fodders; no recommendation label.",
        ),
    ]
    names = [
        "farmlite_feature",
        "available_in_rwanda",
        "exact_source_column",
        "unit_compatibility",
        "missing_percentage",
        "available_at_prediction_time",
        "safe_for_ml",
        "mapping_required",
        "farmlite_form_change_required",
        "notes",
    ]
    return [dict(zip(names, row, strict=True)) for row in rows]


def target_matrix() -> list[dict[str, str]]:
    columns = [
        "desired_farmlite_output",
        "rwanda_source",
        "exact_field_or_table",
        "unit",
        "period",
        "measurement_status",
        "ml_suitability",
        "rule_suitability",
        "decision",
    ]
    rows = [
        (
            "Feed/ration category",
            FODDER_FILENAME,
            "SAMPLE ID",
            "ingredient-list text",
            "per selected cow/day",
            "OBSERVED",
            "Not an expert recommendation label",
            "Ingredient evidence only",
            "EXPERT_LABELS_REQUIRED",
        ),
        (
            "Total feed",
            COW_FILENAME,
            "DM served",
            "kg DM/cow/day",
            "per cow/day",
            "DIRECTLY_MEASURED",
            "Observed offering target only",
            "Supporting input",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "Dry-matter intake",
            COW_FILENAME,
            "DMIcapacity (kgDM)",
            "kg DM/cow/day",
            "per cow/day",
            "CALCULATED",
            "Blocked pending negative-leftover clarification",
            "Equation support with limitations",
            "BLOCKED",
        ),
        (
            "Roughage",
            FODDER_FILENAME,
            "SAMPLE ID",
            "ingredient text; no quantity",
            "per selected cow/day",
            "OBSERVED",
            "No verified category/quantity",
            "Expert mapping required",
            "EXPERT_LABELS_REQUIRED",
        ),
        (
            "Concentrate",
            FODDER_FILENAME,
            "SAMPLE ID",
            "ingredient text; no verified concentrate quantity",
            "per selected cow/day",
            "OBSERVED",
            "Not supported",
            "Not supported",
            "NOT_SUPPORTED",
        ),
        (
            "Mineral mix",
            "None",
            "NOT_AVAILABLE",
            "NOT_AVAILABLE",
            "NOT_AVAILABLE",
            "UNKNOWN",
            "Not supported",
            "Not supported",
            "NOT_SUPPORTED",
        ),
        (
            "Water intake/advice",
            COW_FILENAME,
            "waterday; waterrequi.; gapwater",
            "L/cow/day",
            "per cow/day",
            "OWNER_REPORTED and MODEL_DERIVED",
            "Water intake target with limitations",
            "Requirement equation supported",
            "READY_FOR_BOTH",
        ),
        (
            "Crude protein",
            COW_FILENAME,
            "%Protein; Cpintakeingr; TotalreqCP; gapCP",
            "percent and g/cow/day",
            "per cow/day",
            "DIRECTLY_MEASURED, CALCULATED, MODEL_DERIVED",
            "Formula-derived target only",
            "Supported with formula caveat",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "Energy",
            COW_FILENAME,
            "MEfeeds; MEIntake; MEmaint+peakmilk; gapME",
            "MJ/kg DM and MJ/cow/day",
            "per cow/day",
            "CALCULATED and MODEL_DERIVED",
            "Formula-derived target only",
            "Supported with missing inputs",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "Milk yield",
            COW_FILENAME,
            "hand-milked yield; Total milk performance",
            "L/cow/day",
            "per cow/day",
            "DIRECTLY_MEASURED and CALCULATED",
            "Candidate target; grouped validation blocked by missing IDs",
            "Supporting rule input",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "Warnings",
            COW_FILENAME,
            "DMI gap; gapwater; gapME; gapCP",
            "domain-specific daily units",
            "per cow/day",
            "CALCULATED",
            "Not ML labels",
            "Rule warning inputs with limitations",
            "READY_FOR_RULE_ENGINE",
        ),
    ]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def common_schema() -> dict[str, Any]:
    """Return only evidence-supported canonical fields."""

    fields = [
        (
            "source_file",
            "Source Office filename.",
            "filename",
            "record",
            "all four files",
            "all",
            "file path",
            "IDENTIFIER",
            "none",
            True,
            "traceability",
            "traceability",
            "READY",
        ),
        (
            "source_sheet",
            "Source worksheet or DOCX table.",
            "sheet/table name",
            "record",
            "all four files",
            "all",
            "sheet/table",
            "IDENTIFIER",
            "none",
            True,
            "traceability",
            "traceability",
            "READY",
        ),
        (
            "source_row_number",
            "One-based source row number.",
            "integer",
            "record",
            "all structured tables",
            "all",
            "source row",
            "IDENTIFIER",
            "none",
            True,
            "exclude from X",
            "traceability",
            "READY",
        ),
        (
            "sample_id",
            "Composite laboratory feed-sample identifier.",
            "identifier",
            "sample",
            COW_FILENAME + "; " + FODDER_FILENAME,
            "Raw data; Composites feeds",
            "LabN°; Lab N°",
            "IDENTIFIER",
            "string preservation only",
            True,
            "exclude from X",
            "join key with limitations",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "site_category",
            "Study site code: 1 lowlands; 2 highlands.",
            "category",
            "observation",
            COW_FILENAME,
            "Raw data",
            "sites",
            "OBSERVED",
            "1=lowlands; 2=highlands",
            True,
            "optional feature",
            "context",
            "READY",
        ),
        (
            "breed_category",
            "Broad source breed category Cross or exotic.",
            "category",
            "observation",
            COW_FILENAME,
            "Raw data",
            "cowbreed",
            "OBSERVED",
            "no inferred breed standardisation",
            False,
            "candidate feature",
            "none",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "age_years",
            "Cow age in years where the source cell is numeric.",
            "years",
            "observation",
            COW_FILENAME,
            "Raw data",
            "cowageinyears",
            "OBSERVED",
            "none",
            True,
            "candidate feature",
            "none",
            "BLOCKED_SOURCE_COLUMN_CONTAMINATION",
        ),
        (
            "parity",
            "Number of births.",
            "count",
            "observation",
            COW_FILENAME,
            "Raw data",
            "parity",
            "OBSERVED",
            "none",
            True,
            "candidate feature",
            "none",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "weight_kg",
            "Tape-estimated cow body weight before morning feeding.",
            "kg",
            "observation",
            COW_FILENAME,
            "Raw data",
            "Bodyweight",
            "DIRECTLY_MEASURED",
            "none",
            True,
            "candidate feature",
            "requirement input",
            "READY",
        ),
        (
            "lactation_stage",
            "Peak, Mid, or Late stage derived from days in milk.",
            "category",
            "observation",
            COW_FILENAME,
            "Raw data",
            "lactationperiod",
            "CALCULATED",
            "Peak <=100; Mid 101-200; Late >=201 days",
            True,
            "candidate feature",
            "context",
            "READY",
        ),
        (
            "days_in_milk",
            "Days spent being milked.",
            "days",
            "observation",
            COW_FILENAME,
            "Raw data",
            "daysinmilk",
            "OBSERVED",
            "none",
            True,
            "candidate feature",
            "context",
            "READY",
        ),
        (
            "hand_milk_yield_l_day",
            "Hand-milked yield recorded with graduated jars.",
            "L/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "hand-milked yield",
            "DIRECTLY_MEASURED",
            "none",
            True,
            "candidate target",
            "production input",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "total_milk_yield_l_day",
            "Hand-milked yield plus assumed calf suckling.",
            "L/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "Total milk performance",
            "CALCULATED",
            "Ass.calfmilk + hand-milked yield",
            True,
            "calculated target",
            "production input",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "dry_matter_served_kg_day",
            "Dry matter in feed served.",
            "kg DM/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "DM served",
            "DIRECTLY_MEASURED",
            "none",
            True,
            "observed target",
            "DMI input",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "dry_matter_leftover_kg_day",
            "Next-morning dry-matter leftovers.",
            "kg DM/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "leftover",
            "DIRECTLY_MEASURED",
            "none",
            True,
            "DMI input",
            "DMI input",
            "BLOCKED_NEGATIVE_VALUES",
        ),
        (
            "dry_matter_intake_kg_day",
            "Calculated daily DMI as served DM minus leftovers.",
            "kg DM/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "DMIcapacity (kgDM)",
            "CALCULATED",
            "DM served - leftover",
            True,
            "candidate target",
            "nutrition input",
            "BLOCKED_PENDING_LEFTOVER_CLARIFICATION",
        ),
        (
            "water_intake_l_day",
            "Water recorded from jerry cans provided to one cow daily.",
            "L/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "waterday",
            "OWNER_REPORTED",
            "none",
            True,
            "candidate target",
            "water validation",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "dry_matter_percent",
            "Composite-feed dry matter after oven drying.",
            "percent",
            "sample",
            COW_FILENAME,
            "Raw data",
            "DMfeeds",
            "DIRECTLY_MEASURED",
            "none",
            True,
            "candidate feature",
            "dry-matter conversion",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "crude_protein_percent",
            "Composite-feed crude protein percentage.",
            "percent",
            "sample",
            COW_FILENAME,
            "Raw data",
            "%Protein",
            "DIRECTLY_MEASURED",
            "none",
            True,
            "candidate feature",
            "protein calculation",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "crude_protein_intake_g_day",
            "Calculated CP intake.",
            "g/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "Cpintakeingr",
            "CALCULATED",
            "protein g/kg DM x DMI kg/day",
            True,
            "calculated target",
            "protein validation",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "crude_protein_requirement_g_day",
            "Model-derived CP requirement for maintenance and potential milk.",
            "g/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "TotalreqCP",
            "MODEL_DERIVED",
            "CPmaint + CPmilk",
            True,
            "not direct ML target",
            "protein validation",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "metabolizable_energy_intake_mj_day",
            "Calculated ME intake.",
            "MJ/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "MEIntake",
            "CALCULATED",
            "MEfeeds x DMI",
            True,
            "calculated target",
            "energy validation",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "metabolizable_energy_requirement_mj_day",
            "Model-derived ME requirement for maintenance and potential milk.",
            "MJ/cow/day",
            "per cow/day",
            COW_FILENAME,
            "Raw data",
            "MEmaint+peakmilk",
            "MODEL_DERIVED",
            "maintenance ME + potential-milk ME",
            True,
            "not direct ML target",
            "energy validation",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "feed_ingredient_list",
            "Exact comma-separated observed fodder ingredients.",
            "text",
            "per selected cow/day",
            FODDER_FILENAME,
            "Composites feeds",
            "SAMPLE ID",
            "OBSERVED",
            "no automatic standardisation",
            False,
            "supporting feature",
            "ingredient lookup",
            "READY_WITH_LIMITATIONS",
        ),
        (
            "calf_age_band",
            "Calf growth-stage band in the farmer bucket-feeding table.",
            "age band",
            "feeding-plan row",
            BUCKET_FILENAME,
            "Table 1",
            "Age",
            "OBSERVED",
            "none",
            True,
            "not lactating-cow ML",
            "calf guidance evidence",
            "SUPPORTING_ONLY",
        ),
        (
            "calf_milk_allocation_l_day",
            "Milk consumption per calf per day in reported farmer practice.",
            "L/calf/day",
            "per calf/day",
            BUCKET_FILENAME,
            "Table 1",
            "Milk consumption/day",
            "OBSERVED",
            "none",
            True,
            "not lactating-cow ML",
            "calf allocation support",
            "SUPPORTING_ONLY",
        ),
    ]
    names = [
        "canonical_field",
        "definition",
        "canonical_unit",
        "period",
        "source_file",
        "source_sheet",
        "source_column",
        "measurement_status",
        "conversion_rule",
        "conversion_documented",
        "ml_role",
        "rule_engine_role",
        "current_readiness",
    ]
    return {
        "schema_version": "rwanda_dairy_common_schema_v1",
        "audit_version": AUDIT_VERSION,
        "scope": "AUDIT_ONLY_NO_TRAINING",
        "unsupported_fields_are_omitted": True,
        "fields": [dict(zip(names, row, strict=True)) for row in fields],
        "limitations": [
            "No cow_id, farm_id, or observation date is supplied.",
            "The age column is contaminated with breed text for highland rows.",
            "Negative leftover values block unqualified DMI use.",
            "No recommendation or optimized-ration label exists.",
            "No unsupported unit conversion is authorised.",
        ],
    }


def build_inventory(
    files: dict[str, Path],
    workbooks: dict[str, WorkbookData],
    document: DocxData,
) -> dict[str, Any]:
    records = []
    for filename in EXPECTED_FILENAMES:
        path = files[filename]
        workbook = workbooks.get(filename)
        is_docx = filename == BUCKET_FILENAME
        if workbook:
            sheet_records = [
                {
                    "sheet_name": sheet.name,
                    "state": sheet.state,
                    "row_count": sheet.row_count,
                    "column_count": sheet.column_count,
                    "dimension": sheet.dimension,
                    "formula_count": sheet.formula_count,
                    "merged_cell_count": len(sheet.merged_ranges),
                    "comment_count": len(sheet.comments),
                }
                for sheet in workbook.sheets
            ]
            properties = workbook.properties
            archive_entries = workbook.archive_entries
        else:
            sheet_records = []
            properties = document.properties
            archive_entries = document.archive_entries
        searchable = " ".join(
            [
                json.dumps(properties, ensure_ascii=False),
                *(
                    str(value)
                    for workbook_item in ([workbook] if workbook else [])
                    for sheet in workbook_item.sheets
                    for row in sheet.rows[:20]
                    for value in row
                    if value is not None
                ),
                *(document.paragraphs if is_docx else []),
            ]
        ).casefold()
        records.append(
            {
                "filename": filename,
                "relative_path": path.relative_to(PROJECT_ROOT).as_posix(),
                "extension": path.suffix.casefold(),
                "file_size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "last_modified_utc": datetime.fromtimestamp(
                    path.stat().st_mtime,
                    tz=UTC,
                ).isoformat(),
                "opens_successfully": True,
                "excel_sheet_count": len(workbook.sheets) if workbook else None,
                "sheet_names": (
                    [sheet.name for sheet in workbook.sheets]
                    if workbook
                    else []
                ),
                "formulas_exist": (
                    any(sheet.formula_count for sheet in workbook.sheets)
                    if workbook
                    else False
                ),
                "formula_count": (
                    sum(sheet.formula_count for sheet in workbook.sheets)
                    if workbook
                    else 0
                ),
                "merged_cells_exist": (
                    any(sheet.merged_ranges for sheet in workbook.sheets)
                    if workbook
                    else False
                ),
                "hidden_sheets_exist": (
                    any(sheet.state != "visible" for sheet in workbook.sheets)
                    if workbook
                    else False
                ),
                "comments_or_notes_exist": (
                    any(sheet.comments for sheet in workbook.sheets)
                    if workbook
                    else bool(document.comments)
                ),
                "contains_metadata_or_citation_information": any(
                    token in searchable
                    for token in (
                        "author",
                        "journal",
                        "department",
                        "corresponding",
                        "supplemental",
                    )
                ),
                "contains_licence_information": (
                    "licen" in searchable or "creative commons" in searchable
                ),
                "package_properties": properties,
                "archive_entry_count": len(archive_entries),
                "sheets": sheet_records,
                "docx_table_count": len(document.tables) if is_docx else None,
            }
        )
    return {
        "audit_version": AUDIT_VERSION,
        "audit_scope": "READ_ONLY_NO_TRAINING",
        "source_directory": SOURCE_DIR.relative_to(PROJECT_ROOT).as_posix(),
        "expected_file_count": 4,
        "all_required_files_detected": len(records) == 4,
        "all_files_open_successfully": all(
            item["opens_successfully"] for item in records
        ),
        "files": records,
        "repository_citation": DATASET_CITATION,
        "raw_records_included": False,
    }


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )


def write_csv(path: str | Path, records: list[dict[str, Any]]) -> None:
    if not records:
        raise RwandaAuditError(f"Refusing empty CSV output: {path}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(records[0])
    with target.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(records)


__all__ = [
    "AUDIT_VERSION",
    "BUCKET_FILENAME",
    "COW_FILENAME",
    "DATASET_CITATION",
    "EXPECTED_FILENAMES",
    "EXPECTED_SHA256",
    "EXTERNAL_METHOD_EVIDENCE",
    "FODDER_FILENAME",
    "METADATA_FILENAME",
    "REPORT_DIR",
    "RwandaAuditError",
    "SCHEMA_PATH",
    "SOURCE_DIR",
    "VariableDefinition",
    "analyze_join",
    "build_inventory",
    "candidate_feature_register",
    "classify_feed_label",
    "classify_measurement_status",
    "classify_target",
    "column_profile",
    "common_schema",
    "cow_quality_issues",
    "dataframe_from_sheet",
    "detect_repeated_cows",
    "detect_target_fields",
    "discover_rwanda_files",
    "extract_unit_period",
    "farmlite_compatibility",
    "fodder_quality_issues",
    "formula_consistency_issues",
    "missing_value_report",
    "numeric_summary",
    "parse_metadata_definitions",
    "sha256_file",
    "target_matrix",
    "write_csv",
    "write_json",
]
