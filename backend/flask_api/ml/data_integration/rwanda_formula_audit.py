"""Read-only formula reconstruction for the Rwanda dairy clarification phase.

The functions in this module compare documented calculations with stored
workbook values. They never edit a source cell, choose between conflicting
interpretations, or create a cleaned dataset.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd


EXACT_TOLERANCE = 1e-9
ROUNDING_TOLERANCE = 0.01

FORMULA_STATUSES = {
    "FULLY_REPRODUCIBLE",
    "REPRODUCIBLE_WITH_TOLERANCE",
    "PARTIALLY_REPRODUCIBLE",
    "NOT_REPRODUCIBLE_MISSING_INPUT",
    "NOT_REPRODUCIBLE_CONFLICT",
    "FORMULA_NOT_DOCUMENTED",
    "UNCLEAR",
}


Calculator = Callable[[pd.Series], Any]


@dataclass(frozen=True)
class FormulaDefinition:
    """One documented or explicitly plausible source calculation."""

    formula_id: str
    domain: str
    target_field: str
    documented_formula: str
    required_inputs: tuple[str, ...]
    calculator: Calculator | None
    evidence_source: str
    interpretation: str = "DOCUMENTED"
    ambiguity: str = "NO"
    notes: str = ""


def _calf_milk(row: pd.Series) -> float:
    days = float(row["daysinmilk"])
    if days <= 60:
        return 6.0
    if days <= 90:
        return 4.0
    if days <= 120:
        return 2.0
    if days <= 200:
        return 1.0
    return 0.0


def _lactation_stage(row: pd.Series) -> str:
    days = float(row["daysinmilk"])
    if days <= 100:
        return "Peak"
    if days <= 200:
        return "Mid"
    return "Late"


FORMULA_DEFINITIONS = (
    FormulaDefinition(
        "RW-FORM-MILK-001",
        "MILK",
        "Ass.calfmilk",
        "6 L through day 60; 4 L days 61-90; 2 L days 91-120; "
        "1 L days 121-200; 0 L from day 201",
        ("daysinmilk",),
        _calf_milk,
        "Metadata.xlsx",
        notes=(
            "Uses days in milk as the available proxy for calf age. The "
            "allocation is estimated, not measured calf consumption."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-MILK-002",
        "MILK",
        "Total milk performance",
        "Ass.calfmilk + hand-milked yield",
        ("Ass.calfmilk", "hand-milked yield"),
        lambda row: float(row["Ass.calfmilk"])
        + float(row["hand-milked yield"]),
        "Metadata.xlsx and Mendeley reproduction notes",
    ),
    FormulaDefinition(
        "RW-FORM-MILK-003",
        "MILK",
        "gapmilk",
        "potentialmilk - Total milk performance",
        ("potentialmilk", "Total milk performance"),
        lambda row: float(row["potentialmilk"])
        - float(row["Total milk performance"]),
        "Metadata.xlsx and Mendeley reproduction notes",
    ),
    FormulaDefinition(
        "RW-FORM-MILK-004",
        "MILK",
        "%gapmilk",
        "gapmilk * 100 / potentialmilk",
        ("gapmilk", "potentialmilk"),
        lambda row: float(row["gapmilk"])
        * 100.0
        / float(row["potentialmilk"]),
        "Stored values and repository result semantics",
        notes=(
            "Metadata wording says total milk performance * 100 / potential "
            "milk, but the stored values reproduce gapmilk / potentialmilk."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-MILK-005",
        "MILK",
        "potentialmilk",
        "Estimated from similar breed in the same village",
        (),
        None,
        "Metadata.xlsx",
        interpretation="MODEL_DERIVED_UNDOCUMENTED_ALGORITHM",
        ambiguity="YES",
        notes="No row-level peer group or calculation algorithm is supplied.",
    ),
    FormulaDefinition(
        "RW-FORM-ANIMAL-001",
        "ANIMAL",
        "MW",
        "Bodyweight ** 0.75",
        ("Bodyweight",),
        lambda row: float(row["Bodyweight"]) ** 0.75,
        "Metadata.xlsx",
    ),
    FormulaDefinition(
        "RW-FORM-LACTATION-001",
        "LACTATION",
        "lactationperiod",
        "Peak: days 1-100; middle: days 101-200; late: day 201+",
        ("daysinmilk",),
        _lactation_stage,
        "Metadata.xlsx",
    ),
    FormulaDefinition(
        "RW-FORM-DMI-001",
        "DMI",
        "DMIR kg",
        "Bodyweight * 0.035",
        ("Bodyweight",),
        lambda row: float(row["Bodyweight"]) * 0.035,
        "Mendeley reproduction notes",
        ambiguity="YES",
        notes=(
            "Repository text prints BW x 3.5; stored values reproduce 3.5% "
            "of BW. This is a requirement estimate, not observed intake."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-DMI-002A",
        "DMI",
        "DMIcapacity (kgDM)",
        "DM served - leftover",
        ("DM served", "leftover"),
        lambda row: float(row["DM served"]) - float(row["leftover"]),
        "Mendeley reproduction notes",
        interpretation="DOCUMENTED_DMI_INTAKE_EQUATION",
        ambiguity="YES",
        notes=(
            "Reproduces the stored field, but the target name says capacity "
            "and negative leftovers make consumed-intake semantics unsafe."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-DMI-002B",
        "DMI",
        "DMIcapacity (kgDM)",
        "(120 / NDF feeds) * Bodyweight / 100",
        ("NDF feeds", "Bodyweight"),
        lambda row: (120.0 / float(row["NDF feeds"]))
        * float(row["Bodyweight"])
        / 100.0,
        "Metadata.xlsx",
        interpretation="DOCUMENTED_CAPACITY_EQUATION",
        ambiguity="YES",
        notes=(
            "This is the second documented meaning for the same stored "
            "field and does not reproduce every row."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-DMI-003",
        "DMI",
        "DMIindex",
        "120 / NDF feeds",
        ("NDF feeds",),
        lambda row: 120.0 / float(row["NDF feeds"]),
        "Metadata.xlsx",
        ambiguity="YES",
        notes="The NDF unit remains disputed between metadata and values.",
    ),
    FormulaDefinition(
        "RW-FORM-DMI-004",
        "DMI",
        "DMI gap",
        "DMIR kg - DMIcapacity (kgDM)",
        ("DMIR kg", "DMIcapacity (kgDM)"),
        lambda row: float(row["DMIR kg"])
        - float(row["DMIcapacity (kgDM)"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        ambiguity="YES",
        notes="The arithmetic is reproducible but inherits DMIcapacity ambiguity.",
    ),
    FormulaDefinition(
        "RW-FORM-DMI-005",
        "DMI",
        "%gapDMI",
        "DMI gap * 100 / DMIR kg",
        ("DMI gap", "DMIR kg"),
        lambda row: float(row["DMI gap"])
        * 100.0
        / float(row["DMIR kg"]),
        "Stored values and metadata",
        ambiguity="YES",
        notes="Inherits the unresolved DMIcapacity interpretation.",
    ),
    FormulaDefinition(
        "RW-FORM-WATER-001",
        "WATER",
        "waterrequi.",
        "12.3 + 2.15 * DMIR kg + 0.73 * potentialmilk",
        ("DMIR kg", "potentialmilk"),
        lambda row: 12.3
        + 2.15 * float(row["DMIR kg"])
        + 0.73 * float(row["potentialmilk"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        ambiguity="YES",
        notes=(
            "The formula is documented, but stored values are missing or "
            "mismatched for a subset of rows."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-WATER-002",
        "WATER",
        "gapwater",
        "waterrequi. - waterday",
        ("waterrequi.", "waterday"),
        lambda row: float(row["waterrequi."]) - float(row["waterday"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        notes="Repository language identifies waterday as water provided.",
    ),
    FormulaDefinition(
        "RW-FORM-WATER-003",
        "WATER",
        "%watergap",
        "gapwater * 100 / waterrequi.",
        ("gapwater", "waterrequi."),
        lambda row: float(row["gapwater"])
        * 100.0
        / float(row["waterrequi."]),
        "Metadata.xlsx",
    ),
    FormulaDefinition(
        "RW-FORM-CP-001",
        "PROTEIN",
        "Protein/content/gr/kg",
        "%Protein * 10",
        ("%Protein",),
        lambda row: float(row["%Protein"]) * 10.0,
        "Stored values and unit relationship",
    ),
    FormulaDefinition(
        "RW-FORM-CP-002",
        "PROTEIN",
        "Cpintakeingr",
        "Protein/content/gr/kg * DMIcapacity (kgDM)",
        ("Protein/content/gr/kg", "DMIcapacity (kgDM)"),
        lambda row: float(row["Protein/content/gr/kg"])
        * float(row["DMIcapacity (kgDM)"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        ambiguity="YES",
        notes="Reproducibility inherits the DMIcapacity target ambiguity.",
    ),
    FormulaDefinition(
        "RW-FORM-CP-003",
        "PROTEIN",
        "CPmaint=6.27*MW",
        "6.27 * MW",
        ("MW",),
        lambda row: 6.27 * float(row["MW"]),
        "Metadata.xlsx and Mendeley reproduction notes",
    ),
    FormulaDefinition(
        "RW-FORM-CP-004",
        "PROTEIN",
        "CPmilk",
        "82 * potentialmilk",
        ("potentialmilk",),
        lambda row: 82.0 * float(row["potentialmilk"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        notes="A subset of stored rows use values inconsistent with this formula.",
    ),
    FormulaDefinition(
        "RW-FORM-CP-005",
        "PROTEIN",
        "TotalreqCP",
        "CPmaint=6.27*MW + CPmilk",
        ("CPmaint=6.27*MW", "CPmilk"),
        lambda row: float(row["CPmaint=6.27*MW"])
        + float(row["CPmilk"]),
        "Metadata.xlsx",
    ),
    FormulaDefinition(
        "RW-FORM-CP-006A",
        "PROTEIN",
        "gapCP",
        "TotalreqCP - Cpintakeingr",
        ("TotalreqCP", "Cpintakeingr"),
        lambda row: float(row["TotalreqCP"])
        - float(row["Cpintakeingr"]),
        "Mendeley reproduction notes and stored values",
        interpretation="REPOSITORY_FORMULA",
        ambiguity="YES",
        notes="Reproduces stored values where CP intake is available.",
    ),
    FormulaDefinition(
        "RW-FORM-CP-006B",
        "PROTEIN",
        "gapCP",
        "TotalreqCP - CPmaint=6.27*MW",
        ("TotalreqCP", "CPmaint=6.27*MW"),
        lambda row: float(row["TotalreqCP"])
        - float(row["CPmaint=6.27*MW"]),
        "Metadata.xlsx wording",
        interpretation="METADATA_FORMULA",
        ambiguity="YES",
        notes="Conflicts with repository notes and stored values.",
    ),
    FormulaDefinition(
        "RW-FORM-CP-007",
        "PROTEIN",
        "%CP gap",
        "gapCP * 100 / TotalreqCP",
        ("gapCP", "TotalreqCP"),
        lambda row: float(row["gapCP"])
        * 100.0
        / float(row["TotalreqCP"]),
        "Metadata.xlsx",
    ),
    FormulaDefinition(
        "RW-FORM-ME-001",
        "ENERGY",
        "MEfeeds",
        "2.2 + 0.136 * G24 + 0.057 * CP + 0.0029 * CP**2",
        ("G24", "%Protein"),
        None,
        "Metadata.xlsx and Mendeley reproduction notes",
        ambiguity="YES",
        notes=(
            "G24 gas volume is not present in the supplied workbook; CP basis "
            "within this equation also requires confirmation."
        ),
    ),
    FormulaDefinition(
        "RW-FORM-ME-002",
        "ENERGY",
        "MEIntake",
        "MEfeeds * DMIcapacity (kgDM)",
        ("MEfeeds", "DMIcapacity (kgDM)"),
        lambda row: float(row["MEfeeds"])
        * float(row["DMIcapacity (kgDM)"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        ambiguity="YES",
        notes="Reproducibility inherits DMIcapacity ambiguity.",
    ),
    FormulaDefinition(
        "RW-FORM-ME-003",
        "ENERGY",
        "MW*0.589=Energyformaintenance",
        "MW * 0.589",
        ("MW",),
        lambda row: float(row["MW"]) * 0.589,
        "Metadata.xlsx and Mendeley reproduction notes",
    ),
    FormulaDefinition(
        "RW-FORM-ME-004",
        "ENERGY",
        "5.023*peakMilk",
        "5.023 * potentialmilk",
        ("potentialmilk",),
        lambda row: 5.023 * float(row["potentialmilk"]),
        "Metadata.xlsx and Mendeley reproduction notes",
        notes="A subset of stored rows use values inconsistent with this formula.",
    ),
    FormulaDefinition(
        "RW-FORM-ME-005",
        "ENERGY",
        "MEmaint+peakmilk",
        "MW*0.589=Energyformaintenance + 5.023*peakMilk",
        (
            "MW*0.589=Energyformaintenance",
            "5.023*peakMilk",
        ),
        lambda row: float(row["MW*0.589=Energyformaintenance"])
        + float(row["5.023*peakMilk"]),
        "Metadata.xlsx",
    ),
    FormulaDefinition(
        "RW-FORM-ME-006",
        "ENERGY",
        "gapME",
        "MEmaint+peakmilk - MEIntake",
        ("MEmaint+peakmilk", "MEIntake"),
        lambda row: float(row["MEmaint+peakmilk"])
        - float(row["MEIntake"]),
        "Metadata.xlsx and Mendeley reproduction notes",
    ),
    FormulaDefinition(
        "RW-FORM-ME-007",
        "ENERGY",
        "%MEgap",
        "gapME * 100 / MEmaint+peakmilk",
        ("gapME", "MEmaint+peakmilk"),
        lambda row: float(row["gapME"])
        * 100.0
        / float(row["MEmaint+peakmilk"]),
        "Metadata.xlsx",
    ),
)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return bool(result) if isinstance(result, bool) else False


def _numeric(value: Any) -> float | None:
    if _is_missing(value) or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _status_for_counts(
    *,
    exact: int,
    within_tolerance: int,
    mismatches: int,
    missing_inputs: int,
    stored_missing_with_inputs: int,
    comparable: int,
) -> str:
    matches = exact + within_tolerance
    if comparable == 0:
        return "NOT_REPRODUCIBLE_MISSING_INPUT"
    if mismatches and not matches:
        return "NOT_REPRODUCIBLE_CONFLICT"
    if mismatches or missing_inputs or stored_missing_with_inputs:
        return "PARTIALLY_REPRODUCIBLE"
    if within_tolerance:
        return "REPRODUCIBLE_WITH_TOLERANCE"
    return "FULLY_REPRODUCIBLE"


def audit_formula(
    frame: pd.DataFrame,
    definition: FormulaDefinition,
) -> dict[str, Any]:
    """Compare one definition to stored values without modifying the frame."""

    missing_columns = [
        column
        for column in (*definition.required_inputs, definition.target_field)
        if column not in frame.columns
    ]
    base = {
        "formula_id": definition.formula_id,
        "domain": definition.domain,
        "target_field": definition.target_field,
        "documented_formula": definition.documented_formula,
        "required_inputs": "; ".join(definition.required_inputs),
        "evidence_source": definition.evidence_source,
        "interpretation": definition.interpretation,
        "ambiguity": definition.ambiguity,
        "row_count": len(frame),
        "stored_value_count": (
            int(frame[definition.target_field].notna().sum())
            if definition.target_field in frame
            else 0
        ),
        "calculable_row_count": 0,
        "exact_match_count": 0,
        "tolerance_match_count": 0,
        "mismatch_count": 0,
        "missing_input_row_count": len(frame) if missing_columns else 0,
        "stored_missing_with_inputs_count": 0,
        "missing_required_columns": "; ".join(missing_columns),
        "maximum_absolute_difference": None,
        "mismatch_source_rows": "",
        "status": "UNCLEAR",
        "notes": definition.notes,
    }
    if definition.calculator is None:
        base["status"] = (
            "NOT_REPRODUCIBLE_MISSING_INPUT"
            if missing_columns
            else "FORMULA_NOT_DOCUMENTED"
        )
        return base
    if missing_columns:
        base["status"] = "NOT_REPRODUCIBLE_MISSING_INPUT"
        return base

    exact = 0
    within_tolerance = 0
    mismatches = 0
    missing_inputs = 0
    stored_missing = 0
    calculable = 0
    differences: list[float] = []
    mismatch_rows: list[int] = []

    for _, row in frame.iterrows():
        if any(_is_missing(row[column]) for column in definition.required_inputs):
            missing_inputs += 1
            continue
        try:
            expected = definition.calculator(row)
        except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
            missing_inputs += 1
            continue
        calculable += 1
        stored = row[definition.target_field]
        if _is_missing(stored):
            stored_missing += 1
            continue

        expected_number = _numeric(expected)
        stored_number = _numeric(stored)
        if expected_number is not None and stored_number is not None:
            difference = abs(stored_number - expected_number)
            differences.append(difference)
            if difference <= EXACT_TOLERANCE:
                exact += 1
            elif difference <= ROUNDING_TOLERANCE:
                within_tolerance += 1
            else:
                mismatches += 1
                mismatch_rows.append(int(row["source_row_number"]))
        elif str(stored).strip().casefold() == str(expected).strip().casefold():
            exact += 1
        else:
            mismatches += 1
            mismatch_rows.append(int(row["source_row_number"]))

    comparable = exact + within_tolerance + mismatches
    status = _status_for_counts(
        exact=exact,
        within_tolerance=within_tolerance,
        mismatches=mismatches,
        missing_inputs=missing_inputs,
        stored_missing_with_inputs=stored_missing,
        comparable=comparable,
    )
    base.update(
        {
            "calculable_row_count": calculable,
            "exact_match_count": exact,
            "tolerance_match_count": within_tolerance,
            "mismatch_count": mismatches,
            "missing_input_row_count": missing_inputs,
            "stored_missing_with_inputs_count": stored_missing,
            "maximum_absolute_difference": (
                max(differences) if differences else None
            ),
            "mismatch_source_rows": "; ".join(map(str, mismatch_rows)),
            "status": status,
        }
    )
    if status not in FORMULA_STATUSES:
        raise ValueError(f"Unsupported formula status: {status}")
    return base


def audit_all_formulas(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Run every documented and alternative interpretation."""

    return [audit_formula(frame, item) for item in FORMULA_DEFINITIONS]


