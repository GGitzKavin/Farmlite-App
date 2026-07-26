"""Focused tests for unfitted sklearn preprocessing-only factories."""

from __future__ import annotations

import unittest

import numpy as np

from ml.preprocessing.feature_builder import build_features
from ml.preprocessing.preprocessing_factory import (
    build_linear_preprocessor,
    build_preprocessor,
    build_tree_preprocessor,
)
from tests.preprocessing_fixtures import make_fixture


class PreprocessingFactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = make_fixture(16)
        self.built = build_features(self.fixture, "feed_type_classifier")

    def test_factory_returns_unfitted_preprocessing_only_object(self) -> None:
        preprocessor = build_preprocessor("feed_type_classifier")

        self.assertFalse(hasattr(preprocessor, "transformers_"))
        self.assertFalse(any(name == "estimator" for name, _, _ in preprocessor.transformers))

    def test_numeric_missing_values_are_imputed(self) -> None:
        training = self.built.X.copy()
        training.loc[0, "days_in_milk"] = np.nan
        transformed = build_tree_preprocessor(
            "feed_type_classifier"
        ).fit_transform(training)

        dense = transformed.toarray() if hasattr(transformed, "toarray") else transformed
        self.assertFalse(np.isnan(dense).any())

    def test_categorical_missing_values_are_imputed(self) -> None:
        training = self.built.X.copy()
        training.loc[0, "breed"] = None
        transformed = build_tree_preprocessor(
            "feed_type_classifier"
        ).fit_transform(training)

        dense = transformed.toarray() if hasattr(transformed, "toarray") else transformed
        self.assertFalse(np.isnan(dense).any())

    def test_unknown_breed_transforms_without_crashing(self) -> None:
        preprocessor = build_tree_preprocessor("feed_type_classifier")
        preprocessor.fit(self.built.X)
        unseen = self.built.X.iloc[[0]].copy()
        unseen.loc[:, "breed"] = "Future_Breed"

        transformed = preprocessor.transform(unseen)

        self.assertEqual(transformed.shape[0], 1)

    def test_dry_stage_transforms_without_false_remapping(self) -> None:
        preprocessor = build_tree_preprocessor("feed_type_classifier")
        preprocessor.fit(self.built.X)
        unseen = self.built.X.iloc[[0]].copy()
        unseen.loc[:, "lactation_stage"] = "Dry"

        transformed = preprocessor.transform(unseen)
        encoder = preprocessor.named_transformers_[
            "categorical"
        ].named_steps["encoder"]

        self.assertEqual(transformed.shape[0], 1)
        self.assertNotIn("Dry", set(encoder.categories_[1]))

    def test_linear_preprocessor_applies_numeric_scaling(self) -> None:
        preprocessor = build_linear_preprocessor("feed_type_classifier")
        preprocessor.fit(self.built.X)

        self.assertIn(
            "scaler",
            preprocessor.named_transformers_["numeric"].named_steps,
        )

    def test_tree_preprocessor_does_not_scale_numeric_features(self) -> None:
        preprocessor = build_tree_preprocessor("feed_type_classifier")
        preprocessor.fit(self.built.X)

        self.assertNotIn(
            "scaler",
            preprocessor.named_transformers_["numeric"].named_steps,
        )

    def test_feature_output_order_is_stable(self) -> None:
        first = build_tree_preprocessor("feed_type_classifier")
        second = build_tree_preprocessor("feed_type_classifier")
        first.fit(self.built.X)
        second.fit(self.built.X)

        self.assertEqual(
            first.get_feature_names_out().tolist(),
            second.get_feature_names_out().tolist(),
        )

    def test_design_b_declares_predicted_feed_type_as_categorical(self) -> None:
        preprocessor = build_preprocessor("feed_quantity_regressor_design_b")
        categorical_columns = preprocessor.transformers[0][2]

        self.assertEqual(
            categorical_columns,
            ["breed", "lactation_stage", "predicted_feed_type"],
        )


if __name__ == "__main__":
    unittest.main()
