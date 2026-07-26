# FarmLite Synthetic Milk-Yield Regressor Candidate

## Model Purpose

Estimate the publisher-declared synthetic milk-yield target with an unvalidated measurement period.

## Intended Use

Undergraduate demonstration of a reproducible synthetic tabular ML workflow.

## Out-of-Scope Use

Veterinary, nutritional, commercial, farm-control, safety-critical, or real-world feeding decisions.

## Synthetic-Data Warning

FarmLite is an undergraduate prototype using publisher-declared synthetic cattle data. Predictions demonstrate an ML pipeline and are not veterinary, nutritional, commercial, or real-world feeding guidance.

## Inputs and Target

- Features: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`
- Target: `milk_yield_l`

## Algorithm and Training

- Configuration: `milk_yield_hist_gradient_boosting`
- Algorithm: HistGradientBoostingRegressor
- Hyperparameters: `{"l2_regularization": 0.1, "learning_rate": 0.08, "max_iter": 100, "max_leaf_nodes": 31, "random_state": 42}`
- Fit partition: locked 175,000-row training split only.
- Selection partition: locked 37,500-row validation split.
- Final evaluation: one-time locked 37,500-row test split.
- Random seed: 42 where supported.

## Results and Baseline Comparison

- Validation metrics: `{"mae": 1.0809263037904226, "maximum_prediction": 29.566704862011818, "mean_residual": -0.004076437474686489, "median_absolute_error": 0.9127717689180184, "minimum_prediction": 0.5126322505266452, "negative_prediction_count": 0, "r2": 0.9447814267553013, "residual_standard_deviation": 1.3525678591214019, "rmse": 1.3525559677178034}`
- Final test metrics: `{"mae": 1.0758821757269925, "maximum_prediction": 29.477271547003102, "mean_residual": 0.013168569645332452, "median_absolute_error": 0.9088906440821973, "minimum_prediction": 0.5126322505266452, "negative_prediction_count": 0, "r2": 0.9452182112415201, "residual_standard_deviation": 1.3471413976485904, "rmse": 1.3471877976312587}`
- Final baseline metrics: `{"mae": 4.562869066666667, "maximum_prediction": 7.62, "mean_residual": 1.0821810666666665, "median_absolute_error": 3.77, "minimum_prediction": 7.62, "negative_prediction_count": 0, "r2": -0.035349216383167015, "residual_standard_deviation": 5.755934281047123, "rmse": 5.856706567801851}`
- Status: `BEATS_BASELINE`

## Known and Ethical Limitations

- Synthetic generation formulas and dependency structure are undocumented.
- Feed and yield labels are not expert-validated recommendations or measurements.
- Feature importance is association, not causation or biological evidence.
- Dataset licensing remains unresolved.

## Dairy-Scope Limitation

The interface is scoped to dairy cattle, while the synthetic dataset contains cattle whose production purpose is not fully documented.

## Deployment Status

CANDIDATE_ONLY - integration review is not yet approved.

## Recommended Next Action

Review the ablation dependence and synthetic limitation before requesting a separate integration decision.
