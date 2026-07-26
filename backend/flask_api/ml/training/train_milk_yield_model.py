"""Train the final FarmLite milk-yield prediction pipeline.

This model predicts Milk_Yield_L only. It is intended to support a later
rule-based feed planner, not to produce direct feed recommendations.
"""

from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

try:
    import joblib
    import pandas as pd
    from pandas.api.types import is_numeric_dtype
    from sklearn.compose import ColumnTransformer
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except ImportError as error:
    print(
        "ERROR: Missing Python package. Make sure pandas, scikit-learn, and "
        "joblib are installed from backend/flask_api/requirements.txt.",
        file=sys.stderr,
    )
    print(f"Import error: {error}", file=sys.stderr)
    raise SystemExit(1)

try:
    from config.settings import (
        MILK_YIELD_DATASET_PATH,
        MILK_YIELD_MODEL_PATH,
        ML_REPORTS_DIR,
        PROCESSED_DATA_DIR,
    )
except ModuleNotFoundError:
    # Support both ``python -m`` and direct script execution.
    flask_api_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(flask_api_dir))
    from config.settings import (
        MILK_YIELD_DATASET_PATH,
        MILK_YIELD_MODEL_PATH,
        ML_REPORTS_DIR,
        PROCESSED_DATA_DIR,
    )

DATASET_PATH = MILK_YIELD_DATASET_PATH
MODEL_PATH = MILK_YIELD_MODEL_PATH
REPORT_PATH = ML_REPORTS_DIR / "milk_yield_model_report.txt"

TARGET_COLUMN = "Milk_Yield_L"
MAX_ROWS = 60_000
RANDOM_STATE = 42

PREFERRED_FEATURES = [
    "Breed",
    "Age_Months",
    "Weight_kg",
    "Lactation_Stage",
    "Days_in_Milk",
    "Ambient_Temperature_C",
    "Humidity_percent",
    "Previous_Week_Avg_Yield",
    "Body_Condition_Score",
]


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


def is_target_leakage_column(column_name: str) -> bool:
    if column_name == TARGET_COLUMN:
        return True

    normalized_column = normalize_column_name(column_name)
    normalized_target = normalize_column_name(TARGET_COLUMN)
    return normalized_column == normalized_target


