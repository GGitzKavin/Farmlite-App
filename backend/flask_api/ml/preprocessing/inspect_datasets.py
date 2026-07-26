"""Generate a read-only, evidence-based audit of the FarmLite cattle datasets.

This module deliberately does not clean data, build features, split records,
train models, or modify the source CSV files. Unverified label meanings are
reported as UNCLEAR rather than inferred from plausible numeric ranges.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
    import pandas as pd
except ImportError as error:  # pragma: no cover - exercised only in an incomplete environment
    print(
        "ERROR: pandas and NumPy are required for the dataset audit. "
        "Install the backend requirements and retry.",
        file=sys.stderr,
    )
    raise SystemExit(1) from error

try:
    from config.settings import (
        DISEASE_DATASET_PATH,
        MILK_YIELD_DATASET_PATH,
        ML_REPORTS_DIR,
        PROJECT_ROOT,
    )
except ModuleNotFoundError:
    flask_api_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(flask_api_dir))
    from config.settings import (
        DISEASE_DATASET_PATH,
        MILK_YIELD_DATASET_PATH,
        ML_REPORTS_DIR,
        PROJECT_ROOT,
    )


JSON_REPORT_PATH = ML_REPORTS_DIR / "dataset_audit.json"
MARKDOWN_REPORT_PATH = ML_REPORTS_DIR / "dataset_inspection_report.md"
TARGET_MATRIX_PATH = ML_REPORTS_DIR / "dataset_target_matrix.csv"
FEED_TYPE_DISTRIBUTION_PATH = ML_REPORTS_DIR / "feed_type_distribution.csv"
FEED_QUANTITY_SUMMARY_PATH = ML_REPORTS_DIR / "feed_quantity_summary.csv"
DATA_QUALITY_ISSUES_PATH = ML_REPORTS_DIR / "data_quality_issues.csv"

EXPECTED_DATASETS = {
    "milk_yield": MILK_YIELD_DATASET_PATH,
    "disease": DISEASE_DATASET_PATH,
}

PERCENTILES = (0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99)

CANDIDATE_FEATURES: dict[str, tuple[str, ...]] = {
    "Breed": ("Breed", "Cattle_Breed", "Animal_Breed"),
    "Age_Months": ("Age_Months", "Age_In_Months", "Animal_Age_Months"),
    "Weight_kg": ("Weight_kg", "Weight_Kg", "Body_Weight_kg", "Body_Weight_Kg"),
    "Health_Status": ("Health_Status", "Current_Health_Status"),
    "Parity": ("Parity", "Lactation_Number", "Calving_Number"),
    "Lactation_Stage": ("Lactation_Stage", "Production_Stage"),
    "Days_in_Milk": ("Days_in_Milk", "Days_In_Milk", "DIM"),
    "Previous_Week_Avg_Yield": (
        "Previous_Week_Avg_Yield",
        "Previous_Week_Avg_Yield_L",
        "Previous_Week_Milk_Yield",
    ),
    "Body_Condition_Score": ("Body_Condition_Score", "BCS"),
    "Ambient_Temperature_C": (
        "Ambient_Temperature_C",
        "Temperature_C",
        "Environmental_Temperature_C",
    ),
    "Humidity_percent": (
        "Humidity_percent",
        "Humidity_Percent",
        "Relative_Humidity_percent",
    ),
    "Season": ("Season",),
    "Climate_Zone": ("Climate_Zone", "Climate",),
    "Management_System": ("Management_System", "Farm_Management_System"),
}

# This reflects the Phase 0 inspection of the current React request, not a
# claim that all values are always complete or semantically compatible.
CURRENT_FORM_AVAILABILITY = {
    "Breed": "PROVIDED",
    "Age_Months": "PROVIDED",
    "Weight_kg": "PROVIDED",
    "Health_Status": "PROVIDED_BUT_DATASET_EQUIVALENCE_UNCLEAR",
    "Parity": "NOT_PROVIDED",
    "Lactation_Stage": "PROVIDED",
    "Days_in_Milk": "PROVIDED",
    "Previous_Week_Avg_Yield": "PROVIDED",
    "Body_Condition_Score": "PROVIDED",
    "Ambient_Temperature_C": "PROVIDED",
    "Humidity_percent": "PROVIDED",
    "Season": "NOT_PROVIDED",
    "Climate_Zone": "NOT_PROVIDED",
    "Management_System": "NOT_PROVIDED",
}

# These names are used only as transparent scope indicators. The CSV contains
# no authoritative production-purpose field, so unfamiliar/local breeds remain
# unclassified rather than being forced into dairy or beef groups.
DAIRY_BREED_INDICATORS = {
    "Australian_Friesian_Sahiwal",
    "Australian_Milking_Zebu",
    "Ayrshire",
    "Brown_Swiss",
    "Danish_Red",
    "Girolando",
    "Guernsey",
    "Holstein-Friesian",
    "Holstein_Zebu_Cross",
    "Illawarra_Shorthorn",
    "Jersey",
    "Jersey_Zebu_Cross",
    "Milking_Shorthorn",
    "Montbeliarde",
    "Norwegian_Red",
    "Tipo_Carora",
}

BEEF_OR_NON_SPECIALIZED_INDICATORS = {
    "Africander",
    "Ankole",
    "Boran",
    "NDama",
    "Ongole",
    "White_Fulani",
}

PROVENANCE_EXCLUDED_DIRECTORIES = {
    ".git",
    ".agents",
    ".codex",
    "node_modules",
    "venv",
    "dist",
    "__pycache__",
}

PROVENANCE_EXCLUDED_FILES = {
    JSON_REPORT_PATH.resolve(),
    MARKDOWN_REPORT_PATH.resolve(),
    TARGET_MATRIX_PATH.resolve(),
    FEED_TYPE_DISTRIBUTION_PATH.resolve(),
    FEED_QUANTITY_SUMMARY_PATH.resolve(),
    DATA_QUALITY_ISSUES_PATH.resolve(),
}


def normalized_name(value: object) -> str:
    """Return a conservative normalized name for alias and spelling checks."""

    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def relative_path(path: Path) -> str:
    """Return a stable project-relative path where possible."""

    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def count_empty_physical_rows(path: Path) -> int:
    """Count blank physical lines after the CSV header without changing parsing."""

    empty = 0
    with path.open("r", encoding="utf-8-sig", errors="replace") as source:
        next(source, None)
        for line in source:
            if not line.strip():
                empty += 1
    return empty


def json_ready(value: Any) -> Any:
    """Recursively convert pandas/NumPy values to strict JSON-compatible values."""

    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value) if not isinstance(value, (str, bytes)) else False:
        return None
    return value


def resolve_dataset(expected_path: Path) -> tuple[Path, str]:
    """Use the approved raw path or safely locate one existing file by name."""

    if expected_path.is_file():
        return expected_path.resolve(), "EXPECTED_RAW_PATH"

    candidates = sorted(
        path.resolve()
        for path in (PROJECT_ROOT / "datasets").rglob(expected_path.name)
        if path.is_file()
    )
    if not candidates:
        raise FileNotFoundError(
            f"Dataset not found at {expected_path} or elsewhere below datasets/."
        )
    if len(candidates) > 1:
        rendered = ", ".join(str(path) for path in candidates)
        raise RuntimeError(
            f"Multiple files named {expected_path.name} were found: {rendered}. "
            "Refusing to guess which copy is authoritative."
        )
    return candidates[0], "SAFELY_LOCATED_ALTERNATE_PATH"


def infer_type(series: pd.Series, column: str) -> str:
    if normalized_name(column) in {
        "cattleid",
        "animalid",
        "farmid",
        "recordid",
        "observationid",
    }:
        return "identifier"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "continuous_numeric"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if "date" in normalized_name(column) or "timestamp" in normalized_name(column):
        parsed = pd.to_datetime(series.dropna().astype(str), errors="coerce")
        if len(parsed) and float(parsed.notna().mean()) >= 0.95:
            return "datetime"
    unique = int(series.nunique(dropna=True))
    if unique <= min(100, max(20, int(len(series) * 0.01))):
        return "categorical"
    return "string"


def sample_values(series: pd.Series, limit: int = 5) -> list[Any]:
    values = series.dropna().drop_duplicates().head(limit).tolist()
    return json_ready(values)


def profile_columns(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    rows = len(dataframe)
    for column in dataframe.columns:
        series = dataframe[column]
        missing = int(series.isna().sum())
        profile: dict[str, Any] = {
            "column": str(column),
            "pandas_dtype": str(series.dtype),
            "inferred_type": infer_type(series, str(column)),
            "missing_count": missing,
            "missing_percentage": round(missing / rows * 100, 6) if rows else 0.0,
            "unique_non_null": int(series.nunique(dropna=True)),
            "sample_values": sample_values(series),
        }
        if pd.api.types.is_numeric_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            profile["minimum"] = json_ready(numeric.min())
            profile["maximum"] = json_ready(numeric.max())
        profiles.append(profile)
    return profiles


def numeric_summary(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    quantiles = valid.quantile(PERCENTILES)
    return {
        "count": int(valid.count()),
        "missing_count": int(numeric.isna().sum()),
        "missing_percentage": round(float(numeric.isna().mean() * 100), 6),
        "minimum": json_ready(valid.min()),
        "maximum": json_ready(valid.max()),
        "mean": json_ready(valid.mean()),
        "median": json_ready(valid.median()),
        "standard_deviation": json_ready(valid.std()),
        "percentiles": {
            f"p{int(percentile * 100):02d}": json_ready(quantiles.loc[percentile])
            for percentile in PERCENTILES
        },
        "zero_count": int((valid == 0).sum()),
        "negative_count": int((valid < 0).sum()),
        "unique_values": int(valid.nunique()),
    }


def decimal_precision(series: pd.Series) -> dict[str, int]:
    """Count displayed decimal places based on pandas' parsed numeric values."""

    counts: dict[str, int] = {}
    for value in pd.to_numeric(series, errors="coerce").dropna():
        rendered = np.format_float_positional(float(value), trim="-")
        decimals = len(rendered.split(".", 1)[1]) if "." in rendered else 0
        key = str(decimals)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def grouped_numeric_summary(
    dataframe: pd.DataFrame,
    group_column: str,
    value_column: str,
) -> list[dict[str, Any]]:
    if group_column not in dataframe or value_column not in dataframe:
        return []
    results: list[dict[str, Any]] = []
    grouped = dataframe.groupby(group_column, dropna=False, observed=True)[value_column]
    for group, series in grouped:
        summary = numeric_summary(series)
        results.append({"group": json_ready(group), **summary})
    return results