def negative_leftover_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    """Analyse all negative leftovers without changing or selecting a meaning."""

    negatives = frame[pd.to_numeric(frame["leftover"], errors="coerce") < 0].copy()
    records = []
    for _, row in negatives.iterrows():
        served = float(row["DM served"])
        leftover = float(row["leftover"])
        stored_capacity = float(row["DMIcapacity (kgDM)"])
        records.append(
            {
                "source_row_number": int(row["source_row_number"]),
                "sample_id": row["LabN°"],
                "dm_served": served,
                "leftover": leftover,
                "dmfeeds": row["DMfeeds"],
                "stored_dmi_capacity": stored_capacity,
                "hand_milked_yield": row["hand-milked yield"],
                "total_milk_performance": row["Total milk performance"],
                "weight_kg": row["Bodyweight"],
                "lactation_stage": row["lactationperiod"],
                "served_minus_leftover": served - leftover,
                "served_plus_leftover": served + leftover,
                "ndf_capacity": (
                    120.0
                    / float(row["NDF feeds"])
                    * float(row["Bodyweight"])
                    / 100.0
                ),
            }
        )

    def match_count(key: str) -> int:
        return sum(
            abs(float(item[key]) - float(item["stored_dmi_capacity"]))
            <= ROUNDING_TOLERANCE
            for item in records
        )

    interpretations = [
        {
            "interpretation_id": "A",
            "interpretation": "Positive refused-feed convention",
            "candidate_calculation": "DM served - signed leftover",
            "stored_dmi_capacity_matches": match_count("served_minus_leftover"),
            "physical_conflict_count": sum(
                item["served_minus_leftover"] > item["dm_served"]
                for item in records
            ),
            "assessment": (
                "Arithmetic matches all stored DMIcapacity values, but every "
                "negative row produces intake greater than recorded served DM."
            ),
            "selected": False,
        },
        {
            "interpretation_id": "B",
            "interpretation": "Negative value denotes shortage or extra demand",
            "candidate_calculation": "DM served + absolute shortage",
            "stored_dmi_capacity_matches": match_count("served_minus_leftover"),
            "physical_conflict_count": 0,
            "assessment": (
                "Can reproduce a capacity or demand value, but cannot establish "
                "actual consumption because extra feed provision is unrecorded."
            ),
            "selected": False,
        },
        {
            "interpretation_id": "C",
            "interpretation": "Sign reversed during entry",
            "candidate_calculation": "DM served - absolute(leftover)",
            "stored_dmi_capacity_matches": match_count("served_plus_leftover"),
            "physical_conflict_count": sum(
                item["served_plus_leftover"] < 0 for item in records
            ),
            "assessment": (
                "Does not reproduce stored DMIcapacity and can produce negative "
                "candidate intake; source correction would be required."
            ),
            "selected": False,
        },
        {
            "interpretation_id": "D",
            "interpretation": "Leftover already included in another derived value",
            "candidate_calculation": "Use DM served unchanged",
            "stored_dmi_capacity_matches": sum(
                abs(item["dm_served"] - item["stored_dmi_capacity"])
                <= ROUNDING_TOLERANCE
                for item in records
            ),
            "physical_conflict_count": 0,
            "assessment": (
                "No negative-row stored capacity is explained by DM served "
                "alone; the source does not document double inclusion."
            ),
            "selected": False,
        },
        {
            "interpretation_id": "E",
            "interpretation": "Nonstandard source convention",
            "candidate_calculation": "UNCLEAR",
            "stored_dmi_capacity_matches": None,
            "physical_conflict_count": None,
            "assessment": "Not testable without an author-supplied definition.",
            "selected": False,
        },
    ]
    return {
        "negative_row_count": len(records),
        "records": records,
        "interpretations": interpretations,
        "source_values_modified": False,
        "selected_interpretation": None,
        "status": "AUTHOR_CLARIFICATION_REQUIRED",
    }


