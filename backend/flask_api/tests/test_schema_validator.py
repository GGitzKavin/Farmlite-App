"""Focused tests for training, inference, and fixture schema modes."""

from __future__ import annotations

import unittest

import pandas as pd

from ml.preprocessing.preprocessing_types import ValidationMode
from ml.preprocessing.schema_validator import validate_schema
from tests.preprocessing_fixtures import make_fixture


class SchemaValidatorTests(unittest.TestCase):
    def test_valid_training_schema_passes(self) -> None:
        result = validate_schema(
            make_fixture(),
            "feed_type_classifier",
            mode=ValidationMode.TRAINING_DATA,
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_missing_target_fails_training_mode(self) -> None:
        fixture = make_fixture().drop(columns=["feed_type"])

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.TRAINING_DATA,
        )

        self.assertFalse(result.valid)
        self.assertIn("feed_type", result.missing_required_fields)

    def test_target_is_not_required_in_inference_mode(self) -> None:
        fixture = pd.DataFrame(
            {
                "breed": ["Jersey"],
                "age_months": [48],
                "weight_kg": [400],
                "lactation_stage": ["Mid"],
            }
        )

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.INFERENCE_INPUT,
        )

        self.assertTrue(result.valid)
        self.assertNotIn("feed_type", result.missing_required_fields)

    def test_duplicate_canonical_columns_fail(self) -> None:
        fixture = make_fixture()
        duplicate = pd.concat(
            [fixture, fixture[["breed"]].rename(columns={"breed": "age_months"})],
            axis=1,
        )

        result = validate_schema(
            duplicate,
            "feed_type_classifier",
            mode=ValidationMode.TEST_FIXTURE,
        )

        self.assertFalse(result.valid)
        self.assertTrue(
            any(
                issue.issue_type == "DUPLICATE_CANONICAL_COLUMNS"
                for issue in result.errors
            )
        )

    def test_invalid_numeric_value_is_reported(self) -> None:
        fixture = make_fixture()
        fixture["weight_kg"] = fixture["weight_kg"].astype(object)
        fixture.loc[0, "weight_kg"] = "invalid"

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.TEST_FIXTURE,
        )

        self.assertFalse(result.valid)
        self.assertTrue(
            any(
                issue.issue_type == "INVALID_NUMERIC_VALUE"
                for issue in result.errors
            )
        )

    def test_humidity_outside_zero_to_one_hundred_is_rejected(self) -> None:
        fixture = make_fixture()
        fixture.loc[0, "humidity_percent"] = 101

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.TEST_FIXTURE,
        )

        self.assertFalse(result.valid)
        self.assertTrue(
            any(
                issue.issue_type == "HARD_INVALID_HUMIDITY"
                for issue in result.errors
            )
        )

    def test_negative_age_is_rejected(self) -> None:
        fixture = make_fixture()
        fixture.loc[0, "age_months"] = -1

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.TEST_FIXTURE,
        )

        self.assertFalse(result.valid)
        self.assertTrue(
            any(
                issue.issue_type == "HARD_INVALID_NEGATIVE"
                for issue in result.errors
            )
        )

    def test_unknown_breed_and_dry_stage_generate_warnings(self) -> None:
        fixture = make_fixture()
        fixture.loc[0, "breed"] = "Future_Breed"
        fixture.loc[1, "lactation_stage"] = "Dry"

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.TEST_FIXTURE,
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.unknown_categories["breed"], ["Future_Breed"])
        self.assertEqual(result.unknown_categories["lactation_stage"], ["Dry"])

    def test_extra_field_is_reported_but_does_not_become_a_feature(self) -> None:
        result = validate_schema(
            make_fixture(),
            "feed_type_classifier",
            mode=ValidationMode.TEST_FIXTURE,
        )

        self.assertIn("unapproved_extra", result.unexpected_fields)
        self.assertTrue(result.valid)

    def test_inference_target_field_is_rejected_as_leakage(self) -> None:
        fixture = pd.DataFrame(
            {
                "breed": ["Jersey"],
                "age_months": [48],
                "weight_kg": [400],
                "lactation_stage": ["Mid"],
                "feed_type": ["Silage"],
            }
        )

        result = validate_schema(
            fixture,
            "feed_type_classifier",
            mode=ValidationMode.INFERENCE_INPUT,
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.leakage_fields, ["feed_type"])


if __name__ == "__main__":
    unittest.main()
