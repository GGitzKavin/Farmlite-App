"""Run Phase 4.5D Bangladesh DMI and milk experiments.

Run from ``backend/flask_api``:

    venv\\Scripts\\python.exe -m ml.training.run_bangladesh_model_experiments

This runner creates candidate-only research artifacts.  It does not import or
modify Flask routes, runtime inference, the frontend, PDFs, or nutrition rules.
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config.settings import FLASK_API_DIR, ML_REPORTS_DIR, PROJECT_ROOT
from ml.data_integration.bangladesh_audit import (
    BLOOD_FILENAME,
    DMI_FILENAME,
    EXPECTED_SHA256,
    METADATA_FILENAME,
    PHYSIOLOGY_FILENAME,
    SOURCE_DIR,
    canonical_cow_id,
    canonical_thi,
    dataframe_from_sheet,
    sha256_file,
)
from ml.data_integration.office_reader import read_xlsx
from ml.data_integration.validate_bangladesh_dataset import (
    _protected_snapshot,
)
from ml.training.bangladesh_modeling import (
    CONTRACT_PATH,
    LINEAGE_FIELDS,
    PRIMARY_FEATURES,
    PROCESSED_DIR,
    RANDOM_SEED,
    TASKS,
    BangladeshExperimentError,
    build_pipeline,
    build_task_frame,
    candidate_specs,
    create_group_assignments,
    evaluate_final_holdout,
    evaluate_grouped_candidate,
    feature_analysis,
    find_spec,
    flatten_candidate_metrics,
    grouped_breakdown,
    leave_one_cow_out_analysis,
    load_contract,
    load_source_frame,
    save_and_reload_candidate,
    select_grouped_candidate,
    smoke_validate,
    utc_now,
    write_processed_task_frame,
)
from ml.training.metrics import json_safe


RUNNER_VERSION = "bangladesh_phase45d_runner_v1"
CANDIDATE_DIR = (
    FLASK_API_DIR / "ml" / "models" / "candidates" / "bangladesh"
)
SPLIT_MANIFEST_PATH = (
    ML_REPORTS_DIR / "bangladesh_group_split_manifest.csv"
)
SPLIT_REPORT_PATH = ML_REPORTS_DIR / "bangladesh_group_split_report.md"
LOCK_PATH = ML_REPORTS_DIR / "bangladesh_locked_model_selection.json"
HOLDOUT_PATH = (
    ML_REPORTS_DIR / "bangladesh_final_holdout_evaluation.md"
)
GROUP_SUMMARY_PATH = (
    ML_REPORTS_DIR / "bangladesh_group_validation_summary.json"
)
TRAINING_SUMMARY_PATH = (
    ML_REPORTS_DIR / "bangladesh_training_summary.json"
)
MODEL_COMPARISON_PATH = (
    ML_REPORTS_DIR / "bangladesh_model_comparison.md"
)
INTEGRATION_GATE_PATH = (
    PROJECT_ROOT / "documentation" / "bangladesh_integration_approval_gate.md"
)
AMENDMENT_PATH = (
    ML_REPORTS_DIR / "bangladesh_locked_model_selection_amendment.json"
)
PHYSIOLOGY_RESEARCH_PATH = (
    ML_REPORTS_DIR / "bangladesh_physiology_research_only.md"
)
PHYSIOLOGY_METRICS_PATH = (
    ML_REPORTS_DIR / "bangladesh_physiology_research_metrics.csv"
)


def _task_paths(task: str) -> dict[str, Path]:
    return {
        "metrics": (
            ML_REPORTS_DIR / f"bangladesh_{task}_candidate_metrics.csv"
        ),
        "model_report": (
            ML_REPORTS_DIR / f"bangladesh_{task}_model_report.md"
        ),
        "feature_analysis": (
            ML_REPORTS_DIR / f"bangladesh_{task}_feature_analysis.md"
        ),
        "artifact": (
            CANDIDATE_DIR
            / (
                "bangladesh_dmi_regressor_candidate_v1.joblib"
                if task == "dmi"
                else "bangladesh_milk_yield_regressor_candidate_v1.joblib"
            )
        ),
        "metadata": (
            CANDIDATE_DIR
            / (
                "bangladesh_dmi_regressor_candidate_v1.metadata.json"
                if task == "dmi"
                else "bangladesh_milk_yield_regressor_candidate_v1.metadata.json"
            )
        ),
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            json_safe(value),
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise BangladeshExperimentError(f"Refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _all_raw_hashes() -> dict[str, str]:
    return {
        name: sha256_file(SOURCE_DIR / name)
        for name in (
            METADATA_FILENAME,
            DMI_FILENAME,
            PHYSIOLOGY_FILENAME,
            BLOOD_FILENAME,
        )
    }


def _assert_training_scope() -> None:
    """Fail if feed classification or forbidden training calls appear here."""

    paths = [Path(__file__), Path(__file__).with_name("bangladesh_modeling.py")]
    forbidden_import_roots = {
        "flask",
        "tensorflow",
        "torch",
        "xgboost",
    }
    forbidden_names = {
        "DummyClassifier",
        "LogisticRegression",
        "DecisionTreeClassifier",
        "RandomForestClassifier",
        "HistGradientBoostingClassifier",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in forbidden_import_roots:
                        findings.append(f"import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".", 1)[0]
                if root in forbidden_import_roots:
                    findings.append(f"import:{node.module}")
                for alias in node.names:
                    if alias.name in forbidden_names:
                        findings.append(f"classifier:{alias.name}")
            elif isinstance(node, ast.Name) and node.id in forbidden_names:
                findings.append(f"classifier:{node.id}")
        if findings:
            raise BangladeshExperimentError(
                f"Forbidden training scope in {path}: {sorted(set(findings))}"
            )


def _prepare_output_lock(force_rerun: bool) -> None:
    """Protect prior locked results unless rerun is explicit and amended."""

    existing = [
        path for path in (LOCK_PATH, TRAINING_SUMMARY_PATH)
        if path.exists()
    ]
    if existing and not force_rerun:
        raise BangladeshExperimentError(
            "Bangladesh experiment outputs already exist. Use --force-rerun "
            "only for a documented controlled rerun."
        )
    if not force_rerun or not LOCK_PATH.exists():
        return
    old_lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    amendment = {
        "amendment_version": "bangladesh_selection_amendment_v1",
        "reason": (
            "Explicit --force-rerun requested. This archives the prior lock "
            "before any replacement and does not authorize integration."
        ),
        "created_at": utc_now(),
        "prior_lock_sha256": sha256_file(LOCK_PATH),
        "prior_lock": old_lock,
    }
    _write_json(AMENDMENT_PATH, amendment)
    LOCK_PATH.unlink()
    history = CANDIDATE_DIR / "history" / utc_now().replace(":", "-")
    candidates = [
        path for task in TASKS for path in (
            _task_paths(task)["artifact"],
            _task_paths(task)["metadata"],
        ) if path.exists()
    ]
    if candidates:
        history.mkdir(parents=True, exist_ok=True)
        for path in candidates:
            shutil.move(str(path), str(history / path.name))


def _distribution(
    manifest: pd.DataFrame,
    mask: pd.Series,
    field: str,
) -> str:
    values = (
        manifest.loc[mask, field].value_counts().sort_index().to_dict()
    )
    return ", ".join(f"{key}={value}" for key, value in values.items())


def _render_split_report(
    manifest: pd.DataFrame,
    validation: dict[str, Any],
) -> str:
    lines = [
        "# Bangladesh Group Split Report",
        "",
        "## Design",
        "",
        (
            "A fixed-seed `GroupShuffleSplit` creates a final 20% complete-cow "
            "holdout. Only the remaining development cows enter "
            "`GroupKFold(n_splits=5)`. Every observation from a cow remains "
            "in one partition and one validation fold."
        ),
        "",
        f"- Random seed: `{RANDOM_SEED}`.",
        (
            f"- Development: {validation['development_row_count']} rows / "
            f"{validation['development_cow_count']} cows."
        ),
        (
            f"- Final holdout: {validation['holdout_row_count']} rows / "
            f"{validation['holdout_cow_count']} cows."
        ),
        f"- Cow overlap: {validation['cow_overlap_count']}.",
        (
            "- Missing partition/fold assignments: "
            f"{validation['missing_partition_assignments']}/"
            f"{validation['missing_development_fold_assignments']}."
        ),
        "",
        "## Fold Inventory",
        "",
        "| Fold | Cows | Rows | THI distribution | Genetic distribution |",
        "|---:|---:|---:|---|---|",
    ]
    for fold in range(1, 6):
        mask = manifest["group_cv_fold"].eq(fold)
        lines.append(
            f"| {fold} | {manifest.loc[mask, 'cow_id'].nunique()} | "
            f"{int(mask.sum())} | {_distribution(manifest, mask, 'thi_category')} "
            f"| {_distribution(manifest, mask, 'genetic_group')} |"
        )
    holdout = manifest["partition"].eq("holdout")
    lines.extend(
        [
            "",
            "## Final Holdout",
            "",
            f"- Cow IDs: {', '.join(validation['holdout_cow_ids'])}.",
            f"- THI: {_distribution(manifest, holdout, 'thi_category')}.",
            (
                "- Genetic groups: "
                f"{_distribution(manifest, holdout, 'genetic_group')}."
            ),
            "",
            "## Leakage Checks",
            "",
            "- No cow appears in both development and holdout.",
            "- No development cow appears in more than one GroupKFold validation fold.",
            "- Holdout rows have no CV-fold assignment.",
            "- Replication number is lineage only, not a model feature.",
            "- Final holdout metrics are calculated only after the selection lock is written.",
        ]
    )
    return "\n".join(lines)


def _baseline_rows(evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item for item in evaluations
        if item["configuration"]["is_baseline"]
    ]


def _selected_metrics(task_result: dict[str, Any]) -> dict[str, Any] | None:
    selected = task_result["selection"]["selected"]
    return selected["aggregate_metrics"] if selected else None


def _render_task_report(task: str, result: dict[str, Any]) -> str:
    target = TASKS[task]["target"]
    unit = TASKS[task]["unit"]
    baselines = _baseline_rows(result["evaluations"])
    selected = result["selection"]["selected"]
    holdout = result.get("holdout")
    lines = [
        f"# Bangladesh {task.upper()} Model Report",
        "",
        "## Scope",
        "",
        f"- Target: `{target}` ({unit}).",
        "- Primary features: `genetic_group`, `thi_category`.",
        "- Group field: `cow_id`; cow ID is not predictive.",
        "- Selection: development-only five-fold GroupKFold.",
        "- Final evaluation: one untouched complete-cow holdout.",
        "",
        "## Grouped Baselines",
        "",
        "| Baseline | MAE | RMSE | R² | Median AE | Mean residual |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in baselines:
        metrics = item["aggregate_metrics"]
        lines.append(
            f"| `{item['configuration']['configuration_id']}` | "
            f"{metrics['mae']:.4f} | {metrics['rmse']:.4f} | "
            f"{metrics['r2']:.4f} | "
            f"{metrics['median_absolute_error']:.4f} | "
            f"{metrics['mean_residual']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Candidate Selection",
            "",
            f"- Status: `{result['selection']['selection_status']}`.",
            f"- Reason: {result['selection']['selection_reason']}",
        ]
    )
    if selected is None:
        lines.extend(
            [
                "- Locked candidate: `NONE`.",
                "",
                "## Final Holdout",
                "",
                "Not evaluated because no configuration passed the grouped gate.",
            ]
        )
        return "\n".join(lines)
    metrics = selected["aggregate_metrics"]
    gate = selected["selection_gate"]
    lines.extend(
        [
            (
                f"- Locked configuration: "
                f"`{selected['configuration']['configuration_id']}`."
            ),
            (
                f"- Group-CV MAE/RMSE/R²: {metrics['mae']:.4f} / "
                f"{metrics['rmse']:.4f} / {metrics['r2']:.4f}."
            ),
            (
                f"- Relative MAE/RMSE improvement: "
                f"{100 * gate['relative_mae_improvement_vs_best_baseline']:.2f}% "
                f"/ {100 * gate['relative_rmse_improvement_vs_best_baseline']:.2f}%."
            ),
            (
                f"- Fold MAE CV: "
                f"{selected['stability']['fold_mae_coefficient_of_variation']:.4f}; "
                f"all fold R² positive: "
                f"{selected['stability']['all_fold_r2_positive']}."
            ),
            "",
            "## Final Holdout",
            "",
        ]
    )
    if holdout is None:
        lines.append("Not evaluated.")
        return "\n".join(lines)
    configuration = holdout["selected_configuration"]
    candidate = holdout["evaluations"][configuration]["metrics"]
    lines.extend(
        [
            (
                f"- Unseen cows/rows: {holdout['holdout_cow_count']} / "
                f"{holdout['holdout_row_count']}."
            ),
            (
                f"- MAE/RMSE/R²: {candidate['mae']:.4f} / "
                f"{candidate['rmse']:.4f} / {candidate['r2']:.4f}."
            ),
            (
                f"- Median AE/mean residual: "
                f"{candidate['median_absolute_error']:.4f} / "
                f"{candidate['mean_residual']:.4f}."
            ),
            (
                f"- Prediction range: {candidate['minimum_prediction']:.4f}–"
                f"{candidate['maximum_prediction']:.4f}; negatives: "
                f"{candidate['negative_prediction_count']}."
            ),
            (
                f"- Relative MAE/RMSE improvement: "
                f"{100 * holdout['candidate_relative_mae_improvement']:.2f}% / "
                f"{100 * holdout['candidate_relative_rmse_improvement']:.2f}%."
            ),
            f"- Decision: `{holdout['decision']}`.",
            "",
            "## Controlled Leave-One-Cow-Out Analysis",
            "",
            (
                f"- Folds: {result['loco']['fold_count']}; aggregate "
                f"MAE/RMSE/R²: "
                f"{result['loco']['aggregate_metrics']['mae']:.4f} / "
                f"{result['loco']['aggregate_metrics']['rmse']:.4f} / "
                f"{result['loco']['aggregate_metrics']['r2']:.4f}."
            ),
            "",
            "## Holdout Breakdowns",
            "",
            "### By THI category",
            "",
            "| THI | Rows | MAE | RMSE | R² |",
            "|---|---:|---:|---:|---:|",
            *[
                f"| {item['thi_category']} | {item['rows']} | "
                f"{item['mae']:.4f} | {item['rmse']:.4f} | "
                f"{item['r2']:.4f} |"
                for item in result["holdout_by_thi"]
            ],
            "",
            "### By genetic group",
            "",
            "| Genetic group | Rows | MAE | RMSE | R² |",
            "|---|---:|---:|---:|---:|",
            *[
                f"| {item['genetic_group']} | {item['rows']} | "
                f"{item['mae']:.4f} | {item['rmse']:.4f} | "
                f"{item['r2']:.4f} |"
                for item in result["holdout_by_genetic_group"]
            ],
            "",
            "## Interpretation Boundary",
            "",
            (
                "Performance reflects in-study categorical group signal. It "
                "is not a causal effect, commercial validation, veterinary "
                "advice, or evidence that individual cow variation is fully "
                "captured."
            ),
        ]
    )
    return "\n".join(lines)


def _render_feature_report(task: str, result: dict[str, Any]) -> str:
    analysis = result["feature_analysis"]
    importance = {
        item["feature"]: item for item in analysis["importance"]
    }
    lines = [
        f"# Bangladesh {task.upper()} Feature Analysis",
        "",
        "## Method",
        "",
        analysis["method"],
        "",
        "## Permutation Importance",
        "",
        "| Feature | Mean MAE increase | SD |",
        "|---|---:|---:|",
    ]
    for item in analysis["importance"]:
        lines.append(
            f"| `{item['feature']}` | "
            f"{item['importance_mean_mae_increase']:.4f} | "
            f"{item['importance_standard_deviation']:.4f} |"
        )
    thi = importance["thi_category"]["importance_mean_mae_increase"]
    genetic = importance["genetic_group"][
        "importance_mean_mae_increase"
    ]
    lines.extend(
        [
            "",
            "## Findings",
            "",
            (
                f"- THI-category contribution is "
                f"`{'POSITIVE' if thi > 0 else 'NOT_DEMONSTRATED'}` under "
                f"holdout permutation (MAE increase {thi:.4f})."
            ),
            (
                f"- Genetic-group contribution is "
                f"`{'POSITIVE' if genetic > 0 else 'NOT_DEMONSTRATED'}` "
                f"(MAE increase {genetic:.4f})."
            ),
            (
                "- With only two categorical features, predictions primarily "
                "represent learned group-level differences. They do not "
                "capture individual cow state, ration, weight, DIM, BCS, or "
                "numeric weather variation."
            ),
            "",
            "## Category Prediction Summary",
            "",
            "| Genetic group | THI | Rows | Actual mean | Prediction mean |",
            "|---|---|---:|---:|---:|",
            *[
                f"| {item['genetic_group']} | {item['thi_category']} | "
                f"{item['rows']} | {item['actual_mean']:.4f} | "
                f"{item['prediction_mean']:.4f} |"
                for item in analysis["category_prediction_summary"]
            ],
            "",
            "## Boundary",
            "",
            (
                "Permutation importance is predictive and descriptive, not "
                "causal or biological evidence."
            ),
        ]
    )
    return "\n".join(lines)


def _clean_holdout(holdout: dict[str, Any] | None) -> dict[str, Any] | None:
    if holdout is None:
        return None
    return {
        key: value for key, value in holdout.items()
        if key not in {
            "selected_pipeline",
            "holdout_actual",
            "holdout_predictions",
            "holdout_frame",
        }
    }


def _metadata_payload(
    task: str,
    result: dict[str, Any],
    source_metadata: dict[str, Any],
    manifest_hash: str,
    contract: dict[str, Any],
    reload_check: dict[str, Any],
) -> dict[str, Any]:
    selected = result["selection"]["selected"]
    holdout = result["holdout"]
    configuration = selected["configuration"]
    holdout_metrics = holdout["evaluations"][
        configuration["configuration_id"]
    ]["metrics"]
    return {
        "artifact_status": "CANDIDATE_ONLY",
        "model_name": TASKS[task]["model_name"],
        "model_task": task,
        "model_algorithm": configuration["algorithm"],
        "hyperparameters": configuration["parameters"],
        "feature_order": PRIMARY_FEATURES,
        "target": TASKS[task]["target"],
        "target_definition": contract["models"][
            TASKS[task]["model_name"]
        ]["target_definition"],
        "dataset_source": "Bangladesh HF Cross",
        "synthetic_data": False,
        "study_dataset": "Bangladesh HF Cross",
        "dataset_checksum": source_metadata["source_sha256"],
        "dataset_doi": contract["dataset"]["doi"],
        "dataset_licence": contract["dataset"]["licence"],
        "dataset_citation": (
            "Pehan Eshtiak Ahamed (2026), Physiological responses, Dry "
            "matter Intake, milk yield, composition and blood metabolites "
            "of HF Cross cows, Mendeley Data V2, "
            "doi:10.17632/954f6g36sb.2"
        ),
        "number_of_unique_cows": 50,
        "development_cow_count": holdout["development_cow_count"],
        "final_holdout_cow_count": holdout["holdout_cow_count"],
        "repeated_measurements": True,
        "observations_per_cow": 15,
        "group_validation_method": (
            "GroupKFold(n_splits=5) by cow_id on development cows; "
            "LeaveOneGroupOut sensitivity analysis"
        ),
        "final_holdout_method": (
            "GroupShuffleSplit(test_size=0.20, random_state=42) by cow_id"
        ),
        "split_manifest_sha256": manifest_hash,
        "group_validation_metrics": selected["aggregate_metrics"],
        "holdout_metrics": holdout_metrics,
        "holdout_gate_passed": holdout["holdout_gate_passed"],
        "random_seed": RANDOM_SEED,
        "contract_version": contract["contract_version"],
        "production_approved": False,
        "commercial_use_approved": False,
        "veterinary_use_approved": False,
        "known_limitations": contract["known_limitations"],
        "reload_check": reload_check,
        "created_at": utc_now(),
    }


def _validate_metadata(value: dict[str, Any]) -> None:
    required = {
        "artifact_status",
        "model_name",
        "feature_order",
        "target",
        "dataset_source",
        "synthetic_data",
        "number_of_unique_cows",
        "repeated_measurements",
        "group_validation_method",
        "holdout_metrics",
        "production_approved",
        "commercial_use_approved",
        "veterinary_use_approved",
        "known_limitations",
        "reload_check",
    }
    missing = required - set(value)
    if missing:
        raise BangladeshExperimentError(
            f"Candidate metadata missing: {sorted(missing)}"
        )
    if value["artifact_status"] != "CANDIDATE_ONLY":
        raise BangladeshExperimentError("Candidate status changed")
    if any(
        value[key] is not False for key in (
            "production_approved",
            "commercial_use_approved",
            "veterinary_use_approved",
        )
    ):
        raise BangladeshExperimentError("Candidate approval flag is not false")
    if value["synthetic_data"] is not False:
        raise BangladeshExperimentError("Bangladesh data marked synthetic")
    if value["number_of_unique_cows"] != 50:
        raise BangladeshExperimentError("Candidate cow count changed")
    if value["repeated_measurements"] is not True:
        raise BangladeshExperimentError("Repeated-measure flag changed")


def _render_holdout_report(task_results: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Bangladesh Final Complete-Cow Holdout Evaluation",
        "",
        (
            "Selections were locked before this evaluation. The holdout "
            "contains complete cows never used in candidate selection or "
            "development fitting."
        ),
        "",
        "| Task | Baseline | Selected model | Group-CV result | Holdout result | Decision |",
        "|---|---|---|---|---|---|",
    ]
    for task, result in task_results.items():
        selected = result["selection"]["selected"]
        if selected is None:
            lines.append(
                f"| {task.upper()} | Mean + median | None | No grouped "
                "candidate passed | Not evaluated | `DOES_NOT_BEAT_BASELINE` |"
            )
            continue
        holdout = result["holdout"]
        metrics = holdout["evaluations"][
            holdout["selected_configuration"]
        ]["metrics"]
        cv = selected["aggregate_metrics"]
        lines.append(
            f"| {task.upper()} | Mean + median | "
            f"`{holdout['selected_configuration']}` | "
            f"MAE {cv['mae']:.4f}, R² {cv['r2']:.4f} | "
            f"MAE {metrics['mae']:.4f}, R² {metrics['r2']:.4f} | "
            f"`{holdout['decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                "Positive in-study holdout performance does not establish "
                "production, commercial, veterinary, or cross-population "
                "validity."
            ),
        ]
    )
    return "\n".join(lines)


def _comparison_answers(task_results: dict[str, dict[str, Any]]) -> list[str]:
    def passed(task: str) -> bool:
        value = task_results.get(task)
        return bool(value and value.get("holdout")
                    and value["holdout"]["holdout_gate_passed"])

    dmi_passed = passed("dmi")
    milk_passed = passed("milk")
    stable = all(
        result["selection"]["selected"] is not None
        and result["selection"]["selected"]["selection_gate"][
            "stable_across_grouped_folds"
        ]
        for result in task_results.values()
    )
    return [
        f"1. Does DMI beat its grouped baseline? **{'Yes' if dmi_passed else 'No'}**.",
        f"2. Does milk yield beat its grouped baseline? **{'Yes' if milk_passed else 'No'}**.",
        f"3. Are results stable across cows? **{'Grouped-fold stability passed' if stable else 'No or incomplete'}**; LOCO and per-cow metrics remain part of the uncertainty record.",
        "4. Does THI add signal? See the task feature reports; importance is predictive, not causal.",
        "5. Does genetic group add signal? See the task feature reports; much of the model is group-average structure.",
        f"6. Do results generalize to unseen cows? **{'Within this study holdout, yes' if dmi_passed or milk_passed else 'Not demonstrated'}**; external populations are untested.",
        f"7. Suitable for integration review? **{'Candidate review only' if dmi_passed or milk_passed else 'No'}**; never automatic integration.",
        f"8. Feed-quantity restoration? **{'Prototype DMI prediction restored with limitations' if dmi_passed else 'No'}**; ration selection and ingredient quantities remain absent.",
        "9. Limitations: 50 cows, categorical THI only, incomplete DMI protocol, two categorical inputs, no commercial validation, and no expert feed labels.",
        "10. Synthetic milk candidate: retain unchanged and compare further as a separate-provenance prototype; do not replace it automatically.",
    ]


def _integration_recommendation(
    task_results: dict[str, dict[str, Any]],
) -> str:
    passed = {
        task: bool(
            result.get("holdout")
            and result["holdout"]["holdout_gate_passed"]
            and result.get("artifact_reload", {}).get(
                "reload_predictions_identical"
            )
        )
        for task, result in task_results.items()
    }
    if passed.get("dmi") and passed.get("milk"):
        return "READY_FOR_DMI_AND_MILK_INTEGRATION_REVIEW"
    if passed.get("dmi"):
        return "READY_FOR_DMI_INTEGRATION_REVIEW"
    if passed.get("milk"):
        return "READY_FOR_MILK_INTEGRATION_REVIEW"
    return "MODEL_REDESIGN_REQUIRED"


def _render_integration_gate(
    task_results: dict[str, dict[str, Any]],
    protected_unchanged: bool,
) -> str:
    def task_status(task: str) -> tuple[str, str]:
        result = task_results.get(task)
        if not result or not result.get("holdout"):
            return "FAIL", "No locked holdout result"
        holdout = result["holdout"]
        metrics = holdout["evaluations"][
            holdout["selected_configuration"]
        ]["metrics"]
        return (
            "PASS" if holdout["holdout_gate_passed"] else "FAIL",
            (
                f"Holdout R²={metrics['r2']:.4f}; MAE improvement="
                f"{100 * holdout['candidate_relative_mae_improvement']:.2f}%"
            ),
        )
    dmi_status, dmi_evidence = task_status("dmi")
    milk_status, milk_evidence = task_status("milk")
    reload_pass = all(
        result.get("artifact_reload", {}).get(
            "reload_predictions_identical", False
        )
        for result in task_results.values()
        if result.get("holdout") and result["holdout"]["holdout_gate_passed"]
    )
    recommendation = _integration_recommendation(task_results)
    rows = [
        ("DMI beats grouped baseline", dmi_status, dmi_evidence, "Review candidate limitations."),
        ("DMI generalizes to unseen cows", dmi_status, dmi_evidence, "Require external/population validation before production."),
        ("Milk beats grouped baseline", milk_status, milk_evidence, "Review candidate limitations."),
        ("Milk generalizes to unseen cows", milk_status, milk_evidence, "Require external/population validation before production."),
        ("Cow leakage prevented", "PASS", "GroupShuffleSplit + GroupKFold; zero overlap", "Preserve cow grouping in every future run."),
        ("Feature timing defensible", "PASS_WITH_LIMITATIONS", "Genetic group and derived THI category are pre-prediction concepts", "Specify and validate runtime THI derivation before integration."),
        ("Candidate artifacts reload", "PASS" if reload_pass else "FAIL", f"Exact prediction equality={reload_pass}", "Do not review a failed artifact."),
        ("Existing models preserved", "PASS" if protected_unchanged else "FAIL", f"Protected hash equality={protected_unchanged}", "Stop if any protected file differs."),
        ("Dataset licence documented", "PASS", "CC BY 4.0; DOI 10.17632/954f6g36sb.2", "Retain attribution with artifacts."),
        ("Integration not performed", "PASS", "No runtime, route, frontend, PDF, or nutrition changes", "Require explicit approval for any integration."),
    ]
    return "\n".join(
        [
            "# Bangladesh Integration Approval Gate",
            "",
            "| Check | Status | Evidence | Required action |",
            "|---|---|---|---|",
            *[
                f"| {check} | `{status}` | {evidence} | {action} |"
                for check, status, evidence, action in rows
            ],
            "",
            "## Future FarmLite THI-Category Derivation",
            "",
            (
                "A future, separately approved request adapter may calculate "
                "THI from farmer-provided dry-bulb temperature `T` (°C) and "
                "relative humidity `RH` (%) using the study article's cited "
                "formula:"
            ),
            "",
            (
                "`THI = (1.8 × T + 32) − [(0.55 − 0.0055 × RH) × "
                "(1.8 × T − 26)]`"
            ),
            "",
            (
                "Map the result to the source categories exactly: "
                "`T0` for THI ≤75, `T1` for 75<THI<80, and `T2` for THI ≥80. "
                "Validate input units and boundary behavior before use. Do "
                "not invent a numeric THI for historical rows and do not "
                "back-calculate temperature or humidity from category labels."
            ),
            "",
            (
                "Source: Pehan et al., *Effects of cyclic "
                "temperature-humidity index on milk production, physiological "
                "and haematobiochemical responses in Holstein-Friesian cows "
                "of varied genetic proportions*, DOI "
                "`10.1016/j.anopes.2026.100139`."
            ),
            "",
            f"## Final Recommendation: `{recommendation}`",
            "",
            (
                "This is an integration-review recommendation only. It is not "
                "production, commercial, veterinary, deployment, or automatic "
                "integration approval."
            ),
        ]
    )


def _run_optional_physiology(
    source_frame: pd.DataFrame,
    tasks: list[str],
) -> dict[str, Any]:
    """Run a separate 45-cow, research-only physiology ablation."""

    physiology_workbook = read_xlsx(SOURCE_DIR / PHYSIOLOGY_FILENAME)
    physiology = dataframe_from_sheet(physiology_workbook.sheets[0])
    physiology_view = pd.DataFrame(
        {
            "cow_id": physiology["Animal ID"].map(canonical_cow_id),
            "thi_category": physiology["THI Range"].map(canonical_thi),
            "replication": pd.to_numeric(
                physiology["Replication No"], errors="raise"
            ).astype(int),
            "rectal_temperature_f": pd.to_numeric(
                physiology["Rectal Temp (F)"], errors="raise"
            ),
            "pulse_rate_per_min": pd.to_numeric(
                physiology["Pulse Rate (bpm)"], errors="raise"
            ),
            "respiration_rate_per_min": pd.to_numeric(
                physiology["Respiration Rate (bpm)"], errors="raise"
            ),
        }
    )
    results = {}
    for task in tasks:
        primary = build_task_frame(source_frame, task)
        joined = primary.merge(
            physiology_view,
            on=["cow_id", "thi_category", "replication"],
            how="inner",
            validate="one_to_one",
        )
        if len(joined) != 675 or joined["cow_id"].nunique() != 45:
            raise BangladeshExperimentError(
                "Physiology research join is not the audited 675 rows/45 cows"
            )
        assignments = create_group_assignments(joined)
        features = [
            *PRIMARY_FEATURES,
            "rectal_temperature_f",
            "pulse_rate_per_min",
            "respiration_rate_per_min",
        ]
        specs = candidate_specs(task)
        selected_spec = next(
            item for item in specs
            if item.algorithm == "Ridge" and item.parameters == {"alpha": 1.0}
        )
        evaluations = [
            evaluate_grouped_candidate(
                joined,
                task,
                spec,
                assignments["cv_splits"],
                features,
            )
            for spec in (specs[0], specs[1], selected_spec)
        ]
        selection = select_grouped_candidate(evaluations)
        results[task] = {
            "artifact_status": "RESEARCH_ONLY",
            "rows": len(joined),
            "cows": int(joined["cow_id"].nunique()),
            "features": features,
            "join_key": "cow_id + thi_category + replication",
            "selection": selection,
            "timing_warning": (
                "Physiological values may be same-day/post-outcome and are not "
                "available in normal FarmLite inference."
            ),
        }
    rows = []
    for task, result in results.items():
        selected = result["selection"]["selected"]
        rows.append(
            {
                "task": task,
                "artifact_status": "RESEARCH_ONLY",
                "rows": result["rows"],
                "cows": result["cows"],
                "configuration": (
                    selected["configuration"]["configuration_id"]
                    if selected else "NONE"
                ),
                "group_cv_mae": (
                    selected["aggregate_metrics"]["mae"] if selected else None
                ),
                "group_cv_rmse": (
                    selected["aggregate_metrics"]["rmse"] if selected else None
                ),
                "group_cv_r2": (
                    selected["aggregate_metrics"]["r2"] if selected else None
                ),
            }
        )
    _write_csv(PHYSIOLOGY_METRICS_PATH, rows)
    _write_text(
        PHYSIOLOGY_RESEARCH_PATH,
        "\n".join(
            [
                "# Bangladesh Physiology Ablation — RESEARCH ONLY",
                "",
                "- Explicit composite-key inner join: 675 rows / 45 cows.",
                "- No row-order join.",
                "- Grouped by cow.",
                "- Not part of the primary model contract.",
                "- Not available in normal FarmLite inference.",
                "- Timing relative to DMI/milk remains unresolved.",
                "",
                *[
                    f"- {task.upper()}: `{row['configuration']}`, grouped "
                    f"R²={row['group_cv_r2']}."
                    for task, row in zip(results, rows, strict=True)
                ],
            ]
        ),
    )
    return results


def run_experiments(
    *,
    selected_task: str | None = None,
    include_research_physiology: bool = False,
    force_rerun: bool = False,
) -> dict[str, Any]:
    """Run grouped selection, lock it, then inspect final holdout exactly once."""

    _assert_training_scope()
    _prepare_output_lock(force_rerun)
    contract = load_contract()
    raw_before = _all_raw_hashes()
    expected = {
        name: EXPECTED_SHA256[name] for name in raw_before
    }
    if raw_before != expected:
        raise BangladeshExperimentError(
            f"Bangladesh raw checksums changed: {raw_before}"
        )
    protected_before = _protected_snapshot()
    source_frame, source_metadata = load_source_frame()
    tasks = [selected_task] if selected_task else list(TASKS)
    frames = {
        task: build_task_frame(source_frame, task) for task in tasks
    }
    processed_paths = {
        task: write_processed_task_frame(frame, task)
        for task, frame in frames.items()
    }

    # Targets are not consulted by this deterministic grouping step.
    first_task = tasks[0]
    assignments = create_group_assignments(frames[first_task])
    manifest = assignments["manifest"]
    SPLIT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(SPLIT_MANIFEST_PATH, index=False)
    manifest_hash = sha256_file(SPLIT_MANIFEST_PATH)
    _write_text(
        SPLIT_REPORT_PATH,
        _render_split_report(manifest, assignments["validation"]),
    )

    task_results: dict[str, dict[str, Any]] = {}
    for task, frame in frames.items():
        evaluations = [
            evaluate_grouped_candidate(
                frame,
                task,
                spec,
                assignments["cv_splits"],
            )
            for spec in candidate_specs(task)
        ]
        selection = select_grouped_candidate(evaluations)
        _write_csv(
            _task_paths(task)["metrics"],
            flatten_candidate_metrics(evaluations),
        )
        task_results[task] = {
            "evaluations": evaluations,
            "selection": selection,
        }

    # Lock selection before any call that calculates holdout metrics.
    lock = {
        "lock_version": "bangladesh_locked_selection_v1",
        "runner_version": RUNNER_VERSION,
        "selected_dmi_configuration": (
            task_results["dmi"]["selection"]["selected"][
                "configuration"
            ]["configuration_id"]
            if "dmi" in task_results
            and task_results["dmi"]["selection"]["selected"]
            else None
        ),
        "selected_milk_configuration": (
            task_results["milk"]["selection"]["selected"][
                "configuration"
            ]["configuration_id"]
            if "milk" in task_results
            and task_results["milk"]["selection"]["selected"]
            else None
        ),
        "group_validation_metrics": {
            task: _selected_metrics(result)
            for task, result in task_results.items()
        },
        "selection_reasons": {
            task: result["selection"]["selection_reason"]
            for task, result in task_results.items()
        },
        "cow_grouping_method": (
            "GroupShuffleSplit final cow holdout; GroupKFold(n_splits=5) "
            "on development cows"
        ),
        "random_seed": RANDOM_SEED,
        "dataset_checksum": source_metadata["source_sha256"],
        "split_manifest_sha256": manifest_hash,
        "contract_version": contract["contract_version"],
        "selection_timestamp": utc_now(),
        "holdout_metrics_evaluated_before_lock": False,
        "holdout_cows_used_in_model_selection": False,
    }
    if LOCK_PATH.exists():
        raise BangladeshExperimentError(
            "Selection lock exists at write boundary"
        )
    _write_json(LOCK_PATH, lock)
    lock_hash = sha256_file(LOCK_PATH)

    # Final holdout begins only below this boundary.
    for task, result in task_results.items():
        selected = result["selection"]["selected"]
        if selected is None:
            result["holdout"] = None
            result["loco"] = None
            continue
        selected_spec = find_spec(
            task, selected["configuration"]["configuration_id"]
        )
        holdout = evaluate_final_holdout(
            frames[task],
            task,
            assignments["development_indices"],
            assignments["holdout_indices"],
            selected_spec,
        )
        result["holdout"] = holdout
        result["loco"] = leave_one_cow_out_analysis(
            frames[task],
            task,
            assignments["development_indices"],
            selected_spec,
        )
        holdout_frame = holdout["holdout_frame"].reset_index(drop=True)
        result["holdout_by_thi"] = grouped_breakdown(
            holdout_frame,
            holdout["holdout_actual"],
            holdout["holdout_predictions"],
            "thi_category",
        )
        result["holdout_by_genetic_group"] = grouped_breakdown(
            holdout_frame,
            holdout["holdout_actual"],
            holdout["holdout_predictions"],
            "genetic_group",
        )
        result["holdout_by_cow"] = grouped_breakdown(
            holdout_frame,
            holdout["holdout_actual"],
            holdout["holdout_predictions"],
            "cow_id",
        )
        result["feature_analysis"] = feature_analysis(
            holdout["selected_pipeline"],
            holdout_frame,
            task,
        )
        if holdout["holdout_gate_passed"]:
            paths = _task_paths(task)
            reload_check = save_and_reload_candidate(
                holdout["selected_pipeline"],
                paths["artifact"],
                holdout_frame[PRIMARY_FEATURES].head(30),
            )
            metadata = _metadata_payload(
                task,
                result,
                source_metadata,
                manifest_hash,
                contract,
                reload_check,
            )
            _validate_metadata(metadata)
            _write_json(paths["metadata"], metadata)
            result["artifact_reload"] = reload_check
            result["candidate_metadata"] = metadata
        else:
            result["artifact_reload"] = {
                "saved": False,
                "reason": "Final complete-cow holdout gate did not pass.",
            }
        _write_text(
            _task_paths(task)["feature_analysis"],
            _render_feature_report(task, result),
        )

    for task, result in task_results.items():
        _write_text(
            _task_paths(task)["model_report"],
            _render_task_report(task, result),
        )
    _write_text(HOLDOUT_PATH, _render_holdout_report(task_results))

    physiology_result = (
        _run_optional_physiology(source_frame, tasks)
        if include_research_physiology
        else {
            "status": "NOT_RUN",
            "reason": (
                "Optional research-only ablation was not requested; "
                "physiology is excluded from primary models."
            ),
        }
    )

    group_summary = {
        "summary_version": "bangladesh_group_validation_summary_v1",
        "created_at": utc_now(),
        "split_validation": assignments["validation"],
        "split_manifest_sha256": manifest_hash,
        "selection_lock_sha256": lock_hash,
        "tasks": {
            task: {
                "selected_configuration": (
                    result["selection"]["selected"]["configuration"][
                        "configuration_id"
                    ]
                    if result["selection"]["selected"] else None
                ),
                "group_validation_metrics": _selected_metrics(result),
                "selection_status": result["selection"]["selection_status"],
                "fold_metrics": (
                    result["selection"]["selected"]["fold_metrics"]
                    if result["selection"]["selected"] else []
                ),
                "leave_one_cow_out": result["loco"],
            }
            for task, result in task_results.items()
        },
    }
    _write_json(GROUP_SUMMARY_PATH, group_summary)

    raw_after = _all_raw_hashes()
    protected_after = _protected_snapshot()
    if raw_before != raw_after:
        raise BangladeshExperimentError("Bangladesh raw source changed")
    if protected_before != protected_after:
        changed = sorted(
            key for key in protected_before
            if protected_before[key] != protected_after[key]
        )
        raise BangladeshExperimentError(
            "Protected project state changed: " + ", ".join(changed)
        )

    recommendation = _integration_recommendation(task_results)
    _write_text(
        MODEL_COMPARISON_PATH,
        "\n".join(
            [
                "# Bangladesh Model Comparison",
                "",
                *[
                    f"## {answer.split('. ', 1)[0]}\n\n"
                    f"{answer.split('. ', 1)[1]}"
                    for answer in _comparison_answers(task_results)
                ],
                "",
                f"## Recommendation\n\n`{recommendation}`",
                "",
                (
                    "No existing or candidate synthetic model was replaced. "
                    "No integration was performed."
                ),
            ]
        ),
    )
    _write_text(
        INTEGRATION_GATE_PATH,
        _render_integration_gate(task_results, True),
    )
    summary = {
        "summary_version": "bangladesh_training_summary_v1",
        "runner_version": RUNNER_VERSION,
        "status": "COMPLETED_CONTROLLED_EXPERIMENT",
        "created_at": utc_now(),
        "contract_version": contract["contract_version"],
        "dataset_source": source_metadata,
        "dataset_licence": contract["dataset"]["licence"],
        "dataset_doi": contract["dataset"]["doi"],
        "raw_hashes_before": raw_before,
        "raw_hashes_after": raw_after,
        "raw_files_unchanged": raw_before == raw_after,
        "protected_files_unchanged": protected_before == protected_after,
        "feature_order": PRIMARY_FEATURES,
        "grouping_field": "cow_id",
        "split_validation": assignments["validation"],
        "split_manifest_sha256": manifest_hash,
        "selection_lock_sha256": lock_hash,
        "processed_files": {
            task: {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "sha256": sha256_file(path),
                "rows": len(frames[task]),
                "columns": list(frames[task].columns),
            }
            for task, path in processed_paths.items()
        },
        "tasks": {
            task: {
                "selection": {
                    key: value
                    for key, value in result["selection"].items()
                    if key != "selected"
                },
                "selected_configuration": (
                    result["selection"]["selected"]["configuration"][
                        "configuration_id"
                    ]
                    if result["selection"]["selected"] else None
                ),
                "group_validation_metrics": _selected_metrics(result),
                "holdout": _clean_holdout(result["holdout"]),
                "holdout_by_thi": result.get("holdout_by_thi", []),
                "holdout_by_genetic_group": result.get(
                    "holdout_by_genetic_group", []
                ),
                "holdout_by_cow": result.get("holdout_by_cow", []),
                "feature_analysis": result.get("feature_analysis"),
                "artifact_reload": result.get("artifact_reload"),
                "candidate_metadata_path": (
                    str(_task_paths(task)["metadata"].relative_to(PROJECT_ROOT))
                    if _task_paths(task)["metadata"].is_file() else None
                ),
            }
            for task, result in task_results.items()
        },
        "physiology_research_experiment": physiology_result,
        "feed_type_model_trained": False,
        "source_datasets_concatenated": False,
        "holdout_cows_used_in_selection": False,
        "integration_performed": False,
        "production_model_replaced": False,
        "integration_readiness_recommendation": recommendation,
    }
    _write_json(TRAINING_SUMMARY_PATH, summary)
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run controlled Bangladesh DMI/milk experiments."
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Run development-only smoke validation; write no model artifact.",
    )
    parser.add_argument(
        "--task",
        choices=sorted(TASKS),
        help="Run only one approved regression task.",
    )
    parser.add_argument(
        "--include-research-physiology",
        action="store_true",
        help="Run the separate 45-cow research-only physiology ablation.",
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Explicitly rerun and document replacement of prior outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.smoke_only:
            result = smoke_validate()
            print(
                "BANGLADESH_SMOKE_PASSED "
                f"tasks={','.join(result['tasks'])} "
                f"holdout_inspected={result['holdout_targets_inspected']}",
                flush=True,
            )
            return 0
        result = run_experiments(
            selected_task=args.task,
            include_research_physiology=args.include_research_physiology,
            force_rerun=args.force_rerun,
        )
    except Exception as error:
        print(
            f"BANGLADESH_EXPERIMENT_FAILED: {type(error).__name__}: {error}",
            file=sys.stderr,
            flush=True,
        )
        return 1
    decisions = {
        task: item["holdout"]["decision"]
        if item["holdout"] else "NO_SELECTION"
        for task, item in result["tasks"].items()
    }
    print(
        "BANGLADESH_EXPERIMENT_PASSED "
        f"decisions={json.dumps(decisions, sort_keys=True)} "
        f"recommendation={result['integration_readiness_recommendation']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
