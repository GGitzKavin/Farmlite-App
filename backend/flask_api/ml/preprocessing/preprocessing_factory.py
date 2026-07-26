"""Factories for unfitted sklearn preprocessing-only pipelines."""

from __future__ import annotations

from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.impute import MissingIndicator, SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.preprocessing.feature_builder import (
    DEFAULT_CONTRACT_PATH,
    get_model_spec,
)


OPTIONAL_NUMERIC_FEATURES = [
    "days_in_milk",
    "previous_week_avg_yield_l",
    "body_condition_score",
    "ambient_temperature_c",
    "humidity_percent",
]


def build_preprocessor(
    model_name: str,
    *,
    scale_numeric: bool = False,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> ColumnTransformer:
    """Build an unfitted preprocessing object with no prediction estimator."""

    spec = get_model_spec(model_name, contract_path=contract_path)
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            ),
        ]
    )
    numeric_steps: list[tuple[str, object]] = [
        ("imputer", SimpleImputer(strategy="median"))
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipeline = Pipeline(steps=numeric_steps)
    optional_numeric = [
        name for name in OPTIONAL_NUMERIC_FEATURES if name in spec.feature_names
    ]

    transformers: list[tuple[str, object, list[str]]] = [
        ("categorical", categorical_pipeline, spec.categorical_features),
        ("numeric", numeric_pipeline, spec.numeric_features),
    ]
    if optional_numeric:
        transformers.append(
            (
                "optional_numeric_missing",
                MissingIndicator(features="all"),
                optional_numeric,
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=True,
    )


def build_linear_preprocessor(
    model_name: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> ColumnTransformer:
    """Build an unfitted preprocessor with scaled numeric features."""

    return build_preprocessor(
        model_name,
        scale_numeric=True,
        contract_path=contract_path,
    )


def build_tree_preprocessor(
    model_name: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> ColumnTransformer:
    """Build an unfitted preprocessor without unnecessary numeric scaling."""

    return build_preprocessor(
        model_name,
        scale_numeric=False,
        contract_path=contract_path,
    )


__all__ = [
    "OPTIONAL_NUMERIC_FEATURES",
    "build_linear_preprocessor",
    "build_preprocessor",
    "build_tree_preprocessor",
]