def age_column_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    """Describe age contamination without filling or changing any cell."""

    numeric = pd.to_numeric(frame["cowageinyears"], errors="coerce")
    source_nonmissing = frame["cowageinyears"].notna()
    text_mask = source_nonmissing & numeric.isna()
    texts = frame.loc[text_mask, "cowageinyears"].astype(str)
    other_age_columns = [
        column
        for column in frame.columns
        if column != "cowageinyears" and "age" in column.casefold()
    ]
    cowbreed_values = set(
        frame["cowbreed"].dropna().astype(str).str.strip().str.casefold()
    )
    text_values = set(texts.str.strip().str.casefold())
    return {
        "row_count": len(frame),
        "numeric_age_count": int(numeric.notna().sum()),
        "breed_text_count": int(text_mask.sum()),
        "missing_age_count": int((~source_nonmissing).sum()),
        "unique_text_count": int(texts.nunique()),
        "unique_text_entries": sorted(texts.unique().tolist()),
        "other_age_columns": other_age_columns,
        "displaced_age_values_found": False,
        "row_shift_evidence": "NOT_FOUND",
        "exactly_duplicates_cowbreed_values": bool(
            text_values and text_values.issubset(cowbreed_values)
        ),
        "cowbreed_values": sorted(
            frame["cowbreed"].dropna().astype(str).unique().tolist()
        ),
        "deterministic_repair_possible": False,
        "values_modified": False,
        "status": "SOURCE_CORRECTION_REQUIRED",
        "notes": (
            "The text entries are detailed cross-breed descriptions while "
            "cowbreed contains only broad Cross/exotic categories. No second "
            "age field or displaced numeric values were found."
        ),
    }


__all__ = [
    "EXACT_TOLERANCE",
    "FORMULA_DEFINITIONS",
    "FORMULA_STATUSES",
    "FormulaDefinition",
    "ROUNDING_TOLERANCE",
    "age_column_analysis",
    "audit_all_formulas",
    "audit_formula",
    "negative_leftover_analysis",
]
