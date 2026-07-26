"""Focused unittest coverage for the controlled Phase 4 training stack."""

from __future__ import annotations

import hashlib
import inspect
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from config.settings import (
    DISEASE_DATASET_PATH,
    FLASK_API_DIR,
    MILK_YIELD_DATASET_PATH,
    MILK_YIELD_MODEL_PATH,
    PROJECT_ROOT,
)
from ml.preprocessing.feature_builder import (
    ModelContractError,
    build_features,
    get_model_spec,
)
from ml.training.experiment_utils import (
    Phase4ExperimentError,
    build_candidate_pipeline,
    reload_prediction_check,
    sha256_file,
    validate_candidate_metadata,
    write_json,
    write_locked_selection,
)
from ml.training.generate_feed_type_oof_predictions import (
    generate_oof_feed_type_predictions,
)
from ml.training.metrics import classification_metrics, regression_metrics
from ml.training.model_registry import (
    SUPPORTED_TASKS,
    candidate_configs,
    get_candidate,
)
from ml.training.run_phase4_experiments import run_full_experiment
from ml.training.train_feed_quantity_regressor import (
    add_predicted_feed_type,
    build_feed_quantity_views,
)
from ml.training.train_feed_type_classifier import approved_labels
from ml.training.train_milk_yield_regressor import (
    select_milk_yield_candidate,
)
from tests.preprocessing_fixtures import BASE_FEATURES, FEED_TYPES, make_fixture


EXPECTED_PRIMARY_HASH = (
    "26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3"
)
EXPECTED_DISEASE_HASH = (
    "4CEDFA77234FE45B441E303FF051C33123969E37C3B484A03387094A613DC4B9"
)
EXPECTED_EXISTING_MODEL_HASH = (
    "B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA"
)
EXPECTED_ROUTE_HASH = (
    "843D623EFF7B48497BB95A07ADF3222D7F94C66C03B091F24A9976D77AE7A0F0"
)
EXPECTED_NUTRITION_HASH = (
    "3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C"
)
# Phase 7 establishes the next authorized route/frontend security snapshot.
# Model, dataset and nutrition hashes remain frozen.
EXPECTED_FRONTEND_AGGREGATE_HASH = (
    "DCA5E5B5C3F1A7FEBE06196A70FDA4639C4166E17055C7293A8DF4616B5FBA58"
)