def one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def select_features(columns: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    excluded: dict[str, list[str]] = {
        "target/leakage": [],
        "circular feed dependency": [],
        "identifier/date": [],
        "not selected": [],
    }

    selected = [feature for feature in PREFERRED_FEATURES if feature in columns]

    for column in columns:
        if is_target_leakage_column(column):
            excluded["target/leakage"].append(column)
        elif column == "Feed_Quantity_kg":
            excluded["circular feed dependency"].append(column)
        elif is_identifier_column(column) or is_date_column(column):
            excluded["identifier/date"].append(column)
        elif column not in selected:
            excluded["not selected"].append(column)

    return selected, excluded


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


def format_feature_list(columns: list[str]) -> str:
    if not columns:
        return "  - None"
    return "\n".join(f"  - {column}" for column in columns)


def format_excluded_columns(excluded_columns: dict[str, list[str]]) -> str:
    lines = []
    for reason, columns in excluded_columns.items():
        lines.append(f"  {reason}:")
        if columns:
            lines.extend(f"    - {column}" for column in columns)
        else:
            lines.append("    - None")
    return "\n".join(lines)


def build_report(
    *,
    original_row_count: int,
    sampled_row_count: int,
    train_row_count: int,
    test_row_count: int,
    selected_features: list[str],
    numeric_features: list[str],
    categorical_features: list[str],
    excluded_columns: dict[str, list[str]],
    baseline_metrics: dict[str, float],
    final_metrics: dict[str, float],
    model_file_size: int,
) -> str:
    sampling_note = (
        f"Dataset exceeded {MAX_ROWS:,} rows and was randomly sampled to "
        f"{sampled_row_count:,} rows using random_state={RANDOM_STATE}."
        if original_row_count > MAX_ROWS
        else "The full dataset was used because it did not exceed the sampling limit."
    )

    return f"""FarmLite Milk Yield Model Report
================================

Dataset path: {DATASET_PATH}
Original row count: {original_row_count:,}
Rows used after sampling: {sampled_row_count:,}
Training row count: {train_row_count:,}
Test row count: {test_row_count:,}
Sampling note: {sampling_note}

Target column: {TARGET_COLUMN}

Selected feature columns:
{format_feature_list(selected_features)}

Numeric feature columns:
{format_feature_list(numeric_features)}

Categorical feature columns:
{format_feature_list(categorical_features)}

Excluded columns:
{format_excluded_columns(excluded_columns)}

Baseline model
--------------
Model type: DummyRegressor(strategy="mean")
MAE: {baseline_metrics["MAE"]:.4f} L
RMSE: {baseline_metrics["RMSE"]:.4f} L
R2 score: {baseline_metrics["R2"]:.4f}

Final model
-----------
Model type: HistGradientBoostingRegressor
Model parameters: max_iter=200, learning_rate=0.08, max_leaf_nodes=31, random_state=42
MAE: {final_metrics["MAE"]:.4f} L
RMSE: {final_metrics["RMSE"]:.4f} L
R2 score: {final_metrics["R2"]:.4f}

Saved model path: {MODEL_PATH}
Model file size: {model_file_size:,} bytes ({model_file_size / (1024 * 1024):.2f} MiB)

Limitations
-----------
- The model predicts milk yield only.
- It does not directly produce optimal feed recommendations.
- Feed recommendation must be generated using rule-based nutritional logic.
- Output is advisory only and should not replace guidance from a veterinarian or qualified animal nutritionist.
- Dataset provenance and real-world validity have not been independently verified.
- The rejected Feed_Quantity_kg model remains a failed experiment and must not be presented as production-ready.
"""


def main() -> int:
    if not DATASET_PATH.is_file():
        print(f"ERROR: Dataset not found at: {DATASET_PATH}", file=sys.stderr)
        return 1

    try:
        dataframe = pd.read_csv(DATASET_PATH, low_memory=False)
    except Exception as error:
        print(f"ERROR: Could not load dataset: {error}", file=sys.stderr)
        return 1

    print(f"Dataset loaded: {DATASET_PATH}")
    original_row_count = len(dataframe)
    print(f"Original rows: {original_row_count:,}")

    if dataframe.empty:
        print("ERROR: Dataset is empty.", file=sys.stderr)
        return 1

    if TARGET_COLUMN not in dataframe.columns:
        print(
            f"ERROR: Required target column '{TARGET_COLUMN}' was not found.",
            file=sys.stderr,
        )
        return 1

    selected_features, excluded_columns = select_features(
        [str(column) for column in dataframe.columns]
    )
    if not selected_features:
        print("ERROR: No preferred feature columns were found.", file=sys.stderr)
        return 1

    print(f"Features selected ({len(selected_features)}):")
    for feature in selected_features:
        print(f"  - {feature}")

    if original_row_count > MAX_ROWS:
        working_data = dataframe.sample(n=MAX_ROWS, random_state=RANDOM_STATE).copy()
        print(
            f"Sampled {MAX_ROWS:,} rows using random_state={RANDOM_STATE}."
        )
    else:
        working_data = dataframe.copy()
        print("Using all dataset rows.")

    working_data[TARGET_COLUMN] = pd.to_numeric(
        working_data[TARGET_COLUMN], errors="coerce"
    )
    invalid_target_count = int(working_data[TARGET_COLUMN].isna().sum())
    if invalid_target_count:
        print(
            f"Dropped {invalid_target_count:,} rows with missing or non-numeric "
            f"{TARGET_COLUMN} values."
        )
        working_data = working_data.dropna(subset=[TARGET_COLUMN])

    if working_data.empty:
        print("ERROR: No valid rows remain after target validation.", file=sys.stderr)
        return 1

    numeric_features, categorical_features = split_feature_types(
        working_data, selected_features
    )

    features = working_data[selected_features]
    target = working_data[TARGET_COLUMN]
    train_features, test_features, train_target, test_target = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    print(
        f"Training started with {len(train_features):,} training rows and "
        f"{len(test_features):,} test rows."
    )

    baseline_model = DummyRegressor(strategy="mean")
    baseline_model.fit(train_features, train_target)
    baseline_metrics = regression_metrics(
        test_target, baseline_model.predict(test_features)
    )
    print(
        "Baseline evaluated: "
        f"MAE={baseline_metrics['MAE']:.4f} L, "
        f"RMSE={baseline_metrics['RMSE']:.4f} L, "
        f"R2={baseline_metrics['R2']:.4f}"
    )

    final_pipeline = Pipeline(
        steps=[
            ("preprocessing", make_preprocessor(numeric_features, categorical_features)),
            (
                "model",
                HistGradientBoostingRegressor(
                    max_iter=200,
                    learning_rate=0.08,
                    max_leaf_nodes=31,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    final_pipeline.fit(train_features, train_target)
    final_metrics = regression_metrics(
        test_target, final_pipeline.predict(test_features)
    )
    print(
        "Final model evaluated: "
        f"MAE={final_metrics['MAE']:.4f} L, "
        f"RMSE={final_metrics['RMSE']:.4f} L, "
        f"R2={final_metrics['R2']:.4f}"
    )

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, MODEL_PATH, compress=3)
    model_file_size = MODEL_PATH.stat().st_size
    print(
        f"Model saved: {MODEL_PATH} "
        f"({model_file_size:,} bytes, {model_file_size / (1024 * 1024):.2f} MiB)"
    )

    report = build_report(
        original_row_count=original_row_count,
        sampled_row_count=len(working_data),
        train_row_count=len(train_features),
        test_row_count=len(test_features),
        selected_features=selected_features,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        excluded_columns=excluded_columns,
        baseline_metrics=baseline_metrics,
        final_metrics=final_metrics,
        model_file_size=model_file_size,
    )
    ML_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved: {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
