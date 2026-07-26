"""Focused Phase 5 controls for Bangladesh backend candidate integration."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from app import create_app
from config.settings import (
    FLASK_API_DIR,
    PROJECT_ROOT,
    bangladesh_candidate_models_enabled,
    parse_feature_flag,
)
from ml.inference.bangladesh_artifact_loader import (
    ArtifactLoadError,
    LoadedCandidate,
    VerifiedArtifact,
    clear_candidate_cache,
    get_artifact_spec,
    load_candidate,
    verify_candidate_integrity,
)
from ml.inference.bangladesh_eligibility import evaluate_eligibility
from ml.inference.bangladesh_model_service import (
    predict_bangladesh_candidates,
    validate_prediction_value,
)
from ml.inference.bangladesh_thi import (
    ThiResult,
    calculate_thi,
    categorize_thi,
)


FLAG = "BANGLADESH_CANDIDATE_MODELS_ENABLED"
CANDIDATE_DIR = (
    FLASK_API_DIR / "ml" / "models" / "candidates" / "bangladesh"
)
VALID_REQUEST = {
    "breed": "Holstein-Friesian",
    "genetic_group": "HF75",
    "age_months": 48,
    "weight_kg": 420,
    "lactation_stage": "Mid Lactation",
    "days_in_milk": 120,
    "previous_week_avg_yield_l": 7.0,
    "body_condition_score": 3.0,
    "ambient_temperature_c": 28,
    "humidity_percent": 75,
    "health_status": "Healthy",
}
REQUIRED_RESPONSE_SECTIONS = {
    "schema_version",
    "prediction_status",
    "eligibility",
    "environment",
    "ml_predictions",
    "model_sources",
    "rule_recommendation",
    "warnings",
    "limitations",
    "fallback_reasons",
}

ROUTES_HASH = (
    "843D623EFF7B48497BB95A07ADF3222D7F94C66C03B091F24A9976D77AE7A0F0"
)
# Phase 7 authorizes removal of Firebase-user console logging and raw v1
# exception disclosure. The Phase 5 model safeguards and API contracts stay
# unchanged.
FRONTEND_TREE_HASH = (
    "7E8361DDEB0FA4F75AE28D484D3BDB75732C784E489F2C50332419C5576BCB88"
)
PDF_HASH = (
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


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


class _StubModel:
    def __init__(self, output: object) -> None:
        self.output = output
        self.columns: list[str] | None = None

    def predict(self, frame):
        self.columns = list(frame.columns)
        return self.output


def _loaded(task: str, output: object) -> LoadedCandidate:
    return LoadedCandidate(
        spec=get_artifact_spec(task),
        metadata={},
        model=_StubModel(output),
    )


class Phase5BackendIntegrationTests(unittest.TestCase):
    """Exercise the approved controls and all 40 requested test categories."""

    def setUp(self) -> None:
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        clear_candidate_cache()

    def tearDown(self) -> None:
        clear_candidate_cache()

    def _enabled_post(self, value: dict | None = None):
        with patch.dict(os.environ, {FLAG: "true"}):
            return self.client.post(
                "/api/v2/predict",
                json=VALID_REQUEST if value is None else value,
            )

    def test_01_feature_flag_defaults_false(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(FLAG, None)
            self.assertFalse(bangladesh_candidate_models_enabled())

    def test_02_invalid_feature_flag_values_default_false(self) -> None:
        for value in ("", "enabled", "2", "truth", " false "):
            with self.subTest(value=value):
                self.assertFalse(parse_feature_flag(value))

    def test_03_true_feature_flag_values_are_explicit(self) -> None:
        for value in ("1", "true", "TRUE", " yes ", "On"):
            with self.subTest(value=value):
                self.assertTrue(parse_feature_flag(value))

    def test_04_disabled_service_never_loads_or_calculates(self) -> None:
        with (
            patch(
                "ml.inference.bangladesh_model_service.load_candidate"
            ) as loader,
            patch(
                "ml.inference.bangladesh_model_service.calculate_thi"
            ) as thi,
        ):
            body = predict_bangladesh_candidates(VALID_REQUEST, enabled=False)
        self.assertEqual(body["prediction_status"], "DISABLED")
        loader.assert_not_called()
        thi.assert_not_called()

    def test_05_disabled_endpoint_is_structured(self) -> None:
        with patch.dict(os.environ, {FLAG: "false"}):
            response = self.client.post("/api/v2/predict", json={})
        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(REQUIRED_RESPONSE_SECTIONS <= set(body))
        self.assertEqual(body["fallback_reasons"], ["FEATURE_DISABLED"])
        self.assertIsNone(body["ml_predictions"]["dmi_kg_day"])
        self.assertIsNone(body["ml_predictions"]["milk_yield_l_day"])

    def test_06_candidate_hashes_match_approved_values(self) -> None:
        expected = {
            "dmi": "312DDBAADA9A92A8B52E4ED95B254ACE0FD3EBEE1C6DD0B12BB003562EDD035B",
            "milk": "AA650EA16D4E89BB6A660778854138BEECCCCBEA9B3C589E2E549EF823D5F56E",
        }
        for task, approved in expected.items():
            verified = verify_candidate_integrity(task)
            self.assertEqual(verified.artifact_sha256, approved)

    def test_07_hash_mismatch_blocks_deserialization(self) -> None:
        original = get_artifact_spec("dmi")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "candidate.joblib"
            metadata = root / "candidate.metadata.json"
            shutil.copyfile(original.artifact_path, artifact)
            shutil.copyfile(original.metadata_path, metadata)
            bad = replace(
                original,
                artifact_path=artifact,
                metadata_path=metadata,
                artifact_sha256="0" * 64,
            )
            with (
                patch(
                    "ml.inference.bangladesh_artifact_loader.joblib.load"
                ) as deserialize,
                self.assertRaises(ArtifactLoadError) as raised,
            ):
                load_candidate("dmi", spec=bad, trusted_root=root)
        self.assertEqual(raised.exception.code, "ARTIFACT_HASH_MISMATCH")
        deserialize.assert_not_called()

    def test_08_missing_candidate_blocks_loading(self) -> None:
        original = get_artifact_spec("dmi")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = replace(
                original,
                artifact_path=root / "missing.joblib",
                metadata_path=root / "missing.json",
            )
            with self.assertRaises(ArtifactLoadError) as raised:
                load_candidate("dmi", spec=missing, trusted_root=root)
        self.assertEqual(raised.exception.code, "ARTIFACT_UNAVAILABLE")

    def test_09_invalid_metadata_blocks_loading(self) -> None:
        original = get_artifact_spec("dmi")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "candidate.joblib"
            metadata = root / "candidate.metadata.json"
            shutil.copyfile(original.artifact_path, artifact)
            metadata.write_text("{}", encoding="utf-8")
            invalid = replace(
                original,
                artifact_path=artifact,
                metadata_path=metadata,
                metadata_sha256=_sha256(metadata),
            )
            with self.assertRaises(ArtifactLoadError) as raised:
                load_candidate("dmi", spec=invalid, trusted_root=root)
        self.assertEqual(raised.exception.code, "ARTIFACT_METADATA_INVALID")

    def test_10_feature_order_contract_is_exact(self) -> None:
        for task in ("dmi", "milk"):
            self.assertEqual(
                get_artifact_spec(task).feature_order,
                ("genetic_group", "thi_category"),
            )

    def test_11_loaded_pipeline_categories_are_compatible(self) -> None:
        for task in ("dmi", "milk"):
            self.assertTrue(hasattr(load_candidate(task).model, "predict"))

    def test_12_successful_candidate_load_is_cached(self) -> None:
        import joblib

        real_load = joblib.load
        with patch(
            "ml.inference.bangladesh_artifact_loader.joblib.load",
            side_effect=real_load,
        ) as deserialize:
            first = load_candidate("dmi")
            second = load_candidate("dmi")
        self.assertIs(first, second)
        self.assertEqual(deserialize.call_count, 1)

    def test_13_path_outside_trusted_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ArtifactLoadError) as raised:
                verify_candidate_integrity(
                    "dmi",
                    trusted_root=Path(directory),
                )
        self.assertEqual(raised.exception.code, "ARTIFACT_INCOMPATIBLE")

    def test_14_known_genetic_groups_are_accepted(self) -> None:
        thi = calculate_thi(28, 75)
        for group in ("Local", "HF50", "HF62.5", "HF75", "HF87.5"):
            request_value = dict(VALID_REQUEST, genetic_group=group)
            with self.subTest(group=group):
                self.assertEqual(
                    evaluate_eligibility(request_value, thi).status,
                    "ELIGIBLE",
                )

    def test_15_unknown_genetic_group_fails_closed(self) -> None:
        result = evaluate_eligibility(
            dict(VALID_REQUEST, genetic_group="HF80"),
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "UNKNOWN_GENETIC_GROUP")
        self.assertEqual(result.scope, "OUT_OF_SCOPE")

    def test_16_breed_never_infers_genetic_group(self) -> None:
        request_value = dict(VALID_REQUEST)
        request_value.pop("genetic_group")
        result = evaluate_eligibility(
            request_value,
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "MISSING_REQUIRED_INPUT")
        self.assertEqual(result.fallback_reason, "GENETIC_GROUP_MISSING")

    def test_17_local_has_limited_support(self) -> None:
        result = evaluate_eligibility(
            dict(VALID_REQUEST, genetic_group="Local"),
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "ELIGIBLE")
        self.assertEqual(result.scope, "LIMITED_SUPPORT")

    def test_18_dry_cow_is_out_of_scope(self) -> None:
        result = evaluate_eligibility(
            dict(VALID_REQUEST, lactation_stage="Dry"),
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "OUT_OF_SCOPE_POPULATION")

    def test_19_non_lactating_cow_is_out_of_scope(self) -> None:
        result = evaluate_eligibility(
            dict(VALID_REQUEST, lactation_stage="Non-lactating cow"),
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "OUT_OF_SCOPE_POPULATION")

    def test_20_calf_is_out_of_scope(self) -> None:
        result = evaluate_eligibility(
            dict(VALID_REQUEST, lactation_stage="Calf"),
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "OUT_OF_SCOPE_POPULATION")

    def test_21_bull_is_out_of_scope(self) -> None:
        result = evaluate_eligibility(
            dict(VALID_REQUEST, lactation_stage="Bull"),
            calculate_thi(28, 75),
        )
        self.assertEqual(result.status, "OUT_OF_SCOPE_POPULATION")

    def test_22_missing_temperature_causes_fallback(self) -> None:
        body = predict_bangladesh_candidates(
            dict(VALID_REQUEST, ambient_temperature_c=None),
            enabled=True,
        )
        self.assertEqual(body["prediction_status"], "FALLBACK_REQUIRED")
        self.assertIn("ENVIRONMENT_MISSING", body["fallback_reasons"])

    def test_23_missing_humidity_causes_fallback(self) -> None:
        body = predict_bangladesh_candidates(
            dict(VALID_REQUEST, humidity_percent=None),
            enabled=True,
        )
        self.assertEqual(body["prediction_status"], "FALLBACK_REQUIRED")
        self.assertIn("ENVIRONMENT_MISSING", body["fallback_reasons"])

    def test_24_invalid_humidity_causes_fallback(self) -> None:
        for humidity in (-0.1, 100.1):
            body = predict_bangladesh_candidates(
                dict(VALID_REQUEST, humidity_percent=humidity),
                enabled=True,
            )
            with self.subTest(humidity=humidity):
                self.assertEqual(
                    body["eligibility"]["dmi"]["status"],
                    "INVALID_ENVIRONMENT_INPUT",
                )
                self.assertIn("ENVIRONMENT_INVALID", body["fallback_reasons"])

    def test_25_thi_calculation_matches_contract(self) -> None:
        result = calculate_thi(28, 75)
        self.assertEqual(result.calculated_thi, 79.045)
        self.assertEqual(result.display_thi, 79.05)
        self.assertEqual(result.thi_category, "T1")

    def test_26_exact_and_adjacent_thi_boundaries_are_correct(self) -> None:
        cases = (
            (74.999999, "T0"),
            (75.0, "T0"),
            (75.000001, "T1"),
            (79.999999, "T1"),
            (80.0, "T2"),
            (80.000001, "T2"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(categorize_thi(value), expected)

    def test_27_non_numeric_environment_is_rejected(self) -> None:
        for temperature, humidity in (("hot", 75), (28, "humid")):
            result = calculate_thi(temperature, humidity)
            with self.subTest(value=(temperature, humidity)):
                self.assertEqual(
                    result.status,
                    "INVALID_ENVIRONMENT_INPUT",
                )

    def test_28_unsupported_thi_category_fails_closed(self) -> None:
        unsupported = ThiResult(
            "ELIGIBLE",
            70.0,
            70.0,
            "T9",
            "test",
            "VERIFIED_WITH_LIMITATIONS",
            None,
            (),
        )
        result = evaluate_eligibility(VALID_REQUEST, unsupported)
        self.assertEqual(result.status, "UNKNOWN_THI_CATEGORY")

    def test_29_eligible_dmi_prediction_is_finite(self) -> None:
        body = self._enabled_post().get_json()
        self.assertTrue(math.isfinite(body["ml_predictions"]["dmi_kg_day"]))

    def test_30_eligible_milk_prediction_is_finite(self) -> None:
        body = self._enabled_post().get_json()
        self.assertTrue(
            math.isfinite(body["ml_predictions"]["milk_yield_l_day"])
        )

    def test_31_negative_prediction_is_rejected(self) -> None:
        value, warning = validate_prediction_value(
            -1.0,
            minimum=0.0,
            maximum=20.0,
        )
        self.assertIsNone(value)
        self.assertIn("negative", warning or "")

    def test_32_nan_prediction_is_rejected(self) -> None:
        value, warning = validate_prediction_value(
            float("nan"),
            minimum=0.0,
            maximum=20.0,
        )
        self.assertIsNone(value)
        self.assertIn("finite", warning or "")

    def test_33_out_of_range_prediction_is_rejected_without_clipping(self) -> None:
        value, warning = validate_prediction_value(
            99.0,
            minimum=4.48,
            maximum=14.82,
        )
        self.assertIsNone(value)
        self.assertIn("outside", warning or "")

    def test_34_prediction_units_remain_exact(self) -> None:
        body = self._enabled_post().get_json()
        self.assertEqual(
            body["prediction_units"]["dmi_kg_day"],
            "kg dry matter/cow/day",
        )
        self.assertEqual(
            body["prediction_units"]["milk_yield_l_day"],
            "L/cow/day",
        )

    def test_35_dmi_is_not_exposed_as_total_feed(self) -> None:
        body = self._enabled_post().get_json()
        serialized = json.dumps(body)
        self.assertNotIn("totalFeedKg", serialized)
        self.assertNotIn("total_feed_kg", serialized)

    def test_36_rule_recommendation_remains_empty(self) -> None:
        rule = self._enabled_post().get_json()["rule_recommendation"]
        self.assertTrue(rule)
        self.assertTrue(all(value is None for value in rule.values()))

    def test_37_nutrition_rules_are_not_called(self) -> None:
        with patch(
            "ml.inference.feed_planner.generate_feed_plan"
        ) as nutrition:
            response = self._enabled_post()
        self.assertEqual(response.status_code, 200)
        nutrition.assert_not_called()

    def test_38_no_automatic_milk_fallback_occurs(self) -> None:
        dmi = _loaded("dmi", [10.0])

        def candidate(task: str):
            if task == "dmi":
                return dmi
            raise ArtifactLoadError(
                "ARTIFACT_UNAVAILABLE",
                "milk unavailable",
                "milk",
            )

        with patch(
            "ml.inference.bangladesh_model_service.load_candidate",
            side_effect=candidate,
        ):
            body = predict_bangladesh_candidates(VALID_REQUEST, enabled=True)
        self.assertEqual(body["prediction_status"], "PARTIAL")
        self.assertIsNone(body["ml_predictions"]["milk_yield_l_day"])
        self.assertIsNone(body["model_sources"]["milk"])

    def test_39_disabled_response_matches_required_schema(self) -> None:
        with patch.dict(os.environ, {FLAG: "not-valid"}):
            body = self.client.post("/api/v2/predict", json={}).get_json()
        self.assertTrue(REQUIRED_RESPONSE_SECTIONS <= set(body))
        self.assertEqual(
            set(body["eligibility"]),
            {"dmi", "milk"},
        )

    def test_40_eligible_response_matches_required_schema(self) -> None:
        response = self._enabled_post()
        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["prediction_status"], "ELIGIBLE")
        self.assertTrue(REQUIRED_RESPONSE_SECTIONS <= set(body))
        self.assertEqual(
            set(body["eligibility"]["dmi"]),
            {"status", "scope", "fallback_reason"},
        )

    def test_41_ineligible_response_matches_required_schema(self) -> None:
        body = self._enabled_post(
            dict(VALID_REQUEST, genetic_group="Unknown")
        ).get_json()
        self.assertEqual(body["prediction_status"], "FALLBACK_REQUIRED")
        self.assertTrue(REQUIRED_RESPONSE_SECTIONS <= set(body))
        self.assertIsNone(body["ml_predictions"]["dmi_kg_day"])
        self.assertIn("GENETIC_GROUP_UNKNOWN", body["fallback_reasons"])

    def test_42_malformed_json_returns_controlled_error(self) -> None:
        with patch.dict(os.environ, {FLAG: "true"}):
            response = self.client.post(
                "/api/v2/predict",
                data='{"breed":',
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_code"], "INVALID_JSON")

    def test_43_invalid_primitive_type_returns_422(self) -> None:
        body = dict(VALID_REQUEST, age_months="48")
        response = self._enabled_post(body)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.get_json()["error_code"],
            "INVALID_FIELD_TYPE",
        )

    def test_44_oversized_request_returns_controlled_422(self) -> None:
        with patch.dict(os.environ, {FLAG: "true"}):
            response = self.client.post(
                "/api/v2/predict",
                data=json.dumps({"breed": "x" * (17 * 1024)}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.get_json()["error_code"],
            "REQUEST_TOO_LARGE",
        )

    def test_45_partial_artifact_availability_preserves_valid_output(self) -> None:
        milk = _loaded("milk", [6.0])

        def candidate(task: str):
            if task == "milk":
                return milk
            raise ArtifactLoadError(
                "ARTIFACT_HASH_MISMATCH",
                "dmi hash mismatch",
                "dmi",
            )

        with patch(
            "ml.inference.bangladesh_model_service.load_candidate",
            side_effect=candidate,
        ):
            body = predict_bangladesh_candidates(VALID_REQUEST, enabled=True)
        self.assertEqual(body["prediction_status"], "PARTIAL")
        self.assertIsNone(body["ml_predictions"]["dmi_kg_day"])
        self.assertEqual(body["ml_predictions"]["milk_yield_l_day"], 6.0)

    def test_46_model_frame_preserves_exact_feature_order(self) -> None:
        dmi = _loaded("dmi", [10.0])
        milk = _loaded("milk", [6.0])
        with patch(
            "ml.inference.bangladesh_model_service.load_candidate",
            side_effect=lambda task: dmi if task == "dmi" else milk,
        ):
            predict_bangladesh_candidates(VALID_REQUEST, enabled=True)
        self.assertEqual(
            dmi.model.columns,
            ["genetic_group", "thi_category"],
        )
        self.assertEqual(
            milk.model.columns,
            ["genetic_group", "thi_category"],
        )

    def test_47_existing_v1_health_behavior_is_unchanged(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"status": "healthy", "service": "FarmLite AI API"},
        )
        self.assertEqual(_sha256(FLASK_API_DIR / "api" / "routes.py"), ROUTES_HASH)

    def test_48_frontend_files_are_unchanged(self) -> None:
        self.assertEqual(_frontend_tree_hash(), FRONTEND_TREE_HASH)

    def test_49_pdf_source_is_unchanged(self) -> None:
        source = (
            PROJECT_ROOT / "frontend" / "src" / "pages" / "FeedRecommendation.tsx"
        )
        self.assertEqual(_sha256(source), PDF_HASH)

    def test_50_nutrition_rule_files_are_unchanged(self) -> None:
        self.assertEqual(
            _sha256(FLASK_API_DIR / "ml" / "inference" / "feed_planner.py"),
            FEED_PLANNER_HASH,
        )
        self.assertEqual(
            _sha256(
                FLASK_API_DIR / "ml" / "validation" / "nutrition_rules.py"
            ),
            NUTRITION_RULES_HASH,
        )

    def test_51_candidate_artifacts_are_unchanged(self) -> None:
        self.assertEqual(
            _sha256(
                CANDIDATE_DIR
                / "bangladesh_dmi_regressor_candidate_v1.joblib"
            ),
            "312DDBAADA9A92A8B52E4ED95B254ACE0FD3EBEE1C6DD0B12BB003562EDD035B",
        )
        self.assertEqual(
            _sha256(
                CANDIDATE_DIR
                / "bangladesh_milk_yield_regressor_candidate_v1.joblib"
            ),
            "AA650EA16D4E89BB6A660778854138BEECCCCBEA9B3C589E2E549EF823D5F56E",
        )

    def test_52_existing_model_is_unchanged(self) -> None:
        self.assertEqual(
            _sha256(
                FLASK_API_DIR / "ml" / "models" / "milk_yield_model.joblib"
            ),
            RETAINED_MODEL_HASH,
        )

    def test_53_no_model_training_occurs_in_phase5_modules(self) -> None:
        paths = (
            FLASK_API_DIR
            / "ml"
            / "inference"
            / "bangladesh_artifact_loader.py",
            FLASK_API_DIR / "ml" / "inference" / "bangladesh_thi.py",
            FLASK_API_DIR / "ml" / "inference" / "bangladesh_eligibility.py",
            FLASK_API_DIR
            / "ml"
            / "inference"
            / "bangladesh_model_service.py",
        )
        for path in paths:
            self.assertNotIn(".fit(", path.read_text(encoding="utf-8"))

    def test_54_production_approval_remains_false(self) -> None:
        contract = json.loads(
            (
                FLASK_API_DIR
                / "config"
                / "farmlite_prediction_api_contract_v2.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(contract["production_approved"])
        for task in ("dmi", "milk"):
            metadata = verify_candidate_integrity(task).metadata
            self.assertEqual(metadata["artifact_status"], "CANDIDATE_ONLY")
            self.assertFalse(metadata["production_approved"])

    def test_55_unknown_request_field_is_rejected(self) -> None:
        response = self._enabled_post(dict(VALID_REQUEST, cow_id="COW-1"))
        self.assertEqual(response.status_code, 422)
        self.assertIn("cow_id", response.get_json()["field_errors"])

    def test_56_unexpected_service_exception_is_controlled(self) -> None:
        with (
            patch.dict(os.environ, {FLAG: "true"}),
            patch(
                "api.v2_routes.predict_bangladesh_candidates",
                side_effect=RuntimeError("private detail"),
            ),
        ):
            response = self.client.post(
                "/api/v2/predict",
                json=VALID_REQUEST,
            )
        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertEqual(body["error_code"], "INTERNAL_SERVER_ERROR")
        self.assertNotIn("private detail", body["message"])


if __name__ == "__main__":
    unittest.main()
