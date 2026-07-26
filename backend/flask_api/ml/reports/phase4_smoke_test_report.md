# FarmLite Phase 4 Smoke-Test Report

# SMOKE_TEST_ONLY

- Status: `PASSED`
- Source: deterministic Feed_Type-stratified subset of training only
- Rows sampled: 4,000 (3,000 fit; 1,000 internal smoke evaluation)
- Tasks: feed_type, feed_quantity, milk_yield
- Expensive candidates skipped by flag: False
- Design B smoke input uses cross-fitted classifier predictions; true same-row Feed_Type is not substituted.
- Temporary joblib files were isolated in an auto-removed temp folder.
- Metrics from this run are not final experimental results.

| Model view | Configuration | Status | Fit s | Predict s | Rows | Reload equal |
|---|---|---|---:|---:|---:|---|
| `feed_type_classifier` | `feed_type_dummy_most_frequent` | PASSED | 0.0073 | 0.0033 | 1000 | True |
| `feed_type_classifier` | `feed_type_dummy_stratified` | PASSED | 0.0085 | 0.0039 | 1000 | True |
| `feed_type_classifier` | `feed_type_logistic_c1` | PASSED | 0.0216 | 0.0039 | 1000 | True |
| `feed_type_classifier` | `feed_type_decision_tree` | PASSED | 0.0231 | 0.0040 | 1000 | True |
| `feed_type_classifier` | `feed_type_random_forest` | PASSED | 0.1535 | 0.0152 | 1000 | True |
| `feed_type_classifier` | `feed_type_hist_gradient_boosting` | PASSED | 1.6749 | 0.0188 | 1000 | True |
| `feed_quantity_regressor_design_a` | `feed_quantity_dummy_mean` | PASSED | 0.0083 | 0.0040 | 1000 | True |
| `feed_quantity_regressor_design_a` | `feed_quantity_dummy_median` | PASSED | 0.0081 | 0.0038 | 1000 | True |
| `feed_quantity_regressor_design_a` | `feed_quantity_ridge` | PASSED | 0.0100 | 0.0041 | 1000 | True |
| `feed_quantity_regressor_design_a` | `feed_quantity_decision_tree` | PASSED | 0.0250 | 0.0055 | 1000 | True |
| `feed_quantity_regressor_design_a` | `feed_quantity_random_forest` | PASSED | 0.5174 | 0.0160 | 1000 | True |
| `feed_quantity_regressor_design_a` | `feed_quantity_hist_gradient_boosting` | PASSED | 0.2115 | 0.0061 | 1000 | True |
| `feed_quantity_regressor_design_b` | `feed_quantity_dummy_mean` | PASSED | 0.0091 | 0.0041 | 1000 | True |
| `feed_quantity_regressor_design_b` | `feed_quantity_dummy_median` | PASSED | 0.0087 | 0.0042 | 1000 | True |
| `feed_quantity_regressor_design_b` | `feed_quantity_ridge` | PASSED | 0.0112 | 0.0044 | 1000 | True |
| `feed_quantity_regressor_design_b` | `feed_quantity_decision_tree` | PASSED | 0.0286 | 0.0041 | 1000 | True |
| `feed_quantity_regressor_design_b` | `feed_quantity_random_forest` | PASSED | 0.5694 | 0.0160 | 1000 | True |
| `feed_quantity_regressor_design_b` | `feed_quantity_hist_gradient_boosting` | PASSED | 0.2303 | 0.0072 | 1000 | True |
| `milk_yield_regressor` | `milk_yield_dummy_mean` | PASSED | 0.0084 | 0.0043 | 1000 | True |
| `milk_yield_regressor` | `milk_yield_dummy_median` | PASSED | 0.0081 | 0.0039 | 1000 | True |
| `milk_yield_regressor` | `milk_yield_ridge` | PASSED | 0.0100 | 0.0040 | 1000 | True |
| `milk_yield_regressor` | `milk_yield_decision_tree` | PASSED | 0.0233 | 0.0036 | 1000 | True |
| `milk_yield_regressor` | `milk_yield_random_forest` | PASSED | 0.5185 | 0.0150 | 1000 | True |
| `milk_yield_regressor` | `milk_yield_hist_gradient_boosting` | PASSED | 0.2588 | 0.0070 | 1000 | True |
