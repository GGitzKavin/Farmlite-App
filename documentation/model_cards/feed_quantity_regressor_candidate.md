# FarmLite Synthetic Feed-Quantity Regressor Candidate

## Model Purpose

Estimate the publisher-declared synthetic feed-quantity target; this is not validated daily total feed.

## Intended Use

Undergraduate demonstration of a reproducible synthetic tabular ML workflow.

## Out-of-Scope Use

Veterinary, nutritional, commercial, farm-control, safety-critical, or real-world feeding decisions.

## Synthetic-Data Warning

FarmLite is an undergraduate prototype using publisher-declared synthetic cattle data. Predictions demonstrate an ML pipeline and are not veterinary, nutritional, commercial, or real-world feeding guidance.

## Inputs and Target

- Features: `breed`, `age_months`, `weight_kg`, `lactation_stage`, `days_in_milk`, `previous_week_avg_yield_l`, `body_condition_score`, `ambient_temperature_c`, `humidity_percent`
- Target: `feed_quantity_kg`

## Algorithm and Training

- Configuration: `feed_quantity_hist_gradient_boosting`
- Algorithm: HistGradientBoostingRegressor
- Hyperparameters: `{"l2_regularization": 0.1, "learning_rate": 0.08, "max_iter": 100, "max_leaf_nodes": 31, "random_state": 42}`
- Fit partition: locked 175,000-row training split only.
- Selection partition: locked 37,500-row validation split.
- Final evaluation: one-time locked 37,500-row test split.
- Random seed: 42 where supported.

## Results and Baseline Comparison

- Validation metrics: `{"mae": 3.178907013974234, "maximum_prediction": 13.26171838261149, "mean_residual": -0.029976805441610705, "median_absolute_error": 2.710618515349972, "minimum_prediction": 10.87404456473557, "negative_prediction_count": 0, "r2": 0.0028758132823899496, "residual_standard_deviation": 3.9595066864446693, "rmse": 3.9595673674084475}`
- Final test metrics: `{"mae": 3.179454853319791, "maximum_prediction": 13.357388134134371, "mean_residual": -0.028485085937071646, "median_absolute_error": 2.7144213662861434, "minimum_prediction": 10.539716165668484, "negative_prediction_count": 0, "r2": 0.00274632424519472, "residual_standard_deviation": 3.950203980197319, "rmse": 3.9502540140664344}`
- Final baseline metrics: `{"mae": 3.1806026666666667, "maximum_prediction": 12.0, "mean_residual": -0.004021333333333326, "median_absolute_error": 2.6999999999999993, "minimum_prediction": 12.0, "negative_prediction_count": 0, "r2": -1.0334649382937044e-06, "residual_standard_deviation": 3.9557422952126684, "rmse": 3.95569159566314}`
- Status: `DOES_NOT_BEAT_BASELINE`

## Known and Ethical Limitations

- Synthetic generation formulas and dependency structure are undocumented.
- Feed and yield labels are not expert-validated recommendations or measurements.
- Feature importance is association, not causation or biological evidence.
- Dataset licensing remains unresolved.

## Dairy-Scope Limitation

The interface is scoped to dairy cattle, while the synthetic dataset contains cattle whose production purpose is not fully documented.

## Deployment Status

NO ELIGIBLE CANDIDATE - research-only result.

## Recommended Next Action

Review the locked A/B evidence and acquire a validated quantity definition before any user-facing interpretation.
