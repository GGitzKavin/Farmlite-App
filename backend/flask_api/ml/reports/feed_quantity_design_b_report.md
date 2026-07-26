# FarmLite Synthetic Feed-Quantity Regressor — Design B

## Scope

Feed_Quantity_kg is a synthetic regression target whose material basis and measurement period are not independently validated. It must not be described as validated daily total feed.

## Candidate Validation Metrics

| Configuration | Algorithm | Baseline | MAE | RMSE | R² | Median AE | Mean residual | Residual std | Negative | Train s | Predict s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `feed_quantity_dummy_mean` | DummyRegressor | True | 3.180754 | 3.965386 | -0.000057 | 2.723848 | -0.029952 | 3.965326 | 0 | 0.194 | 0.023 |
| `feed_quantity_dummy_median` | DummyRegressor | True | 3.180323 | 3.965278 | -0.000002 | 2.700000 | -0.006104 | 3.965326 | 0 | 0.170 | 0.023 |
| `feed_quantity_ridge` | Ridge | False | 3.179527 | 3.958510 | 0.003408 | 2.711843 | -0.028351 | 3.958461 | 0 | 0.234 | 0.023 |
| `feed_quantity_decision_tree` | DecisionTreeRegressor | False | 3.236696 | 4.031446 | -0.033655 | 2.763134 | -0.027591 | 4.031406 | 0 | 2.602 | 0.026 |
| `feed_quantity_random_forest` | RandomForestRegressor | False | 3.183803 | 3.964971 | 0.000153 | 2.715633 | -0.027206 | 3.964930 | 0 | 89.568 | 0.120 |
| `feed_quantity_hist_gradient_boosting` | HistGradientBoostingRegressor | False | 3.178797 | 3.959885 | 0.002716 | 2.710251 | -0.030772 | 3.959819 | 0 | 0.527 | 0.038 |

## Locked Validation Selection

- Configuration: `feed_quantity_hist_gradient_boosting`
- Algorithm: HistGradientBoostingRegressor
- Beats baseline: False
- Release status before test: `RESEARCH_ONLY`
- Reason: Lowest validation MAE, then RMSE and higher R² within the controlled Design B candidate set. It does not clear the baseline rule and remains research-only.

## Subgroup Diagnostics

- feed_type: 8 groups; highest validation MAE `Silage` = 3.235324.
- lactation_stage: 3 groups; highest validation MAE `Mid` = 3.186104.
- largest_breeds: 10 groups; highest validation MAE `Tharparkar` = 3.299776.
- feed_quantity_ranges: 5 groups; highest validation MAE `>19` = 8.675657.

## Feature Importance

- `previous_week_avg_yield_l`: 0.008527 ± 0.002854
- `breed`: 0.004899 ± 0.000731
- `ambient_temperature_c`: 0.001277 ± 0.000251
- `humidity_percent`: 0.000674 ± 0.000213
- `days_in_milk`: 0.000548 ± 0.001338
- `age_months`: 0.000361 ± 0.000109
- `body_condition_score`: 0.000152 ± 0.000058
- `predicted_feed_type`: 0.000092 ± 0.000086
- `weight_kg`: -0.000374 ± 0.000018
- `lactation_stage`: -0.000426 ± 0.000481

Ground-truth Feed_Type is used only for subgroup reporting. It is not a Design A input and is never substituted for predicted_feed_type in Design B.

Feature importance is synthetic-data association, not causal or nutritional evidence.
