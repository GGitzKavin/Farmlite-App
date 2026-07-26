# FarmLite Phase 4 Model-Training Approval Gate

## Recommendation

**READY_FOR_PHASE_4_WITH_LIMITATIONS**

This recommendation records that the reusable preprocessing boundary passed
Phase 3 validation. It does not authorize model training. Phase 4 may begin
only after explicit owner approval.

| Check | Status | Evidence | Required action |
|---|---|---|---|
| Raw dataset preserved | `PASSED` | Primary SHA-256 `26D6D08F...1B3`; disease SHA-256 `4CEDFA77...C4B9`; both match the Phase 3 baseline | Continue read-only use |
| Canonical mapping validated | `PASSED` | 19 approved primary columns mapped; 18 unmapped columns preserved; zero ambiguous aliases | Keep alias changes versioned and owner-approved |
| Training schema validated | `PASSED` | All nine features and all three targets are present and convertible; zero hard-invalid schema findings | Revalidate before each future training run |
| Model 1 features validated | `PASSED` | Exact nine-feature order built; `feed_type` separated from X | Use the committed feature builder |
| Model 2 Design A features validated | `PASSED` | Exact nine-feature order built; `feed_quantity_kg` separated from X | Use the same base split and preprocessing boundary |
| Model 2 Design B interface validated | `PASSED_WITH_LIMITATIONS` | Builder is disabled by default, requires explicit `predicted_feed_type`, and refuses true same-row `feed_type` substitution | Phase 4 must implement genuine out-of-fold predictions before Design B can train |
| Model 3 features validated | `PASSED` | Exact nine-feature order built; current `milk_yield_l` excluded; previous-week yield retained as historical input | Preserve the lagged meaning |
| Own targets excluded from inputs | `PASSED` | Automated feature-builder and artifact tests passed | Keep target-leakage tests mandatory |
| Identifier leakage excluded | `PASSED` | Cattle/farm IDs, dates, and row numbers are absent from every X frame | Retain identifiers only in traceability manifests |
| Split manifest deterministic | `PASSED` | 175,000/37,500/37,500; seed 42; repeated SHA-256 `A7C206B0...DADFB` | Freeze the manifest for comparable experiments |
| OOF fold manifest deterministic | `PASSED` | Five folds of 35,000 training rows; repeated SHA-256 `B1B546A1...77EB1`; validation/test excluded | Use these folds only for future cross-fitting |
| Unknown-category handling tested | `PASSED` | Unknown breed and `Dry` warn and transform without false remapping or crashing | Surface warnings in a later approved integration phase |
| Missing-value handling tested | `PASSED` | Tiny training fixtures confirm numeric and categorical imputation and no NaN output | Fit statistics on training rows only |
| Existing tests pass | `PASSED_WITH_LIMITATIONS` | 72/72 tests passed with `unittest`; pytest is not installed and was not added without approval | Optionally approve pytest installation later; no test failure is hidden |
| Synthetic-data limitation documented | `PASSED_WITH_LIMITATIONS` | Validation report and implementation guide state publisher-declared synthetic, prototype-only use | Carry the disclaimer into every future model/report |
| Model training not yet executed | `PASSED` | No classifier/regressor fit, comparison, evaluation, prediction generation, or new model artifact occurred | Wait for explicit Phase 4 approval |

## Phase 3 Evidence

- `backend/flask_api/ml/reports/preprocessing_validation_report.md`
- `backend/flask_api/ml/reports/data_split_summary.json`
- `backend/flask_api/ml/reports/data_split_report.md`
- `backend/flask_api/ml/reports/feed_type_oof_fold_summary.json`
- `documentation/preprocessing_implementation_guide.md`

## Remaining Limitations

- The Kaggle license has not been confirmed.
- Detailed synthetic-data generation formulas are unavailable.
- `Feed_Quantity_kg` material basis and measurement period are unvalidated.
- `Milk_Yield_L` measurement period and zero meaning are unvalidated.
- The training data is not verified dairy-only.
- Strategy A therefore remains an all-synthetic-cattle prototype strategy.
- An explicit training experiment plan, metrics, baselines, and candidate-model
  scope still require Phase 4 approval.

## Exact Next Proposed Action

Review the Phase 3 evidence and approve or revise a narrowly scoped Phase 4
training plan. Do not run a classifier, regressor, hyperparameter search, model
comparison, prediction generation, or persistence command before that
approval.
