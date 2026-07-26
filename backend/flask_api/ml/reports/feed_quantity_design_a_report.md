# FarmLite Synthetic Feed-Quantity Regressor — Design A

## Scope

Feed_Quantity_kg is a synthetic regression target whose material basis and measurement period are not independently validated. It must not be described as validated daily total feed.

## Candidate Validation Metrics

| Configuration | Algorithm | Baseline | MAE | RMSE | R² | Median AE | Mean residual | Residual std | Negative | Train s | Predict s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `feed_quantity_dummy_mean` | DummyRegressor | True | 3.180754 | 3.965386 | -0.000057 | 2.723848 | -0.029952 | 3.965326 | 0 | 0.170 | 0.020 |
| `feed_quantity_dummy_median` | DummyRegressor | True | 3.180323 | 3.965278 | -0.000002 | 2.700000 | -0.006104 | 3.965326 | 0 | 0.165 | 0.019 |
| `feed_quantity_ridge` | Ridge | False | 3.179414 | 3.958410 | 0.003459 | 2.708609 | -0.028211 | 3.958362 | 0 | 0.216 | 0.020 |
| `feed_quantity_decision_tree` | DecisionTreeRegressor | False | 3.235620 | 4.029588 | -0.032702 | 2.763184 | -0.029490 | 4.029534 | 0 | 2.234 | 0.023 |
| `feed_quantity_random_forest` | RandomForestRegressor | False | 3.185162 | 3.967174 | -0.000959 | 2.721688 | -0.027187 | 3.967134 | 0 | 75.047 | 0.114 |
| `feed_quantity_hist_gradient_boosting` | HistGradientBoostingRegressor | False | 3.178907 | 3.959567 | 0.002876 | 2.710619 | -0.029977 | 3.959507 | 0 | 0.615 | 0.042 |

## Locked Validation Selection

- Configuration: `feed_quantity_hist_gradient_boosting`
- Algorithm: HistGradientBoostingRegressor
- Beats baseline: False
- Release status before test: `RESEARCH_ONLY`
- Reason: Lowest validation MAE, then RMSE and higher R² within the controlled Design A candidate set. It does not clear the baseline rule and remains research-only.

## Subgroup Diagnostics

- feed_type: 8 groups; highest validation MAE `Silage` = 3.237125.
- lactation_stage: 3 groups; highest validation MAE `Mid` = 3.185422.
- largest_breeds: 10 groups; highest validation MAE `Tharparkar` = 3.302421.
- feed_quantity_ranges: 5 groups; highest validation MAE `>19` = 8.673573.

## Feature Importance

- `previous_week_avg_yield_l`: 0.011469 ± 0.002637
- `breed`: 0.006432 ± 0.001656
- `days_in_milk`: 0.002759 ± 0.001517
- `ambient_temperature_c`: 0.000930 ± 0.000369
- `body_condition_score`: 0.000748 ± 0.000150
- `humidity_percent`: 0.000059 ± 0.000344
- `age_months`: -0.000002 ± 0.000217
- `weight_kg`: -0.000826 ± 0.000379
- `lactation_stage`: -0.000867 ± 0.001020

Ground-truth Feed_Type is used only for subgroup reporting. It is not a Design A input and is never substituted for predicted_feed_type in Design B.

Feature importance is synthetic-data association, not causal or nutritional evidence.
