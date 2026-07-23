"""Inspect FarmLite cattle datasets without training or modifying any data."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = (SCRIPT_DIR / "../../../datasets").resolve()
REPORT_PATH = SCRIPT_DIR / "dataset_inspection_report.txt"
DATASET_PATHS = (
    DATASET_DIR / "global_cattle_milk_yield_prediction_dataset.csv",
    DATASET_DIR / "global_cattle_disease_detection_dataset.csv",
)

KEYWORDS = (
    "age",
    "weight",
    "breed",
    "health",
    "disease",
    "milk",
    "yield",
    "feed",
    "intake",
    "roughage",
    "concentrate",
    "nutrient",
    "lactation",
    "production",
    "stage",
    "ration",
    "diet",
    "recommendation",
    "recommended",
    "quantity",
    "kg",
)

CONCEPT_KEYWORDS = {
    "Cattle ID": ("cattle id", "cow id", "animal id", "tag id"),
    "Breed": ("breed",),
    "Age": ("age",),
    "Weight": ("weight", "body weight", "live weight"),
    "Health status / disease": (
        "health status",
        "health",
        "disease status",
        "disease",
        "diagnosis",
        "symptom",
    ),
    "Milk yield": ("milk yield", "milk production", "yield"),
    "Feed type": ("feed type", "feed", "ration", "diet"),
    "Feed intake / quantity": (
        "feed intake",
        "dry matter intake",
        "intake",
        "feed quantity",
        "quantity",
    ),
    "Nutrient composition": (
        "nutrient",
        "nutrition",
        "protein",
        "energy",
        "fiber",
        "fibre",
        "calcium",
        "phosphorus",
    ),
    "Roughage": ("roughage", "forage"),
    "Concentrate": ("concentrate",),
    "Production stage": ("production stage", "production", "stage"),
    "Lactation stage": (
        "lactation stage",
        "lactation",
        "lactating",
        "days in milk",
    ),
    "Possible target / output": (
        "target",
        "label",
        "outcome",
        "recommendation",
        "recommended",
        "milk yield",
        "disease status",
        "feed quantity",
    ),
}


class Reporter:
    """Print messages to the console while retaining them for the report file."""

    def __init__(self) -> None:
        self._entries: list[str] = []

    def line(self, value: object = "") -> None:
        text = str(value)
        print(text)
        self._entries.append(text)

    def save(self) -> None:
        REPORT_PATH.write_text("\n".join(self._entries) + "\n", encoding="utf-8")


def normalize_name(value: str) -> str:
    """Normalize a column or keyword into space-separated lowercase tokens."""

    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def matches_keyword(column_name: str, keyword: str) -> bool:
    """Match whole normalized words or phrases, avoiding matches such as age/management."""

    normalized_column = f" {normalize_name(column_name)} "
    normalized_keyword = f" {normalize_name(keyword)} "
    return normalized_keyword in normalized_column


def columns_matching(columns: list[str], keywords: tuple[str, ...]) -> list[str]:
    return [
        column
        for column in columns
        if any(matches_keyword(column, keyword) for keyword in keywords)
    ]


def keyword_matches(columns: list[str]) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}
    for column in columns:
        matched_keywords = [
            keyword for keyword in KEYWORDS if matches_keyword(column, keyword)
        ]
        if matched_keywords:
            matches[column] = matched_keywords
    return matches


def has_matching_column(columns: list[str], keywords: tuple[str, ...]) -> bool:
    return bool(columns_matching(columns, keywords))


def assess_use_cases(columns: list[str]) -> dict[str, str]:
    has_milk_target = has_matching_column(
        columns, ("milk yield", "milk production")
    )
    has_disease_target = has_matching_column(
        columns, ("disease status", "disease label", "diagnosis")
    )
    has_feed_quantity = has_matching_column(
        columns, ("feed quantity", "feed intake", "dry matter intake")
    )
    has_feed_context = has_matching_column(
        columns, ("feed type", "feed", "ration", "diet")
    )
    has_health_context = has_matching_column(
        columns, ("health", "disease", "body condition", "temperature")
    )
    has_recommendation_target = has_matching_column(
        columns,
        (
            "feed recommendation",
            "recommended feed",
            "recommended quantity",
            "optimal feed",
            "optimal ration",
            "target ration",
        ),
    )

    return {
        "Milk yield prediction": (
            "SUPPORTED: an explicit milk-yield column could be used as a target."
            if has_milk_target
            else "NOT DIRECTLY SUPPORTED: no explicit milk-yield target was identified."
        ),
        "Disease detection": (
            "SUPPORTED: an explicit disease/diagnosis column could be used as a target."
            if has_disease_target
            else "NOT DIRECTLY SUPPORTED: no explicit disease target was identified."
        ),
        "Feed intake prediction": (
            "POSSIBLE: feed quantity/intake can be treated as a historical prediction target, "
            "but it is not proof of an optimal ration."
            if has_feed_quantity
            else "NOT DIRECTLY SUPPORTED: no feed intake or quantity target was identified."
        ),
        "Feed recommendation": (
            "POSSIBLE: an explicit recommended/optimal feed target was identified, but its "
            "meaning and provenance still require validation."
            if has_recommendation_target
            else "NOT DIRECTLY SUPPORTED: feed observations may be present, but there is no "
            "explicit recommended or optimal feed/ration target."
        ),
        "Health-risk assisted feeding": (
            "POSSIBLE AS A RESEARCH PIPELINE: health and feed context coexist, but veterinary "
            "and nutrition rules are still required to turn risk predictions into safe feeding advice."
            if has_health_context and (has_feed_context or has_feed_quantity)
            else "NOT DIRECTLY SUPPORTED: both health-risk and feeding context were not identified."
        ),
    }


def inspect_dataset(dataframe: Any, path: Path, reporter: Reporter) -> dict[str, Any]:
    columns = [str(column) for column in dataframe.columns]
    concepts = {
        concept: columns_matching(columns, keywords)
        for concept, keywords in CONCEPT_KEYWORDS.items()
    }
    use_cases = assess_use_cases(columns)

    reporter.line("=" * 100)
    reporter.line(f"DATASET: {path.name}")
    reporter.line(f"Resolved path: {path}")
    reporter.line(f"Rows: {len(dataframe):,}")
    reporter.line(f"Columns: {len(columns):,}")
    reporter.line()

    reporter.line("FULL COLUMN LIST")
    for index, column in enumerate(columns, start=1):
        reporter.line(f"  {index:>2}. {column}")
    reporter.line()

    reporter.line("FIRST 5 ROWS")
    reporter.line(dataframe.head(5).to_string(index=False, max_cols=None))
    reporter.line()

    reporter.line("DATA TYPES")
    reporter.line(dataframe.dtypes.to_string())
    reporter.line()

    reporter.line("MISSING VALUES PER COLUMN")
    reporter.line(dataframe.isna().sum().to_string())
    reporter.line()

    reporter.line(f"DUPLICATE ROW COUNT: {int(dataframe.duplicated().sum()):,}")
    reporter.line()

    reporter.line("POSSIBLE COLUMNS BY CONCEPT")
    for concept, matched_columns in concepts.items():
        result = ", ".join(matched_columns) if matched_columns else "None identified"
        reporter.line(f"  - {concept}: {result}")
    reporter.line()

    reporter.line("REQUESTED KEYWORD MATCHES")
    matches = keyword_matches(columns)
    if matches:
        for column, matched_keywords in matches.items():
            reporter.line(f"  - {column}: {', '.join(matched_keywords)}")
    else:
        reporter.line("  No requested keywords matched any columns.")
    reporter.line()

    reporter.line("POSSIBLE MACHINE LEARNING USE CASES")
    for use_case, assessment in use_cases.items():
        reporter.line(f"  - {use_case}: {assessment}")
    reporter.line()

    return {
        "filename": path.name,
        "columns": columns,
        "concepts": concepts,
        "use_cases": use_cases,
    }


def print_conclusion(results: list[dict[str, Any]], reporter: Reporter) -> None:
    reporter.line("=" * 100)
    reporter.line("OVERALL CONCLUSION")

    if not results:
        reporter.line("No datasets were successfully loaded, so suitability could not be assessed.")
        reporter.line(
            "Check the absolute paths printed above and confirm that pandas is installed."
        )
        return

    all_columns = [
        column for result in results for column in result.get("columns", [])
    ]
    has_milk_yield = has_matching_column(
        all_columns, ("milk yield", "milk production")
    )
    has_disease_status = has_matching_column(
        all_columns, ("disease status", "disease label", "diagnosis")
    )
    has_feed_quantity = has_matching_column(
        all_columns, ("feed quantity", "feed intake", "dry matter intake")
    )
    has_direct_recommendation = has_matching_column(
        all_columns,
        (
            "feed recommendation",
            "recommended feed",
            "recommended quantity",
            "optimal feed",
            "optimal ration",
            "target ration",
        ),
    )

    reporter.line(
        "- Direct feed recommendation support: "
        + (
            "POTENTIALLY YES, because an explicit recommendation/optimal-ration column was found. "
            "Its definition must still be verified before use."
            if has_direct_recommendation
            else "NO. Feed_Type and Feed_Quantity_kg describe observed feeding, but no column says "
            "that the feed or quantity is recommended, optimal, safe, or responsible for an outcome."
        )
    )
    reporter.line(
        "- Milk-yield prediction support: "
        + (
            "YES. Milk_Yield_L is a plausible supervised target with multiple predictor columns."
            if has_milk_yield
            else "NO explicit milk-yield target was identified."
        )
    )
    reporter.line(
        "- Disease detection support: "
        + (
            "YES. Disease_Status is a plausible classification target in the disease dataset."
            if has_disease_status
            else "NO explicit disease target was identified."
        )
    )
    reporter.line(
        "- Feed-intake prediction support: "
        + (
            "POSSIBLE. Feed_Quantity_kg can be predicted as historical intake/usage, but should not "
            "be presented as an optimal recommendation."
            if has_feed_quantity
            else "NO explicit feed-intake or feed-quantity target was identified."
        )
    )
    reporter.line(
        "- Only milk-yield prediction: NO. The combined files also support disease classification "
        "and exploratory feed-quantity prediction, subject to validation."
        if has_milk_yield and has_disease_status
        else "- Only milk-yield prediction: Cannot be confirmed from the available targets."
    )
    reporter.line(
        "- Rule-based feed recommendation: STILL NEEDED unless a separate dataset supplies "
        "expert-validated optimal ration targets, nutrient requirements, constraints, and measured outcomes."
    )
    reporter.line(
        "- Health-risk assisted feeding: POSSIBLE as a future combination of disease-risk predictions "
        "and veterinary/nutrition rules; disease predictions alone do not define a safe ration."
    )
    reporter.line(
        "- Real-world claim safety: UNSUITABLE FOR REAL-WORLD CLAIMS AS-IS. CSV structure alone does "
        "not establish provenance, representative sampling, measurement quality, licensing, causal "
        "validity, or veterinary/nutrition review. Sequential identifiers and highly regular schemas "
        "may indicate synthetic or generated data, but provenance must be checked rather than assumed."
    )
    reporter.line(
        "Use these files only for exploratory/educational analysis until their source and validity are documented."
    )


def main() -> int:
    reporter = Reporter()
    reporter.line("FarmLite Dataset Inspection Report")
    reporter.line(f"Dataset directory: {DATASET_DIR}")
    reporter.line()

    try:
        import pandas as pd
    except ImportError:
        reporter.line(
            "ERROR: pandas is not installed. Install the backend requirements or run "
            "'python -m pip install pandas', then run this script again."
        )
        reporter.line(f"Report output path: {REPORT_PATH}")
        reporter.save()
        return 1

    results: list[dict[str, Any]] = []
    had_error = False

    for dataset_path in DATASET_PATHS:
        if not dataset_path.is_file():
            reporter.line("=" * 100)
            reporter.line(f"FILE ERROR: {dataset_path.name}")
            reporter.line(f"Expected CSV file was not found at: {dataset_path}")
            reporter.line(
                "Place the dataset in the project-root datasets folder and rerun the script."
            )
            reporter.line()
            had_error = True
            continue

        try:
            dataframe = pd.read_csv(dataset_path, low_memory=False)
            results.append(inspect_dataset(dataframe, dataset_path, reporter))
        except Exception as error:  # Keep the second dataset inspectable if one file is malformed.
            reporter.line("=" * 100)
            reporter.line(f"LOAD ERROR: {dataset_path.name}")
            reporter.line(f"Could not read {dataset_path}: {error}")
            reporter.line()
            had_error = True

    print_conclusion(results, reporter)
    reporter.line()
    reporter.line(f"Report output path: {REPORT_PATH}")

    try:
        reporter.save()
    except OSError as error:
        print(f"ERROR: Could not write report to {REPORT_PATH}: {error}", file=sys.stderr)
        return 1

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
