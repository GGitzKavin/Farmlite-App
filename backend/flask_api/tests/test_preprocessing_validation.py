"""Phase 3 artifact and protected-behaviour checks."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import pandas as pd

from config.settings import (
    FLASK_API_DIR,
    MILK_YIELD_DATASET_PATH,
    MILK_YIELD_MODEL_PATH,
    ML_REPORTS_DIR,
    PROJECT_ROOT,
)


RAW_DATASET_HASHES = {
    "global_cattle_milk_yield_prediction_dataset.csv": (
        "26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3"
    ),
    "global_cattle_disease_detection_dataset.csv": (
        "4CEDFA77234FE45B441E303FF051C33123969E37C3B484A03387094A613DC4B9"
    ),
}
MODEL_HASH = "B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA"
# Phase 7 removes raw exception details from the existing v1 route without
# changing the request or success-response contract.
ROUTES_HASH = "843D623EFF7B48497BB95A07ADF3222D7F94C66C03B091F24A9976D77AE7A0F0"
FEED_PLANNER_HASH = (
    "27C17A8DBDF8111FC961DD4DF06CB51201C7C480600494AA52D871C777B72F2A"
)
NUTRITION_RULES_HASH = (
    "3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C"
)
FEED_RECOMMENDATION_HASH = (
    "B57E8CBF4CFFABAEE85C917737990DACE10B8BACB8DA68D0AFC06D39DE0B9AD1"
)
FRONTEND_TREE_HASH = (
    "5E5DDFC9E091B93DA10E6B2026BCB399BDB6CC077ABC3B3487CA0427560E26C5"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def frontend_tree_hash() -> str:
    root = PROJECT_ROOT / "frontend"
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {"node_modules", "dist", "build"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest().upper()


class PreprocessingValidationArtifactTests(unittest.TestCase):
    def test_generated_split_and_fold_artifacts_parse(self) -> None:
        split = pd.read_csv(ML_REPORTS_DIR / "data_split_manifest.csv")
        folds = pd.read_csv(ML_REPORTS_DIR / "feed_type_oof_fold_manifest.csv")
        split_summary = json.loads(
            (ML_REPORTS_DIR / "data_split_summary.json").read_text(
                encoding="utf-8"
            )
        )
        fold_summary = json.loads(
            (ML_REPORTS_DIR / "feed_type_oof_fold_summary.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(len(split), 250_000)
        self.assertEqual(len(folds), 175_000)
        self.assertTrue(split_summary["checks"]["each_row_assigned_once"])
        self.assertTrue(
            fold_summary["checks"]["every_training_row_assigned_once"]
        )

    def test_manifests_contain_no_targets_or_predictions(self) -> None:
        split_columns = pd.read_csv(
            ML_REPORTS_DIR / "data_split_manifest.csv", nrows=0
        ).columns
        fold_columns = pd.read_csv(
            ML_REPORTS_DIR / "feed_type_oof_fold_manifest.csv", nrows=0
        ).columns

        for forbidden in ("feed_type", "feed_quantity_kg", "milk_yield_l"):
            self.assertNotIn(forbidden, split_columns)
            self.assertNotIn(forbidden, fold_columns)
        self.assertFalse(
            any("predict" in column.casefold() for column in fold_columns)
        )

    def test_validation_report_has_required_sections_and_status(self) -> None:
        report = (
            ML_REPORTS_DIR / "preprocessing_validation_report.md"
        ).read_text(encoding="utf-8")

        for heading in (
            "## Executive Summary",
            "## Canonical Column Mapping",
            "## Model 2 Design B Interface Validation",
            "## Leakage Checks",
            "## Determinism Checks",
            "## Phase 4 Readiness Decision",
        ):
            self.assertIn(heading, report)
        self.assertIn("READY_FOR_PHASE_4_WITH_LIMITATIONS", report)

    def test_raw_dataset_checksums_remain_unchanged(self) -> None:
        raw_directory = MILK_YIELD_DATASET_PATH.parent
        missing = [
            name
            for name in RAW_DATASET_HASHES
            if not (raw_directory / name).exists()
        ]
        if missing:
            self.skipTest(
                "Raw dataset CSVs are gitignored local files and are not "
                f"present in this checkout: {missing}"
            )

        self.assertEqual(
            {
                name: sha256_file(raw_directory / name)
                for name in RAW_DATASET_HASHES
            },
            RAW_DATASET_HASHES,
        )

    def test_existing_model_artifact_remains_unchanged_and_no_new_model_exists(
        self,
    ) -> None:
        model_files = sorted(MILK_YIELD_MODEL_PATH.parent.glob("*.joblib"))

        self.assertEqual(model_files, [MILK_YIELD_MODEL_PATH])
        self.assertEqual(sha256_file(MILK_YIELD_MODEL_PATH), MODEL_HASH)

    def test_api_route_remains_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(FLASK_API_DIR / "api" / "routes.py"),
            ROUTES_HASH,
        )

    def test_frontend_and_pdf_source_remain_unchanged(self) -> None:
        self.assertEqual(frontend_tree_hash(), FRONTEND_TREE_HASH)
        self.assertEqual(
            sha256_file(
                PROJECT_ROOT / "frontend" / "src" / "pages" / "FeedRecommendation.tsx"
            ),
            FEED_RECOMMENDATION_HASH,
        )

    def test_feed_planning_and_nutrition_rules_remain_unchanged(self) -> None:
        self.assertEqual(
            sha256_file(FLASK_API_DIR / "ml" / "inference" / "feed_planner.py"),
            FEED_PLANNER_HASH,
        )
        self.assertEqual(
            sha256_file(
                FLASK_API_DIR / "ml" / "validation" / "nutrition_rules.py"
            ),
            NUTRITION_RULES_HASH,
        )


if __name__ == "__main__":
    unittest.main()
