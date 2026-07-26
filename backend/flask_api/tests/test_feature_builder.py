"""Focused tests for exact model-specific logical feature views."""

from __future__ import annotations

import unittest

from ml.preprocessing.feature_builder import (
    ModelContractError,
    build_features,
)
from tests.preprocessing_fixtures import BASE_FEATURES, make_fixture


class FeatureBuilderTests(unittest.TestCase):
    def test_model_one_returns_exact_approved_feature_order(self) -> None:
        result = build_features(make_fixture(), "feed_type_classifier")

        self.assertEqual(result.feature_names, BASE_FEATURES)
        self.assertEqual(result.X.columns.tolist(), BASE_FEATURES)

    def test_model_one_excludes_feed_type_from_x(self) -> None:
        result = build_features(make_fixture(), "feed_type_classifier")

        self.assertNotIn("feed_type", result.X.columns)
        self.assertEqual(result.target_name, "feed_type")

    def test_design_a_excludes_feed_quantity_target(self) -> None:
        result = build_features(
            make_fixture(), "feed_quantity_regressor_design_a"
        )

        self.assertNotIn("feed_quantity_kg", result.X.columns)
        self.assertEqual(result.target_name, "feed_quantity_kg")

    def test_design_b_refuses_true_feed_type_substitution(self) -> None:
        with self.assertRaisesRegex(
            ModelContractError, "True same-row feed_type"
        ):
            build_features(
                make_fixture(),
                "feed_quantity_regressor_design_b",
                allow_predicted_feature=True,
            )

    def test_design_b_accepts_explicit_predicted_feed_type(self) -> None:
        fixture = make_fixture()
        fixture["predicted_feed_type"] = "Silage"

        result = build_features(
            fixture,
            "feed_quantity_regressor_design_b",
            allow_predicted_feature=True,
        )

        self.assertEqual(
            result.feature_names, [*BASE_FEATURES, "predicted_feed_type"]
        )
        self.assertNotIn("feed_type", result.X.columns)

    def test_model_three_excludes_current_milk_target(self) -> None:
        result = build_features(make_fixture(), "milk_yield_regressor")

        self.assertNotIn("milk_yield_l", result.X.columns)
        self.assertIn("previous_week_avg_yield_l", result.X.columns)

    def test_identifiers_and_dates_are_excluded(self) -> None:
        result = build_features(make_fixture(), "feed_type_classifier")

        self.assertNotIn("cattle_id", result.X.columns)
        self.assertNotIn("observation_date", result.X.columns)

    def test_same_record_outcomes_are_excluded(self) -> None:
        result = build_features(make_fixture(), "feed_type_classifier")

        self.assertNotIn("feed_quantity_kg", result.X.columns)
        self.assertNotIn("milk_yield_l", result.X.columns)
        reasons = {item["field"]: item["reason"] for item in result.excluded_fields}
        self.assertEqual(
            reasons["feed_quantity_kg"], "SAME_RECORD_TARGET_OR_OUTCOME"
        )

    def test_missing_required_feature_raises_clear_error(self) -> None:
        fixture = make_fixture().drop(columns=["weight_kg"])

        with self.assertRaisesRegex(ModelContractError, "weight_kg"):
            build_features(fixture, "feed_type_classifier")

    def test_inference_build_supports_y_none(self) -> None:
        fixture = make_fixture().drop(columns=["feed_type"])

        result = build_features(
            fixture,
            "feed_type_classifier",
            include_target=False,
        )

        self.assertIsNone(result.y)
        self.assertEqual(result.X.columns.tolist(), BASE_FEATURES)

    def test_inference_build_adds_absent_optional_values_as_missing(self) -> None:
        fixture = make_fixture(1)[
            ["breed", "age_months", "weight_kg", "lactation_stage"]
        ]

        result = build_features(
            fixture,
            "feed_type_classifier",
            include_target=False,
        )

        self.assertEqual(result.X.columns.tolist(), BASE_FEATURES)
        self.assertTrue(result.X["days_in_milk"].isna().all())


if __name__ == "__main__":
    unittest.main()
