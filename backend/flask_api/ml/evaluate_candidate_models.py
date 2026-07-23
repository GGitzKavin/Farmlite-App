"""Evaluate candidate ML targets for FarmLite's feed recommendation module.

This script does not save production models. It only compares simple
scikit-learn candidates against dummy baselines and writes an evaluation report.
"""

from __future__ import annotations

import math
import os
import re
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pandas as pd
    from pandas.api.types import is_numeric_dtype
except ImportError:
    print(
        "ERROR: pandas is required to run this script. Install the project "
        "requirements before evaluating the datasets.",
        file=sys.stderr,
    )
    raise SystemExit(1)

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.dummy import DummyClassifier, DummyRegressor
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
        mean_absolute_error,
        mean_squared_error,
        precision_score,
        r2_score,
        recall_score,
    )
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except ImportError:
    print(
        "ERROR: scikit-learn is required to run this script. Install the "
        "project requirements before evaluating candidate models.",
        file=sys.stderr,
    )
    raise SystemExit(1)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = (SCRIPT_DIR / "../../..").resolve()
DATASET_DIR = PROJECT_ROOT / "datasets"
REPORT_PATH = SCRIPT_DIR / "candidate_model_evaluation_report.txt"
FAILED_FEED_REPORT_PATH = SCRIPT_DIR / "feed_model_report.txt"

MAX_ROWS = 60_000
RANDOM_STATE = 42

warnings.filterwarnings(
    "ignore",
    message="Could not find the number of physical cores.*",
    category=UserWarning,
)

MILK_DATASET = DATASET_DIR / "global_cattle_milk_yield_prediction_dataset.csv"
DISEASE_DATASET = DATASET_DIR / "global_cattle_disease_detection_dataset.csv"


@dataclass
class CandidateResult:
    name: str
    dataset_path: Path
    target_column: str
    original_rows: int
    sampled_rows: int
    target_distribution: str
    selected_features: list[str]
    excluded_columns: dict[str, list[str]]
    leakage_warnings: list[str]
    suitability_notes: list[str]
    metrics: dict[str, dict[str, Any]]
    recommended: bool


def normalize_column_name(column_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", column_name.lower()).strip()


def token_set(column_name: str) -> set[str]:
    return set(normalize_column_name(column_name).split())


def is_identifier_column(column_name: str) -> bool:
    tokens = token_set(column_name)
    return "id" in tokens or "identifier" in tokens


def is_date_column(column_name: str) -> bool:
    tokens = token_set(column_name)
    return "date" in tokens or "timestamp" in tokens


def one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Place the CSV file in the project-root datasets folder."
        )
    return pd.read_csv(path, low_memory=False)


def sample_dataset(dataframe: pd.DataFrame) -> pd.DataFrame:
    if len(dataframe) > MAX_ROWS:
        return dataframe.sample(n=MAX_ROWS, random_state=RANDOM_STATE).copy()
    return dataframe.copy()


def format_distribution(series: pd.Series, max_rows: int = 20) -> str:
    if is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        return (
            f"count={numeric.count():,}, missing={numeric.isna().sum():,}, "
            f"mean={numeric.mean():.4f}, std={numeric.std():.4f}, "
            f"min={numeric.min():.4f}, median={numeric.median():.4f}, "
            f"max={numeric.max():.4f}"
        )

    counts = series.astype("string").fillna("<missing>").value_counts(dropna=False)
    lines = []
    for label, count in counts.head(max_rows).items():
        percent = count / len(series) * 100 if len(series) else 0
        lines.append(f"  - {label}: {count:,} ({percent:.2f}%)")
    if len(counts) > max_rows:
        lines.append(f"  - ... {len(counts) - max_rows:,} more classes")
    return "\n".join(lines)


