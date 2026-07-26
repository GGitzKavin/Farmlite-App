# Current FarmLite ML Status

## Available datasets

Two raw CSV files are available under `datasets/raw/`:

- `global_cattle_milk_yield_prediction_dataset.csv`: 250,000 rows and 37
  columns. It contains `Milk_Yield_L`, `Feed_Quantity_kg`, animal attributes,
  lactation fields, environment fields, and management fields.
- `global_cattle_disease_detection_dataset.csv`: 250,000 rows and 41 columns.
  It contains `Disease_Status`, feed and milk fields, vital signs, animal
  attributes, and environment fields.

The inspection report warns that provenance, licensing, representativeness,
measurement quality, and real-world validity are not verified.

## Existing model files

`backend/flask_api/ml/models/milk_yield_model.joblib` is the only retained
trained model. It is a scikit-learn pipeline using
`HistGradientBoostingRegressor`.

The saved model predicts `Milk_Yield_L`. Its recorded test metrics are:

- MAE: 1.0801 L
- RMSE: 1.3532 L
- R²: 0.9446

The model uses breed, age, weight, lactation stage, days in milk, ambient
temperature, humidity, previous-week average yield, and body condition score.

## Current runtime prediction and recommendation

The Flask inference service predicts `Milk_Yield_L`. The API then calculates an
estimated total feed quantity from body weight and predicted milk yield and
passes that value through the rule-based feed planner.

Therefore, the current runtime is not yet a genuine ML feed recommendation
system. The ML model supplies a milk-yield signal; nutrition-style rules remain
the source of total feed, roughage, concentrate, mineral mix, frequency, water
advice, warnings, confidence, and explanation.

## Current scripts

- `ml/training/train_milk_yield_model.py`: trains the retained milk-yield
  pipeline.
- `ml/training/train_feed_model.py`: trains an experimental
  `Feed_Quantity_kg` regressor.
- `ml/training/evaluate_candidate_models.py`: evaluates milk-yield regression
  and disease-status classification candidates.
- `ml/preprocessing/inspect_datasets.py`: inspects both raw CSV files.
- `ml/inference/model_service.py`: loads the retained model and predicts milk
  yield.
- `ml/inference/feed_planner.py`: applies the existing rule-based feed plan.

## Existing reports

The following preserved reports are in `backend/flask_api/ml/reports/`:

- `candidate_model_evaluation_report.txt`
- `dataset_inspection_report.txt`
- `feed_model_report.txt`
- `milk_yield_model_report.txt`

The reports are historical records and contain absolute paths from their
original run locations.

## Missing or rejected feed-related model

No accepted trained model predicts genuine feed-related targets such as total
feed, dry-matter intake, concentrate, roughage, protein requirement, or energy
requirement.

The historical `Feed_Quantity_kg` RandomForest experiment recorded R² =
`-0.0065`, worse than predicting the mean. Its report is retained, but its model
artifact is absent and it must not be integrated into the API or frontend.

## Path findings

Before restructuring, scripts relied on directory-depth calculations and wrote
models and reports beside source code. Runtime model loading expected the model
beside `model_service.py`. Those active paths now come from
`config/settings.py`, which derives the project root with `pathlib.Path`.

The absolute paths embedded in existing reports are historical text, not active
runtime paths. Regenerating those reports would require rerunning evaluation or
training and was deliberately not done during this restructuring.