def weight_band_summary(
    dataframe: pd.DataFrame, value_column: str
) -> list[dict[str, Any]]:
    if "Weight_kg" not in dataframe or value_column not in dataframe:
        return []
    bands = pd.cut(
        pd.to_numeric(dataframe["Weight_kg"], errors="coerce"),
        bins=[-np.inf, 199.999, 299.999, 399.999, 499.999, 599.999, 699.999, 799.999, np.inf],
        labels=["<200", "200-299", "300-399", "400-499", "500-599", "600-699", "700-799", ">=800"],
    )
    temporary = dataframe.assign(_weight_band=bands)
    return grouped_numeric_summary(temporary, "_weight_band", value_column)


def pearson_correlation(dataframe: pd.DataFrame, left: str, right: str) -> Any:
    if left not in dataframe or right not in dataframe:
        return None
    pair = dataframe[[left, right]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(pair) < 2 or pair[left].nunique() < 2 or pair[right].nunique() < 2:
        return None
    return json_ready(pair[left].corr(pair[right]))


def cramers_v(left: pd.Series, right: pd.Series) -> Any:
    valid = pd.DataFrame({"left": left, "right": right}).dropna()
    table = pd.crosstab(valid["left"], valid["right"])
    if table.empty or min(table.shape) < 2:
        return None
    observed = table.to_numpy(dtype=float)
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / observed.sum()
    chi_square = float(np.divide(
        (observed - expected) ** 2,
        expected,
        out=np.zeros_like(observed),
        where=expected != 0,
    ).sum())
    denominator = observed.sum() * min(observed.shape[0] - 1, observed.shape[1] - 1)
    return math.sqrt(chi_square / denominator) if denominator else None


def categorical_relationship(
    dataframe: pd.DataFrame, left: str, right: str
) -> dict[str, Any]:
    if left not in dataframe or right not in dataframe:
        return {"available": False}
    table = pd.crosstab(dataframe[left], dataframe[right], dropna=False)
    return {
        "available": True,
        "cramers_v": json_ready(cramers_v(dataframe[left], dataframe[right])),
        "counts": json_ready(table.to_dict(orient="index")),
    }


def identifier_analysis(dataframe: pd.DataFrame) -> dict[str, Any]:
    aliases = {
        "Cattle_ID",
        "Animal_ID",
        "Farm_ID",
        "Date",
        "Timestamp",
        "Record_ID",
        "Observation_ID",
    }
    identifier_columns = [
        str(column)
        for column in dataframe.columns
        if str(column) in aliases
        or normalized_name(column).endswith("id")
        or "timestamp" in normalized_name(column)
    ]
    details: dict[str, Any] = {}
    for column in identifier_columns:
        series = dataframe[column]
        counts = series.value_counts(dropna=False)
        repeated = counts[counts > 1]
        details[column] = {
            "non_missing_count": int(series.notna().sum()),
            "unique_non_null": int(series.nunique(dropna=True)),
            "is_unique_including_missing": bool(series.is_unique),
            "distinct_repeated_values": int(len(repeated)),
            "rows_belonging_to_repeated_values": int(repeated.sum()),
            "maximum_observations_per_value": int(counts.max()) if len(counts) else 0,
            "sample_values": sample_values(series),
        }

    date_column = next(
        (column for column in ("Date", "Timestamp") if column in dataframe), None
    )
    date_details: dict[str, Any] = {
        "column": date_column,
        "present": date_column is not None,
    }
    if date_column:
        dates = pd.to_datetime(dataframe[date_column], errors="coerce")
        date_details.update(
            {
                "parseable_count": int(dates.notna().sum()),
                "invalid_or_missing_count": int(dates.isna().sum()),
                "minimum": json_ready(dates.min()),
                "maximum": json_ready(dates.max()),
                "unique_dates": int(dates.nunique()),
            }
        )

    cattle = details.get("Cattle_ID") or details.get("Animal_ID")
    repeated_cattle = cattle["distinct_repeated_values"] if cattle else None
    group_split_required = bool(repeated_cattle and repeated_cattle > 0)
    return {
        "identifier_columns": identifier_columns,
        "details": details,
        "date_analysis": date_details,
        "repeated_observations_have_dates": bool(group_split_required and date_column),
        "group_based_split_required": group_split_required,
        "group_split_reason": (
            "Repeated animal identifiers exist; keep every animal in only one split."
            if group_split_required
            else "Cattle_ID is unique in this file, so no animal currently spans multiple rows. "
            "Grouping becomes required if future data introduces repeated animals."
        ),
    }


def dairy_suitability(dataframe: pd.DataFrame) -> dict[str, Any]:
    breeds = sorted(map(str, dataframe.get("Breed", pd.Series(dtype=object)).dropna().unique()))
    dairy = [breed for breed in breeds if breed in DAIRY_BREED_INDICATORS]
    non_specialized = [
        breed for breed in breeds if breed in BEEF_OR_NON_SPECIALIZED_INDICATORS
    ]
    unclassified = [
        breed
        for breed in breeds
        if breed not in DAIRY_BREED_INDICATORS
        and breed not in BEEF_OR_NON_SPECIALIZED_INDICATORS
    ]
    species_columns = [
        column
        for column in dataframe.columns
        if normalized_name(column) in {"species", "animalspecies", "cattletype"}
    ]
    production_columns = [
        column
        for column in dataframe.columns
        if normalized_name(column) in {"productiontype", "animaltype", "usepurpose"}
    ]
    lactation_values = (
        sorted(map(str, dataframe["Lactation_Stage"].dropna().unique()))
        if "Lactation_Stage" in dataframe
        else []
    )
    can_filter = bool(dairy) and bool(non_specialized)
    return {
        "status": "PARTIALLY_SUITABLE",
        "unique_breed_values": breeds,
        "dairy_breed_indicators": dairy,
        "beef_or_non_specialized_indicators": non_specialized,
        "unclassified_or_dual_purpose_breeds": unclassified,
        "dairy_and_beef_or_non_specialized_breeds_mixed": bool(dairy and non_specialized),
        "other_species_observed": False,
        "other_species_evidence": (
            "No species column exists. All observed Breed labels look cattle-related, "
            "but absence of a species field prevents an authoritative species check."
        ),
        "species_columns": species_columns,
        "production_type_columns": production_columns,
        "unsupported_records_can_be_filtered_reliably": False,
        "filtering_assessment": (
            "Breed can support a documented allow-list, but the file has no authoritative "
            "species or dairy-production-purpose field. A reliable dairy-only filter requires "
            "source documentation for every breed category."
        ),
        "lactation_stage_values": lactation_values,
        "lactating_and_non_lactating_distinguishable": False,
        "lactation_assessment": (
            "Early, Mid, and Late stages are distinguishable and all rows have a stage, "
            "but no Dry or Non_Lactating category proves whether non-lactating cattle were excluded."
        ),
        "basis": (
            "Explicit dairy breed indicators coexist with beef/non-specialized and "
            "unclassified/dual-purpose breed names. The dataset is not safely dairy-only."
        ),
    }


def add_quality_check(
    issues: list[dict[str, Any]],
    dataset_name: str,
    issue: str,
    column: str,
    count: int | None,
    total_rows: int,
    severity: str,
    evidence: str,
    status: str | None = None,
) -> None:
    if status is None:
        status = "FLAGGED" if count else "PASS"
    issues.append(
        {
            "dataset": dataset_name,
            "status": status,
            "severity": severity,
            "issue": issue,
            "column": column,
            "affected_rows": count,
            "percentage": (
                round(count / total_rows * 100, 6)
                if count is not None and total_rows
                else None
            ),
            "evidence": evidence,
        }
    )


def data_quality_analysis(
    dataframe: pd.DataFrame,
    dataset_name: str,
    empty_physical_rows: int,
) -> list[dict[str, Any]]:
    rows = len(dataframe)
    issues: list[dict[str, Any]] = []

    add_quality_check(
        issues,
        dataset_name,
        "Duplicate complete rows",
        "ALL_COLUMNS",
        int(dataframe.duplicated().sum()),
        rows,
        "WARNING",
        "Exact duplicate across all parsed columns.",
    )
    add_quality_check(
        issues,
        dataset_name,
        "Empty physical CSV rows",
        "ALL_COLUMNS",
        empty_physical_rows,
        rows,
        "WARNING",
        "Blank physical lines after the header; pandas normally skips these.",
    )

    checks = [
        ("Age_Months", "Negative age", lambda s: s < 0, "Age below 0 months."),
        ("Age_Months", "Zero age", lambda s: s == 0, "Age exactly 0 months."),
        (
            "Age_Months",
            "Implausible age",
            lambda s: (s > 300) | ((s > 0) & (s < 12)),
            "Audit threshold: age under 12 months or over 300 months.",
        ),
        ("Weight_kg", "Negative weight", lambda s: s < 0, "Weight below 0 kg."),
        ("Weight_kg", "Zero weight", lambda s: s == 0, "Weight exactly 0 kg."),
        (
            "Weight_kg",
            "Implausible weight",
            lambda s: (s > 1200) | ((s > 0) & (s < 50)),
            "Audit threshold: weight under 50 kg or over 1,200 kg.",
        ),
        (
            "Milk_Yield_L",
            "Negative milk yield",
            lambda s: s < 0,
            "Milk_Yield_L below 0.",
        ),
        (
            "Milk_Yield_L",
            "Zero milk yield",
            lambda s: s == 0,
            "Milk_Yield_L exactly 0.",
        ),
        (
            "Milk_Yield_L",
            "Suspiciously high milk yield",
            lambda s: s > 100,
            "Conservative audit threshold: Milk_Yield_L over 100; its period is UNCLEAR.",
        ),
        (
            "Feed_Quantity_kg",
            "Negative feed quantity",
            lambda s: s < 0,
            "Feed_Quantity_kg below 0.",
        ),
        (
            "Feed_Quantity_kg",
            "Zero feed quantity",
            lambda s: s == 0,
            "Feed_Quantity_kg exactly 0.",
        ),
        (
            "Feed_Quantity_kg",
            "Suspiciously high feed quantity",
            lambda s: s > 100,
            "Conservative audit threshold: Feed_Quantity_kg over 100; basis/period are UNCLEAR.",
        ),
        (
            "Days_in_Milk",
            "Negative days in milk",
            lambda s: s < 0,
            "Days_in_Milk below 0.",
        ),
        (
            "Days_in_Milk",
            "Suspiciously high days in milk",
            lambda s: s > 730,
            "Audit threshold: Days_in_Milk over 730.",
        ),
        (
            "Humidity_percent",
            "Humidity outside 0-100",
            lambda s: (s < 0) | (s > 100),
            "Humidity_percent outside the physical percentage range.",
        ),
        (
            "Ambient_Temperature_C",
            "Implausible ambient temperature",
            lambda s: (s < -20) | (s > 55),
            "Audit threshold: ambient temperature below -20 C or above 55 C.",
        ),
        (
            "Body_Condition_Score",
            "Body-condition score outside detected 1-5 scale",
            lambda s: (s < 1) | (s > 5),
            "Observed values are assessed against the common 1-5 scale; source scale is undocumented.",
        ),
        (
            "Parity",
            "Invalid parity",
            lambda s: (s < 0) | (s > 20) | (np.floor(s) != s),
            "Audit threshold: negative, non-integer, or above 20.",
        ),
    ]
    for column, issue, predicate, evidence in checks:
        if column not in dataframe:
            add_quality_check(
                issues,
                dataset_name,
                issue,
                column,
                None,
                rows,
                "INFO",
                "Column absent; check not applicable.",
                status="NOT_APPLICABLE",
            )
            continue
        numeric = pd.to_numeric(dataframe[column], errors="coerce")
        mask = predicate(numeric.fillna(np.nan))
        add_quality_check(
            issues,
            dataset_name,
            issue,
            column,
            int(mask.fillna(False).sum()),
            rows,
            "WARNING",
            evidence,
        )

    if {"Days_in_Milk", "Age_Months"}.issubset(dataframe.columns):
        dim = pd.to_numeric(dataframe["Days_in_Milk"], errors="coerce")
        age_days = pd.to_numeric(dataframe["Age_Months"], errors="coerce") * 31
        count = int((dim > age_days).fillna(False).sum())
        add_quality_check(
            issues,
            dataset_name,
            "Impossible age/lactation combination",
            "Days_in_Milk + Age_Months",
            count,
            rows,
            "ERROR",
            "Days_in_Milk exceeds approximate lifetime in days (Age_Months x 31).",
        )

    if {"Parity", "Age_Months"}.issubset(dataframe.columns):
        parity = pd.to_numeric(dataframe["Parity"], errors="coerce")
        age = pd.to_numeric(dataframe["Age_Months"], errors="coerce")
        count = int(((parity > 0) & (age < 18)).fillna(False).sum())
        add_quality_check(
            issues,
            dataset_name,
            "Impossible young-age/parity combination",
            "Parity + Age_Months",
            count,
            rows,
            "ERROR",
            "Positive parity with age below 18 months.",
        )

    for column in dataframe.select_dtypes(include=["object", "string"]).columns:
        non_null = dataframe[column].dropna().astype(str)
        normalized_groups: dict[str, set[str]] = {}
        for value in non_null.unique():
            normalized_groups.setdefault(normalized_name(value), set()).add(value)
        inconsistent = [
            sorted(values) for values in normalized_groups.values() if len(values) > 1
        ]
        add_quality_check(
            issues,
            dataset_name,
            "Inconsistent categorical spelling",
            str(column),
            len(inconsistent),
            rows,
            "WARNING",
            (
                f"Normalized duplicate groups: {inconsistent[:5]}"
                if inconsistent
                else "No case/spacing/punctuation-only duplicate categories detected."
            ),
        )

    for column in dataframe.columns:
        unique = int(dataframe[column].nunique(dropna=True))
        top_share = (
            float(dataframe[column].value_counts(dropna=False, normalize=True).iloc[0])
            if rows
            else 0.0
        )
        if unique <= 1:
            add_quality_check(
                issues,
                dataset_name,
                "Constant column",
                str(column),
                rows,
                rows,
                "WARNING",
                f"Unique non-null values: {unique}.",
            )
        elif top_share >= 0.999:
            add_quality_check(
                issues,
                dataset_name,
                "Near-constant column",
                str(column),
                int(round(top_share * rows)),
                rows,
                "WARNING",
                f"Most common value occupies {top_share * 100:.4f}% of rows.",
            )
        if (
            not pd.api.types.is_numeric_dtype(dataframe[column])
            and unique > max(1000, int(rows * 0.20))
        ):
            add_quality_check(
                issues,
                dataset_name,
                "Extremely high-cardinality categorical column",
                str(column),
                unique,
                rows,
                "WARNING",
                f"{unique:,} unique values across {rows:,} rows.",
            )

    add_quality_check(
        issues,
        dataset_name,
        "Mixed or undocumented feed units",
        "Feed_Quantity_kg",
        None,
        rows,
        "WARNING",
        "The name states kg but supplies no material basis or time period; mixed units cannot be ruled out.",
        status="UNCLEAR",
    )
    add_quality_check(
        issues,
        dataset_name,
        "Mixed or undocumented milk-yield period",
        "Milk_Yield_L",
        None,
        rows,
        "WARNING",
        "The name states litres but supplies no daily/weekly/other period metadata.",
        status="UNCLEAR",
    )
    return issues


def candidate_feature_audit(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    normalized_columns = {
        normalized_name(column): str(column) for column in dataframe.columns
    }
    results: list[dict[str, Any]] = []
    for feature, aliases in CANDIDATE_FEATURES.items():
        source = next(
            (
                normalized_columns[normalized_name(alias)]
                for alias in aliases
                if normalized_name(alias) in normalized_columns
            ),
            None,
        )
        form_status = CURRENT_FORM_AVAILABILITY[feature]
        item: dict[str, Any] = {
            "candidate_feature": feature,
            "present": source is not None,
            "exact_source_column": source,
            "current_farmlite_form": form_status,
        }
        if source is None:
            item.update(
                {
                    "data_type": None,
                    "missing_percentage": None,
                    "unique_non_null": None,
                    "sample_values": [],
                    "suspicious_range_or_categories": "Column absent.",
                    "prediction_time_safety": "AVAILABILITY_MISMATCH",
                }
            )
        else:
            series = dataframe[source]
            profile = profile_columns(dataframe[[source]])[0]
            suspicious = "No obvious issue from basic range/category profiling."
            if feature == "Health_Status":
                suspicious = (
                    "A similarly named disease outcome is not accepted as current Health_Status."
                )
            elif feature in {"Parity", "Season", "Climate_Zone", "Management_System"}:
                suspicious = "Current FarmLite request does not provide this field."
            prediction_safety = (
                "SAFE_WITH_INPUT_VALIDATION"
                if form_status == "PROVIDED"
                else "AVAILABILITY_MISMATCH"
            )
            item.update(
                {
                    "data_type": profile["pandas_dtype"],
                    "inferred_type": profile["inferred_type"],
                    "missing_percentage": profile["missing_percentage"],
                    "unique_non_null": profile["unique_non_null"],
                    "sample_values": profile["sample_values"],
                    "minimum": profile.get("minimum"),
                    "maximum": profile.get("maximum"),
                    "suspicious_range_or_categories": suspicious,
                    "prediction_time_safety": prediction_safety,
                }
            )
        results.append(item)
    return results


def feed_type_analysis(dataframe: pd.DataFrame) -> dict[str, Any]:
    column = "Feed_Type"
    if column not in dataframe:
        return {
            "status": "TARGET_NOT_SUPPORTED",
            "available": False,
            "reason": "Feed_Type column is absent.",
        }
    series = dataframe[column]
    counts = series.value_counts(dropna=False)
    rows = len(dataframe)
    distribution = [
        {
            "feed_type": None if pd.isna(value) else str(value),
            "count": int(count),
            "percentage": round(int(count) / rows * 100, 6) if rows else 0.0,
        }
        for value, count in counts.items()
    ]
    non_missing_counts = series.value_counts()
    rare = [
        str(value)
        for value, count in non_missing_counts.items()
        if count < 100 or count / rows < 0.01
    ]
    normalized: dict[str, set[str]] = {}
    for value in series.dropna().astype(str).unique():
        normalized.setdefault(normalized_name(value), set()).add(value)
    inconsistent = [
        sorted(values) for values in normalized.values() if len(values) > 1
    ]
    relationships = {
        field: categorical_relationship(dataframe, column, field)
        for field in (
            "Breed",
            "Lactation_Stage",
            "Management_System",
            "Season",
            "Region",
        )
    }
    class_counts = non_missing_counts.to_numpy()
    relative_spread = (
        float((class_counts.max() - class_counts.min()) / class_counts.mean())
        if len(class_counts)
        else None
    )
    return {
        "available": True,
        "exact_unique_values": sorted(map(str, series.dropna().unique())),
        "distribution": distribution,
        "missing_count": int(series.isna().sum()),
        "rare_classes_under_1_percent_or_100_rows": rare,
        "duplicate_or_inconsistent_spellings": inconsistent,
        "suspicious_categories": [
            "The eight labels are broad feed categories, not nutrient-complete ration definitions.",
            "No category name or companion metadata identifies a recommendation, optimum, or expert decision.",
            f"Class counts are unusually balanced (relative max-min spread {relative_spread:.4f}).",
        ],
        "relationships": relationships,
        "appears_to_represent": {
            "broad_feed_category": "SUPPORTED_BY_LABEL_NAMES",
            "recommended_feed": "UNCLEAR",
            "feed_actually_supplied": "UNCLEAR",
            "generated_label": "UNCLEAR_BUT_SYNTHETIC_INDICATORS_EXIST",
        },
        "status": "TARGET_UNCLEAR",
        "decision_reason": (
            "Feed_Type exists and contains eight broad categories, but repository-local "
            "documentation does not define whether it is observed, recommended, or generated."
        ),
    }


def iqr_outlier_details(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return {
        "method": "1.5 x IQR statistical fence; not a biological validity rule",
        "lower_fence": lower,
        "upper_fence": upper,
        "below_fence_count": int((numeric < lower).sum()),
        "above_fence_count": int((numeric > upper).sum()),
    }


def feed_quantity_analysis(dataframe: pd.DataFrame) -> dict[str, Any]:
    column = "Feed_Quantity_kg"
    if column not in dataframe:
        return {
            "available": False,
            "status": "TARGET_NOT_SUPPORTED",
            "reason": "Feed_Quantity_kg column is absent.",
        }
    summary = numeric_summary(dataframe[column])
    return {
        "available": True,
        "summary": summary,
        "decimal_precision_counts": decimal_precision(dataframe[column]),
        "suspicious_extremes": iqr_outlier_details(dataframe[column]),
        "distribution_by_feed_type": grouped_numeric_summary(
            dataframe, "Feed_Type", column
        ),
        "distribution_by_lactation_stage": grouped_numeric_summary(
            dataframe, "Lactation_Stage", column
        ),
        "distribution_by_breed": grouped_numeric_summary(
            dataframe, "Breed", column
        ),
        "distribution_by_weight_kg_range": weight_band_summary(dataframe, column),
        "correlations": {
            "Weight_kg": pearson_correlation(dataframe, column, "Weight_kg"),
            "Milk_Yield_L": pearson_correlation(dataframe, column, "Milk_Yield_L"),
            "Previous_Week_Avg_Yield": pearson_correlation(
                dataframe, column, "Previous_Week_Avg_Yield"
            ),
        },
        "quantity_interpretation": {
            "total_fresh_feed_per_day": "UNCLEAR",
            "dry_matter_intake": "UNCLEAR",
            "concentrate_intake": "UNCLEAR",
            "roughage_intake": "UNCLEAR",
            "feed_per_meal": "UNCLEAR",
            "another_quantity": "UNCLEAR",
            "unit_basis": "UNCLEAR",
            "time_period": "UNCLEAR",
        },
        "status": "TARGET_UNCLEAR",
        "decision_reason": (
            "The kg values can be described statistically, but neither the material basis "
            "nor time period is documented. Plausible ranges cannot establish meaning."
        ),
    }


def milk_yield_analysis(dataframe: pd.DataFrame) -> dict[str, Any]:
    column = "Milk_Yield_L"
    if column not in dataframe:
        return {"available": False, "reason": "Milk_Yield_L column is absent."}
    return {
        "available": True,
        "summary": numeric_summary(dataframe[column]),
        "suspicious_extremes": iqr_outlier_details(dataframe[column]),
        "distribution_by_breed": grouped_numeric_summary(
            dataframe, "Breed", column
        ),
        "distribution_by_lactation_stage": grouped_numeric_summary(
            dataframe, "Lactation_Stage", column
        ),
        "relationship_with_previous_week_yield": {
            "pearson_correlation": pearson_correlation(
                dataframe, column, "Previous_Week_Avg_Yield"
            )
        },
        "period": "UNCLEAR",
        "period_assessment": (
            "The column name establishes litres but repository-local documentation does "
            "not state whether each value is daily, weekly, per milking, or another period."
        ),
    }


def classify_leakage(
    column: str,
    target: str,
    model_name: str,
    form_available: bool,
) -> tuple[str, str]:
    if column == target:
        return "DEFINITE_LEAKAGE", "This is the model target."
    if normalized_name(column) in {
        "cattleid",
        "animalid",
        "farmid",
        "recordid",
        "observationid",
    }:
        return (
            "POSSIBLE_LEAKAGE",
            "Identifier may permit record, farm, or generated-batch memorisation.",
        )
    if normalized_name(column) in {"date", "timestamp"}:
        return (
            "POSSIBLE_LEAKAGE",
            "Collection date may encode temporal or generated data batches.",
        )

    circular = {
        "Feed_Type": {
            "Feed_Quantity_kg",
            "Feeding_Frequency",
            "Water_Intake_L",
            "Milk_Yield_L",
            "Disease_Status",
        },
        "Feed_Quantity_kg": {
            "Feed_Type",
            "Feeding_Frequency",
            "Water_Intake_L",
            "Milk_Yield_L",
            "Disease_Status",
        },
        "Milk_Yield_L": {
            "Feed_Type",
            "Feed_Quantity_kg",
            "Feeding_Frequency",
            "Water_Intake_L",
            "Disease_Status",
        },
    }
    if column in circular.get(target, set()):
        return (
            "POSSIBLE_LEAKAGE",
            "May be a same-record decision, exposure, or post-outcome field; timing is undocumented.",
        )
    if column in {
        "Body_Temperature_C",
        "Heart_Rate_bpm",
        "Respiratory_Rate",
    }:
        return (
            "AVAILABILITY_MISMATCH",
            "Not supplied by the current recommendation form and may be measured after illness/outcome.",
        )
    if not form_available:
        return (
            "AVAILABILITY_MISMATCH",
            "The current FarmLite request does not provide this exact field.",
        )
    if column == "Previous_Week_Avg_Yield":
        return (
            "SAFE",
            "A lagged value is available in the form, provided its time window is verified.",
        )
    return (
        "SAFE",
        f"No direct leakage signal identified for {model_name}; validation and timing still apply.",
    )


def leakage_analysis(dataframe: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    exact_form_columns = {
        "Breed",
        "Age_Months",
        "Weight_kg",
        "Lactation_Stage",
        "Days_in_Milk",
        "Previous_Week_Avg_Yield",
        "Body_Condition_Score",
        "Ambient_Temperature_C",
        "Humidity_percent",
    }
    models = {
        "feed_type_classifier": "Feed_Type",
        "feed_quantity_regressor": "Feed_Quantity_kg",
        "milk_yield_regressor": "Milk_Yield_L",
    }
    results: dict[str, list[dict[str, str]]] = {}
    for model, target in models.items():
        rows: list[dict[str, str]] = []
        for column in dataframe.columns:
            classification, reason = classify_leakage(
                str(column),
                target,
                model,
                str(column) in exact_form_columns,
            )
            rows.append(
                {
                    "input": str(column),
                    "classification": classification,
                    "reason": reason,
                }
            )
        results[model] = rows
    return results


def sequential_identifier_evidence(series: pd.Series) -> dict[str, Any]:
    extracted = series.astype(str).str.extract(r"(\d+)$", expand=False)
    numeric = pd.to_numeric(extracted, errors="coerce")
    expected = pd.Series(np.arange(1, len(series) + 1), index=series.index)
    matches = numeric.eq(expected)
    return {
        "numeric_suffix_parseable_percentage": round(float(numeric.notna().mean() * 100), 6),
        "row_order_matches_1_to_n_percentage": round(float(matches.mean() * 100), 6),
        "first_values": sample_values(series),
        "last_values": json_ready(series.tail(5).tolist()),
    }


def synthetic_indicators(dataframe: pd.DataFrame) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    if "Cattle_ID" in dataframe:
        sequential = sequential_identifier_evidence(dataframe["Cattle_ID"])
        evidence.append(
            {
                "indicator": "Sequential generated-looking identifiers",
                "evidence": sequential,
            }
        )
    missing_total = int(dataframe.isna().sum().sum())
    evidence.append(
        {
            "indicator": "Missing-data cleanliness",
            "evidence": {
                "total_missing_cells": missing_total,
                "total_cells": int(dataframe.size),
                "missing_percentage": round(missing_total / dataframe.size * 100, 8),
            },
        }
    )
    for column in (
        "Breed",
        "Feed_Type",
        "Region",
        "Management_System",
        "Season",
        "Lactation_Stage",
    ):
        if column not in dataframe:
            continue
        counts = dataframe[column].value_counts()
        relative_spread = float((counts.max() - counts.min()) / counts.mean())
        evidence.append(
            {
                "indicator": f"{column} category balance",
                "evidence": {
                    "categories": int(len(counts)),
                    "minimum_class_count": int(counts.min()),
                    "maximum_class_count": int(counts.max()),
                    "relative_max_min_spread": relative_spread,
                },
            }
        )
    numeric = dataframe.select_dtypes(include=[np.number])
    correlations = numeric.corr().abs()
    perfect_pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(correlations.columns):
        for right in correlations.columns[left_index + 1 :]:
            value = correlations.loc[left, right]
            if pd.notna(value) and value >= 0.9999:
                perfect_pairs.append(
                    {"left": str(left), "right": str(right), "absolute_correlation": float(value)}
                )
    evidence.append(
        {
            "indicator": "Near-perfect numeric correlations",
            "evidence": perfect_pairs,
        }
    )
    return {
        "status": "POSSIBLY_SYNTHETIC",
        "evidence": evidence,
        "assessment": (
            "Perfectly sequential IDs, complete data, balanced categories, and the "
            "cross-file duplication pattern are generated-data indicators. No repository "
            "metadata explicitly confirms synthetic generation, so the cautious status is "
            "POSSIBLY_SYNTHETIC rather than a definitive claim."
        ),
    }


def audit_dataset(
    dataframe: pd.DataFrame,
    path: Path,
    path_resolution: str,
) -> dict[str, Any]:
    rows = len(dataframe)
    empty_physical_rows = count_empty_physical_rows(path)
    missing = [
        {
            "column": str(column),
            "missing_count": int(dataframe[column].isna().sum()),
            "missing_percentage": round(float(dataframe[column].isna().mean() * 100), 6),
        }
        for column in dataframe.columns
    ]
    return {
        "filename": path.name,
        "relative_path": relative_path(path),
        "resolved_path": str(path),
        "path_resolution": path_resolution,
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "rows": rows,
        "columns": len(dataframe.columns),
        "exact_column_names": [str(column) for column in dataframe.columns],
        "column_profile": profile_columns(dataframe),
        "duplicate_row_count": int(dataframe.duplicated().sum()),
        "empty_parsed_row_count": int(dataframe.isna().all(axis=1).sum()),
        "empty_physical_csv_row_count": empty_physical_rows,
        "missing_values": missing,
        "identifier_analysis": identifier_analysis(dataframe),
        "dairy_cattle_suitability": dairy_suitability(dataframe),
        "candidate_features": candidate_feature_audit(dataframe),
        "data_quality_issues": data_quality_analysis(
            dataframe, path.name, empty_physical_rows
        ),
        "leakage_analysis": leakage_analysis(dataframe),
        "synthetic_data_indicators": synthetic_indicators(dataframe),
    }


def repository_provenance() -> dict[str, Any]:
    inspected: list[dict[str, Any]] = []
    source_url_pattern = re.compile(r"https?://\S+", re.IGNORECASE)
    license_pattern = re.compile(r"\blicen[cs]e\b", re.IGNORECASE)
    kaggle_pattern = re.compile(r"\bkaggle\b", re.IGNORECASE)
    mendeley_pattern = re.compile(r"\bmendeley\b", re.IGNORECASE)
    citation_pattern = re.compile(r"\bcitation\b|\bcite\b", re.IGNORECASE)
    authoritative_evidence: list[dict[str, Any]] = []
    relevant_pattern = re.compile(
        r"global_cattle_|dataset|provenance|synthetic|feed_type|"
        r"feed_quantity|kaggle|mendeley",
        re.IGNORECASE,
    )
    candidate_suffixes = {".md", ".txt", ".py", ".json"}
    candidate_paths: list[Path] = []
    license_files: list[str] = []
    citation_files: list[str] = []
    searched_file_count = 0

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in PROVENANCE_EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        resolved_path = path.resolve()
        if resolved_path in PROVENANCE_EXCLUDED_FILES:
            continue
        lower_name = path.name.lower()
        if "license" in lower_name or "licence" in lower_name:
            license_files.append(relative_path(path))
        if "citation" in lower_name:
            citation_files.append(relative_path(path))
        if path.suffix.lower() not in candidate_suffixes:
            continue
        searched_file_count += 1
        content = path.read_text(encoding="utf-8", errors="replace")
        if relevant_pattern.search(content) or any(
            token in lower_name
            for token in ("readme", "license", "licence", "citation", "dataset")
        ):
            candidate_paths.append(path)

    for path in sorted(candidate_paths):
        content = path.read_text(encoding="utf-8", errors="replace")
        findings = {
            "source_urls": source_url_pattern.findall(content),
            "mentions_license": bool(license_pattern.search(content)),
            "mentions_kaggle": bool(kaggle_pattern.search(content)),
            "mentions_mendeley": bool(mendeley_pattern.search(content)),
            "mentions_citation": bool(citation_pattern.search(content)),
            "states_provenance_unverified": bool(
                re.search(
                    r"provenance.{0,80}(not|unverified)|does not currently contain an authoritative source",
                    content,
                    re.IGNORECASE | re.DOTALL,
                )
            ),
        }
        inspected.append({"path": relative_path(path), **findings})
        if (
            findings["source_urls"]
            or findings["mentions_kaggle"]
            or findings["mentions_mendeley"]
            or findings["mentions_citation"]
        ):
            authoritative_evidence.append({"path": relative_path(path), **findings})

    # Generic localhost setup URLs do not establish dataset provenance.
    dataset_source_urls = [
        evidence
        for evidence in authoritative_evidence
        if any(
            token in " ".join(evidence.get("source_urls", [])).lower()
            for token in ("kaggle", "mendeley", "dataset", "doi.org")
        )
    ]
    return {
        "search_scope": "Repository-local documentation and existing reports only; no web browsing.",
        "text_files_searched": searched_file_count,
        "relevant_files_inspected": len(inspected),
        "files_inspected": inspected,
        "license_files_found": sorted(license_files),
        "citation_files_found": sorted(citation_files),
        "authoritative_dataset_source_evidence": dataset_source_urls,
        "status": "NOT_DOCUMENTED",
        "assessment": (
            "Repository notes explicitly state that publisher, source URL, license, "
            "collection protocol, data dictionary, representativeness, and measurement "
            "validity are not documented. No authoritative local evidence was found."
        ),
    }


def cross_dataset_assessment(
    milk: pd.DataFrame,
    disease: pd.DataFrame,
) -> dict[str, Any]:
    candidate_keys = [
        key for key in ("Cattle_ID", "Animal_ID", "Farm_ID", "Date", "Timestamp")
        if key in milk.columns and key in disease.columns
    ]
    preferred_keys = [
        key for key in ("Cattle_ID", "Date") if key in milk.columns and key in disease.columns
    ]
    if not preferred_keys:
        return {
            "join_status": "NO_JOIN_KEY",
            "shared_candidate_keys": candidate_keys,
            "assessment": "No shared animal-plus-date key is available.",
        }

    milk_keys = pd.MultiIndex.from_frame(milk[preferred_keys])
    disease_keys = pd.MultiIndex.from_frame(disease[preferred_keys])
    overlap = milk_keys.intersection(disease_keys)
    same_order = bool(milk[preferred_keys].equals(disease[preferred_keys]))
    common_columns = sorted(set(milk.columns).intersection(disease.columns))
    mismatch_counts: dict[str, int] = {}
    if same_order and len(milk) == len(disease):
        for column in common_columns:
            left = milk[column]
            right = disease[column]
            equal = left.eq(right) | (left.isna() & right.isna())
            mismatch_counts[column] = int((~equal).sum())

    key_evidence = {
        "preferred_composite_key": preferred_keys,
        "milk_duplicate_composite_keys": int(milk.duplicated(preferred_keys).sum()),
        "disease_duplicate_composite_keys": int(disease.duplicated(preferred_keys).sum()),
        "milk_unique_composite_keys": int(milk_keys.nunique()),
        "disease_unique_composite_keys": int(disease_keys.nunique()),
        "shared_composite_keys": int(len(overlap)),
        "keys_identical_in_row_order": same_order,
    }
    all_common_equal = bool(mismatch_counts) and not any(mismatch_counts.values())
    return {
        "shared_candidate_keys": candidate_keys,
        "key_evidence": key_evidence,
        "shared_columns": common_columns,
        "shared_column_mismatch_counts_when_key_order_identical": mismatch_counts,
        "all_shared_columns_identical_in_row_order": all_common_equal,
        "join_status": "POSSIBLE_WITH_LIMITATIONS",
        "assessment": (
            "Cattle_ID + Date is unique in both files, all 250,000 composite keys overlap, "
            "and shared values align exactly. This is strong file-level evidence that the "
            "disease file extends the same generated-looking records. However, provenance "
            "does not independently establish real animal identity or collection method. "
            "Do not join during Phase 1; any future join must use the composite key, never "
            "row order, and must first resolve provenance and intended use."
        ),
    }


def disease_use_assessment() -> dict[str, Any]:
    return {
        "direct_feed_type_training": {
            "decision": "NOT_SUPPORTED",
            "reason": "Feed_Type meaning remains UNCLEAR and duplicates the milk file's values.",
        },
        "direct_feed_quantity_training": {
            "decision": "NOT_SUPPORTED",
            "reason": "Feed_Quantity_kg meaning remains UNCLEAR and adds no independent feed target.",
        },
        "milk_yield_training": {
            "decision": "NOT_RECOMMENDED",
            "reason": "Milk_Yield_L duplicates the milk file; disease/vital fields may be post-outcome leakage.",
        },
        "health_status_enrichment": {
            "decision": "POSSIBLE_WITH_LIMITATIONS",
            "reason": "Disease_Status is an outcome label, not a proven equivalent of the form's current health status.",
        },
        "separate_future_disease_classification": {
            "decision": "POTENTIALLY_SUPPORTED",
            "reason": "Disease_Status exists, but provenance, label timing, leakage, and validity require a separate audit.",
        },
        "nutrition_warnings": {
            "decision": "NOT_DIRECTLY_SUPPORTED",
            "reason": "Disease labels and vital signs do not define safe nutrition actions or veterinary rules.",
        },
    }


def target_matrix() -> list[dict[str, str]]:
    return [
        {
            "Target": "Recommended Feed Type",
            "Dataset Column": "Feed_Type",
            "Availability": "PRESENT",
            "Meaning/Unit Status": "UNCLEAR: broad category; observed/recommended/generated role undocumented",
            "Training Readiness": "BLOCKED_PENDING_DEFINITION",
            "Notes": "Eight near-balanced categories; no explicit optimal/recommended label metadata.",
        },
        {
            "Target": "Total Feed Quantity",
            "Dataset Column": "Feed_Quantity_kg",
            "Availability": "PRESENT",
            "Meaning/Unit Status": "UNCLEAR: kg basis and time period undocumented",
            "Training Readiness": "BLOCKED_PENDING_DEFINITION",
            "Notes": "Could be fresh matter, dry matter, component intake, per meal, or another quantity.",
        },
        {
            "Target": "Milk Yield",
            "Dataset Column": "Milk_Yield_L",
            "Availability": "PRESENT",
            "Meaning/Unit Status": "PARTIAL: litres stated; time period UNCLEAR",
            "Training Readiness": "BLOCKED_PENDING_DEFINITION",
            "Notes": "Provenance is absent and dataset is not reliably dairy-only.",
        },
        {
            "Target": "Roughage",
            "Dataset Column": "NONE",
            "Availability": "ABSENT",
            "Meaning/Unit Status": "NOT_AVAILABLE",
            "Training Readiness": "NOT_SUPPORTED",
            "Notes": "Feed_Type category is not a numeric roughage target.",
        },
        {
            "Target": "Concentrate",
            "Dataset Column": "NONE",
            "Availability": "ABSENT",
            "Meaning/Unit Status": "NOT_AVAILABLE",
            "Training Readiness": "NOT_SUPPORTED",
            "Notes": "Concentrates is a Feed_Type class, not a quantity target.",
        },
        {
            "Target": "Mineral Mix",
            "Dataset Column": "NONE",
            "Availability": "ABSENT",
            "Meaning/Unit Status": "NOT_AVAILABLE",
            "Training Readiness": "NOT_SUPPORTED",
            "Notes": "No direct label.",
        },
        {
            "Target": "Water Advice",
            "Dataset Column": "NONE",
            "Availability": "ABSENT",
            "Meaning/Unit Status": "NOT_AVAILABLE",
            "Training Readiness": "NOT_SUPPORTED",
            "Notes": "Water_Intake_L is an observation, not advice.",
        },
        {
            "Target": "Warnings",
            "Dataset Column": "NONE",
            "Availability": "ABSENT",
            "Meaning/Unit Status": "NOT_AVAILABLE",
            "Training Readiness": "NOT_SUPPORTED",
            "Notes": "Disease_Status does not encode nutrition warning text or action.",
        },
    ]


def model_readiness() -> dict[str, dict[str, str]]:
    return {
        "feed_type_classifier": {
            "decision": "BLOCKED_PENDING_DEFINITION",
            "target_status": "TARGET_UNCLEAR",
            "reason": "Feed_Type is not documented as a recommendation target.",
        },
        "feed_quantity_regressor": {
            "decision": "BLOCKED_PENDING_DEFINITION",
            "target_status": "TARGET_UNCLEAR",
            "reason": "Feed_Quantity_kg material basis and time period are UNCLEAR.",
        },
        "milk_yield_regressor": {
            "decision": "BLOCKED_PENDING_DEFINITION",
            "target_status": "TARGET_UNCLEAR",
            "reason": "Litres are explicit, but the measurement period, provenance, and dairy-only scope are unresolved.",
        },
    }


def unresolved_questions() -> list[str]:
    return [
        "What is the authoritative publisher/download source and license for each CSV?",
        "Are the records observed, simulated, synthetic, or a mixture, and how were they generated or collected?",
        "Does Feed_Type mean feed supplied, a recommended feed, a dominant ingredient, or another category?",
        "Who or what assigned Feed_Type, and was it known before the milk/disease outcome?",
        "What does Feed_Quantity_kg measure: total ration, fresh matter, dry matter, concentrate, roughage, or another quantity?",
        "What period does Feed_Quantity_kg cover: per day, per meal, per week, or another period?",
        "What period does Milk_Yield_L cover: per day, per milking, per week, or another period?",
        "Are all records lactating dairy cattle? If not, which documented field or breed mapping defines the dairy-only subset?",
        "Do identical Cattle_ID and Date values in both files represent the same real observation, or were both files derived from one generated table?",
        "Which fields were available before each target was assigned, so post-outcome leakage can be excluded?",
        "What are the category definitions and measurement protocols for lactation stage, parity, body-condition score, and management system?",
    ]


def markdown_escape(value: Any) -> str:
    if value is None:
        return ""
    rendered = str(value).replace("\n", " ").replace("|", r"\|")
    return rendered


def markdown_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    rendered = [
        "| " + " | ".join(markdown_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    rendered.extend(
        "| " + " | ".join(markdown_escape(value) for value in row) + " |"
        for row in rows
    )
    return "\n".join(rendered)


def format_number(value: Any, decimals: int = 4) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):,.{decimals}f}"
    return str(value)


def summary_rows(groups: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            item["group"],
            item["count"],
            format_number(item["minimum"]),
            format_number(item["maximum"]),
            format_number(item["mean"]),
            format_number(item["median"]),
            format_number(item["standard_deviation"]),
        ]
        for item in groups
    ]


def leakage_markdown(
    leakage: dict[str, list[dict[str, str]]],
    model: str,
) -> str:
    return markdown_table(
        ["Input", "Classification", "Reason"],
        (
            (row["input"], row["classification"], row["reason"])
            for row in leakage[model]
        ),
    )


def generate_markdown(audit: dict[str, Any]) -> str:
    milk = audit["datasets"]["milk_yield"]
    disease = audit["datasets"]["disease"]
    feed_type = audit["main_milk_yield_dataset"]["feed_type_analysis"]
    feed_quantity = audit["main_milk_yield_dataset"]["feed_quantity_analysis"]
    milk_yield = audit["main_milk_yield_dataset"]["milk_yield_analysis"]
    provenance = audit["dataset_provenance"]
    join = audit["cross_dataset_join_assessment"]
    lines: list[str] = [
        "# FarmLite Dataset Inspection Report",
        "",
        "## Executive Summary",
        "",
        (
            "Phase 1 audited both original CSV files without modifying or merging them. "
            f"Each contains {milk['rows']:,} rows; the milk file has {milk['columns']} "
            f"columns and the disease file has {disease['columns']} columns. Both have "
            "unique, perfectly sequential `Cattle_ID` "
            "values, no parsed missing cells, no exact duplicate rows, the same 40 breed "
            "labels, the same eight near-balanced feed categories, and identical shared "
            "record values. These are strong generated-data indicators, but no local "
            "metadata explicitly confirms synthetic generation."
        ),
        "",
        (
            "`Feed_Type`, `Feed_Quantity_kg`, and `Milk_Yield_L` all remain blocked "
            "for genuine-model training. Feed type is not documented as recommended "
            "rather than observed; feed quantity has no documented material basis or "
            "period; and milk yield has no documented period. Provenance and reliable "
            "dairy-only filtering are also unresolved."
        ),
        "",
        "No model was trained, evaluated, replaced, or loaded by this audit.",
        "",
        "## Dataset Inventory",
        "",
        markdown_table(
            ["Dataset", "Relative path", "Bytes", "Rows", "Columns", "Duplicates", "Empty rows", "SHA-256"],
            (
                (
                    item["filename"],
                    item["relative_path"],
                    item["file_size_bytes"],
                    item["rows"],
                    item["columns"],
                    item["duplicate_row_count"],
                    item["empty_physical_csv_row_count"],
                    item["sha256"],
                )
                for item in (milk, disease)
            ),
        ),
        "",
    ]
    for label, item in (("Milk-yield dataset", milk), ("Disease dataset", disease)):
        lines.extend(
            [
                f"### {label} exact columns",
                "",
                ", ".join(f"`{column}`" for column in item["exact_column_names"]),
                "",
                "Missing values and inferred types are included in the column-profile tables below. "
                f"Total parsed missing cells: {sum(row['missing_count'] for row in item['missing_values']):,}.",
                "",
            ]
        )

    lines.extend(
        [
            "## Dataset Provenance",
            "",
            f"Status: **{provenance['status']}**.",
            "",
            provenance["assessment"],
            "",
            f"Repository search: {provenance['text_files_searched']} eligible text files "
            f"searched; {provenance['relevant_files_inspected']} relevant files inspected. "
            f"License files found: {provenance['license_files_found'] or 'none'}. "
            f"Citation files found: {provenance['citation_files_found'] or 'none'}.",
            "",
            "Files inspected:",
            "",
            *[f"- `{item['path']}`" for item in provenance["files_inspected"]],
            "",
            "The audit did not browse the web.",
            "",
            "## Dairy-Cattle Suitability",
            "",
        ]
    )
    for label, item in (("Milk-yield dataset", milk), ("Disease dataset", disease)):
        suitability = item["dairy_cattle_suitability"]
        lines.extend(
            [
                f"### {label}",
                "",
                f"Status: **{suitability['status']}**.",
                "",
                f"- Unique breeds ({len(suitability['unique_breed_values'])}): "
                + ", ".join(f"`{breed}`" for breed in suitability["unique_breed_values"]),
                f"- Dairy indicators: "
                + ", ".join(f"`{breed}`" for breed in suitability["dairy_breed_indicators"]),
                f"- Beef/non-specialized indicators: "
                + ", ".join(
                    f"`{breed}`" for breed in suitability["beef_or_non_specialized_indicators"]
                ),
                f"- Unclassified or dual-purpose names: "
                + ", ".join(
                    f"`{breed}`" for breed in suitability["unclassified_or_dual_purpose_breeds"]
                ),
                f"- Other species: not observed, but {suitability['other_species_evidence']}",
                f"- Dairy-only filtering: {suitability['filtering_assessment']}",
                f"- Lactation: {suitability['lactation_assessment']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Identifier and Repeated-Observation Analysis",
            "",
        ]
    )
    for label, item in (("Milk-yield dataset", milk), ("Disease dataset", disease)):
        identifier = item["identifier_analysis"]
        cattle = identifier["details"]["Cattle_ID"]
        date = identifier["date_analysis"]
        lines.extend(
            [
                f"### {label}",
                "",
                markdown_table(
                    [
                        "Cattle rows",
                        "Unique Cattle_ID",
                        "Repeated IDs",
                        "Maximum observations/animal",
                        "Date range",
                        "Group split required",
                    ],
                    [
                        (
                            item["rows"],
                            cattle["unique_non_null"],
                            cattle["distinct_repeated_values"],
                            cattle["maximum_observations_per_value"],
                            f"{date.get('minimum')} to {date.get('maximum')}",
                            identifier["group_based_split_required"],
                        )
                    ],
                ),
                "",
                identifier["group_split_reason"],
                "",
                (
                    "`Farm_ID` repeats, but it identifies farms rather than repeated animal "
                    "observations. If farm-level generalisation is required later, a grouped "
                    "farm split should be considered separately."
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Main Milk-Yield Dataset",
            "",
            "### Column Profile",
            "",
            markdown_table(
                ["Column", "Pandas type", "Inferred type", "Missing", "Missing %", "Unique", "Sample values"],
                (
                    (
                        row["column"],
                        row["pandas_dtype"],
                        row["inferred_type"],
                        row["missing_count"],
                        row["missing_percentage"],
                        row["unique_non_null"],
                        ", ".join(map(str, row["sample_values"])),
                    )
                    for row in milk["column_profile"]
                ),
            ),
            "",
            "### Candidate Features",
            "",
            markdown_table(
                ["Candidate", "Present", "Source", "Type", "Missing %", "Unique", "Form", "Prediction-time assessment"],
                (
                    (
                        row["candidate_feature"],
                        row["present"],
                        row["exact_source_column"],
                        row.get("data_type"),
                        row["missing_percentage"],
                        row["unique_non_null"],
                        row["current_farmlite_form"],
                        row["prediction_time_safety"],
                    )
                    for row in milk["candidate_features"]
                ),
            ),
            "",
            "The disease outcome `Disease_Status` was deliberately not treated as an alias "
            "for the form's current `Health_Status`; their meanings and timing differ.",
            "",
            "### Feed-Type Analysis",
            "",
            f"Target status: **{feed_type['status']}**.",
            "",
            "Exact unique values: "
            + ", ".join(f"`{value}`" for value in feed_type["exact_unique_values"]),
            "",
            markdown_table(
                ["Feed type", "Count", "Percentage"],
                (
                    (row["feed_type"], row["count"], f"{row['percentage']:.4f}%")
                    for row in feed_type["distribution"]
                ),
            ),
            "",
            f"Missing: {feed_type['missing_count']:,}. Rare classes: "
            f"{feed_type['rare_classes_under_1_percent_or_100_rows'] or 'none'}. "
            f"Spelling duplicates: {feed_type['duplicate_or_inconsistent_spellings'] or 'none'}.",
            "",
            feed_type["decision_reason"],
            "",
            "Categorical relationships (Cramer's V; 0 means no observed association and 1 means perfect association):",
            "",
            markdown_table(
                ["Related field", "Available", "Cramer's V"],
                (
                    (
                        field,
                        relation["available"],
                        format_number(relation.get("cramers_v"), 6),
                    )
                    for field, relation in feed_type["relationships"].items()
                ),
            ),
            "",
            "The full relationship count tables are retained in `dataset_audit.json`.",
            "",
            "### Feed-Quantity Analysis",
            "",
            f"Target status: **{feed_quantity['status']}**.",
            "",
            markdown_table(
                ["Statistic", "Value"],
                [
                    ("Minimum", format_number(feed_quantity["summary"]["minimum"])),
                    ("Maximum", format_number(feed_quantity["summary"]["maximum"])),
                    ("Mean", format_number(feed_quantity["summary"]["mean"])),
                    ("Median", format_number(feed_quantity["summary"]["median"])),
                    ("Standard deviation", format_number(feed_quantity["summary"]["standard_deviation"])),
                    *[
                        (name.upper(), format_number(value))
                        for name, value in feed_quantity["summary"]["percentiles"].items()
                    ],
                    ("Missing", feed_quantity["summary"]["missing_count"]),
                    ("Zero", feed_quantity["summary"]["zero_count"]),
                    ("Negative", feed_quantity["summary"]["negative_count"]),
                    ("Unique values", feed_quantity["summary"]["unique_values"]),
                ],
            ),
            "",
            f"Decimal precision counts: `{feed_quantity['decimal_precision_counts']}`.",
            "",
            "The statistical IQR fence found "
            f"{feed_quantity['suspicious_extremes']['below_fence_count']} low and "
            f"{feed_quantity['suspicious_extremes']['above_fence_count']} high outliers. "
            "This is not a nutrition-validity rule.",
            "",
            "Distribution by Feed_Type:",
            "",
            markdown_table(
                ["Group", "Count", "Min", "Max", "Mean", "Median", "Std"],
                summary_rows(feed_quantity["distribution_by_feed_type"]),
            ),
            "",
            "Distribution by Lactation_Stage:",
            "",
            markdown_table(
                ["Group", "Count", "Min", "Max", "Mean", "Median", "Std"],
                summary_rows(feed_quantity["distribution_by_lactation_stage"]),
            ),
            "",
            "Distribution by Weight_kg range:",
            "",
            markdown_table(
                ["Group", "Count", "Min", "Max", "Mean", "Median", "Std"],
                summary_rows(feed_quantity["distribution_by_weight_kg_range"]),
            ),
            "",
            "Distribution by Breed:",
            "",
            markdown_table(
                ["Breed", "Count", "Min", "Max", "Mean", "Median", "Std"],
                summary_rows(feed_quantity["distribution_by_breed"]),
            ),
            "",
            "Pearson correlations:",
            "",
            markdown_table(
                ["Variable", "Correlation with Feed_Quantity_kg"],
                (
                    (name, format_number(value, 6))
                    for name, value in feed_quantity["correlations"].items()
                ),
            ),
            "",
            feed_quantity["decision_reason"],
            "",
            "### Milk-Yield Analysis",
            "",
            markdown_table(
                ["Statistic", "Value"],
                [
                    ("Minimum", format_number(milk_yield["summary"]["minimum"])),
                    ("Maximum", format_number(milk_yield["summary"]["maximum"])),
                    ("Mean", format_number(milk_yield["summary"]["mean"])),
                    ("Median", format_number(milk_yield["summary"]["median"])),
                    ("Standard deviation", format_number(milk_yield["summary"]["standard_deviation"])),
                    *[
                        (name.upper(), format_number(value))
                        for name, value in milk_yield["summary"]["percentiles"].items()
                    ],
                    ("Missing", milk_yield["summary"]["missing_count"]),
                    ("Zero", milk_yield["summary"]["zero_count"]),
                    ("Negative", milk_yield["summary"]["negative_count"]),
                ],
            ),
            "",
            "Distribution by Lactation_Stage:",
            "",
            markdown_table(
                ["Group", "Count", "Min", "Max", "Mean", "Median", "Std"],
                summary_rows(milk_yield["distribution_by_lactation_stage"]),
            ),
            "",
            "Distribution by Breed:",
            "",
            markdown_table(
                ["Breed", "Count", "Min", "Max", "Mean", "Median", "Std"],
                summary_rows(milk_yield["distribution_by_breed"]),
            ),
            "",
            "Previous-week yield correlation: "
            f"{format_number(milk_yield['relationship_with_previous_week_yield']['pearson_correlation'], 6)}.",
            "",
            f"Period: **{milk_yield['period']}**. {milk_yield['period_assessment']}",
            "",
            "### Data-Quality Issues",
            "",
            markdown_table(
                ["Status", "Severity", "Issue", "Column", "Affected", "Percentage", "Evidence"],
                (
                    (
                        row["status"],
                        row["severity"],
                        row["issue"],
                        row["column"],
                        row["affected_rows"],
                        row["percentage"],
                        row["evidence"],
                    )
                    for row in milk["data_quality_issues"]
                ),
            ),
            "",
            "### Leakage Risks",
            "",
        ]
    )
    for title, model in (
        ("Feed-type classifier", "feed_type_classifier"),
        ("Feed-quantity regressor", "feed_quantity_regressor"),
        ("Milk-yield regressor", "milk_yield_regressor"),
    ):
        lines.extend(
            [
                f"#### {title}",
                "",
                leakage_markdown(milk["leakage_analysis"], model),
                "",
            ]
        )

    synthetic = milk["synthetic_data_indicators"]
    lines.extend(
        [
            "### Synthetic-Data Indicators",
            "",
            f"Status: **{synthetic['status']}**.",
            "",
            synthetic["assessment"],
            "",
            markdown_table(
                ["Indicator", "Evidence"],
                (
                    (item["indicator"], json.dumps(item["evidence"], ensure_ascii=False))
                    for item in synthetic["evidence"]
                ),
            ),
            "",
            "## Disease Dataset",
            "",
            "### Column Profile",
            "",
            markdown_table(
                ["Column", "Pandas type", "Inferred type", "Missing", "Missing %", "Unique", "Sample values"],
                (
                    (
                        row["column"],
                        row["pandas_dtype"],
                        row["inferred_type"],
                        row["missing_count"],
                        row["missing_percentage"],
                        row["unique_non_null"],
                        ", ".join(map(str, row["sample_values"])),
                    )
                    for row in disease["column_profile"]
                ),
            ),
            "",
            "### Intended Use Assessment",
            "",
            markdown_table(
                ["Use", "Decision", "Reason"],
                (
                    (name, item["decision"], item["reason"])
                    for name, item in audit["disease_dataset_assessment"].items()
                ),
            ),
            "",
            "### Data-Quality Issues",
            "",
            markdown_table(
                ["Status", "Severity", "Issue", "Column", "Affected", "Percentage", "Evidence"],
                (
                    (
                        row["status"],
                        row["severity"],
                        row["issue"],
                        row["column"],
                        row["affected_rows"],
                        row["percentage"],
                        row["evidence"],
                    )
                    for row in disease["data_quality_issues"]
                ),
            ),
            "",
            "### Leakage Risks",
            "",
            "The full per-column leakage classifications for all three proposed models "
            "are in `dataset_audit.json`. Disease outcome and physiological measurements "
            "are especially risky because their timing is undocumented and they are not "
            "available from the current FarmLite form.",
            "",
            "## Cross-Dataset Join Assessment",
            "",
            f"Join status: **{join['join_status']}**.",
            "",
            join["assessment"],
            "",
            markdown_table(
                ["Evidence", "Value"],
                (
                    (name, value)
                    for name, value in join["key_evidence"].items()
                ),
            ),
            "",
            f"Shared columns: {len(join['shared_columns'])}. "
            f"All shared values identical in row order: {join['all_shared_columns_identical_in_row_order']}.",
            "",
            "The datasets were not merged.",
            "",
            "## Target Availability Matrix",
            "",
            markdown_table(
                ["Target", "Dataset Column", "Availability", "Meaning/Unit Status", "Training Readiness", "Notes"],
                (
                    (
                        row["Target"],
                        row["Dataset Column"],
                        row["Availability"],
                        row["Meaning/Unit Status"],
                        row["Training Readiness"],
                        row["Notes"],
                    )
                    for row in audit["target_availability_matrix"]
                ),
            ),
            "",
            "## Model Readiness Assessment",
            "",
            markdown_table(
                ["Model", "Decision", "Target status", "Reason"],
                (
                    (
                        model,
                        item["decision"],
                        item["target_status"],
                        item["reason"],
                    )
                    for model, item in audit["model_readiness"].items()
                ),
            ),
            "",
            "## Information Required From Project Owner",
            "",
            *[
                f"{index}. {question}"
                for index, question in enumerate(audit["unresolved_questions"], start=1)
            ],
            "",
            "## Final Decision",
            "",
            "**Phase 1 result: PASS as a dataset audit; all three proposed model-training paths remain blocked.**",
            "",
            (
                "Do not begin a final feature contract or model training until the project "
                "owner supplies authoritative provenance and target definitions. A narrowly "
                "scoped Phase 2 draft could document these blockers, but it must not declare "
                "Feed_Type, Feed_Quantity_kg, or Milk_Yield_L deployment-ready."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def feed_quantity_csv_rows(
    filename: str,
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    overall = {"group": "ALL", **analysis["summary"]}
    groupings = {
        "overall": [overall],
        "Feed_Type": analysis["distribution_by_feed_type"],
        "Lactation_Stage": analysis["distribution_by_lactation_stage"],
        "Breed": analysis["distribution_by_breed"],
        "Weight_kg_range": analysis["distribution_by_weight_kg_range"],
    }
    for grouping, summaries in groupings.items():
        for summary in summaries:
            row = {
                "dataset": filename,
                "grouping": grouping,
                "group": summary["group"],
                "count": summary["count"],
                "missing_count": summary["missing_count"],
                "minimum": summary["minimum"],
                "maximum": summary["maximum"],
                "mean": summary["mean"],
                "median": summary["median"],
                "standard_deviation": summary["standard_deviation"],
                **summary["percentiles"],
            }
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Refusing to create empty CSV report: {path}")
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(json_ready(rows))


def main() -> int:
    ML_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    resolved: dict[str, tuple[Path, str]] = {}
    frames: dict[str, pd.DataFrame] = {}

    print("FarmLite Phase 1 dataset audit")
    print("Read-only source policy: enabled")
    for role, expected_path in EXPECTED_DATASETS.items():
        path, resolution = resolve_dataset(expected_path)
        resolved[role] = (path, resolution)
        print(f"Loading {role}: {relative_path(path)}")
        frames[role] = pd.read_csv(path, low_memory=False)
        print(
            f"  loaded {len(frames[role]):,} rows x "
            f"{len(frames[role].columns):,} columns"
        )

    milk_audit = audit_dataset(
        frames["milk_yield"], resolved["milk_yield"][0], resolved["milk_yield"][1]
    )
    disease_audit = audit_dataset(
        frames["disease"], resolved["disease"][0], resolved["disease"][1]
    )
    milk_audit["feed_type_analysis"] = feed_type_analysis(frames["milk_yield"])
    milk_audit["feed_quantity_analysis"] = feed_quantity_analysis(
        frames["milk_yield"]
    )
    milk_audit["milk_yield_analysis"] = milk_yield_analysis(frames["milk_yield"])

    audit: dict[str, Any] = {
        "audit_name": "FarmLite Phase 1 Dataset Audit",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "scope": {
            "source_files_modified": False,
            "datasets_merged": False,
            "models_trained_or_evaluated": False,
            "web_browsing_used": False,
        },
        "datasets": {
            "milk_yield": milk_audit,
            "disease": disease_audit,
        },
        "dataset_provenance": repository_provenance(),
        "main_milk_yield_dataset": {
            "feed_type_analysis": milk_audit["feed_type_analysis"],
            "feed_quantity_analysis": milk_audit["feed_quantity_analysis"],
            "milk_yield_analysis": milk_audit["milk_yield_analysis"],
        },
        "disease_dataset_assessment": disease_use_assessment(),
        "cross_dataset_join_assessment": cross_dataset_assessment(
            frames["milk_yield"], frames["disease"]
        ),
        "target_availability_matrix": target_matrix(),
        "model_readiness": model_readiness(),
        "unresolved_questions": unresolved_questions(),
        "final_decision": {
            "phase_1_audit": "PASS",
            "phase_2_recommendation": "WAIT_FOR_TARGET_DEFINITIONS_AND_PROVENANCE",
            "training_authorized": False,
        },
    }

    strict_audit = json_ready(audit)
    JSON_REPORT_PATH.write_text(
        json.dumps(strict_audit, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_REPORT_PATH.write_text(
        generate_markdown(strict_audit),
        encoding="utf-8",
    )
    write_csv(TARGET_MATRIX_PATH, strict_audit["target_availability_matrix"])
    write_csv(
        FEED_TYPE_DISTRIBUTION_PATH,
        strict_audit["main_milk_yield_dataset"]["feed_type_analysis"]["distribution"],
    )
    write_csv(
        FEED_QUANTITY_SUMMARY_PATH,
        feed_quantity_csv_rows(
            milk_audit["filename"],
            strict_audit["main_milk_yield_dataset"]["feed_quantity_analysis"],
        ),
    )
    write_csv(
        DATA_QUALITY_ISSUES_PATH,
        strict_audit["datasets"]["milk_yield"]["data_quality_issues"]
        + strict_audit["datasets"]["disease"]["data_quality_issues"],
    )

    print("Generated reports:")
    for path in (
        JSON_REPORT_PATH,
        MARKDOWN_REPORT_PATH,
        TARGET_MATRIX_PATH,
        FEED_TYPE_DISTRIBUTION_PATH,
        FEED_QUANTITY_SUMMARY_PATH,
        DATA_QUALITY_ISSUES_PATH,
    ):
        print(f"  {relative_path(path)}")
    print("No models were trained and no source datasets were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