def detect_target_risks(series: pd.Series, task_type: str) -> list[str]:
    notes: list[str] = []

    if series.isna().any():
        notes.append(
            f"Target contains {int(series.isna().sum()):,} missing values; rows with "
            "missing targets are removed before training."
        )

    if task_type == "classification":
        counts = series.astype("string").fillna("<missing>").value_counts(dropna=False)
        if counts.empty:
            notes.append("Target has no usable classes.")
            return notes

        majority_share = float(counts.iloc[0] / counts.sum())
        minority_share = float(counts.iloc[-1] / counts.sum())
        if len(counts) < 2:
            notes.append("Target has only one class and is unsuitable for classification.")
        if majority_share >= 0.80:
            notes.append(
                f"Target is heavily imbalanced; largest class is {majority_share:.2%}."
            )
        if len(counts) > 1 and minority_share <= 0.05:
            notes.append(
                f"Target has a very small minority class at {minority_share:.2%}."
            )
        if len(counts) > 20:
            notes.append(
                "Target has many classes for a simple undergraduate classifier; "
                "verify that these are true disease labels."
            )
    else:
        numeric = pd.to_numeric(series, errors="coerce")
        valid = numeric.dropna()
        if valid.empty:
            notes.append("Target has no numeric values after conversion.")
            return notes
        if valid.nunique() < 10:
            notes.append(
                "Regression target has very few unique values; it may behave more "
                "like categories than a continuous outcome."
            )
        if math.isclose(float(valid.std()), 0.0):
            notes.append("Regression target has near-zero variance and is unsuitable.")

    return notes


def leakage_column_reason(column: str, target_column: str, extra_terms: set[str]) -> str | None:
    if column == target_column:
        return "target column"

    normalized_column = normalize_column_name(column)
    normalized_target = normalize_column_name(target_column)
    column_tokens = token_set(column)
    target_tokens = token_set(target_column)

    if normalized_column == normalized_target:
        return "direct target duplicate"

    if target_tokens and target_tokens.issubset(column_tokens):
        return "column name contains all target tokens"

    matched_terms = sorted(column_tokens.intersection(extra_terms))
    if matched_terms:
        return "possible target leakage term: " + ", ".join(matched_terms)

    return None


def split_feature_types(
    dataframe: pd.DataFrame, features: list[str]
) -> tuple[list[str], list[str]]:
    numeric_features = [
        feature for feature in features if is_numeric_dtype(dataframe[feature])
    ]
    categorical_features = [
        feature for feature in features if feature not in numeric_features
    ]
    return numeric_features, categorical_features


def make_preprocessor(
    numeric_features: list[str], categorical_features: list[str]
) -> ColumnTransformer:
    transformers = []
    if numeric_features:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )

    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("one_hot", one_hot_encoder()),
                    ]
                ),
                categorical_features,
            )
        )

    return ColumnTransformer(transformers=transformers, sparse_threshold=0.0)


def regression_metrics(actual: pd.Series, predicted: Any) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": math.sqrt(float(mean_squared_error(actual, predicted))),
        "R2": float(r2_score(actual, predicted)),
    }


