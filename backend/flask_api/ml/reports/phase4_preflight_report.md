# FarmLite Phase 4 Preflight Report

- Status: `PASSED`
- Checked at: `2026-07-25T16:47:14.581319+00:00`
- Runner: `phase4_runner_v1`
- Configuration hash: `4DFBB3946768D56F2D1650F2A6481D189B1E4850B3A220BD3FE32E8AC7464521`
- Primary dataset SHA-256: `26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3`
- Existing retained milk-yield model SHA-256: `B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA`
- Split manifest SHA-256: `A7C206B058CBD04AED428F9C44228653AF4CBEB6F86D90317A0A847BC02DADFB`
- OOF fold manifest SHA-256: `B1B546A11903F65E9A91824B6E25E2897E15F80A1619E08A5918652CAB377EB1`
- Contract version: `1.0.0`

## Locked Partition Checks

- Source rows: 250,000
- Training rows: 175,000
- Validation rows: 37,500
- Test rows: 37,500
- Duplicate split assignments: 0
- Missing split assignments: 0
- Cattle_ID overlap count: 0
- OOF fold counts: 1=35,000, 2=35,000, 3=35,000, 4=35,000, 5=35,000
- Every training row has exactly one OOF fold: True

## Feature and Leakage Checks

- `feed_type_classifier`: `breed, age_months, weight_kg, lactation_stage, days_in_milk, previous_week_avg_yield_l, body_condition_score, ambient_temperature_c, humidity_percent`; target absent from X.
- `feed_quantity_regressor_design_a`: `breed, age_months, weight_kg, lactation_stage, days_in_milk, previous_week_avg_yield_l, body_condition_score, ambient_temperature_c, humidity_percent`; target absent from X.
- `milk_yield_regressor`: `breed, age_months, weight_kg, lactation_stage, days_in_milk, previous_week_avg_yield_l, body_condition_score, ambient_temperature_c, humidity_percent`; target absent from X.
- Design B is separately gated and accepts only an explicit `predicted_feed_type` in addition to the nine base features.

## Installed Runtime

- python: `3.12.10`
- platform: `Windows-11-10.0.26200-SP0`
- numpy: `2.4.4`
- pandas: `3.0.2`
- scikit_learn: `1.8.0`
- joblib: `1.5.3`

No package was installed. XGBoost, LightGBM, CatBoost, matplotlib, Pillow, pytest, and psutil are not required by this runner.

The preflight passed before any estimator fit.
