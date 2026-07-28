"""Focused Phase 4.5B clarification and protected-state tests."""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

import pandas as pd

from ml.data_integration.office_reader import read_xlsx
from ml.data_integration.rwanda_audit import (
    COW_FILENAME,
    EXPECTED_SHA256,
    SOURCE_DIR,
    dataframe_from_sheet,
    discover_rwanda_files,
    sha256_file,
)
from ml.data_integration.rwanda_formula_audit import (
    FORMULA_DEFINITIONS,
    age_column_analysis,
    audit_all_formulas,
    negative_leftover_analysis,
)
from config.settings import PROJECT_ROOT
from ml.data_integration.validate_rwanda_clarification import (
    AUTHOR_QUESTIONS_PATH,
    IDENTIFIER_PATH,
    NUTRIENT_PATH,
    OPTION_B_PATH,
    SYNTHETIC_SOURCE_HASHES,
    TARGET_REPAIR_PATH,
    TRAINING_GATE_PATH,
    WATER_PATH,
    _load_prior_reports,
    run_clarification,
)
from ml.data_integration.validate_rwanda_dataset import _protected_snapshot


class RwandaClarificationTests(unittest.TestCase):
    """Load source data once and cover all 27 requested invariants."""

    @classmethod
    def setUpClass(cls) -> None:
        missing = [
            relative
            for relative in SYNTHETIC_SOURCE_HASHES
            if not (PROJECT_ROOT / relative).exists()
        ]
        if missing:
            raise unittest.SkipTest(
                "Raw synthetic dataset CSVs are gitignored local files and "
                f"are not present in this checkout: {missing}"
            )
        cls.files = discover_rwanda_files()
        cls.raw_before = {
            name: sha256_file(path) for name, path in cls.files.items()
        }
        cls.protected_before = _protected_snapshot()
        cls.result = run_clarification()
        cls.raw_after = {
            name: sha256_file(path) for name, path in cls.files.items()
        }
        cls.protected_after = _protected_snapshot()
        cls.prior = _load_prior_reports()

        workbook = read_xlsx(cls.files[COW_FILENAME])
        cls.frame = dataframe_from_sheet(workbook.sheets[0], header_row=11)
        cls.original_age = cls.frame["cowageinyears"].copy(deep=True)
        cls.original_leftover = cls.frame["leftover"].copy(deep=True)
        cls.formulas = audit_all_formulas(cls.frame)
        cls.formulas_by_id = {
            item["formula_id"]: item for item in cls.formulas
        }
        cls.negative = negative_leftover_analysis(cls.frame)
        cls.age = age_column_analysis(cls.frame)
        cls.repair = pd.read_csv(TARGET_REPAIR_PATH)
        cls.gate_text = TRAINING_GATE_PATH.read_text(encoding="utf-8")

    def test_01_prior_audit_reports_load(self) -> None:
        self.assertTrue(self.result["prior_reports_loaded"])
        self.assertEqual(self.prior["inventory"]["expected_file_count"], 4)
        self.assertGreaterEqual(len(self.prior["csv_shapes"]), 4)

    def test_02_rwanda_source_checksums_remain_unchanged(self) -> None:
        self.assertEqual(self.raw_before, EXPECTED_SHA256)
        self.assertEqual(self.raw_after, EXPECTED_SHA256)

    def test_03_formula_definitions_are_parsed(self) -> None:
        self.assertEqual(len(FORMULA_DEFINITIONS), 31)
        self.assertEqual(len(self.formulas), 31)
        self.assertTrue(
            all(item["documented_formula"] for item in self.formulas)
        )

    def test_04_missing_formula_inputs_are_reported(self) -> None:
        mefeeds = self.formulas_by_id["RW-FORM-ME-001"]
        self.assertEqual(
            mefeeds["status"],
            "NOT_REPRODUCIBLE_MISSING_INPUT",
        )
        self.assertIn("G24", mefeeds["missing_required_columns"])
        self.assertEqual(mefeeds["missing_input_row_count"], 96)

    def test_05_formula_mismatches_are_reported(self) -> None:
        water = self.formulas_by_id["RW-FORM-WATER-001"]
        cp_milk = self.formulas_by_id["RW-FORM-CP-004"]
        me_milk = self.formulas_by_id["RW-FORM-ME-004"]
        self.assertEqual(water["mismatch_count"], 23)
        self.assertEqual(cp_milk["mismatch_count"], 22)
        self.assertEqual(me_milk["mismatch_count"], 20)

    def test_06_negative_leftovers_remain_unchanged(self) -> None:
        self.assertEqual(self.negative["negative_row_count"], 28)
        pd.testing.assert_series_equal(
            self.frame["leftover"],
            self.original_leftover,
        )
        self.assertFalse(self.negative["source_values_modified"])

    def test_07_alternative_leftover_interpretations_remain_separate(self) -> None:
        self.assertEqual(
            [item["interpretation_id"] for item in self.negative["interpretations"]],
            ["A", "B", "C", "D", "E"],
        )
        self.assertTrue(
            all(not item["selected"] for item in self.negative["interpretations"])
        )
        self.assertIsNone(self.negative["selected_interpretation"])

    def test_08_age_contamination_is_detected(self) -> None:
        self.assertEqual(self.age["numeric_age_count"], 64)
        self.assertEqual(self.age["breed_text_count"], 30)
        self.assertEqual(self.age["missing_age_count"], 2)

    def test_09_age_values_are_not_automatically_repaired(self) -> None:
        self.assertFalse(self.age["deterministic_repair_possible"])
        self.assertFalse(self.age["values_modified"])
        pd.testing.assert_series_equal(
            self.frame["cowageinyears"],
            self.original_age,
        )

    def test_10_lab_sample_is_not_promoted_to_cow_id(self) -> None:
        text = IDENTIFIER_PATH.read_text(encoding="utf-8")
        self.assertIn("Composite feed/laboratory sample identifier", text)
        self.assertIn("Cow or farm identifier without written confirmation", text)
        self.assertNotIn('"cow_id": "LabN°"', text)

    def test_11_waterday_consumption_semantics_remain_unverified(self) -> None:
        text = WATER_PATH.read_text(encoding="utf-8")
        self.assertEqual(
            self.result["water_status"],
            "VERIFIED_WATER_PROVIDED_L_COW_DAY",
        )
        self.assertIn("Direct metering of drinking: `NOT_VERIFIED`", text)
        self.assertIn("water-consumption/intake regressor is not approved", text)

    def test_12_measured_and_calculated_milk_remain_separate(self) -> None:
        rows = self.repair.set_index("target")
        self.assertEqual(
            rows.loc["Measured daily milk", "current_status"],
            "VERIFIED_MEASURED_MILK_L_COW_DAY",
        )
        self.assertEqual(
            rows.loc["Total milk performance", "current_status"],
            "CALCULATED_TOTAL_MILK_L_COW_DAY",
        )

    def test_13_cp_intake_and_requirement_remain_separate(self) -> None:
        rows = self.repair.set_index("target")
        self.assertEqual(
            rows.loc["CP intake", "current_status"],
            "CALCULATED_INTAKE_DMI_DEPENDENT",
        )
        self.assertEqual(
            rows.loc["CP requirement", "current_status"],
            "MODEL_DERIVED_REQUIREMENT",
        )

    def test_14_me_intake_and_requirement_remain_separate(self) -> None:
        rows = self.repair.set_index("target")
        self.assertEqual(
            rows.loc["ME intake", "current_status"],
            "CALCULATED_INTAKE_DMI_DEPENDENT",
        )
        self.assertEqual(
            rows.loc["ME requirement", "current_status"],
            "PARTIALLY_REPRODUCIBLE_REQUIREMENT",
        )

    def test_15_rule_derived_fields_are_not_relabelled_measured(self) -> None:
        text = NUTRIENT_PATH.read_text(encoding="utf-8")
        self.assertIn("Calculated intake", text)
        self.assertIn("Model-derived requirement", text)
        self.assertNotIn("Cpintakeingr | Directly measured", text)
        self.assertNotIn("MEIntake | Directly measured", text)

    def test_16_observed_diets_are_not_relabelled_recommendations(self) -> None:
        row = self.repair.loc[
            self.repair["target"] == "Feed/ration class"
        ].iloc[0]
        self.assertEqual(row["current_status"], "OBSERVED_DIET_ONLY")
        self.assertEqual(row["training_decision"], "EXPERT_LABELS_REQUIRED")

    def test_17_no_expert_labels_are_generated(self) -> None:
        self.assertFalse(self.result["expert_label_generated"])
        self.assertIn(
            "PARTIAL_OPTION_B_SUPPORT",
            OPTION_B_PATH.read_text(encoding="utf-8"),
        )

    def test_18_target_repair_matrix_parses(self) -> None:
        self.assertEqual(self.repair.shape, (11, 6))
        self.assertEqual(
            list(self.repair.columns),
            [
                "target",
                "current_source_field",
                "current_status",
                "required_clarification",
                "possible_repair",
                "training_decision",
            ],
        )

    def test_19_author_questionnaire_contains_required_sections(self) -> None:
        text = AUTHOR_QUESTIONS_PATH.read_text(encoding="utf-8")
        for heading in (
            "## Dataset identity",
            "## Age",
            "## Feed and DMI",
            "## Water",
            "## Milk",
            "## Protein",
            "## Energy",
            "## NDF",
            "## Feeding plan",
            "## Corrected data",
        ):
            self.assertIn(heading, text)
        numbered = [
            line for line in text.splitlines() if line[:1].isdigit()
        ]
        self.assertEqual(len(numbered), 44)

    def test_20_training_gate_contains_all_required_rows(self) -> None:
        required = (
            "Source licence verified",
            "Measured milk target verified",
            "Row independence verified",
            "Cow grouping available",
            "Water target verified",
            "DMI target verified",
            "Age data repair approved",
            "Negative leftovers resolved",
            "CP formulas reproducible",
            "ME formulas reproducible",
            "NDF unit verified",
            "Feed recommendation labels available",
            "Model training not executed",
        )
        self.assertTrue(all(item in self.gate_text for item in required))
        self.assertIn("`WAITING_FOR_DATA_CLARIFICATION`", self.gate_text)

    def test_21_no_raw_file_changed(self) -> None:
        self.assertEqual(self.raw_before, self.raw_after)
        self.assertTrue(self.result["raw_files_unchanged"])

    def test_22_no_model_changed(self) -> None:
        for key in ("retained_model", "phase4_candidates"):
            self.assertEqual(
                self.protected_before[key],
                self.protected_after[key],
            )

    def test_23_no_flask_route_changed(self) -> None:
        self.assertEqual(
            self.protected_before["routes"],
            self.protected_after["routes"],
        )

    def test_24_no_frontend_file_changed(self) -> None:
        self.assertEqual(
            self.protected_before["frontend_tree"],
            self.protected_after["frontend_tree"],
        )

    def test_25_no_nutrition_rule_changed(self) -> None:
        self.assertEqual(
            self.protected_before["nutrition_rules"],
            self.protected_after["nutrition_rules"],
        )

    def test_26_no_training_command_ran(self) -> None:
        self.assertFalse(self.result["model_training_occurred"])
        self.assertFalse(self.result["prediction_occurred"])
        source = Path(
            "ml/data_integration/validate_rwanda_clarification.py"
        ).read_text(encoding="utf-8")
        ast.parse(source)

    def test_27_no_processed_dataset_was_created(self) -> None:
        self.assertFalse(self.result["processed_rwanda_dataset_created"])
        self.assertEqual(
            self.protected_before["processed_files"],
            self.protected_after["processed_files"],
        )


if __name__ == "__main__":
    unittest.main()