def classification_metrics(actual: pd.Series, predicted: Any) -> dict[str, Any]:
    labels = sorted(actual.astype("string").unique())
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)),
        "precision_weighted": float(
            precision_score(actual, predicted, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(actual, predicted, average="weighted", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(actual, predicted, average="weighted", zero_division=0)
        ),
        "labels": labels,
        "confusion_matrix": confusion_matrix(actual, predicted, labels=labels).tolist(),
    }


def evaluate_milk_yield() -> CandidateResult:
    target_column = "Milk_Yield_L"
    preferred_features = [
        "Breed",
        "Age_Months",
        "Weight_kg",
        "Lactation_Stage",
        "Days_in_Milk",
        "Body_Condition_Score",
        "Previous_Week_Avg_Yield",
        "Ambient_Temperature_C",
        "Humidity_percent",
    ]
    forbidden_inputs = {"Feed_Quantity_kg"}
    leakage_terms: set[str] = set()

    dataframe = load_dataset(MILK_DATASET)
    if target_column not in dataframe.columns:
        raise ValueError(f"Target '{target_column}' was not found in {MILK_DATASET}")

    sampled = sample_dataset(dataframe)
    sampled[target_column] = pd.to_numeric(sampled[target_column], errors="coerce")
    sampled = sampled.dropna(subset=[target_column])

    excluded: dict[str, list[str]] = {
        "identifier/date": [],
        "target/leakage": [],
        "not preferred for this candidate": [],
    }
    leakage_warnings = detect_target_risks(sampled[target_column], "regression")

    features: list[str] = []
    for column in dataframe.columns:
        if is_identifier_column(column) or is_date_column(column):
            excluded["identifier/date"].append(column)
            continue
        if column in forbidden_inputs:
            excluded["target/leakage"].append(
                f"{column} (excluded to avoid circular feed recommendation dependency)"
            )
            continue
        if column != "Previous_Week_Avg_Yield":
            leakage_reason = leakage_column_reason(column, target_column, leakage_terms)
            if leakage_reason:
                excluded["target/leakage"].append(f"{column} ({leakage_reason})")
                continue
        if column in preferred_features:
            features.append(column)
        else:
            excluded["not preferred for this candidate"].append(column)

    features = [feature for feature in preferred_features if feature in features]
    numeric_features, categorical_features = split_feature_types(sampled, features)

    x_train, x_test, y_train, y_test = train_test_split(
        sampled[features],
        sampled[target_column],
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    dummy = DummyRegressor(strategy="mean")
    dummy.fit(x_train, y_train)
    metrics: dict[str, dict[str, Any]] = {
        "DummyRegressor(mean)": regression_metrics(y_test, dummy.predict(x_test))
    }

    rf_pipeline = Pipeline(
        steps=[
            ("preprocessing", make_preprocessor(numeric_features, categorical_features)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=80,
                    max_depth=14,
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                ),
            ),
        ]
    )
    rf_pipeline.fit(x_train, y_train)
    metrics["RandomForestRegressor"] = regression_metrics(
        y_test, rf_pipeline.predict(x_test)
    )

    hgb_pipeline = Pipeline(
        steps=[
            ("preprocessing", make_preprocessor(numeric_features, categorical_features)),
            (
                "model",
                HistGradientBoostingRegressor(
                    max_iter=120,
                    learning_rate=0.08,
                    max_leaf_nodes=31,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    hgb_pipeline.fit(x_train, y_train)
    metrics["HistGradientBoostingRegressor"] = regression_metrics(
        y_test, hgb_pipeline.predict(x_test)
    )

    best_model_name, best_metrics = max(
        (
            (name, model_metrics)
            for name, model_metrics in metrics.items()
            if name != "DummyRegressor(mean)"
        ),
        key=lambda item: item[1]["R2"],
    )
    baseline = metrics["DummyRegressor(mean)"]
    r2_gain = best_metrics["R2"] - baseline["R2"]
    mae_gain = baseline["MAE"] - best_metrics["MAE"]

    suitability_notes = [
        f"Best trained model: {best_model_name}",
        f"R2 improvement over dummy baseline: {r2_gain:.4f}",
        f"MAE improvement over dummy baseline: {mae_gain:.4f} L",
    ]

    recommended = best_metrics["R2"] >= 0.10 and r2_gain >= 0.10 and mae_gain > 0
    if recommended:
        suitability_notes.append(
            "Candidate is usable as a supporting milk-yield predictor, not as an "
            "optimal feed recommender."
        )
    else:
        suitability_notes.append(
            "Candidate is not reliable enough to recommend as an ML support model."
        )

    if best_metrics["R2"] < 0.05:
        leakage_warnings.append(
            "Very weak regression performance suggests the target may be random or "
            "poorly explained by farmer-collectable features."
        )
    if best_metrics["R2"] > 0.98:
        leakage_warnings.append(
            "Extremely high regression performance would require manual leakage review."
        )

    return CandidateResult(
        name="Candidate A - Milk-yield prediction",
        dataset_path=MILK_DATASET,
        target_column=target_column,
        original_rows=len(dataframe),
        sampled_rows=len(sampled),
        target_distribution=format_distribution(sampled[target_column]),
        selected_features=features,
        excluded_columns=excluded,
        leakage_warnings=leakage_warnings,
        suitability_notes=suitability_notes,
        metrics=metrics,
        recommended=recommended,
    )


def evaluate_disease_status() -> CandidateResult:
    target_column = "Disease_Status"
    preferred_features = [
        "Breed",
        "Age_Months",
        "Weight_kg",
        "Lactation_Stage",
        "Days_in_Milk",
        "Body_Temperature_C",
        "Heart_Rate_bpm",
        "Respiratory_Rate",
        "Water_Intake_L",
        "Walking_Distance_km",
        "Grazing_Duration_hrs",
        "Rumination_Time_hrs",
        "Resting_Hours",
        "Ambient_Temperature_C",
        "Humidity_percent",
        "Housing_Score",
        "Milk_Yield_L",
        "Previous_Week_Avg_Yield",
        "Body_Condition_Score",
        "Milking_Interval_hrs",
        "FMD_Vaccine",
        "Brucellosis_Vaccine",
        "HS_Vaccine",
        "BQ_Vaccine",
        "Anthrax_Vaccine",
        "IBR_Vaccine",
        "BVD_Vaccine",
        "Rabies_Vaccine",
    ]
    leakage_terms = {"disease", "diagnosis", "status", "label", "risk"}

    dataframe = load_dataset(DISEASE_DATASET)
    if target_column not in dataframe.columns:
        raise ValueError(f"Target '{target_column}' was not found in {DISEASE_DATASET}")

    sampled = sample_dataset(dataframe)
    sampled[target_column] = sampled[target_column].astype("string")
    sampled = sampled.dropna(subset=[target_column])

    excluded: dict[str, list[str]] = {
        "identifier/date": [],
        "target/leakage": [],
        "not preferred for this candidate": [],
    }
    leakage_warnings = detect_target_risks(sampled[target_column], "classification")

    features: list[str] = []
    for column in dataframe.columns:
        if is_identifier_column(column) or is_date_column(column):
            excluded["identifier/date"].append(column)
            continue
        leakage_reason = leakage_column_reason(column, target_column, leakage_terms)
        if leakage_reason:
            excluded["target/leakage"].append(f"{column} ({leakage_reason})")
            continue
        if column in preferred_features:
            features.append(column)
        else:
            excluded["not preferred for this candidate"].append(column)

    features = [feature for feature in preferred_features if feature in features]
    numeric_features, categorical_features = split_feature_types(sampled, features)

    x_train, x_test, y_train, y_test = train_test_split(
        sampled[features],
        sampled[target_column],
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=sampled[target_column],
    )

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(x_train, y_train)
    metrics: dict[str, dict[str, Any]] = {
        "DummyClassifier(most_frequent)": classification_metrics(
            y_test, dummy.predict(x_test)
        )
    }

    rf_pipeline = Pipeline(
        steps=[
            ("preprocessing", make_preprocessor(numeric_features, categorical_features)),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=16,
                    class_weight="balanced_subsample",
                    random_state=RANDOM_STATE,
                    n_jobs=1,
                ),
            ),
        ]
    )
    rf_pipeline.fit(x_train, y_train)
    metrics["RandomForestClassifier"] = classification_metrics(
        y_test, rf_pipeline.predict(x_test)
    )

    baseline = metrics["DummyClassifier(most_frequent)"]
    model_metrics = metrics["RandomForestClassifier"]
    balanced_gain = (
        model_metrics["balanced_accuracy"] - baseline["balanced_accuracy"]
    )
    f1_gain = model_metrics["f1_weighted"] - baseline["f1_weighted"]

    suitability_notes = [
        "Best trained model: RandomForestClassifier",
        f"Balanced accuracy improvement over dummy baseline: {balanced_gain:.4f}",
        f"Weighted F1 improvement over dummy baseline: {f1_gain:.4f}",
    ]

    recommended = (
        model_metrics["balanced_accuracy"] >= 0.60
        and model_metrics["f1_weighted"] >= 0.60
        and balanced_gain >= 0.10
        and f1_gain > 0.05
    )
    if recommended:
        suitability_notes.append(
            "Candidate is usable as a supporting disease-risk signal for feed planning."
        )
    else:
        suitability_notes.append(
            "Candidate is not reliable enough to recommend as an ML support model."
        )

    if model_metrics["balanced_accuracy"] < 0.55:
        leakage_warnings.append(
            "Weak balanced accuracy suggests the disease target may be random or "
            "poorly explained by available farmer-collectable fields."
        )
    if model_metrics["balanced_accuracy"] > 0.98 or model_metrics["f1_weighted"] > 0.98:
        leakage_warnings.append(
            "Extremely high classification performance would require manual leakage review."
        )

    return CandidateResult(
        name="Candidate B - Disease-status classification",
        dataset_path=DISEASE_DATASET,
        target_column=target_column,
        original_rows=len(dataframe),
        sampled_rows=len(sampled),
        target_distribution=format_distribution(sampled[target_column]),
        selected_features=features,
        excluded_columns=excluded,
        leakage_warnings=leakage_warnings,
        suitability_notes=suitability_notes,
        metrics=metrics,
        recommended=recommended,
    )


def format_metric_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def append_result_report(lines: list[str], result: CandidateResult) -> None:
    lines.extend(
        [
            "",
            result.name,
            "-" * len(result.name),
            f"Dataset: {result.dataset_path}",
            f"Target: {result.target_column}",
            f"Original rows: {result.original_rows:,}",
            f"Rows evaluated: {result.sampled_rows:,}",
            "",
            "Target distribution:",
            result.target_distribution,
            "",
            "Feature columns:",
        ]
    )
    lines.extend(f"  - {feature}" for feature in result.selected_features)

    lines.append("")
    lines.append("Excluded columns:")
    for reason, columns in result.excluded_columns.items():
        if columns:
            lines.append(f"  {reason}:")
            lines.extend(f"    - {column}" for column in columns)
        else:
            lines.append(f"  {reason}: none")

    lines.append("")
    lines.append("Model metrics:")
    for model_name, model_metrics in result.metrics.items():
        lines.append(f"  {model_name}:")
        for metric_name, metric_value in model_metrics.items():
            if metric_name == "confusion_matrix":
                lines.append("    confusion_matrix:")
                for row in metric_value:
                    lines.append(f"      {row}")
            elif metric_name == "labels":
                lines.append(f"    labels: {metric_value}")
            else:
                lines.append(f"    {metric_name}: {format_metric_value(metric_value)}")

    lines.append("")
    lines.append("Leakage and suitability warnings:")
    if result.leakage_warnings:
        lines.extend(f"  - {warning}" for warning in result.leakage_warnings)
    else:
        lines.append("  - No obvious target leakage was detected from column names.")
    lines.extend(f"  - {note}" for note in result.suitability_notes)
    lines.append(
        "  - Dataset provenance and real-world measurement quality are not verified; "
        "do not make real-world nutritional or veterinary claims from this evaluation."
    )
    lines.append(
        "  - Suitability: "
        + ("recommended as a supporting model" if result.recommended else "not recommended")
    )


def choose_final_recommendation(
    milk_result: CandidateResult, disease_result: CandidateResult
) -> str:
    if milk_result.recommended and disease_result.recommended:
        return "Both supporting models + rule-based feed planner"
    if milk_result.recommended:
        return "Milk-yield ML model + rule-based feed planner"
    if disease_result.recommended:
        return "Disease-risk ML model + rule-based feed planner"
    return "Rule-based feed planner only because neither ML target is reliable"


def build_report(results: list[CandidateResult]) -> str:
    final_recommendation = choose_final_recommendation(results[0], results[1])
    lines = [
        "FarmLite Candidate Model Evaluation Report",
        "==========================================",
        "",
        "Purpose: Evaluate alternative tabular ML targets that might support the "
        "FarmLite cattle feed recommendation module.",
        "",
        "Rejected prior experiment:",
        "  - Feed_Quantity_kg RandomForestRegressor is rejected and must not be "
        "integrated into Flask or the frontend.",
        "  - The prior report is preserved at: "
        f"{FAILED_FEED_REPORT_PATH}",
        "  - A negative R2 means that experiment performed worse than predicting "
        "the mean feed quantity.",
        "",
        f"Sampling limit: {MAX_ROWS:,} rows per dataset",
        f"Random state: {RANDOM_STATE}",
        "Train/test split: 80/20",
        "",
        "Important limitation: These datasets do not provide validated optimal feed "
        "recommendation labels. Any ML model here can only be a supporting signal "
        "beside rule-based feed planning.",
    ]

    for result in results:
        append_result_report(lines, result)

    lines.extend(
        [
            "",
            "Final recommendation",
            "--------------------",
            final_recommendation,
            "",
            "Architecture note: Do not integrate the failed feed-quantity model. "
            "Use only recommended supporting model targets, if any, alongside a "
            "transparent rule-based feed planner. Keep real-world claims cautious "
            "because the datasets appear synthetic or at least unsuitable for "
            "validated cattle nutrition claims without external verification.",
        ]
    )
    return "\n".join(lines) + "\n"


def print_summary(results: list[CandidateResult]) -> None:
    print()
    print("Summary")
    print("=======")
    for result in results:
        print(result.name)
        for model_name, model_metrics in result.metrics.items():
            compact_metrics = []
            for metric_name, metric_value in model_metrics.items():
                if metric_name in {"confusion_matrix", "labels"}:
                    continue
                compact_metrics.append(f"{metric_name}={format_metric_value(metric_value)}")
            print(f"  {model_name}: {', '.join(compact_metrics)}")
        print(
            "  Suitability: "
            + ("recommended as supporting ML" if result.recommended else "not recommended")
        )

    print()
    print("Final recommendation:")
    print(f"  {choose_final_recommendation(results[0], results[1])}")


def main() -> int:
    print("WARNING: feed_quantity_model.joblib is a rejected experiment.")
    print("WARNING: Do not integrate it into Flask or the React frontend.")
    if FAILED_FEED_REPORT_PATH.exists():
        print(f"Previous failed experiment report preserved: {FAILED_FEED_REPORT_PATH}")
    else:
        print(
            f"Previous failed experiment report was not found at: {FAILED_FEED_REPORT_PATH}"
        )

    try:
        results = [evaluate_milk_yield(), evaluate_disease_status()]
    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    report = build_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print_summary(results)
    print()
    print(f"Report saved: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
