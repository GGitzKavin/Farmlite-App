"""Focused Phase 4.5A tests for the read-only Rwanda dataset audit."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from config.settings import FLASK_API_DIR
from ml.data_integration.office_reader import read_docx, read_xlsx
from ml.data_integration.rwanda_audit import (
    BUCKET_FILENAME,
    COW_FILENAME,
    EXPECTED_FILENAMES,
    EXPECTED_SHA256,
    FODDER_FILENAME,
    METADATA_FILENAME,
    REPORT_DIR,
    SOURCE_DIR,
    analyze_join,
    classify_feed_label,
    classify_measurement_status,
    classify_target,
    dataframe_from_sheet,
    detect_repeated_cows,
    detect_target_fields,
    discover_rwanda_files,
    extract_unit_period,
    farmlite_compatibility,
    missing_value_report,
    numeric_summary,
    parse_metadata_definitions,
    sha256_file,
)
from ml.data_integration.validate_rwanda_dataset import (
    INVENTORY_PATH,
    TARGET_MATRIX_PATH,
    _protected_snapshot,
    run_audit,
)


class RwandaDatasetAuditTests(unittest.TestCase):
    """Exercise each required audit and safety invariant."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.files = discover_rwanda_files()
        cls.raw_before = {
            name: sha256_file(path) for name, path in cls.files.items()
        }
        cls.protected_before = _protected_snapshot()
        cls.result = run_audit()
        cls.raw_after = {
            name: sha256_file(path) for name, path in cls.files.items()
        }
        cls.protected_after = _protected_snapshot()

        # Load each real source once for all focused tests.
        cls.metadata_workbook = read_xlsx(cls.files[METADATA_FILENAME])
        cls.cow_workbook = read_xlsx(cls.files[COW_FILENAME])
        cls.fodder_workbook = read_xlsx(cls.files[FODDER_FILENAME])
        cls.bucket_document = read_docx(cls.files[BUCKET_FILENAME])
        cls.definitions = parse_metadata_definitions(cls.metadata_workbook)
        cls.cow_frame = dataframe_from_sheet(
            cls.cow_workbook.sheets[0],
            header_row=11,
        )
        cls.fodder_frame = dataframe_from_sheet(
            next(
                sheet
                for sheet in cls.fodder_workbook.sheets
                if sheet.name == "Composites feeds"
            ),
            header_row=11,
        )
        cls.cow_profiles = {
            column: {
                "missing_percentage": (
                    100.0
                    * cls.cow_frame[column].isna().sum()
                    / len(cls.cow_frame)
                )
            }
            for column in cls.cow_frame.columns
            if column != "source_row_number"
        }
        cls.inventory = json.loads(
            INVENTORY_PATH.read_text(encoding="utf-8")
        )

    @staticmethod
    def _write_hidden_xlsx(path: Path) -> None:
        workbook_xml = """<?xml version="1.0" encoding="UTF-8"?>
<workbook
 xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets>
  <sheet name="HiddenData" sheetId="1" state="hidden" r:id="rId1"/>
 </sheets>
</workbook>
"""
        relationships_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships
 xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship
  Id="rId1"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
  Target="worksheets/sheet1.xml"/>
