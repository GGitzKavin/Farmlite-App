"""Focused tests for the safe read-only dataset loader."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ml.preprocessing.data_loader import (
    EmptyDatasetError,
    MissingRequiredColumnsError,
    UnsupportedDatasetFormatError,
    load_dataset,
)


class DataLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_loads_valid_csv_and_records_metadata(self) -> None:
        source = self.directory / "valid.csv"
        source.write_text("Breed,Age_Months\nJersey,48\n", encoding="utf-8")

        result = load_dataset(source)

        self.assertEqual(result.dataframe.shape, (1, 2))
        self.assertEqual(result.metadata.row_count, 1)
        self.assertEqual(result.metadata.source_path, source.resolve())

    def test_missing_file_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "not found"):
            load_dataset(self.directory / "missing.csv")

    def test_unsupported_extension_is_rejected(self) -> None:
        source = self.directory / "data.json"
        source.write_text("[]", encoding="utf-8")

        with self.assertRaisesRegex(
            UnsupportedDatasetFormatError, "Unsupported dataset format"
        ):
            load_dataset(source)

    def test_empty_file_is_rejected(self) -> None:
        source = self.directory / "empty.csv"
        source.write_text("", encoding="utf-8")

        with self.assertRaises(EmptyDatasetError):
            load_dataset(source)

    def test_selected_columns_and_row_limit_work(self) -> None:
        source = self.directory / "selected.csv"
        source.write_text(
            "Breed,Age_Months,Weight_kg\nJersey,48,400\nAyrshire,60,450\n",
            encoding="utf-8",
        )

        result = load_dataset(
            source,
            selected_columns=["Breed", "Weight_kg"],
            row_limit=1,
        )

        self.assertEqual(result.dataframe.columns.tolist(), ["Breed", "Weight_kg"])
        self.assertEqual(len(result.dataframe), 1)

    def test_missing_required_columns_are_rejected(self) -> None:
        source = self.directory / "missing_column.csv"
        source.write_text("Breed\nJersey\n", encoding="utf-8")

        with self.assertRaisesRegex(
            MissingRequiredColumnsError, "missing required columns"
        ):
            load_dataset(source, required_columns=["Breed", "Age_Months"])


if __name__ == "__main__":
    unittest.main()
