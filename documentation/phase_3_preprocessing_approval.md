# FarmLite Phase 3 Preprocessing Approval Gate

## Current Decision

**READY_FOR_PHASE_3_PREPROCESSING_WITH_LIMITATIONS**

Phase 3 may implement reusable preprocessing after explicit owner approval. It
must not train, evaluate, save, replace, or deploy a model unless a later phase
explicitly authorizes those actions.

## Approval Table

| Check | Status | Evidence | Required action |
|---|---|---|---|
| Dataset source documented | `PASSED_WITH_LIMITATIONS` | `Cattle Health and Feeding Data`; Kaggle account `ShahHet2812`; human-readable source and local download metadata recorded | Confirm license and capture detailed generation/data-dictionary information if available |
| Synthetic status documented | `PASSED` | Publisher declares the dataset synthetically generated and potentially unrepresentative of real-world data | Carry the synthetic/prototype disclaimer into every future artifact and report |
| Target columns available | `PASSED_WITH_LIMITATIONS` | `Feed_Type`, `Feed_Quantity_kg`, and `Milk_Yield_L` exist with 0% missing values | Use only synthetic-target interpretations; preserve unresolved feed basis and milk period |
| Feature availability mapped | `PASSED` | Nine selected features exist in the primary CSV and current request flow | Implement exact canonical mapping and optional-field flags |
| Leakage fields excluded | `PASSED` | Feature matrix excludes targets from inputs, identifiers, dates, disease outcomes, and same-record unavailable outcomes | Add automated schema/leakage tests in Phase 3 |
| Frontend/model mismatch identified | `PASSED` | Parity, season, climate, and management are CSV-only; health is app-only; UI `Dry` lacks a dataset class; animal type is not currently sent | Preserve exclusions and reject/resolve unsupported `Dry`; do not add fields during Phase 3 |
| Dairy-scope limitation documented | `PASSED_WITH_LIMITATIONS` | Interim Strategy A and required honesty wording are documented | Use all synthetic rows without calling the training data dairy-only; do not apply a breed filter |
| API input contract defined | `PASSED` | `documentation/ml_api_input_contract.md` defines required, optional, derived, and unsupported fields | Do not implement route/frontend changes during preprocessing |
| Model output contract defined | `PASSED` | `documentation/ml_api_output_contract.md` separates synthetic ML targets and rule-derived outputs | Do not implement response changes during preprocessing |
| Model training still disabled | `PASSED` | Model contract status is `DESIGN_ONLY_NO_TRAINING_AUTHORIZED`; Phase 2 ran no training | Keep training entry points out of Phase 3 execution and tests |

## Required Conditions Review

### Features explicitly selected

Selected for all three model tasks:

- `breed`;
- `age_months`;
- `weight_kg`;
- `lactation_stage`;
- `days_in_milk`;
- `previous_week_avg_yield_l`;
- `body_condition_score`;
- `ambient_temperature_c`;
- `humidity_percent`.

Feed Quantity Design B additionally uses `predicted_feed_type` under an
out-of-fold requirement.

Status: **SATISFIED**

### Targets explicitly synthetic

- Model 1: synthetic feed-category label;
- Model 2: synthetic feed-quantity target;
- Model 3: synthetic milk-yield target.

Status: **SATISFIED**

### Leakage exclusions defined

Targets, identifiers, direct row indices, current/future outcomes, disease
outcomes, treatment outcomes, and unavailable true feed type in Design B are
excluded.

Status: **SATISFIED**

### Prediction-time availability documented

All nine selected base features are present in the current request. Required
versus optional behaviour and missing policies are documented.

Status: **SATISFIED**

### Application mismatches documented

The field and category mismatches are recorded in:

- `documentation/current_input_inventory.md`;
- `backend/flask_api/ml/reports/feature_decision_matrix.csv`;
- `documentation/ml_api_input_contract.md`.

Status: **SATISFIED**

### Misleading implementation risk

The preprocessing design remains honest if it:

- labels every target synthetic;
- does not call the CSV dairy-only;
- does not map `Dry` silently;
- does not infer missing CSV-only fields;
- does not use target/leakage fields;
- does not train models;
- does not imply real-world nutrition validity.

Status: **CONTROLLED_WITH_LIMITATIONS**

## Remaining Non-Blocking Phase 3 Limitations

- Kaggle license confirmation is pending.
- Detailed synthetic generation formulas are unavailable.
- Feed quantity basis/period remains unvalidated.
- Milk-yield period and zero meaning remain unvalidated.
- No documented dairy breed filter exists.

These prevent stronger scientific claims and remain training/publication gates.
They do not prevent building a transparent, read-only preprocessing pipeline
for the explicitly synthetic prototype.

## Exact Next Action After Approval

Implement only the Phase 3 reusable loader, canonical mapper, schema validator,
model-specific feature builders, deterministic split manifest, preprocessing
pipelines, and focused tests described in
`documentation/preprocessing_design.md`.

Stop again before any model training command.
