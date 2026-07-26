"""Leakage-safe OOF feed-category predictions for Design B."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ml.preprocessing.feature_builder import build_features
from ml.training.experiment_types import CandidateConfig
from ml.training.experiment_utils import (
    Phase4ExperimentError,
    build_candidate_pipeline,
    ensure_valid_predictions,
)
from ml.training.metrics import classification_metrics
from ml.training.train_feed_type_classifier import approved_labels


@dataclass
class OOFGenerationResult:
    """OOF records plus training-only classifier products for Design B."""

    predictions: pd.DataFrame
    summary: dict[str, Any]
    training_fitted_pipeline: Any
    validation_predictions: np.ndarray
    test_predictions: np.ndarray | None


def generate_oof_feed_type_predictions(
    training: pd.DataFrame,
    validation: pd.DataFrame,
    fold_manifest: pd.DataFrame,
    config: CandidateConfig,
    *,
    test: pd.DataFrame | None = None,
) -> OOFGenerationResult:
    """Cross-fit training rows and predict non-training partitions safely.

    Test features are optional so validation selection can be locked before
    final test prediction occurs.
    """

    train_built = build_features(training, "feed_type_classifier")
    validation_built = build_features(validation, "feed_type_classifier")
    fold_by_source = fold_manifest.set_index("source_row_number")["training_fold"]
    source_rows = training["source_row_number"]
    try:
        folds = source_rows.map(fold_by_source).astype(int)
    except (KeyError, ValueError, TypeError) as error:
        raise Phase4ExperimentError(
            "Training rows do not align to the Phase 3 OOF manifest"
        ) from error
    if folds.isna().any():
        raise Phase4ExperimentError("At least one training row lacks an OOF fold")

    oof = np.empty(len(training), dtype=object)
    audits: list[dict[str, Any]] = []
    total_fit_seconds = 0.0
    total_prediction_seconds = 0.0
    for fold in sorted(folds.unique()):
        heldout_mask = folds.to_numpy() == fold
        fit_mask = ~heldout_mask
        pipeline = build_candidate_pipeline(config, "feed_type_classifier")
        started = time.perf_counter()
        pipeline.fit(
            train_built.X.loc[fit_mask],
            train_built.y.loc[fit_mask],
        )
        total_fit_seconds += time.perf_counter() - started
        predict_started = time.perf_counter()
        fold_predictions = pipeline.predict(train_built.X.loc[heldout_mask])
        total_prediction_seconds += time.perf_counter() - predict_started
        ensure_valid_predictions(
            fold_predictions, expected_rows=int(heldout_mask.sum())
        )
        oof[heldout_mask] = fold_predictions
        fit_source_rows = set(source_rows.loc[fit_mask])
        heldout_source_rows = set(source_rows.loc[heldout_mask])
        audits.append(
            {
                "training_fold": int(fold),
                "fit_row_count": int(fit_mask.sum()),
                "heldout_row_count": int(heldout_mask.sum()),
                "heldout_rows_in_fit_count": len(
                    fit_source_rows.intersection(heldout_source_rows)
                ),
                "validation_rows_used_for_fit": False,
                "test_rows_used_for_fit": False,
            }
        )
    if pd.isna(oof).any():
        raise Phase4ExperimentError("At least one training row lacks an OOF prediction")

    oof_metrics = classification_metrics(
        train_built.y,
        oof,
        labels=approved_labels(),
    )
    final_pipeline = build_candidate_pipeline(config, "feed_type_classifier")
    started = time.perf_counter()
    final_pipeline.fit(train_built.X, train_built.y)
    full_train_fit_seconds = time.perf_counter() - started
    validation_predictions = final_pipeline.predict(validation_built.X)
    ensure_valid_predictions(
        validation_predictions, expected_rows=len(validation)
    )
    test_predictions = None
    if test is not None:
        test_built = build_features(test, "feed_type_classifier")
        test_predictions = np.asarray(final_pipeline.predict(test_built.X))
        ensure_valid_predictions(test_predictions, expected_rows=len(test))

    records = pd.DataFrame(
        {
            "source_row_number": training["source_row_number"].to_numpy(),
            "cattle_id": training["cattle_id"].to_numpy(),
            "training_fold": folds.to_numpy(),
            "predicted_feed_type": oof,
            "model_configuration_id": config.configuration_id,
        }
    ).sort_values("source_row_number", ignore_index=True)
    if records["source_row_number"].duplicated().any():
        raise Phase4ExperimentError("OOF output contains duplicate rows")
    if "feed_type" in records.columns:
        raise Phase4ExperimentError("True feed type leaked into OOF output")

    summary = {
        "model_configuration_id": config.configuration_id,
        "training_row_count": len(training),
        "prediction_row_count": len(records),
        "every_training_row_has_one_prediction": len(records) == len(training),
        "duplicate_prediction_rows": int(
            records["source_row_number"].duplicated().sum()
        ),
        "true_feed_type_in_output": False,
        "validation_rows_used_in_oof_fit": False,
        "test_rows_used_in_oof_fit": False,
        "fold_audit": audits,
        "oof_metrics": oof_metrics,
        "cross_fit_training_seconds": round(total_fit_seconds, 6),
        "cross_fit_prediction_seconds": round(total_prediction_seconds, 6),
        "full_training_classifier_fit_seconds": round(
            full_train_fit_seconds, 6
        ),
    }
    return OOFGenerationResult(
        predictions=records,
        summary=summary,
        training_fitted_pipeline=final_pipeline,
        validation_predictions=np.asarray(validation_predictions),
        test_predictions=test_predictions,
    )


__all__ = [
    "OOFGenerationResult",
    "generate_oof_feed_type_predictions",
]
