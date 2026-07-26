"""Small candidate registry using only installed scikit-learn estimators."""

from __future__ import annotations

from typing import Any

from sklearn.base import BaseEstimator
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from ml.training.experiment_types import CandidateConfig


RANDOM_SEED = 42
SUPPORTED_TASKS = {"feed_type", "feed_quantity", "milk_yield"}


def _classifier_configs() -> list[CandidateConfig]:
    return [
        CandidateConfig(
            "feed_type_dummy_most_frequent",
            "feed_type",
            "DummyClassifier",
            "dummy_classifier",
            {"strategy": "most_frequent"},
            "tree",
            is_baseline=True,
        ),
        CandidateConfig(
            "feed_type_dummy_stratified",
            "feed_type",
            "DummyClassifier",
            "dummy_classifier",
            {"strategy": "stratified", "random_state": RANDOM_SEED},
            "tree",
            is_baseline=True,
        ),
        CandidateConfig(
            "feed_type_logistic_c1",
            "feed_type",
            "LogisticRegression",
            "logistic_regression",
            {
                "C": 1.0,
                "max_iter": 300,
                "solver": "lbfgs",
                "random_state": RANDOM_SEED,
            },
            "linear",
        ),
        CandidateConfig(
            "feed_type_decision_tree",
            "feed_type",
            "DecisionTreeClassifier",
            "decision_tree_classifier",
            {
                "max_depth": 14,
                "min_samples_leaf": 20,
                "random_state": RANDOM_SEED,
            },
            "tree",
        ),
        CandidateConfig(
            "feed_type_random_forest",
            "feed_type",
            "RandomForestClassifier",
            "random_forest_classifier",
            {
                "n_estimators": 60,
                "max_depth": 18,
                "min_samples_leaf": 5,
                "n_jobs": 2,
                "random_state": RANDOM_SEED,
            },
            "tree",
            resource_class="EXPENSIVE",
        ),
        CandidateConfig(
            "feed_type_hist_gradient_boosting",
            "feed_type",
            "HistGradientBoostingClassifier",
            "hist_gradient_boosting_classifier",
            {
                "max_iter": 80,
                "learning_rate": 0.08,
                "max_leaf_nodes": 31,
                "l2_regularization": 0.1,
                "random_state": RANDOM_SEED,
            },
            "dense_tree",
            resource_class="EXPENSIVE",
        ),
    ]


def _regression_configs(task: str) -> list[CandidateConfig]:
    prefix = "feed_quantity" if task == "feed_quantity" else "milk_yield"
    return [
        CandidateConfig(
            f"{prefix}_dummy_mean",
            task,
            "DummyRegressor",
            "dummy_regressor",
            {"strategy": "mean"},
            "tree",
            is_baseline=True,
        ),
        CandidateConfig(
            f"{prefix}_dummy_median",
            task,
            "DummyRegressor",
            "dummy_regressor",
            {"strategy": "median"},
            "tree",
            is_baseline=True,
        ),
        CandidateConfig(
            f"{prefix}_ridge",
            task,
            "Ridge",
            "ridge",
            {"alpha": 1.0},
            "linear",
        ),
        CandidateConfig(
            f"{prefix}_decision_tree",
            task,
            "DecisionTreeRegressor",
            "decision_tree_regressor",
            {
                "max_depth": 14,
                "min_samples_leaf": 20,
                "random_state": RANDOM_SEED,
            },
            "tree",
        ),
        CandidateConfig(
            f"{prefix}_random_forest",
            task,
            "RandomForestRegressor",
            "random_forest_regressor",
            {
                "n_estimators": 60,
                "max_depth": 18,
                "min_samples_leaf": 5,
                "max_features": 0.8,
                "n_jobs": 2,
                "random_state": RANDOM_SEED,
            },
            "tree",
            resource_class="EXPENSIVE",
        ),
        CandidateConfig(
            f"{prefix}_hist_gradient_boosting",
            task,
            "HistGradientBoostingRegressor",
            "hist_gradient_boosting_regressor",
            {
                "max_iter": 100,
                "learning_rate": 0.08,
                "max_leaf_nodes": 31,
                "l2_regularization": 0.1,
                "random_state": RANDOM_SEED,
            },
            "dense_tree",
            resource_class="EXPENSIVE",
        ),
    ]


def candidate_configs(
    task: str,
    *,
    skip_expensive: bool = False,
) -> list[CandidateConfig]:
    """Return the locked small registry for a supported task."""

    if task not in SUPPORTED_TASKS:
        raise ValueError(
            f"Unsupported training task '{task}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_TASKS))}"
        )
    configs = (
        _classifier_configs()
        if task == "feed_type"
        else _regression_configs(task)
    )
    if skip_expensive:
        configs = [
            config for config in configs if config.resource_class != "EXPENSIVE"
        ]
    return configs


def get_candidate(configuration_id: str) -> CandidateConfig:
    """Look up one configuration across the registry."""

    for task in sorted(SUPPORTED_TASKS):
        for config in candidate_configs(task):
            if config.configuration_id == configuration_id:
                return config
    raise ValueError(f"Unsupported candidate configuration: {configuration_id}")


def create_estimator(config: CandidateConfig) -> BaseEstimator:
    """Create a fresh estimator for a registered candidate."""

    factories: dict[str, type[BaseEstimator]] = {
        "dummy_classifier": DummyClassifier,
        "dummy_regressor": DummyRegressor,
        "logistic_regression": LogisticRegression,
        "ridge": Ridge,
        "decision_tree_classifier": DecisionTreeClassifier,
        "decision_tree_regressor": DecisionTreeRegressor,
        "random_forest_classifier": RandomForestClassifier,
        "random_forest_regressor": RandomForestRegressor,
        "hist_gradient_boosting_classifier": HistGradientBoostingClassifier,
        "hist_gradient_boosting_regressor": HistGradientBoostingRegressor,
    }
    factory = factories.get(config.estimator_name)
    if factory is None:
        raise ValueError(
            f"Unsupported estimator name: {config.estimator_name}"
        )
    return factory(**config.parameters)


def registry_snapshot() -> dict[str, list[dict[str, Any]]]:
    """Return a deterministic JSON-ready registry snapshot."""

    return {
        task: [config.to_dict() for config in candidate_configs(task)]
        for task in sorted(SUPPORTED_TASKS)
    }


__all__ = [
    "RANDOM_SEED",
    "SUPPORTED_TASKS",
    "candidate_configs",
    "create_estimator",
    "get_candidate",
    "registry_snapshot",
]
