"""Phase 4.5E architecture-freeze controls for Bangladesh candidates."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import joblib

from config.settings import FLASK_API_DIR, PROJECT_ROOT


CONFIG_DIR = FLASK_API_DIR / "config"
REPORTS_DIR = FLASK_API_DIR / "ml" / "reports"
CANDIDATE_DIR = (
    FLASK_API_DIR / "ml" / "models" / "candidates" / "bangladesh"
)
PHASE4_CANDIDATE_DIR = (
    FLASK_API_DIR / "ml" / "models" / "candidates" / "phase4"
)

INVENTORY_PATH = REPORTS_DIR / "bangladesh_candidate_integration_inventory.json"
REVIEW_PATH = CONFIG_DIR / "bangladesh_integration_review.json"
THI_PATH = CONFIG_DIR / "bangladesh_thi_mapping_contract.json"
ELIGIBILITY_PATH = CONFIG_DIR / "bangladesh_model_eligibility_policy.json"
API_V2_PATH = CONFIG_DIR / "farmlite_prediction_api_contract_v2.json"

ROUTES_HASH = "843D623EFF7B48497BB95A07ADF3222D7F94C66C03B091F24A9976D77AE7A0F0"
# Phase 7 authorizes removal of Firebase-user console logging and raw v1
# exception disclosure without changing model safeguards or API contracts.
FRONTEND_TREE_HASH = (
    "7E8361DDEB0FA4F75AE28D484D3BDB75732C784E489F2C50332419C5576BCB88"
)
PDF_SOURCE_HASH = (
    "7F4EE3DE5CC2E5DACD2BF9F050DE682C244EB3282A4E19BA42BFDC6342D8855A"
)
FEED_PLANNER_HASH = (
    "27C17A8DBDF8111FC961DD4DF06CB51201C7C480600494AA52D871C777B72F2A"
)
NUTRITION_RULES_HASH = (
    "3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C"
)
RETAINED_MODEL_HASH = (
    "B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA"
)
PHASE4_MILK_HASH = (
    "5FDA66E3D9879FD6CF49D83B3235781545E5784781509BCC340FBFE03BBA286E"
)
PHASE4_MILK_METADATA_HASH = (
    "27FC611A3B4E3A470DC8ABC97EB2E70EC62DBB6205FD4E1D7F441674E91AF766"
)

EXPECTED_ELIGIBILITY_STATES = {
    "ELIGIBLE",
    "MISSING_REQUIRED_INPUT",
    "UNKNOWN_GENETIC_GROUP",
    "UNKNOWN_THI_CATEGORY",
    "OUT_OF_SCOPE_POPULATION",
    "INVALID_ENVIRONMENT_INPUT",
    "ARTIFACT_UNAVAILABLE",
    "ARTIFACT_HASH_MISMATCH",
    "MODEL_ERROR",
    "FALLBACK_REQUIRED",
}

RAW_SOURCE_HASHES = {
    "datasets/external/raw/bangladesh_hf_cross/metadata.docx":
        "B5C652DAA3C0DB3BCACF6931D46D072ECF6793863821856991B17A994F737A03",
    "datasets/external/raw/bangladesh_hf_cross/DMI, milk yield and composition.xlsx":
        "EC3FECE684C40343C2A4F8F527F2BBE274E7B5B6EBD2B200FCDA623DBDC6A508",
    "datasets/external/raw/bangladesh_hf_cross/physiological responses.xlsx":
        "58F5B01BC771E618C19EE33EC18A96F698EB61E262FE501182E3A2BDDAD01F65",
    "datasets/external/raw/bangladesh_hf_cross/Blood metabolites.xlsx":
        "1328BE3360353212B34E4321C1B77EEC5BB3081CE4002E7E93252310B4C07541",
    "datasets/external/raw/rwanda_dairy_nutrition/Metadata.xlsx":
        "DD3001D696D217C19A6C3198A46F262BFD849BBCD061B62CDF974FE4E778E068",
    "datasets/external/raw/rwanda_dairy_nutrition/Specific data recorded on individual cows under lactation in Rwanda 2020-2021.xlsx":
        "4DADD19810DEA87E1EC2CAE915369E59AB71BF396893496151D8B2F50CF6C876",
    "datasets/external/raw/rwanda_dairy_nutrition/Different fodders components in the samples.xlsx":
        "BA5F9180494FDE7DBC58B95EA4018A08915AE023719D4D453F09D18C25F79D0A",
    "datasets/external/raw/rwanda_dairy_nutrition/Bucket feeding plan (Supplemental Table).docx":
        "B3192EEC974B2599C8607B4458825DA19C7919C87E2FEF263821A584D587493B",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _frontend_tree_hash() -> str:
    root = PROJECT_ROOT / "frontend"
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(
            part in {"node_modules", "dist", "build", "__pycache__"}
            for part in path.parts
        ):
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest().upper()


class BangladeshIntegrationReviewTests(unittest.TestCase):
    """Exercise the 28 required design-review and protection checks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = _json(INVENTORY_PATH)
        cls.review = _json(REVIEW_PATH)
        cls.thi = _json(THI_PATH)
        cls.eligibility = _json(ELIGIBILITY_PATH)
        cls.api_v2 = _json(API_V2_PATH)

    def test_01_candidate_files_discovered(self) -> None:
        names = {path.name for path in CANDIDATE_DIR.iterdir() if path.is_file()}
        self.assertEqual(
            names,
            {
                "bangladesh_dmi_regressor_candidate_v1.joblib",
                "bangladesh_dmi_regressor_candidate_v1.metadata.json",
                "bangladesh_milk_yield_regressor_candidate_v1.joblib",
                "bangladesh_milk_yield_regressor_candidate_v1.metadata.json",
            },
        )

    def test_02_candidate_hashes_match(self) -> None:
        for candidate in self.inventory["candidates"].values():
            self.assertEqual(
                _sha256(FLASK_API_DIR / candidate["artifact_path"]),
                candidate["artifact_sha256"],
            )
            self.assertEqual(
                _sha256(FLASK_API_DIR / candidate["metadata_path"]),
                candidate["metadata_sha256"],
            )

    def test_03_model_contracts_parse(self) -> None:
        paths = [
            CONFIG_DIR / "bangladesh_model_contract.json",
            INVENTORY_PATH,
            REVIEW_PATH,
            THI_PATH,
            ELIGIBILITY_PATH,
            API_V2_PATH,
        ]
        for path in paths:
            self.assertIsInstance(_json(path), dict, path)

    def test_04_feature_order_is_verified(self) -> None:
        expected = ["genetic_group", "thi_category"]
        self.assertEqual(
            self.inventory["shared_pipeline_contract"]["feature_order"],
            expected,
        )
        for candidate in self.inventory["candidates"].values():
            metadata = _json(FLASK_API_DIR / candidate["metadata_path"])
            self.assertEqual(candidate["feature_order"], expected)
            self.assertEqual(metadata["feature_order"], expected)

    def test_05_known_categories_are_extracted(self) -> None:
        expected_genetic = {"Local", "HF50", "HF62.5", "HF75", "HF87.5"}
        expected_thi = {"T0", "T1", "T2"}
        for candidate in self.inventory["candidates"].values():
            pipeline = joblib.load(FLASK_API_DIR / candidate["artifact_path"])
            encoder = pipeline.named_steps[
                "preprocessing"
            ].named_transformers_["categorical"]
            self.assertEqual(set(encoder.categories_[0]), expected_genetic)
            self.assertEqual(set(encoder.categories_[1]), expected_thi)
        self.assertEqual(
            self.inventory["holdout_scope_note"][
                "trained_group_absent_from_locked_holdout"
            ],
            "Local",
        )

    def test_06_genetic_group_is_not_inferred_from_breed(self) -> None:
        genetic = self.review["request_adapter"]["genetic_group"]
        self.assertFalse(genetic["derive_from_free_text_breed"])
        breed_field = next(
            field
            for field in self.api_v2["request"]["fields"]
            if field["name"] == "breed"
        )
        self.assertIn("Never maps automatically", breed_field["notes"])

    def test_07_thi_thresholds_are_evidence_backed(self) -> None:
        self.assertTrue(self.thi["formula"]["verified"])
        self.assertEqual(
            self.thi["formula"]["article_doi"],
            "10.1016/j.anopes.2026.100139",
        )
        self.assertTrue(self.thi["formula"]["local_evidence"])
        self.assertEqual(
            [(item["label"], item["rule"]) for item in self.thi["categories"]],
            [
                ("T0", "THI <= 75"),
                ("T1", "75 < THI < 80"),
                ("T2", "THI >= 80"),
            ],
        )

    def test_08_missing_thi_evidence_blocks_mapping(self) -> None:
        policy = self.thi["evidence_policy"]
        for key in (
            "formula_missing",
            "thresholds_missing",
            "pipeline_categories_missing",
            "evidence_conflict",
            "missing_evidence_policy",
        ):
            self.assertEqual(policy[key], "BLOCKED")

    def test_09_eligibility_states_are_complete(self) -> None:
        self.assertEqual(
            set(self.eligibility["status_values"]),
            EXPECTED_ELIGIBILITY_STATES,
        )
        self.assertEqual(
            [item["priority"] for item in self.eligibility[
                "deterministic_evaluation_order"
            ]],
            list(range(1, 11)),
        )

    def test_10_unknown_categories_cause_fallback(self) -> None:
        policy = self.eligibility["unknown_category_policy"]
        self.assertEqual(policy["genetic_group"], "UNKNOWN_GENETIC_GROUP")
        self.assertEqual(policy["thi_category"], "UNKNOWN_THI_CATEGORY")
        self.assertFalse(policy["call_pipeline_anyway"])
        self.assertEqual(policy["result"], "FALLBACK_REQUIRED")

    def test_11_dmi_unit_remains_kg_dry_matter_per_cow_day(self) -> None:
        dmi = self.inventory["candidates"]["dmi"]
        self.assertEqual(dmi["output_unit"], "kg dry matter/cow/day")
        self.assertEqual(dmi["target"], "dry_matter_intake_kg_day")

    def test_12_dmi_is_not_treated_as_fresh_feed_quantity(self) -> None:
        dmi = self.eligibility["model_specific_output_policy"][
            "bangladesh_dmi_regressor"
        ]
        self.assertFalse(dmi["may_be_used_as_total_fresh_feed"])
        self.assertEqual(
            self.review["response_requirements"][
                "numeric_adjustment_policy"
            ],
            "DO_NOT_CLAMP_OR_CONVERT_DMI_TO_FEED",
        )

    def test_13_milk_unit_remains_litres_per_cow_day(self) -> None:
        milk = self.inventory["candidates"]["milk"]
        self.assertEqual(milk["output_unit"], "L/cow/day")
        self.assertEqual(milk["target"], "milk_yield_l_day")

    def test_14_rule_outputs_are_separated_from_ml_outputs(self) -> None:
        ownership = self.api_v2["output_ownership"]
        ml_outputs = set(ownership["ml_outputs"])
        rule_outputs = set(ownership["rule_outputs"])
        self.assertFalse(ml_outputs & rule_outputs)
        self.assertEqual(
            ml_outputs,
            {
                "ml_predictions.dmi_kg_day",
                "ml_predictions.milk_yield_l_day",
            },
        )
        self.assertIn(
            "rule_recommendation.roughage_kg_day",
            rule_outputs,
        )

    def test_15_blood_variables_remain_excluded(self) -> None:
        self.assertIn(
            "blood_variables",
            self.eligibility["forbidden_inference_features"],
        )

    def test_16_physiology_remains_excluded(self) -> None:
        self.assertIn(
            "physiology_variables",
            self.eligibility["forbidden_inference_features"],
        )

    def test_17_cow_id_remains_excluded(self) -> None:
        self.assertIn(
            "cow_id",
            self.eligibility["forbidden_inference_features"],
        )
        self.assertNotIn("cow_id", self.eligibility["required_model_features"])

    def test_18_api_v2_contract_parses(self) -> None:
        self.assertEqual(self.api_v2["schema_version"], "2.0.0-design")
        self.assertEqual(
            self.api_v2["status"],
            "IMPLEMENTED_BACKEND_PROTOTYPE_DISABLED_BY_DEFAULT",
        )
        self.assertEqual(self.api_v2["endpoint"], "POST /api/v2/predict")
        field_names = {
            field["name"] for field in self.api_v2["request"]["fields"]
        }
        self.assertIn("genetic_group", field_names)
        self.assertNotIn("hf_inheritance_percent", field_names)
        self.assertTrue(
            self.api_v2["response"]["null_policy"][
                "never_substitute_zero_for_missing"
            ]
        )

    def test_19_existing_routes_remain_unchanged(self) -> None:
        self.assertEqual(_sha256(FLASK_API_DIR / "api" / "routes.py"), ROUTES_HASH)

    def test_20_frontend_remains_unchanged(self) -> None:
        self.assertEqual(_frontend_tree_hash(), FRONTEND_TREE_HASH)

    def test_21_pdf_source_remains_unchanged(self) -> None:
        pdf_source = (
            PROJECT_ROOT / "frontend" / "src" / "pages" / "FeedRecommendation.tsx"
        )
        self.assertEqual(_sha256(pdf_source), PDF_SOURCE_HASH)

    def test_22_nutrition_rules_remain_unchanged(self) -> None:
        self.assertEqual(
            _sha256(FLASK_API_DIR / "ml" / "inference" / "feed_planner.py"),
            FEED_PLANNER_HASH,
        )
        self.assertEqual(
            _sha256(FLASK_API_DIR / "ml" / "validation" / "nutrition_rules.py"),
            NUTRITION_RULES_HASH,
        )

    def test_23_candidate_artifacts_remain_unchanged(self) -> None:
        expected = {
            "bangladesh_dmi_regressor_candidate_v1.joblib":
                "312DDBAADA9A92A8B52E4ED95B254ACE0FD3EBEE1C6DD0B12BB003562EDD035B",
            "bangladesh_dmi_regressor_candidate_v1.metadata.json":
                "0016C843FAA9A5BA7C8533F987FA748E8BC021A1ED24F65D9AA53E27D9EAF0DF",
            "bangladesh_milk_yield_regressor_candidate_v1.joblib":
                "AA650EA16D4E89BB6A660778854138BEECCCCBEA9B3C589E2E549EF823D5F56E",
            "bangladesh_milk_yield_regressor_candidate_v1.metadata.json":
                "1D5D2D019B2AE0595D421298386DB4527C1C2D5771BAD69724E6E2727708F303",
        }
        self.assertEqual(
            {path.name: _sha256(path) for path in CANDIDATE_DIR.iterdir()},
            expected,
        )

    def test_24_existing_models_remain_unchanged(self) -> None:
        self.assertEqual(
            _sha256(FLASK_API_DIR / "ml" / "models" / "milk_yield_model.joblib"),
            RETAINED_MODEL_HASH,
        )
        self.assertEqual(
            _sha256(PHASE4_CANDIDATE_DIR / "milk_yield_regressor_candidate_v1.joblib"),
            PHASE4_MILK_HASH,
        )
        self.assertEqual(
            _sha256(
                PHASE4_CANDIDATE_DIR
                / "milk_yield_regressor_candidate_v1.metadata.json"
            ),
            PHASE4_MILK_METADATA_HASH,
        )

    def test_25_no_model_training_occurs(self) -> None:
        self.assertFalse(self.inventory["training_performed"])
        self.assertFalse(self.inventory["prediction_generation_performed"])
        design_paths = [
            INVENTORY_PATH,
            REVIEW_PATH,
            THI_PATH,
            ELIGIBILITY_PATH,
            API_V2_PATH,
        ]
        for path in design_paths:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn(".fit(", source, path)
            self.assertNotIn(".predict(", source, path)

    def test_26_no_model_integration_occurs(self) -> None:
        self.assertFalse(self.review["runtime_integration_performed"])
        self.assertTrue(self.api_v2["runtime_integration_performed"])
        self.assertFalse(self.api_v2["frontend_integration_performed"])
        self.assertFalse(self.api_v2["nutrition_integration_performed"])
        runtime_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                FLASK_API_DIR / "api" / "routes.py",
                FLASK_API_DIR / "ml" / "inference" / "model_service.py",
                FLASK_API_DIR / "ml" / "inference" / "feed_planner.py",
            )
        )
        self.assertNotIn("bangladesh_dmi_regressor", runtime_source)
        self.assertNotIn("bangladesh_milk_yield_regressor", runtime_source)

    def test_27_no_dataset_merge_occurs(self) -> None:
        self.assertFalse(self.inventory["dataset_merge_performed"])
        for relative_path, expected_hash in RAW_SOURCE_HASHES.items():
            self.assertEqual(
                _sha256(PROJECT_ROOT / relative_path),
                expected_hash,
                relative_path,
            )
        training_summary = _json(REPORTS_DIR / "bangladesh_training_summary.json")
        self.assertFalse(training_summary["source_datasets_concatenated"])

    def test_28_production_approval_remains_false(self) -> None:
        self.assertFalse(self.review["production_approved"])
        self.assertFalse(self.review["commercial_use_approved"])
        self.assertFalse(self.review["veterinary_use_approved"])
        self.assertFalse(self.thi["production_approved"])
        self.assertFalse(self.eligibility["production_approved"])
        self.assertFalse(self.api_v2["production_approved"])
        for candidate in self.inventory["candidates"].values():
            metadata = _json(FLASK_API_DIR / candidate["metadata_path"])
            self.assertEqual(metadata["artifact_status"], "CANDIDATE_ONLY")
            self.assertFalse(metadata["production_approved"])


if __name__ == "__main__":
    unittest.main()
