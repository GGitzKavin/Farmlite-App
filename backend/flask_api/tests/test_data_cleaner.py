"""Focused tests for transparent value cleaning and issue metadata."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ml.preprocessing.data_cleaner import clean_data
from tests.preprocessing_fixtures import make_fixture


class DataCleanerTests(unittest.TestCase):
    def test_whitespace_and_approved_case_are_normalized(self) -> None:
        fixture = make_fixture(8)
        fixture.loc[0, "breed"] = " jersey "
        fixture.loc[1, "lactation_stage"] = "mid lactation"

        result = clean_data(fixture)

        self.assertEqual(result.dataframe.loc[0, "breed"], "Jersey")
        self.assertEqual(result.dataframe.loc[1, "lactation_stage"], "Mid")
        self.assertIn("NORMALIZED", result.issues["action"].tolist())

    def test_dry_is_preserved_and_reported_unknown(self) -> None:
        fixture = make_fixture(8)
        fixture.loc[0, "lactation_stage"] = "Dry"

        result = clean_data(fixture)

        self.assertEqual(result.dataframe.loc[0, "lactation_stage"], "Dry")
        issue = result.issues.loc[
            result.issues["field"] == "lactation_stage"
        ].iloc[0]
        self.assertEqual(issue["issue_type"], "UNKNOWN_CATEGORY")
        self.assertEqual(issue["action"], "PRESERVED")

    def test_empty_category_becomes_missing_without_row_deletion(self) -> None:
        fixture = make_fixture(8)
        fixture.loc[0, "breed"] = "   "

        result = clean_data(fixture)

        self.assertTrue(pd.isna(result.dataframe.loc[0, "breed"]))
        self.assertEqual(len(result.dataframe), len(fixture))
        self.assertEqual(result.metadata["rows_dropped"], 0)

    def test_invalid_and_infinite_numbers_are_flagged_and_set_missing(self) -> None:
        fixture = make_fixture(8)
        fixture["weight_kg"] = fixture["weight_kg"].astype(object)
        fixture.loc[0, "weight_kg"] = "not-a-number"
        fixture.loc[1, "weight_kg"] = np.inf

        result = clean_data(fixture)

        self.assertTrue(pd.isna(result.dataframe.loc[0, "weight_kg"]))
        self.assertTrue(pd.isna(result.dataframe.loc[1, "weight_kg"]))
        self.assertEqual(
            set(result.issues["issue_type"]),
            {"INVALID_NUMERIC_VALUE", "NON_FINITE_NUMERIC_VALUE"},
        )

    def test_original_row_order_and_identity_are_preserved(self) -> None:
        fixture = make_fixture(8).iloc[[4, 2, 7]].copy()

        result = clean_data(fixture)

        self.assertTrue(result.dataframe.index.equals(fixture.index))
        self.assertTrue(result.metadata["row_order_preserved"])


if __name__ == "__main__":
    unittest.main()
