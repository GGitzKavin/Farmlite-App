"""Train FarmLite's advisory cattle feed-quantity regression model."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import joblib
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from config.settings import (
        MILK_YIELD_DATASET_PATH,
        ML_MODELS_DIR,
        ML_REPORTS_DIR,
        PROCESSED_DATA_DIR,
    )
except ModuleNotFoundError:
    # Support both ``python -m`` and direct script execution.
    flask_api_dir = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(flask_api_dir))
    from config.settings import (
        MILK_YIELD_DATASET_PATH,
        ML_MODELS_DIR,
        ML_REPORTS_DIR,
        PROCESSED_DATA_DIR,
    )

DATASET_PATH = MILK_YIELD_DATASET_PATH
MODEL_PATH = ML_MODELS_DIR / "feed_quantity_model.joblib"
REPORT_PATH = ML_REPORTS_DIR / "feed_model_report.txt"

TARGET_COLUMN = "Feed_Quantity_kg"
MAX_TRAINING_ROWS = 60_000
RANDOM_STATE = 42

PREFERRED_FEATURE_KEYWORDS = (
    "age",
    "weight",
    "breed",
    "health",
    "milk",
    "yield",
    "lactation",
    "production",
    "stage",
    "animal",
    "temperature",
    "humidity",
    "environment",
    "body",
    "condition",
)

LEAKAGE_PHRASES = (
    "feed quantity",
    "feed intake",
    "daily feed",
    "recommended feed",
    "target feed",
)


def normalize_column_name(column_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", column_name.lower()).strip()


def contains_phrase(column_name: str, phrase: str) -> bool:
    normalized_column = f" {normalize_column_name(column_name)} "
    normalized_phrase = f" {normalize_column_name(phrase)} "
    return normalized_phrase in normalized_column


def is_identifier_column(column_name: str) -> bool:
    tokens = normalize_column_name(column_name).split()
    return "id" in tokens or "identifier" in tokens


def is_date_column(column_name: str) -> bool:
    tokens = normalize_column_name(column_name).split()
    return "date" in tokens or "timestamp" in tokens


def is_target_leakage_column(column_name: str) -> bool:
    if column_name == TARGET_COLUMN:
        return True
    return any(contains_phrase(column_name, phrase) for phrase in LEAKAGE_PHRASES)


def select_feature_columns(columns: list[str]) -> list[str]:
    """Select preferred columns while excluding identifiers, dates, and target leakage."""

    selected: list[str] = []

    for column in columns:
        if (
            is_identifier_column(column)
            or is_date_column(column)
            or is_target_leakage_column(column)
        ):
            continue

        if any(
            contains_phrase(column, keyword)
            for keyword in PREFERRED_FEATURE_KEYWORDS
        ):
            selected.append(column)

    return selected


def format_feature_list(columns: list[str]) -> str:
    if not columns:
        return "  - None"
    return "\n".join(f"  - {column}" for column in columns)


def build_report(
    *,
    original_row_count: int,
    sampled_row_count: int,
    train_row_count: int,
    test_row_count: int,
    selected_features: list[str],
    numeric_features: list[str],
    categorical_features: list[str],
    mae: float,
    rmse: float,
    r2: float,
    model_file_size: int,
) -> str:
    sampling_note = (
        f"Dataset exceeded {MAX_TRAINING_ROWS:,} rows and was randomly sampled to "
        f"{sampled_row_count:,} rows using random_state={RANDOM_STATE}."
        if original_row_count > MAX_TRAINING_ROWS
        else "The complete dataset was used because it did not exceed the sampling limit."
    )
    if r2 < 0:
        metric_interpretation = (
            "The negative R2 score means this model performed worse than predicting the "
            "test-set mean. The selected dataset fields do not currently provide a reliable "
            "feed-quantity model."
        )
    elif r2 < 0.5:
        metric_interpretation = (
            "The R2 score indicates weak predictive performance. Treat predictions as "
            "experimental and do not use them as nutrition guidance."
        )
    else:
        metric_interpretation = (
            "The metrics describe performance only on a held-out sample of this dataset; "
            "they do not validate nutritional correctness or real-world safety."
        )

    return f"""FarmLite Feed Quantity Model Report