</Relationships>
"""
        sheet_xml = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet
 xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <dimension ref="A1"/>
 <sheetData>
  <row r="1">
   <c r="A1" t="inlineStr"><is><t>fixture</t></is></c>
  </row>
 </sheetData>
</worksheet>
"""
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("xl/workbook.xml", workbook_xml)
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                relationships_xml,
            )
            archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    def test_01_rwanda_directory_discovery(self) -> None:
        self.assertTrue(SOURCE_DIR.is_dir())
        self.assertEqual(discover_rwanda_files(), self.files)

    def test_02_all_four_expected_files_detected(self) -> None:
        self.assertEqual(list(self.files), EXPECTED_FILENAMES)
        self.assertEqual(len(self.files), 4)

    def test_03_sha256_checksum_recording(self) -> None:
        recorded = {
            item["filename"]: item["sha256"]
            for item in self.inventory["files"]
        }
        self.assertEqual(recorded, EXPECTED_SHA256)
        self.assertTrue(all(len(value) == 64 for value in recorded.values()))

    def test_04_excel_sheet_inventory(self) -> None:
        self.assertEqual(
            [sheet.name for sheet in self.metadata_workbook.sheets],
            ["Metadata"],
        )
        self.assertEqual(
            [sheet.name for sheet in self.cow_workbook.sheets],
            ["Raw data"],
        )
        self.assertEqual(
            [sheet.name for sheet in self.fodder_workbook.sheets],
            ["Composites feeds", "Sheet2"],
        )

    def test_05_hidden_sheet_detection(self) -> None:
        with tempfile.TemporaryDirectory(dir=FLASK_API_DIR) as directory:
            fixture = Path(directory) / "hidden.xlsx"
            self._write_hidden_xlsx(fixture)
            workbook = read_xlsx(fixture)
        self.assertEqual(workbook.sheets[0].state, "hidden")
        self.assertTrue(
            any(sheet.state != "visible" for sheet in workbook.sheets)
        )

    def test_06_docx_table_extraction(self) -> None:
        self.assertEqual(len(self.bucket_document.tables), 1)
        self.assertEqual(len(self.bucket_document.tables[0]), 11)
        self.assertEqual(
            self.bucket_document.tables[0][0],
            ["Age", "Milk consumption/day", "Milk production/day"],
        )

    def test_07_metadata_variable_parsing(self) -> None:
        self.assertEqual(len(self.definitions), 48)
        names = {item.source_variable_name for item in self.definitions}
        self.assertIn("Bodyweight", names)
        self.assertIn("DMIcapacity (kgDM)", names)
        self.assertIn("Milk consumption/day", names)

    def test_08_numeric_summary_generation(self) -> None:
        summary = numeric_summary([-1, 0, 1, None, "not numeric"])
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["minimum"], -1)
        self.assertEqual(summary["maximum"], 1)
        self.assertEqual(summary["mean"], 0)
        self.assertEqual(summary["zero_count"], 1)
        self.assertEqual(summary["negative_count"], 1)

    def test_09_missing_value_reporting(self) -> None:
        fixture = pd.DataFrame({"a": [1, None], "b": ["", "value"]})
        report = {
            row["column"]: row for row in missing_value_report(fixture)
        }
        self.assertEqual(report["a"]["missing_count"], 1)
        self.assertEqual(report["b"]["missing_count"], 1)
        self.assertEqual(report["a"]["missing_percentage"], 50.0)

    def test_10_repeated_cow_detection(self) -> None:
        fixture = pd.DataFrame({"cow_id": ["A", "A", "B"]})
        result = detect_repeated_cows(fixture, "cow_id")
        self.assertEqual(result["status"], "REPEATED")
        self.assertEqual(result["unique_cows"], 2)
        self.assertEqual(result["repeated_cow_count"], 1)
        self.assertEqual(result["maximum_records_per_cow"], 2)

    def test_11_target_classification(self) -> None:
        milk = classify_target("hand-milked yield")
        self.assertEqual(milk["domain"], "milk")
        self.assertEqual(milk["status"], "VERIFIED_MILK_YIELD_L_DAY")
        self.assertEqual(classify_target("unknown")["status"], "UNCLEAR")

    def test_12_measurement_status_classification(self) -> None:
        self.assertEqual(
            classify_measurement_status("Bodyweight", ""),
            "DIRECTLY_MEASURED",
        )
        self.assertEqual(
            classify_measurement_status("waterday", ""),
            "OWNER_REPORTED",
        )
        self.assertEqual(
            classify_measurement_status("MEIntake", ""),
            "CALCULATED",
        )

    def test_13_unit_extraction(self) -> None:
        self.assertEqual(
            extract_unit_period("hand-milked yield", ""),
            ("L/cow/day", "per cow per day"),
        )
        self.assertEqual(
            extract_unit_period("NDF feeds", "")[0],
            "UNCLEAR",
        )

    def test_14_dmi_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "dmi")
        by_name = {item["source_variable_name"]: item for item in fields}
        self.assertIn("DM served", by_name)
        self.assertIn("leftover", by_name)
        self.assertEqual(
            by_name["DMIcapacity (kgDM)"]["status"],
            "CALCULATED_DMI",
        )

    def test_15_milk_yield_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "milk")
        statuses = {
            item["source_variable_name"]: item["status"]
            for item in fields
        }
        self.assertEqual(
            statuses["hand-milked yield"],
            "VERIFIED_MILK_YIELD_L_DAY",
        )
        self.assertIn("Total milk performance", statuses)

    def test_16_water_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "water")
        statuses = {
            item["source_variable_name"]: item["status"]
            for item in fields
        }
        self.assertEqual(
            statuses["waterday"],
            "VERIFIED_WATER_INTAKE_L_COW_DAY",
        )
        self.assertEqual(
            statuses["waterrequi."],
            "VERIFIED_WATER_REQUIREMENT",
        )

    def test_17_protein_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "protein")
        statuses = {
            item["source_variable_name"]: item["status"]
            for item in fields
        }
        self.assertEqual(
            statuses["Cpintakeingr"],
            "VERIFIED_CP_INTAKE_G_DAY",
        )
        self.assertEqual(
            statuses["TotalreqCP"],
            "VERIFIED_CP_REQUIREMENT_G_DAY",
        )

    def test_18_energy_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "energy")
        statuses = {
            item["source_variable_name"]: item["status"]
            for item in fields
        }
        self.assertEqual(
            statuses["MEIntake"],
            "VERIFIED_ME_INTAKE_MJ_DAY",
        )
        self.assertEqual(
            statuses["MEmaint+peakmilk"],
            "VERIFIED_ME_REQUIREMENT_MJ_DAY",
        )

    def test_19_feed_category_label_classification(self) -> None:
        observed = classify_feed_label(
            "SAMPLE ID",
            "Different fodder ingredients served to a selected cow",
        )
        bucket = classify_feed_label(
            "feeding program",
            "Bucket feeding program followed by farmers",
        )
        self.assertEqual(observed, "OBSERVED_DIET_ONLY")
        self.assertEqual(bucket, "VERIFIED_OBSERVED_PRACTICE")

    def test_20_join_key_analysis(self) -> None:
        result = analyze_join(
            self.cow_frame,
            self.fodder_frame,
            left_key="LabN°",
            right_key="Lab N°",
        )
        self.assertEqual(result["matched_left_row_count"], 96)
        self.assertEqual(result["left_match_percentage"], 100.0)
        self.assertEqual(
            result["join_safety"],
            "POSSIBLE_WITH_LIMITATIONS",
        )
        self.assertFalse(result["many_to_many_risk"])

    def test_21_many_to_many_join_detection(self) -> None:
        left = pd.DataFrame({"key": ["A", "A"]})
        right = pd.DataFrame({"key": ["A", "A"]})
        result = analyze_join(
            left,
            right,
            left_key="key",
            right_key="key",
        )
        self.assertTrue(result["many_to_many_risk"])
        self.assertEqual(result["join_safety"], "MANY_TO_MANY_RISK")

    def test_22_farmlite_feature_compatibility(self) -> None:
        rows = farmlite_compatibility(self.cow_profiles)
        current = {row["farmlite_feature"]: row for row in rows[:9]}
        self.assertEqual(len(current), 9)
        self.assertEqual(current["weight_kg"]["available_in_rwanda"], "YES")
        self.assertEqual(
            current["body_condition_score"]["available_in_rwanda"],
            "NO",
        )
        self.assertEqual(len(rows), 15)

    def test_23_raw_files_unchanged(self) -> None:
        self.assertEqual(self.raw_before, self.raw_after)
        self.assertEqual(self.raw_after, EXPECTED_SHA256)
        self.assertTrue(self.result["raw_files_unchanged"])

    def test_24_existing_models_unchanged(self) -> None:
        for key in ("retained_model", "phase4_candidates"):
            self.assertEqual(
                self.protected_before[key],
                self.protected_after[key],
            )
        self.assertTrue(self.result["protected_files_unchanged"])

    def test_25_flask_routes_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["routes"],
            self.protected_after["routes"],
        )

    def test_26_frontend_files_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["frontend_tree"],
            self.protected_after["frontend_tree"],
        )

    def test_27_no_model_training_occurred(self) -> None:
        self.assertFalse(self.result["model_training_occurred"])
        self.assertFalse(self.result["prediction_occurred"])

    def test_28_no_processed_dataset_generated(self) -> None:
        self.assertFalse(self.result["processed_dataset_generated"])
        self.assertEqual(
            self.protected_before["processed_files"],
            self.protected_after["processed_files"],
        )

    def test_29_no_unsupported_unit_conversion_occurred(self) -> None:
        self.assertFalse(
            self.result["unsupported_unit_conversion_occurred"]
        )
        self.assertEqual(extract_unit_period("unsupported", ""), ("UNCLEAR", "UNCLEAR"))

    def test_30_no_fake_recommendation_labels_created(self) -> None:
        self.assertFalse(
            self.result["fake_recommendation_label_created"]
        )
        matrix = pd.read_csv(TARGET_MATRIX_PATH)
        feed_row = matrix.loc[
            matrix["desired_farmlite_output"] == "Feed/ration category"
        ].iloc[0]
        self.assertEqual(feed_row["decision"], "EXPERT_LABELS_REQUIRED")


if __name__ == "__main__":
    unittest.main()
