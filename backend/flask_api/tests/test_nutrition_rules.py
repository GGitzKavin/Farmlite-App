"""Checks for the future feed-prediction validation boundary."""

import unittest

from ml.validation.nutrition_rules import find_missing_prediction_fields


class NutritionRuleTests(unittest.TestCase):
    def test_complete_prediction_has_no_missing_fields(self) -> None:
        prediction = {
            "total_feed_kg": 14.0,
            "dry_matter_intake_kg": 12.0,
            "concentrate_kg": 5.0,
            "roughage_kg": 9.0,
            "crude_protein_requirement": 2.1,
            "energy_requirement": 120.0,
        }

        self.assertEqual(find_missing_prediction_fields(prediction), [])

    def test_missing_values_are_reported(self) -> None:
        missing = find_missing_prediction_fields({"total_feed_kg": 14.0})

        self.assertIn("dry_matter_intake_kg", missing)
        self.assertIn("energy_requirement", missing)


if __name__ == "__main__":
    unittest.main()
