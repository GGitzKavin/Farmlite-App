"""Focused tests for deterministic base splits and training-only OOF folds."""

from __future__ import annotations

import unittest

from ml.preprocessing.split_data import (
    create_split_assignments,
    create_training_fold_assignments,
)
from tests.preprocessing_fixtures import FEED_TYPES, make_fixture


class SplitDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = make_fixture(800)
        cls.split = create_split_assignments(cls.fixture)
        cls.folds = create_training_fold_assignments(
            cls.fixture, cls.split.manifest
        )

    def test_split_proportions_are_seventy_fifteen_fifteen(self) -> None:
        self.assertEqual(
            self.split.summary["row_counts"],
            {"train": 560, "validation": 120, "test": 120},
        )

    def test_feed_type_stratification_is_preserved(self) -> None:
        distributions = self.split.summary["feed_type_distribution"]
        for split in ("train", "validation", "test"):
            for category in FEED_TYPES:
                self.assertAlmostEqual(
                    distributions[split][category]["percentage"],
                    12.5,
                    delta=0.85,
                )

    def test_each_row_has_exactly_one_split(self) -> None:
        manifest = self.split.manifest
        self.assertEqual(len(manifest), len(self.fixture))
        self.assertFalse(manifest["source_row_number"].duplicated().any())
        self.assertEqual(
            set(manifest["split"]), {"train", "validation", "test"}
        )

    def test_no_cattle_id_overlap_occurs(self) -> None:
        self.assertEqual(
            self.split.summary["checks"]["cattle_id_overlap_count"], 0
        )

    def test_same_seed_produces_identical_assignments(self) -> None:
        repeated = create_split_assignments(self.fixture, random_seed=42)

        self.assertTrue(self.split.manifest.equals(repeated.manifest))
        self.assertEqual(
            self.split.summary["reproducibility_hash_sha256"],
            repeated.summary["reproducibility_hash_sha256"],
        )

    def test_changed_seed_changes_assignments(self) -> None:
        changed = create_split_assignments(self.fixture, random_seed=43)

        self.assertFalse(self.split.manifest.equals(changed.manifest))

    def test_manifest_contains_only_traceability_and_split_fields(self) -> None:
        self.assertEqual(
            self.split.manifest.columns.tolist(),
            [
                "source_row_number",
                "cattle_id",
                "observation_date",
                "split",
                "random_seed",
                "split_version",
            ],
        )
        self.assertNotIn("feed_type", self.split.manifest.columns)
        self.assertNotIn("milk_yield_l", self.split.manifest.columns)

    def test_every_training_row_receives_one_oof_fold(self) -> None:
        training_rows = set(
            self.split.manifest.loc[
                self.split.manifest["split"] == "train", "source_row_number"
            ]
        )
        folded_rows = set(self.folds.manifest["source_row_number"])

        self.assertEqual(training_rows, folded_rows)
        self.assertFalse(
            self.folds.manifest["source_row_number"].duplicated().any()
        )

    def test_validation_and_test_rows_receive_no_oof_fold(self) -> None:
        nontraining_rows = set(
            self.split.manifest.loc[
                self.split.manifest["split"] != "train", "source_row_number"
            ]
        )

        self.assertTrue(
            nontraining_rows.isdisjoint(
                set(self.folds.manifest["source_row_number"])
            )
        )

    def test_oof_assignment_is_deterministic_and_has_no_predictions(self) -> None:
        repeated = create_training_fold_assignments(
            self.fixture,
            self.split.manifest,
        )

        self.assertTrue(self.folds.manifest.equals(repeated.manifest))
        self.assertFalse(
            any(
                "predict" in column.casefold()
                for column in self.folds.manifest.columns
            )
        )


if __name__ == "__main__":
    unittest.main()
