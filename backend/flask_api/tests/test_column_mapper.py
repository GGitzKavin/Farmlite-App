"""Focused tests for approved canonical column mapping."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ml.preprocessing.column_mapper import (
    AliasConfigurationError,
    ColumnMappingError,
    map_api_fields,
    map_columns,
    map_dataset_columns,
)


class ColumnMapperTests(unittest.TestCase):
    def test_dataset_columns_map_to_canonical_fields(self) -> None:
        source = pd.DataFrame(
            {"Breed": ["Jersey"], "Age_Months": [48], "Weight_kg": [400]}
        )

        result = map_dataset_columns(source)

        self.assertEqual(
            result.dataframe.columns.tolist(),
            ["breed", "age_months", "weight_kg"],
        )
        self.assertEqual(result.dataframe.iloc[0]["breed"], "Jersey")

    def test_known_api_aliases_map_separately(self) -> None:
        source = pd.DataFrame(
            {
                "animalId": ["A-1"],
                "ageMonths": [48],
                "weightKg": [400],
                "lactationStage": ["Mid"],
            }
        )

        result = map_api_fields(source)

        self.assertEqual(
            result.dataframe.columns.tolist(),
            ["cattle_id", "age_months", "weight_kg", "lactation_stage"],
        )
        self.assertEqual(result.metadata.operation, "API")

    def test_ambiguous_alias_configuration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aliases.json"
            path.write_text(
                json.dumps({"first": ["duplicate"], "second": ["DUPLICATE"]}),
                encoding="utf-8",
            )

            with self.assertRaises(AliasConfigurationError):
                map_columns(
                    pd.DataFrame({"duplicate": [1]}),
                    operation="DATASET",
                    aliases_path=path,
                )

    def test_two_sources_mapping_to_one_canonical_field_are_rejected(self) -> None:
        source = pd.DataFrame([["Jersey", "Ayrshire"]], columns=["Breed", "breed"])

        with self.assertRaisesRegex(ColumnMappingError, "both map"):
            map_dataset_columns(source)

    def test_missing_required_columns_are_reported(self) -> None:
        result = map_dataset_columns(
            pd.DataFrame({"Breed": ["Jersey"]}),
            required_columns=["breed", "weight_kg"],
        )

        self.assertEqual(result.metadata.missing_required_columns, ["weight_kg"])

    def test_unmapped_fields_are_preserved_and_reported(self) -> None:
        source = pd.DataFrame({"Breed": ["Jersey"], "Region": ["Asia"]})

        result = map_dataset_columns(source)

        self.assertIn("Region", result.dataframe.columns)
        self.assertEqual(result.metadata.unmapped_columns, ["Region"])


if __name__ == "__main__":
    unittest.main()
