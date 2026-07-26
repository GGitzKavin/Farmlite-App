# FarmLite Preprocessing Validation Report

## Executive Summary

**READY_FOR_PHASE_4_WITH_LIMITATIONS**

Phase 3 preprocessing, deterministic split assignment, and training-only fold preparation passed their internal checks. No classifier or regressor was trained, no prediction was generated, and this status does not authorize Phase 4.

## Dataset Source

- Dataset: Cattle Health and Feeding Data
- Publisher/account: ShahHet2812
- Source path: `D:\UOB\FarmLite\datasets\raw\global_cattle_milk_yield_prediction_dataset.csv`
- Rows: 250,000
- Columns loaded: 37
- SHA-256: `26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3`
- Expected checksum matched: True

The disease dataset was not loaded or merged.

## Synthetic-Data Limitation

The publisher declares the dataset synthetic and potentially unrepresentative of real-world cattle. These components support an undergraduate pipeline demonstration only, not veterinary, nutritional, commercial, or real-world feeding claims.

## Canonical Column Mapping

| Source column | Canonical column |
|---|---|
| `Cattle_ID` | `cattle_id` |
| `Breed` | `breed` |
| `Climate_Zone` | `climate_zone` |
| `Management_System` | `management_system` |
| `Age_Months` | `age_months` |
| `Weight_kg` | `weight_kg` |
| `Parity` | `parity` |
| `Lactation_Stage` | `lactation_stage` |
| `Days_in_Milk` | `days_in_milk` |
| `Feed_Type` | `feed_type` |
| `Feed_Quantity_kg` | `feed_quantity_kg` |
| `Ambient_Temperature_C` | `ambient_temperature_c` |
| `Humidity_percent` | `humidity_percent` |
| `Season` | `season` |
| `Previous_Week_Avg_Yield` | `previous_week_avg_yield_l` |
| `Body_Condition_Score` | `body_condition_score` |
| `Date` | `observation_date` |
| `Farm_ID` | `farm_id` |
| `Milk_Yield_L` | `milk_yield_l` |

Unmapped columns were preserved: 18. Ambiguous columns: 0.

## Required Feature Availability

Approved base feature order: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`.

All nine features and all three synthetic targets were present. Only the approved aliases were applied.

## Model 1 Feature Validation

- Valid schema: True
- Features: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`
- Target: `feed_type`
- The target was separated from X.

## Model 2 Design A Feature Validation

- Valid schema: True
- Features: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`
- Target: `feed_quantity_kg`
- The target was separated from X.

## Model 2 Design B Interface Validation

- Default gate refused Design B: True
- True same-row feed type substitution refused: True
- Required derived feature: `predicted_feed_type`.
- No predicted values or fake labels were generated.

## Model 3 Feature Validation

- Valid schema: True
- Features: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`
- Target: `milk_yield_l`
- Current `milk_yield_l` was excluded from X; prior-week yield remains historical input.

## Missing-Value Handling

Numeric medians and categorical modes are defined inside unfitted sklearn pipelines. Optional numeric missingness indicators are included. No full-dataset imputation statistics were fitted.

## Categorical Handling

`breed` and `lactation_stage` use most-frequent imputation followed by OneHotEncoder(handle_unknown="ignore"). Design B additionally defines `predicted_feed_type` as categorical.

## Numeric Handling

Numeric fields are `age_months`, `weight_kg`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`. Tree preprocessors leave numeric values unscaled; linear preprocessors add StandardScaler. All objects remained unfitted.

## Unknown-Category Handling

Unseen categories are warned about and preserved for the encoder. `Dry` is never mapped to Early, Mid, or Late, and an unknown breed is never mapped to Holstein or another breed.

## Data-Quality Flags

- Aggregated validation errors: 0
- Aggregated validation warnings: 1
- Warning-affected rows/events: 5,940
- Cleaner row-level issues: 0
- Rows removed: 0
- Zero synthetic milk-yield targets preserved and flagged: 5,940

Range boundaries describe the synthetic contract/dataset and are not biological safety thresholds.

## Train/Validation/Test Split

- Train: 175,000
- Validation: 37,500
- Test: 37,500
- Seed: 42
- Reproducibility hash: `A7C206B058CBD04AED428F9C44228653AF4CBEB6F86D90317A0A847BC02DADFB`
- Feed-quantity material difference: False
- Milk-yield material difference: False

Full category and numeric summaries are in `data_split_report.md` and `data_split_summary.json`.

## Out-of-Fold Assignment Preparation

- Training rows assigned: 175,000
- Folds: 5
- Fold counts: 1=35,000, 2=35,000, 3=35,000, 4=35,000, 5=35,000
- Reproducibility hash: `B1B546A11903F65E9A91824B6E25E2897E15F80A1619E08A5918652CAB377EB1`
- Validation/test rows received no training fold.
- The artifact contains no predictions.

## Leakage Checks

- Own targets are absent from every X frame.
- Cattle and farm identifiers and observation dates are absent from X.
- Same-record outcomes and disease fields are absent from X.
- Split and fold manifests contain no predictive target values.
- Design B refuses ground-truth `feed_type` substitution.

## Determinism Checks

- Repeated split assignment identical: True
- Repeated OOF assignment identical: True
- Generated artifact structure valid: True

## Application Mismatches

- UI `Dry` has no matching dataset lactation category.
- `healthStatus` is application-only and excluded from ML.
- `productionStage` duplicates lactation stage.
- Parity, season, climate zone, and management system are dataset-only.
- `animalType` is not currently sent to the API.
- The current PDF says L/day although the synthetic target period is unverified.

No mappings were invented to resolve these differences.

## Test Results

The validation command's loading, mapping, schema, feature, leakage, split,
fold, pipeline-factory, artifact, and determinism checks passed.

The complete existing-plus-Phase-3 suite passed **72 of 72 tests** with:

`venv\Scripts\python.exe -m unittest discover -s tests -v`

The requested pytest command could not run because pytest is not installed in
the existing virtual environment. No package was installed without owner
approval; no test failure is hidden.

## Limitations

- Kaggle license confirmation remains pending.
- Detailed synthetic generation formulas are unavailable.
- Feed-quantity material basis and period are unvalidated.
- Milk-yield period and zero meaning are unvalidated.
- The synthetic cattle data is not verified dairy-only.
- No prediction model has been trained or evaluated in Phase 3.

## Phase 4 Readiness Decision

**READY_FOR_PHASE_4_WITH_LIMITATIONS**

This recommendation means the preprocessing boundary is ready for owner review. It does not authorize model training.