def _frontend_aggregate_hash() -> str:
    frontend = PROJECT_ROOT / "frontend"
    files = sorted(
        path
        for path in frontend.rglob("*")
        if path.is_file()
        and "node_modules" not in path.parts
        and "dist" not in path.parts
    )
    lines = [
        (
            f"{path.relative_to(PROJECT_ROOT).as_posix()}|"
            f"{sha256_file(path)}"
        )
        for path in files
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest().upper()


def _candidate_metadata() -> dict[str, object]:
    return {
        "artifact_status": "CANDIDATE_ONLY",
        "model_task": "synthetic_fixture",
        "model_algorithm": "Ridge",
        "hyperparameters": {"alpha": 1.0},
        "feature_order": BASE_FEATURES,
        "target": "milk_yield_l",
        "preprocessing_description": "Complete sklearn pipeline.",
        "dataset_source": {"generation": "synthetic"},
        "synthetic_data_declaration": (
            "Synthetic publisher-declared data for undergraduate prototype "
            "workflow only."
        ),
        "dataset_checksum": EXPECTED_PRIMARY_HASH,
        "split_manifest_hash": "fixture",
        "contract_version": "1.0.0",
        "random_seed": 42,
        "training_row_count": 60,
        "validation_row_count": 10,
        "test_row_count": 10,
        "validation_metrics": {"mae": 1.0},
        "test_metrics": {"mae": 1.1},
        "baseline_metrics": {"mae": 2.0},
        "library_versions": {"scikit_learn": "fixture"},
        "training_timestamp": "2026-01-01T00:00:00+00:00",
        "training_duration_seconds": 0.1,
        "known_limitations": ["synthetic"],
        "deployment_approved": False,
    }


class Phase4RegistryAndMetricTests(unittest.TestCase):
    def test_candidate_registry_creates_valid_configurations(self) -> None:
        for task in SUPPORTED_TASKS:
            configs = candidate_configs(task)
            self.assertGreaterEqual(len(configs), 6)
            self.assertTrue(any(config.is_baseline for config in configs))
            self.assertTrue(all(config.task == task for config in configs))
            self.assertEqual(
                len({config.configuration_id for config in configs}),
                len(configs),
            )

    def test_unsupported_model_name_is_rejected(self) -> None:
        with self.assertRaises(ModelContractError):
            get_model_spec("unsupported_model")

    def test_unknown_configuration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_candidate("not_registered")

    def test_classification_metrics_calculate_correctly(self) -> None:
        actual = ["A", "A", "B", "B"]
        predicted = ["A", "B", "B", "B"]
        metrics = classification_metrics(
            actual, predicted, labels=["A", "B"]
        )
        self.assertAlmostEqual(metrics["accuracy"], 0.75)
        self.assertEqual(metrics["predicted_class_count"], 2)
        self.assertEqual(metrics["confusion_matrix"], [[1, 1], [0, 2]])

    def test_regression_metrics_calculate_correctly(self) -> None:
        metrics = regression_metrics([1.0, 2.0, 3.0], [1.0, 2.0, 4.0])
        self.assertAlmostEqual(metrics["mae"], 1 / 3)
        self.assertGreater(metrics["rmse"], metrics["mae"])
        self.assertEqual(metrics["negative_prediction_count"], 0)

    def test_undefined_classification_metrics_are_explicit_zero(self) -> None:
        metrics = classification_metrics(
            ["A", "B", "B"],
            ["A", "A", "A"],
            labels=["A", "B"],
        )
        self.assertEqual(metrics["per_class"]["B"]["precision"], 0.0)
        self.assertEqual(metrics["per_class"]["B"]["recall"], 0.0)
        self.assertEqual(metrics["per_class"]["B"]["predicted_count"], 0)


class Phase4PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = make_fixture(80)

    def test_training_view_excludes_target(self) -> None:
        built = build_features(self.fixture, "milk_yield_regressor")
        self.assertNotIn("milk_yield_l", built.X.columns)
        self.assertEqual(list(built.X.columns), BASE_FEATURES)

    def test_pipeline_fits_on_small_fixture(self) -> None:
        built = build_features(self.fixture, "milk_yield_regressor")
        pipeline = build_candidate_pipeline(
            get_candidate("milk_yield_ridge"),
            "milk_yield_regressor",
        )
        pipeline.fit(built.X, built.y)
        self.assertTrue(hasattr(pipeline, "predict"))

    def test_pipeline_predicts_expected_row_count(self) -> None:
        built = build_features(self.fixture, "milk_yield_regressor")
        pipeline = build_candidate_pipeline(
            get_candidate("milk_yield_decision_tree"),
            "milk_yield_regressor",
        )
        pipeline.fit(built.X.iloc[:60], built.y.iloc[:60])
        predictions = pipeline.predict(built.X.iloc[60:])
        self.assertEqual(len(predictions), 20)

    def test_prediction_output_has_no_nan(self) -> None:
        built = build_features(self.fixture, "feed_type_classifier")
        pipeline = build_candidate_pipeline(
            get_candidate("feed_type_logistic_c1"),
            "feed_type_classifier",
        )
        pipeline.fit(built.X.iloc[:64], built.y.iloc[:64])
        predictions = pipeline.predict(built.X.iloc[64:])
        self.assertFalse(pd.isna(predictions).any())

    def test_serialized_pipeline_reloads(self) -> None:
        built = build_features(self.fixture, "milk_yield_regressor")
        pipeline = build_candidate_pipeline(
            get_candidate("milk_yield_ridge"),
            "milk_yield_regressor",
        )
        pipeline.fit(built.X.iloc[:60], built.y.iloc[:60])
        with tempfile.TemporaryDirectory() as temp:
            check = reload_prediction_check(
                pipeline,
                Path(temp) / "candidate.joblib",
                built.X.iloc[60:],
            )
        self.assertTrue(check["reload_predictions_identical"])

    def test_reloaded_predictions_match_exactly(self) -> None:
        built = build_features(self.fixture, "feed_type_classifier")
        pipeline = build_candidate_pipeline(
            get_candidate("feed_type_decision_tree"),
            "feed_type_classifier",
        )
        pipeline.fit(built.X.iloc[:64], built.y.iloc[:64])
        with tempfile.TemporaryDirectory() as temp:
            check = reload_prediction_check(
                pipeline,
                Path(temp) / "candidate.joblib",
                built.X.iloc[64:],
            )
        self.assertTrue(check["reload_predictions_identical"])


class Phase4MetadataAndLockTests(unittest.TestCase):
    def test_candidate_metadata_is_valid_json(self) -> None:
        metadata = _candidate_metadata()
        validate_candidate_metadata(metadata)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "metadata.json"
            write_json(path, metadata)
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["artifact_status"], "CANDIDATE_ONLY")

    def test_candidate_metadata_contains_synthetic_warning(self) -> None:
        metadata = _candidate_metadata()
        validate_candidate_metadata(metadata)
        self.assertIn(
            "synthetic",
            str(metadata["synthetic_data_declaration"]).casefold(),
        )

    def test_candidate_metadata_sets_deployment_false(self) -> None:
        metadata = _candidate_metadata()
        validate_candidate_metadata(metadata)
        self.assertIs(metadata["deployment_approved"], False)

    def test_invalid_candidate_metadata_fails_closed(self) -> None:
        metadata = _candidate_metadata()
        metadata["deployment_approved"] = True
        with self.assertRaises(Phase4ExperimentError):
            validate_candidate_metadata(metadata)

    def test_locked_selection_is_created_once(self) -> None:
        payload = {
            "selected_classifier_configuration": "classifier",
            "selected_feed_quantity_design": "A",
            "selected_feed_quantity_configuration": "quantity",
            "selected_milk_yield_configuration": "milk",
            "selected_milk_yield_feature_version": "FULL_NINE_FEATURES",
            "validation_selections": {},
            "random_seed": 42,
            "contract_version": "1.0.0",
            "split_manifest_sha256": "split",
            "dataset_sha256": "dataset",
            "selection_timestamp": "2026-01-01T00:00:00+00:00",
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "lock.json"
            write_locked_selection(path, payload)
            self.assertTrue(path.is_file())
            with self.assertRaises(Phase4ExperimentError):
                write_locked_selection(path, payload)

    def test_lock_write_precedes_test_target_scoring_in_runner(self) -> None:
        source = inspect.getsource(run_full_experiment)
        lock_position = source.index("write_locked_selection(LOCK_PATH, lock)")
        boundary_position = source.index(
            "# No test target is referenced above this boundary."
        )
        test_position = source.index("classifier_test_views")
        self.assertLess(lock_position, boundary_position)
        self.assertLess(boundary_position, test_position)

    def test_candidate_selection_signature_has_no_test_partition(self) -> None:
        parameters = inspect.signature(
            select_milk_yield_candidate
        ).parameters
        self.assertNotIn("test", parameters)


class Phase4OOFAndDesignBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.training = make_fixture(80)
        cls.validation = make_fixture(16).assign(
            source_row_number=range(1_001, 1_017),
            cattle_id=[f"VAL_{index}" for index in range(16)],
        )
        cls.fold_manifest = pd.DataFrame(
            {
                "source_row_number": cls.training["source_row_number"],
                "cattle_id": cls.training["cattle_id"],
                "training_fold": np.tile(np.arange(1, 6), 16),
                "random_seed": 42,
                "fold_version": "fixture",
            }
        )
        cls.result = generate_oof_feed_type_predictions(
            cls.training,
            cls.validation,
            cls.fold_manifest,
            get_candidate("feed_type_logistic_c1"),
        )

    def test_oof_generation_uses_heldout_folds(self) -> None:
        for audit in self.result.summary["fold_audit"]:
            self.assertEqual(audit["heldout_rows_in_fit_count"], 0)

    def test_every_training_row_receives_one_oof_prediction(self) -> None:
        self.assertEqual(len(self.result.predictions), len(self.training))
        self.assertFalse(
            self.result.predictions["source_row_number"].duplicated().any()
        )
        self.assertFalse(
            self.result.predictions["predicted_feed_type"].isna().any()
        )

    def test_validation_rows_are_not_used_in_oof_fit(self) -> None:
        self.assertFalse(
            self.result.summary["validation_rows_used_in_oof_fit"]
        )
        self.assertTrue(
            all(
                not audit["validation_rows_used_for_fit"]
                for audit in self.result.summary["fold_audit"]
            )
        )

    def test_test_partition_is_deferred_until_after_lock(self) -> None:
        self.assertIsNone(self.result.test_predictions)
        self.assertFalse(self.result.summary["test_rows_used_in_oof_fit"])

    def test_true_feed_type_is_not_written_to_oof_output(self) -> None:
        self.assertNotIn("feed_type", self.result.predictions.columns)
        self.assertFalse(self.result.summary["true_feed_type_in_output"])

    def test_design_b_rejects_true_feed_type_substitution(self) -> None:
        with self.assertRaises((ValueError, ModelContractError)):
            build_feed_quantity_views(
                self.training,
                self.validation,
                design="B",
            )

    def test_design_b_accepts_only_explicit_predicted_feed_type(self) -> None:
        train = add_predicted_feed_type(
            self.training,
            self.result.predictions["predicted_feed_type"],
        )
        validation = add_predicted_feed_type(
            self.validation,
            self.result.validation_predictions,
        )
        X_train, _, X_validation, _ = build_feed_quantity_views(
            train,
            validation,
            design="B",
        )
        self.assertIn("predicted_feed_type", X_train.columns)
        self.assertNotIn("feed_type", X_train.columns)
        self.assertEqual(list(X_train.columns), list(X_validation.columns))


class Phase4ProtectedFileTests(unittest.TestCase):
    def test_existing_model_artifact_remains_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(MILK_YIELD_MODEL_PATH),
            EXPECTED_EXISTING_MODEL_HASH,
        )

    def test_raw_dataset_checksums_remain_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(MILK_YIELD_DATASET_PATH),
            EXPECTED_PRIMARY_HASH,
        )
        self.assertEqual(
            sha256_file(DISEASE_DATASET_PATH),
            EXPECTED_DISEASE_HASH,
        )

    def test_flask_routes_remain_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(FLASK_API_DIR / "api" / "routes.py"),
            EXPECTED_ROUTE_HASH,
        )

    def test_frontend_files_remain_unchanged(self) -> None:
        self.assertEqual(
            _frontend_aggregate_hash(),
            EXPECTED_FRONTEND_AGGREGATE_HASH,
        )

    def test_pdf_files_remain_unchanged(self) -> None:
        project_pdfs = [
            path
            for path in PROJECT_ROOT.rglob("*.pdf")
            if "venv" not in path.parts and "node_modules" not in path.parts
        ]
        self.assertEqual(project_pdfs, [])

    def test_nutrition_rules_remain_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(
                FLASK_API_DIR / "ml" / "validation" / "nutrition_rules.py"
            ),
            EXPECTED_NUTRITION_HASH,
        )


if __name__ == "__main__":
    unittest.main()
