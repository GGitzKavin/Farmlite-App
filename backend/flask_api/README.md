# FarmLite Flask API

This folder is an independent Flask application. It serves the existing
FarmLite health and AI feed-recommendation endpoints and contains the
machine-learning training and inference packages.

## Set up and run

From the project root:

```powershell
cd backend/flask_api
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The default base URL is `http://127.0.0.1:5000`.

Available endpoints:

- `GET /api/health`
- `POST /api/ai/feed-recommendation`
- `POST /api/v2/predict` (Bangladesh candidate-only backend prototype)

## Bangladesh candidate prototype

The v2 candidate path is disabled by default. To exercise it in a controlled
backend environment, set:

```powershell
$env:BANGLADESH_CANDIDATE_MODELS_ENABLED = "true"
```

Accepted true values are `1`, `true`, `yes`, and `on`, after trimming and
case normalization. A missing value, an empty value, or any malformed value
is false. No Bangladesh artifact is loaded while the flag is false.

The endpoint requires the existing v2 fields plus an explicit
`genetic_group` and measured `ambient_temperature_c` and
`humidity_percent` for candidate inference. It never derives genetic group
from breed. Responses use HTTP 200 for predictions, disabled mode, and
documented eligibility/artifact fallbacks; malformed JSON uses 400,
primitive/schema validation uses 422, and only unexpected failures use 500.
The route does not call nutrition rules or alter the existing v1 endpoints.

These models remain `CANDIDATE_ONLY`. The flag is not enabled in committed
configuration, and this integration is not production, commercial, or
veterinary approval.

## Package layout

- `api/`: Flask routes and API schema documentation.
- `config/`: project-root-derived filesystem settings.
- `ml/training/`: offline model training and candidate evaluation.
- `ml/inference/`: retained model loading and current feed planning.
- `ml/preprocessing/`: dataset inspection and future feature materialization.
- `ml/validation/`: validation boundary for future feed-model outputs.
- `ml/models/`: retained and future trained model artifacts.
- `ml/reports/`: model, inspection, and evaluation reports.
- `tests/`: standard-library unit and integration smoke tests.

## Data and generated outputs

Training and inspection scripts read source CSV files from:

```text
datasets/raw/
```

Any future persisted feature or training tables belong in:

```text
datasets/processed/
```

Training scripts save models and reports to:

```text
backend/flask_api/ml/models/
backend/flask_api/ml/reports/
```

Run offline scripts from `backend/flask_api` as modules:

```powershell
python -m ml.preprocessing.inspect_datasets
python -m ml.training.evaluate_candidate_models
python -m ml.training.train_milk_yield_model
python -m ml.training.train_feed_model
```

Training is not needed to run the current API. The retained
`milk_yield_model.joblib` predicts `Milk_Yield_L`, not genuine feed outputs.
The recorded `Feed_Quantity_kg` experiment is rejected and must not be
presented as production-ready.

## Checks

```powershell
python -m unittest discover -s tests
```