===================================

Dataset path: {DATASET_PATH}
Original row count: {original_row_count:,}
Rows used after sampling: {sampled_row_count:,}
Training row count: {train_row_count:,}
Test row count: {test_row_count:,}
Sampling note: {sampling_note}

Target column: {TARGET_COLUMN}
Model type: RandomForestRegressor
Model parameters: n_estimators=80, max_depth=14, random_state=42, n_jobs=-1

Selected feature columns:
{format_feature_list(selected_features)}

Numeric feature columns:
{format_feature_list(numeric_features)}

Categorical feature columns:
{format_feature_list(categorical_features)}

Evaluation metrics
------------------
MAE: {mae:.4f} kg
RMSE: {rmse:.4f} kg
R2 score: {r2:.4f}
Interpretation: {metric_interpretation}

Saved model path: {MODEL_PATH}
Model file size: {model_file_size:,} bytes ({model_file_size / (1024 * 1024):.2f} MiB)

Limitations
-----------
- The dataset does not contain validated optimal feed recommendation labels.
- The model predicts historical feed quantity patterns only.
- Final recommendation requires rule-based nutritional logic.
- Output is advisory only and should not replace veterinary or nutritionist advice.
- Dataset provenance, representativeness, and real-world measurement quality have not been verified.
- Evaluation metrics measure fit to this dataset, not nutritional safety or causal feeding outcomes.
- A model with weak or negative R2 should not be integrated as a recommendation signal without redesign and validation.
"""


def main() -> int:
    if not DATASET_PATH.is_file():
        print(f"ERROR: Dataset not found at: {DATASET_PATH}", file=sys.stderr)
        print(
            "Place global_cattle_milk_yield_prediction_dataset.csv in the "
            f"raw dataset folder: {DATASET_PATH.parent}",
            file=sys.stderr,
        )
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

    selected_features = select_feature_columns(
        [str(column) for column in dataframe.columns]
    )
    if not selected_features:
        print(
            "ERROR: No suitable feature columns were selected from the dataset.",
            file=sys.stderr,
        )
        return 1

    print(f"Features selected ({len(selected_features)}):")
    for feature in selected_features:
        print(f"  - {feature}")

    if original_row_count > MAX_TRAINING_ROWS:
        working_data = dataframe.sample(
            n=MAX_TRAINING_ROWS,
            random_state=RANDOM_STATE,
        ).copy()
        print(
            f"Sampled {MAX_TRAINING_ROWS:,} rows for training "
            f"using random_state={RANDOM_STATE}."
        )
    else:
        working_data = dataframe.copy()
        print("Using all dataset rows for training.")

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
        print("ERROR: No valid target rows remain after validation.", file=sys.stderr)
        return 1

    numeric_features = [
        column
        for column in selected_features
        if is_numeric_dtype(working_data[column])
    ]
    categorical_features = [
        column for column in selected_features if column not in numeric_features
    ]

    transformers = []
    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, numeric_features))

    if categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("one_hot", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        transformers.append(
            ("categorical", categorical_pipeline, categorical_features)
        )

    preprocessing = ColumnTransformer(transformers=transformers)
    model = RandomForestRegressor(
        n_estimators=80,
        max_depth=14,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("model", model),
        ]
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
    pipeline.fit(train_features, train_target)

    predictions = pipeline.predict(test_features)
    mae = float(mean_absolute_error(test_target, predictions))
    rmse = math.sqrt(float(mean_squared_error(test_target, predictions)))
    r2 = float(r2_score(test_target, predictions))
    print(
        "Evaluation completed: "
        f"MAE={mae:.4f} kg, RMSE={rmse:.4f} kg, R2={r2:.4f}"
    )

    ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH, compress=3)
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
        mae=mae,
        rmse=rmse,
        r2=r2,
        model_file_size=model_file_size,
    )
    ML_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report saved: {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
