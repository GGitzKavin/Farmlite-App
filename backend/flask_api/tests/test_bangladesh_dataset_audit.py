"""Focused Phase 4.5C tests for the Bangladesh audit-only workflow."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from config.settings import FLASK_API_DIR
from ml.data_integration.bangladesh_audit import (
    BLOOD_FILENAME,
    DMI_FILENAME,
    EXPECTED_FILENAMES,
    EXPECTED_SHA256,
    METADATA_FILENAME,
    PHYSIOLOGY_FILENAME,
    SOURCE_DIR,
    analyze_join,
    classify_leakage,
    dataframe_from_sheet,
    detect_repeated_observations,
    detect_target_fields,
    discover_bangladesh_files,
    duplicate_row_count,
    farmlite_compatibility,
    missing_value_report,
    parse_metadata_document,
    sha256_file,
)
from ml.data_integration.office_reader import read_docx, read_xlsx
from ml.data_integration.validate_bangladesh_dataset import (
    GROUPING_PATH,
    INVENTORY_PATH,
    TARGET_MATRIX_PATH,
    _protected_snapshot,
    run_audit,
)


class BangladeshDatasetAuditTests(unittest.TestCase):
    """Exercise the 32 required audit and safety behaviors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.files = discover_bangladesh_files()
        cls.raw_before = {
            name: sha256_file(path) for name, path in cls.files.items()
        }
        cls.protected_before = _protected_snapshot()
        cls.result = run_audit()
        cls.raw_after = {
            name: sha256_file(path) for name, path in cls.files.items()
        }
        cls.protected_after = _protected_snapshot()

        # Load each real source once for the focused tests.
        cls.document = read_docx(cls.files[METADATA_FILENAME])
        cls.dmi_workbook = read_xlsx(cls.files[DMI_FILENAME])
        cls.physiology_workbook = read_xlsx(
            cls.files[PHYSIOLOGY_FILENAME]
        )
        cls.blood_workbook = read_xlsx(cls.files[BLOOD_FILENAME])
        cls.dmi_frame = dataframe_from_sheet(cls.dmi_workbook.sheets[0])
        cls.physiology_frame = dataframe_from_sheet(
            cls.physiology_workbook.sheets[0]
        )
        cls.blood_frame = dataframe_from_sheet(cls.blood_workbook.sheets[0])
        cls.frames = {
            DMI_FILENAME: cls.dmi_frame,
            PHYSIOLOGY_FILENAME: cls.physiology_frame,
            BLOOD_FILENAME: cls.blood_frame,
        }
        cls.metadata = parse_metadata_document(cls.document)
        cls.definitions = cls.metadata["definitions"]
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
                "xl/_rels/workbook.xml.rels", relationships_xml
            )
            archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)

    def test_01_bangladesh_directory_discovery(self) -> None:
        self.assertTrue(SOURCE_DIR.is_dir())
        self.assertEqual(discover_bangladesh_files(), self.files)

    def test_02_all_four_files_detected(self) -> None:
        self.assertEqual(list(self.files), EXPECTED_FILENAMES)
        self.assertEqual(len(self.files), 4)

    def test_03_raw_checksums_recorded(self) -> None:
        recorded = {
            item["filename"]: item["sha256"]
            for item in self.inventory["files"]
        }
        self.assertEqual(recorded, EXPECTED_SHA256)
        self.assertTrue(all(len(value) == 64 for value in recorded.values()))

    def test_04_docx_metadata_extraction(self) -> None:
        self.assertEqual(len(self.document.paragraphs), 46)
        self.assertEqual(len(self.document.tables), 0)
        self.assertEqual(len(self.definitions), 33)
        self.assertIn("Cyclic THI", self.metadata["title"])

    def test_05_excel_sheet_inventory(self) -> None:
        for workbook in (
            self.dmi_workbook,
            self.physiology_workbook,
            self.blood_workbook,
        ):
            self.assertEqual([sheet.name for sheet in workbook.sheets], ["Sheet1"])
            self.assertEqual(workbook.sheets[0].state, "visible")

    def test_06_hidden_sheet_detection(self) -> None:
        with tempfile.TemporaryDirectory(dir=FLASK_API_DIR) as directory:
            fixture = Path(directory) / "hidden.xlsx"
            self._write_hidden_xlsx(fixture)
            workbook = read_xlsx(fixture)
        self.assertEqual(workbook.sheets[0].state, "hidden")

    def test_07_cow_identifier_detection(self) -> None:
        for frame in self.frames.values():
            self.assertIn("Animal ID", frame)
            self.assertEqual(
                frame["Animal ID"].astype(str).str.strip().nunique(), 50
            )
            self.assertEqual(frame["Animal ID"].isna().sum(), 0)

    def test_08_repeated_observation_detection(self) -> None:
        result = detect_repeated_observations(self.dmi_frame)
        self.assertEqual(result["status"], "REPEATED")
        self.assertEqual(result["unique_cows"], 50)
        self.assertEqual(result["minimum_records_per_cow"], 15)
        self.assertEqual(result["maximum_records_per_cow"], 15)

    def test_09_dmi_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "dmi")
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]["exact_source_column"], "DMI (kg)")
        self.assertEqual(
            self.result["dmi_audit"]["status"],
            "VERIFIED_DMI_KG_COW_DAY",
        )

    def test_10_milk_yield_field_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "milk_yield")
        self.assertEqual(len(fields), 1)
        self.assertEqual(
            fields[0]["exact_source_column"],
            "Milk Yield (L/day/cow)",
        )
        self.assertEqual(
            self.result["milk_audit"]["status"],
            "VERIFIED_MILK_YIELD_L_COW_DAY",
        )

    def test_11_milk_composition_detection(self) -> None:
        columns = {
            item["exact_source_column"]
            for item in detect_target_fields(
                self.definitions, "milk_composition"
            )
        }
        self.assertTrue(
            {"Fat%", "SNF%", "Protein %", "Lactose%", "SCC cells per mL"}
            <= columns
        )

    def test_12_temperature_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "temperature")
        self.assertEqual(
            [item["exact_source_column"] for item in fields],
            ["Rectal Temp (F)"],
        )
        self.assertNotIn("Ambient Temperature", self.physiology_frame)

    def test_13_humidity_detection(self) -> None:
        self.assertEqual(
            detect_target_fields(self.definitions, "humidity"), []
        )
        self.assertFalse(
            any("humidity" in column.casefold()
                for frame in self.frames.values() for column in frame.columns)
        )

    def test_14_thi_detection(self) -> None:
        fields = detect_target_fields(self.definitions, "thi")
        self.assertEqual(len(fields), 3)
        self.assertTrue(
            all(item["measurement_status"] == "TREATMENT_ASSIGNED"
                for item in fields)
        )

    def test_15_physiological_field_detection(self) -> None:
        columns = {
            item["exact_source_column"]
            for item in detect_target_fields(self.definitions, "physiology")
        }
        self.assertEqual(
            columns,
            {
                "Rectal Temp (F)",
                "Pulse Rate (bpm)",
                "Respiration Rate (bpm)",
            },
        )

    def test_16_blood_metabolite_detection(self) -> None:
        columns = {
            item["exact_source_column"]
            for item in detect_target_fields(self.definitions, "blood")
        }
        self.assertEqual(len(columns), 9)
        self.assertIn("Glucose (mmol/L)", columns)
        self.assertIn("Cortisol (µg/dL)", columns)

    def test_17_unit_extraction(self) -> None:
        by_source = {
            item["source_variable"]: item for item in self.definitions
        }
        self.assertEqual(
            by_source["Glucose_mmol_per_L"]["unit"], "mmol/L"
        )
        self.assertEqual(
            by_source["Dry_Matter_Intake_(DMI)_Kg_per_day"]["unit"], "kg"
        )
        self.assertEqual(
            by_source["Milk_Yield_L_per_day"]["measurement_period"],
            "per cow per day",
        )
        self.assertEqual(
            by_source["Respiration_Rate_bpm"]["unit"], "breaths/min"
        )

    def test_18_missing_value_reporting(self) -> None:
        fixture = pd.DataFrame({"a": [1, None], "b": ["", "value"]})
        rows = {item["column"]: item for item in missing_value_report(fixture)}
        self.assertEqual(rows["a"]["missing_count"], 1)
        self.assertEqual(rows["b"]["missing_count"], 1)
        self.assertEqual(rows["a"]["missing_percentage"], 50.0)
        self.assertTrue(
            all(
                item["missing_count"] == 0
                for item in missing_value_report(self.dmi_frame)
                if item["column"] != "source_row_number"
            )
        )

    def test_19_duplicate_row_detection(self) -> None:
        fixture = pd.DataFrame({"a": [1, 1], "b": ["x", "x"]})
        self.assertEqual(duplicate_row_count(fixture), 1)
        self.assertEqual(duplicate_row_count(self.dmi_frame), 0)

    def test_20_cross_workbook_join_analysis(self) -> None:
        dmi_blood = analyze_join(
            self.dmi_frame,
            self.blood_frame,
            DMI_FILENAME,
            BLOOD_FILENAME,
        )
        dmi_phys = analyze_join(
            self.dmi_frame,
            self.physiology_frame,
            DMI_FILENAME,
            PHYSIOLOGY_FILENAME,
        )
        self.assertEqual(dmi_blood["join_safety"], "SAFE_ONE_TO_ONE")
        self.assertEqual(dmi_blood["match_count"], 750)
        self.assertEqual(
            dmi_phys["join_safety"], "POSSIBLE_WITH_LIMITATIONS"
        )
        self.assertEqual(dmi_phys["match_count"], 675)

    def test_21_many_to_many_join_detection(self) -> None:
        left = pd.DataFrame(
            {
                "Animal ID": ["A", "A"],
                "THI Range": ["T0", "T0"],
                "Replication No": [1, 1],
            }
        )
        right = left.copy()
        result = analyze_join(left, right)
        self.assertTrue(result["many_to_many_risk"])
        self.assertEqual(result["join_safety"], "MANY_TO_MANY_RISK")

    def test_22_group_splitting_requirement(self) -> None:
        text = GROUPING_PATH.read_text(encoding="utf-8")
        self.assertIn("Never randomly split repeated cow records by row", text)
        self.assertIn("GroupKFold", text)
        self.assertIn("GroupShuffleSplit", text)

    def test_23_leakage_classification(self) -> None:
        self.assertEqual(classify_leakage("DMI", "Genetic Group"), "SAFE")
        self.assertEqual(
            classify_leakage("DMI", "Milk Yield"),
            "POSSIBLE_LEAKAGE",
        )
        self.assertEqual(
            classify_leakage("MILK", "Blood cortisol"), "RESEARCH_ONLY"
        )

    def test_24_farmlite_compatibility(self) -> None:
        rows = farmlite_compatibility(self.frames)
        current = {item["farmlite_feature"]: item for item in rows[:9]}
        self.assertEqual(len(current), 9)
        self.assertEqual(
            current["breed"]["present_in_bangladesh"], "PARTIAL"
        )
        self.assertEqual(
            current["weight_kg"]["present_in_bangladesh"], "NO"
        )
        self.assertEqual(len(rows), 15)

    def test_25_raw_files_unchanged(self) -> None:
        self.assertEqual(self.raw_before, self.raw_after)
        self.assertEqual(self.raw_after, EXPECTED_SHA256)
        self.assertTrue(self.result["raw_files_unchanged"])

    def test_26_existing_model_files_unchanged(self) -> None:
        for key in ("retained_model", "phase4_candidates"):
            self.assertEqual(
                self.protected_before[key],
                self.protected_after[key],
            )
        self.assertTrue(self.result["protected_files_unchanged"])

    def test_27_flask_routes_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["routes"],
            self.protected_after["routes"],
        )

    def test_28_frontend_files_unchanged(self) -> None:
        self.assertEqual(
            self.protected_before["frontend_tree"],
            self.protected_after["frontend_tree"],
        )

    def test_29_no_processed_dataset_created(self) -> None:
        self.assertFalse(self.result["processed_dataset_generated"])
        self.assertEqual(
            self.protected_before["processed_files"],
            self.protected_after["processed_files"],
        )

    def test_30_no_model_training_occurred(self) -> None:
        self.assertFalse(self.result["model_training_occurred"])
        self.assertFalse(self.result["model_evaluation_occurred"])
        self.assertFalse(self.result["prediction_occurred"])

    def test_31_no_source_concatenation_occurred(self) -> None:
        self.assertFalse(self.result["source_concatenation_occurred"])
        self.assertFalse(self.result["permanent_join_created"])

    def test_32_no_expert_feed_labels_invented(self) -> None:
        self.assertFalse(self.result["expert_feed_labels_invented"])
        matrix = pd.read_csv(TARGET_MATRIX_PATH)
        row = matrix.loc[
            matrix["desired_output"] == "Feed/ration category"
        ].iloc[0]
        self.assertEqual(row["decision"], "EXPERT_LABELS_REQUIRED")


if __name__ == "__main__":
    unittest.main()
