# FarmLite Synthetic Milk-Yield Regressor Report

## Scope

Milk_Yield_L is a publisher-declared synthetic target whose measurement period and zero meaning are not independently validated. It must not be described as verified litres per day.

## Candidate Validation Metrics

| Configuration | Algorithm | Baseline | MAE | RMSE | R² | Median AE | Mean residual | Residual std | Negative | Train s | Predict s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `milk_yield_dummy_mean` | DummyRegressor | True | 4.653789 | 5.755927 | -0.000012 | 4.140252 | -0.020109 | 5.755969 | 0 | 0.144 | 0.019 |
| `milk_yield_dummy_median` | DummyRegressor | True | 4.573895 | 5.858123 | -0.035838 | 3.800000 | 1.089638 | 5.755969 | 0 | 0.149 | 0.020 |
| `milk_yield_ridge` | Ridge | False | 1.101667 | 1.381648 | 0.942381 | 0.925561 | -0.006534 | 1.381651 | 45 | 0.188 | 0.020 |
| `milk_yield_decision_tree` | DecisionTreeRegressor | False | 1.136374 | 1.424039 | 0.938791 | 0.959751 | -0.003718 | 1.424054 | 0 | 3.409 | 0.023 |
| `milk_yield_random_forest` | RandomForestRegressor | False | 1.101515 | 1.378089 | 0.942677 | 0.928055 | -0.007728 | 1.378086 | 0 | 122.421 | 0.148 |
| `milk_yield_hist_gradient_boosting` | HistGradientBoostingRegressor | False | 1.080926 | 1.352556 | 0.944781 | 0.912772 | -0.004076 | 1.352568 | 0 | 1.122 | 0.061 |

## Locked Validation Selection

- Configuration: `milk_yield_hist_gradient_boosting`
- Algorithm: HistGradientBoostingRegressor
- Beats baseline: True
- Release status before test: `CANDIDATE_ACCEPTED_WITH_LIMITATIONS`
- Reason: Lowest validation MAE, then RMSE and higher R² within the controlled candidate set. The full nine-feature contract remains selected; the previous-week-yield removal is a transparency ablation only. The candidate clears the validation baseline rule.

## Subgroup Diagnostics

- lactation_stage: 3 groups; highest validation MAE `Early` = 1.105943.
- largest_breeds: 10 groups; highest validation MAE `Norwegian_Red` = 1.193835.
- previous_week_yield_ranges: 5 groups; highest validation MAE `>20` = 1.161477.
- zero_vs_positive_target: 2 groups; highest validation MAE `zero_target` = 1.364357.

## Feature Importance

- `previous_week_avg_yield_l`: 4.824982 ± 0.064299
- `breed`: 0.133300 ± 0.002085
- `lactation_stage`: 0.018734 ± 0.001246
- `days_in_milk`: 0.016583 ± 0.001858
- `age_months`: 0.004608 ± 0.001056
- `ambient_temperature_c`: 0.001082 ± 0.000454
- `humidity_percent`: 0.000031 ± 0.000071
- `body_condition_score`: -0.000019 ± 0.000009
- `weight_kg`: -0.000056 ± 0.000022

Permutation importance describes association in synthetic validation records. It is not causal or biological evidence.

## Limitations

- Strong performance may reflect an undocumented synthetic generation formula.
- Previous-week yield is historical input, not current target leakage.
- The ablation report quantifies dependence on that historical feature.
- The source population is not verified dairy-only.
