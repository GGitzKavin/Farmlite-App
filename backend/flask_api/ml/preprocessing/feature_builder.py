"""Contract-driven logical feature views for the four approved designs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import FLASK_API_DIR
from ml.preprocessing.preprocessing_types import FeatureBuildResult, ModelSpec


DEFAULT_CONTRACT_PATH = FLASK_API_DIR / "config" / "model_contract.json"

BASE_CATEGORICAL_FEATURES = ["breed", "lactation_stage"]
BASE_NUMERIC_FEATURES = [
    "age_months",
    "weight_kg",
    "days_in_milk",
    "previous_week_avg_yield_l",
    "body_condition_score",
    "ambient_temperature_c",
    "humidity_percent",
]

SUPPORTED_MODEL_NAMES = {
    "feed_type_classifier",
    "feed_quantity_regressor_design_a",
    "feed_quantity_regressor_design_b",
    "milk_yield_regressor",
}

KNOWN_EXCLUSION_REASONS = {
    "cattle_id": "IDENTIFIER_METADATA_ONLY",
    "farm_id": "IDENTIFIER_METADATA_ONLY",
    "observation_date": "DATE_METADATA_ONLY",
    "feed_type": "SAME_RECORD_TARGET_OR_OUTCOME",
    "feed_quantity_kg": "SAME_RECORD_TARGET_OR_OUTCOME",
    "milk_yield_l": "SAME_RECORD_TARGET_OR_OUTCOME",
    "disease_status": "SECONDARY_DATASET_OUTCOME",
    "production_stage": "DUPLICATES_LACTATION_STAGE",
    "health_status": "RULE_INPUT_ONLY",
}


class ModelContractError(ValueError):
    """Raised when a requested feature view violates the approved contract."""


def load_model_contract(
    path: str | Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Load the approved Phase 2 model contract."""

    contract_path = Path(path)
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ModelContractError(
            f"Model contract is not valid JSON: {contract_path}: {error}"
        ) from error
    if not isinstance(contract, dict) or "contract_version" not in contract:
        raise ModelContractError("Model contract lacks contract_version")
    return contract


