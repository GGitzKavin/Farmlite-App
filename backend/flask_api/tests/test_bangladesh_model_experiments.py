"""Thirty focused tests for the controlled Bangladesh Phase 4.5D run."""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from config.settings import FLASK_API_DIR, MILK_YIELD_MODEL_PATH
from ml.data_integration.bangladesh_audit import (
    DMI_FILENAME,
    EXPECTED_SHA256,
    SOURCE_DIR,
    sha256_file,
)
from ml.data_integration.validate_bangladesh_dataset import (
    _protected_snapshot,
)
from ml.training.bangladesh_modeling import (
    LINEAGE_FIELDS,
    PRIMARY_FEATURES,
    PROCESSED_DIR,
    RANDOM_SEED,
    TASKS,
    build_pipeline,
    build_task_frame,
    candidate_specs,
    create_group_assignments,
    evaluate_grouped_candidate,
    load_contract,
    load_source_frame,
    smoke_validate,
)
from ml.training.metrics import regression_metrics
from ml.training.run_bangladesh_model_experiments import (
    LOCK_PATH,
    TRAINING_SUMMARY_PATH,
    _task_paths,
)


class BangladeshModelExperimentTests(unittest.TestCase):
    """Validate features, grouping, artifacts, and protected boundaries."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_before = sha256_file(SOURCE_DIR / DMI_FILENAME)
        cls.protected_before = _protected_snapshot()
        cls.contract = load_contract()
        cls.source, cls.source_metadata = load_source_frame()
        cls.frames = {
            task: build_task_frame(cls.source, task) for task in TASKS
        }
        cls.assignments = create_group_assignments(cls.frames["dmi"])
        cls.smoke = smoke_validate()
        cls.summary = (
            json.loads(TRAINING_SUMMARY_PATH.read_text(encoding="utf-8"))
            if TRAINING_SUMMARY_PATH.is_file()
            else None
        )
        cls.protected_after = _protected_snapshot()
        cls.raw_after = sha256_file(SOURCE_DIR / DMI_FILENAME)

    def _require_full_run(self) -> dict:
        if self.summary is None:
            self.skipTest("Full controlled experiment has not run yet")
        return self.summary

    def test_01_processed_rows_preserve_source_lineage(self) -> None:
        summary = self._require_full_run()
        for task in TASKS:
            path = PROCESSED_DIR / TASKS[task]["processed_filename"]
            processed = pd.read_csv(path, dtype={"cow_id": str})
            expected = self.frames[task]
            self.assertEqual(len(processed), 750)
            self.assertEqual(list(processed.columns), list(expected.columns))
            self.assertEqual(
                processed[LINEAGE_FIELDS].astype(str).to_dict("records"),
                expected[LINEAGE_FIELDS].astype(str).to_dict("records"),
            )
            self.assertEqual(summary["processed_files"][task]["rows"], 750)

    def test_02_raw_workbooks_remain_unchanged(self) -> None:
        self.assertEqual(self.raw_before, self.raw_after)
        self.assertEqual(self.raw_after, EXPECTED_SHA256[DMI_FILENAME])

    def test_03_cow_ids_are_present(self) -> None:
        for frame in self.frames.values():
            self.assertEqual(frame["cow_id"].isna().sum(), 0)
            self.assertEqual(frame["cow_id"].nunique(), 50)

    def test_04_every_cow_remains_in_one_fold_or_holdout(self) -> None:
        manifest = self.assignments["manifest"]
        self.assertTrue(
            (manifest.groupby("cow_id")["partition"].nunique() == 1).all()
        )
        development = manifest["partition"].eq("development")
        self.assertTrue(
            (
                manifest.loc[development]
                .groupby("cow_id")["group_cv_fold"]
                .nunique()
                == 1
            ).all()
        )

    def test_05_no_cow_overlap_occurs(self) -> None:
        manifest = self.assignments["manifest"]
        development = set(
            manifest.loc[
                manifest["partition"].eq("development"), "cow_id"
            ]
        )
        holdout = set(
            manifest.loc[manifest["partition"].eq("holdout"), "cow_id"]
        )
        self.assertFalse(development & holdout)
        self.assertEqual(
            self.assignments["validation"]["cow_overlap_count"], 0
        )

    def test_06_repeated_rows_are_not_randomly_split(self) -> None:
        manifest = self.assignments["manifest"]
        counts = manifest.groupby("cow_id").size()
        self.assertTrue((counts == 15).all())
        self.assertEqual(
            self.assignments["validation"]["grouping_field"], "cow_id"
        )
        self.assertEqual(
            self.assignments["validation"]["holdout_method"],
            "GroupShuffleSplit",
        )

    def test_07_dmi_target_definition_is_correct(self) -> None:
        model = self.contract["models"]["bangladesh_dmi_regressor"]
        self.assertEqual(model["target"], "dry_matter_intake_kg_day")
        self.assertIn("kilograms per cow per day", model["target_definition"])
        self.assertEqual(TASKS["dmi"]["source_target"], "DMI (kg)")

    def test_08_milk_target_definition_is_correct(self) -> None:
        model = self.contract["models"][
            "bangladesh_milk_yield_regressor"
        ]
        self.assertEqual(model["target"], "milk_yield_l_day")
        self.assertIn("litres per cow per day", model["target_definition"])
        self.assertEqual(
            TASKS["milk"]["source_target"], "Milk Yield (L/day/cow)"
        )

    def test_09_target_is_excluded_from_x(self) -> None:
        for task, frame in self.frames.items():
            X = frame[PRIMARY_FEATURES]
            self.assertNotIn(TASKS[task]["target"], X.columns)
            self.assertEqual(list(X.columns), PRIMARY_FEATURES)

    def test_10_cow_id_is_excluded_from_x(self) -> None:
        self.assertNotIn("cow_id", PRIMARY_FEATURES)
        for model in self.contract["models"].values():
            self.assertNotIn("cow_id", model["feature_order"])

    def test_11_milk_composition_is_excluded(self) -> None:
        forbidden = {"SCC", "Fat", "Protein", "Lactose", "SNF", "pH"}
        self.assertFalse(
            any(
                token.casefold() in feature.casefold()
                for feature in PRIMARY_FEATURES for token in forbidden
            )
        )
        for frame in self.frames.values():
            self.assertFalse(
                any(column in frame.columns for column in (
                    "Fat%", "Protein %", "Lactose%", "SNF%", "pH"
                ))
            )

    def test_12_blood_outcomes_are_excluded(self) -> None:
        forbidden = {"glucose", "cortisol", "ast", "alt", "blood"}
        self.assertFalse(
            any(
                token in feature.casefold()
                for feature in PRIMARY_FEATURES for token in forbidden
            )
        )

    def test_13_physiology_is_excluded_from_primary_models(self) -> None:
        forbidden = {"rectal", "pulse", "respiration"}
        self.assertFalse(
            any(
                token in feature.casefold()
                for feature in PRIMARY_FEATURES for token in forbidden
            )
        )
        self.assertEqual(
            self.contract["models"]["bangladesh_dmi_regressor"][
                "feature_order"
            ],
            PRIMARY_FEATURES,
        )

    def test_14_unknown_genetic_group_transforms_safely(self) -> None:
        frame = self.frames["dmi"]
        train_indices, _ = self.assignments["cv_splits"][0]
        train = frame.iloc[train_indices]
        spec = candidate_specs("dmi")[3]
        pipeline = build_pipeline(spec)
        pipeline.fit(
            train[PRIMARY_FEATURES],
            train[TASKS["dmi"]["target"]],
        )
        unknown = pd.DataFrame(
            {"genetic_group": ["UNSEEN"], "thi_category": ["T0"]}
        )
        self.assertTrue(np.isfinite(pipeline.predict(unknown)).all())

    def test_15_unknown_thi_category_transforms_safely(self) -> None:
        frame = self.frames["milk"]
        train_indices, _ = self.assignments["cv_splits"][0]
        train = frame.iloc[train_indices]
        spec = candidate_specs("milk")[3]
        pipeline = build_pipeline(spec)
        pipeline.fit(
            train[PRIMARY_FEATURES],
            train[TASKS["milk"]["target"]],
        )
        unknown = pd.DataFrame(
            {"genetic_group": ["HF50"], "thi_category": ["UNSEEN"]}
        )
        self.assertTrue(np.isfinite(pipeline.predict(unknown)).all())

    def test_16_baseline_metrics_calculate_correctly(self) -> None:
        result = regression_metrics([1.0, 2.0, 3.0], [2.0, 2.0, 2.0])
        self.assertAlmostEqual(result["mae"], 2.0 / 3.0)
        self.assertAlmostEqual(result["rmse"], np.sqrt(2.0 / 3.0))
        self.assertEqual(result["r2"], 0.0)
        self.assertEqual(result["negative_prediction_count"], 0)

    def test_17_grouped_metrics_calculate_correctly(self) -> None:
        frame = self.frames["dmi"]
        result = evaluate_grouped_candidate(
            frame,
            "dmi",
            candidate_specs("dmi")[0],
            self.assignments["cv_splits"],
        )
        self.assertEqual(len(result["fold_metrics"]), 5)
        self.assertEqual(result["selection_cows"], 40)
        self.assertEqual(result["selection_rows"], 600)
        self.assertTrue(np.isfinite(result["aggregate_metrics"]["mae"]))

    def test_18_holdout_data_is_excluded_from_selection(self) -> None:
        holdout = set(self.assignments["holdout_indices"].tolist())
        selection_indices = {
            int(index)
            for _, validation in self.assignments["cv_splits"]
            for index in validation
        }
        self.assertFalse(holdout & selection_indices)
        self.assertEqual(len(selection_indices), 600)

    def test_19_locked_selection_precedes_holdout_evaluation(self) -> None:
        source = Path(
            "ml/training/run_bangladesh_model_experiments.py"
        ).read_text(encoding="utf-8")
        lock_position = source.index("_write_json(LOCK_PATH, lock)")
        holdout_position = source.index(
            "holdout = evaluate_final_holdout("
        )
        self.assertLess(lock_position, holdout_position)
        if LOCK_PATH.is_file() and self.summary is not None:
            lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
            self.assertFalse(
                lock["holdout_metrics_evaluated_before_lock"]
            )
            self.assertFalse(
                self.summary["holdout_cows_used_in_selection"]
            )

    def test_20_candidate_artifact_reloads_successfully(self) -> None:
        summary = self._require_full_run()
        for task in TASKS:
            task_summary = summary["tasks"][task]
            if not task_summary["holdout"]["holdout_gate_passed"]:
                continue
            artifact = _task_paths(task)["artifact"]
            loaded = joblib.load(artifact)
            self.assertTrue(hasattr(loaded, "predict"))

    def test_21_reloaded_predictions_match(self) -> None:
        summary = self._require_full_run()
        for task in TASKS:
            reload_check = summary["tasks"][task]["artifact_reload"]
            if reload_check.get("saved") is False:
                continue
            self.assertTrue(reload_check["reload_predictions_identical"])

    def test_22_metadata_records_50_unique_cows(self) -> None:
        summary = self._require_full_run()
        for task in TASKS:
            if not summary["tasks"][task]["holdout"]["holdout_gate_passed"]:
                continue
            metadata = json.loads(
                _task_paths(task)["metadata"].read_text(encoding="utf-8")
            )
            self.assertEqual(metadata["number_of_unique_cows"], 50)

    def test_23_metadata_records_repeated_observations(self) -> None:
        summary = self._require_full_run()
        for task in TASKS:
            if not summary["tasks"][task]["holdout"]["holdout_gate_passed"]:
                continue
            metadata = json.loads(
                _task_paths(task)["metadata"].read_text(encoding="utf-8")
            )
            self.assertTrue(metadata["repeated_measurements"])
            self.assertEqual(metadata["observations_per_cow"], 15)

    def test_24_metadata_marks_deployment_false(self) -> None:
        summary = self._require_full_run()
        self.assertFalse(self.contract["production_approved"])
        for task in TASKS:
            if not summary["tasks"][task]["holdout"]["holdout_gate_passed"]:
                continue
            metadata = json.loads(
                _task_paths(task)["metadata"].read_text(encoding="utf-8")
            )
            self.assertFalse(metadata["production_approved"])
            self.assertFalse(metadata["commercial_use_approved"])
            self.assertFalse(metadata["veterinary_use_approved"])

    def test_25_existing_model_artifacts_remain_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(MILK_YIELD_MODEL_PATH),
            "B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA",
        )
        self.assertEqual(
            self.protected_before["phase4_candidates"],
            self.protected_after["phase4_candidates"],
        )
        if self.summary is not None:
            self.assertTrue(self.summary["protected_files_unchanged"])

    def test_26_flask_routes_remain_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["routes"],
            self.protected_after["routes"],
        )

    def test_27_frontend_remains_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["frontend_tree"],
            self.protected_after["frontend_tree"],
        )

    def test_28_nutrition_rules_remain_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["nutrition_rules"],
            self.protected_after["nutrition_rules"],
        )

    def test_29_no_feed_type_model_is_trained(self) -> None:
        runner = Path(
            "ml/training/run_bangladesh_model_experiments.py"
        ).read_text(encoding="utf-8")
        modeling = Path(
            "ml/training/bangladesh_modeling.py"
        ).read_text(encoding="utf-8")
        forbidden = {
            "DummyClassifier",
            "LogisticRegression",
            "DecisionTreeClassifier",
            "RandomForestClassifier",
        }
        names = {
            node.id
            for source in (runner, modeling)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Name)
        }
        self.assertFalse(forbidden & names)
        if self.summary is not None:
            self.assertFalse(self.summary["feed_type_model_trained"])

    def test_30_no_source_datasets_are_concatenated(self) -> None:
        for task, frame in self.frames.items():
            self.assertTrue(
                (frame["source_workbook"] == DMI_FILENAME).all(),
                task,
            )
        if self.summary is not None:
            self.assertFalse(self.summary["source_datasets_concatenated"])


if __name__ == "__main__":
    unittest.main()