def get_model_spec(
    model_name: str,
    *,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> ModelSpec:
    """Resolve ordered features and target for an approved model design."""

    if model_name not in SUPPORTED_MODEL_NAMES:
        supported = ", ".join(sorted(SUPPORTED_MODEL_NAMES))
        raise ModelContractError(
            f"Unsupported model design '{model_name}'. Supported: {supported}"
        )

    contract = load_model_contract(contract_path)
    models = contract.get("models", {})
    if model_name == "feed_type_classifier":
        definition = models["feed_type_classifier"]
        features = [
            item["canonical_name"] for item in definition["selected_features"]
        ]
        target = definition["target"]["canonical_name"]
    elif model_name == "feed_quantity_regressor_design_a":
        definition = models["feed_quantity_regressor"]
        features = list(definition["design_a"]["selected_features"])
        target = definition["target"]["canonical_name"]
    elif model_name == "feed_quantity_regressor_design_b":
        definition = models["feed_quantity_regressor"]
        features = list(definition["design_b"]["selected_features"])
        target = definition["target"]["canonical_name"]
    else:
        definition = models["milk_yield_regressor"]
        features = list(definition["selected_features"])
        target = definition["target"]["canonical_name"]

    duplicates = sorted({name for name in features if features.count(name) > 1})
    if duplicates:
        raise ModelContractError(
            f"Model contract contains duplicate features for {model_name}: "
            + ", ".join(duplicates)
        )
    if target in features:
        raise ModelContractError(
            f"Target leakage in contract for {model_name}: '{target}' is an input"
        )

    categorical = [
        name
        for name in features
        if name in BASE_CATEGORICAL_FEATURES or name == "predicted_feed_type"
    ]
    numeric = [name for name in features if name in BASE_NUMERIC_FEATURES]
    if len(categorical) + len(numeric) != len(features):
        unresolved = [
            name for name in features if name not in {*categorical, *numeric}
        ]
        raise ModelContractError(
            f"Unclassified preprocessing feature(s): {', '.join(unresolved)}"
        )

    return ModelSpec(
        model_name=model_name,
        feature_names=features,
        target_name=target,
        contract_version=str(contract["contract_version"]),
        categorical_features=categorical,
        numeric_features=numeric,
    )


def _excluded_field_report(
    dataframe: pd.DataFrame,
    *,
    selected: list[str],
    target: str,
) -> list[dict[str, str]]:
    report: list[dict[str, str]] = []
    for column in map(str, dataframe.columns):
        if column in selected:
            continue
        if column == target:
            reason = "TARGET_SEPARATED_FROM_X"
        else:
            reason = KNOWN_EXCLUSION_REASONS.get(
                column, "NOT_SELECTED_BY_MODEL_CONTRACT"
            )
        report.append({"field": column, "reason": reason})
    return report


def build_features(
    dataframe: pd.DataFrame,
    model_name: str,
    *,
    include_target: bool = True,
    allow_predicted_feature: bool = False,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
) -> FeatureBuildResult:
    """Build an exact ordered feature frame without learned transformations."""

    if dataframe.columns.duplicated().any():
        duplicates = dataframe.columns[
            dataframe.columns.duplicated(keep=False)
        ].tolist()
        raise ModelContractError(
            "Duplicate canonical columns are not allowed: "
            + ", ".join(map(str, duplicates))
        )

    spec = get_model_spec(model_name, contract_path=contract_path)
    contract = load_model_contract(contract_path)
    if model_name == "feed_quantity_regressor_design_b":
        if not allow_predicted_feature:
            raise ModelContractError(
                "Design B is disabled by default. Supply an independently "
                "generated predicted_feed_type and set "
                "allow_predicted_feature=True."
            )
        if "predicted_feed_type" not in dataframe.columns:
            if "feed_type" in dataframe.columns:
                raise ModelContractError(
                    "Design B requires predicted_feed_type. True same-row "
                    "feed_type must not be substituted."
                )
            raise ModelContractError(
                "Design B requires an explicit predicted_feed_type column."
            )

    missing_features = [
        feature for feature in spec.feature_names if feature not in dataframe.columns
    ]
    if include_target:
        missing_required_features = missing_features
        optional_missing_features: list[str] = []
    else:
        catalog = contract["shared_validation"]["feature_catalog"]
        missing_required_features = [
            feature
            for feature in missing_features
            if feature == "predicted_feed_type"
            or catalog.get(feature, {}).get("required", False)
        ]
        optional_missing_features = [
            feature
            for feature in missing_features
            if feature not in missing_required_features
        ]
    if missing_required_features:
        raise ModelContractError(
            f"{model_name} is missing required feature columns: "
            + ", ".join(missing_required_features)
        )
    if include_target and spec.target_name not in dataframe.columns:
        raise ModelContractError(
            f"{model_name} requires training target '{spec.target_name}'"
        )

    feature_source = dataframe
    if optional_missing_features:
        feature_source = dataframe.assign(
            **{feature: pd.NA for feature in optional_missing_features}
        )
    X = feature_source.loc[:, spec.feature_names].copy()
    if spec.target_name in X.columns:
        raise ModelContractError(
            f"Target leakage detected: '{spec.target_name}' is present in X"
        )
    forbidden_identifiers = {"cattle_id", "farm_id", "observation_date"}
    leaked_identifiers = sorted(forbidden_identifiers.intersection(X.columns))
    if leaked_identifiers:
        raise ModelContractError(
            "Identifier/date leakage detected: " + ", ".join(leaked_identifiers)
        )

    y = (
        dataframe.loc[:, spec.target_name].copy()
        if include_target
        else None
    )
    return FeatureBuildResult(
        X=X,
        y=y,
        feature_names=list(spec.feature_names),
        target_name=spec.target_name,
        excluded_fields=_excluded_field_report(
            dataframe,
            selected=spec.feature_names,
            target=spec.target_name,
        ),
        model_contract_version=spec.contract_version,
    )


def build_feed_type_features(
    dataframe: pd.DataFrame,
    *,
    include_target: bool = True,
) -> FeatureBuildResult:
    """Build Model 1 features."""

    return build_features(
        dataframe,
        "feed_type_classifier",
        include_target=include_target,
    )


def build_feed_quantity_design_a_features(
    dataframe: pd.DataFrame,
    *,
    include_target: bool = True,
) -> FeatureBuildResult:
    """Build Model 2 Design A features."""

    return build_features(
        dataframe,
        "feed_quantity_regressor_design_a",
        include_target=include_target,
    )


def build_feed_quantity_design_b_features(
    dataframe: pd.DataFrame,
    *,
    include_target: bool = True,
    allow_predicted_feature: bool = False,
) -> FeatureBuildResult:
    """Build Model 2 Design B features with an explicit derived-value gate."""

    return build_features(
        dataframe,
        "feed_quantity_regressor_design_b",
        include_target=include_target,
        allow_predicted_feature=allow_predicted_feature,
    )


def build_milk_yield_features(
    dataframe: pd.DataFrame,
    *,
    include_target: bool = True,
) -> FeatureBuildResult:
    """Build Model 3 features."""

    return build_features(
        dataframe,
        "milk_yield_regressor",
        include_target=include_target,
    )


__all__ = [
    "BASE_CATEGORICAL_FEATURES",
    "BASE_NUMERIC_FEATURES",
    "DEFAULT_CONTRACT_PATH",
    "ModelContractError",
    "SUPPORTED_MODEL_NAMES",
    "build_features",
    "build_feed_quantity_design_a_features",
    "build_feed_quantity_design_b_features",
    "build_feed_type_features",
    "build_milk_yield_features",
    "get_model_spec",
    "load_model_contract",
]
