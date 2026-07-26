# FarmLite Structure Migration Notes

## File moves

| Original path | New path |
|---|---|
| `datasets/global_cattle_disease_detection_dataset.csv` | `datasets/raw/global_cattle_disease_detection_dataset.csv` |
| `datasets/global_cattle_milk_yield_prediction_dataset.csv` | `datasets/raw/global_cattle_milk_yield_prediction_dataset.csv` |
| `backend/flask_api/ml/train_feed_model.py` | `backend/flask_api/ml/training/train_feed_model.py` |
| `backend/flask_api/ml/train_milk_yield_model.py` | `backend/flask_api/ml/training/train_milk_yield_model.py` |
| `backend/flask_api/ml/evaluate_candidate_models.py` | `backend/flask_api/ml/training/evaluate_candidate_models.py` |
| `backend/flask_api/ml/model_service.py` | `backend/flask_api/ml/inference/model_service.py` |
| `backend/flask_api/ml/feed_planner.py` | `backend/flask_api/ml/inference/feed_planner.py` |
| `backend/flask_api/ml/inspect_datasets.py` | `backend/flask_api/ml/preprocessing/inspect_datasets.py` |
| `backend/flask_api/ml/milk_yield_model.joblib` | `backend/flask_api/ml/models/milk_yield_model.joblib` |
| `backend/flask_api/ml/candidate_model_evaluation_report.txt` | `backend/flask_api/ml/reports/candidate_model_evaluation_report.txt` |
| `backend/flask_api/ml/dataset_inspection_report.txt` | `backend/flask_api/ml/reports/dataset_inspection_report.txt` |
| `backend/flask_api/ml/feed_model_report.txt` | `backend/flask_api/ml/reports/feed_model_report.txt` |
| `backend/flask_api/ml/milk_yield_model_report.txt` | `backend/flask_api/ml/reports/milk_yield_model_report.txt` |

## Imports updated

- `app.py` now registers the API blueprint from `api.routes`.
- Runtime imports changed from `ml.model_service` and `ml.feed_planner` to
  `ml.inference.model_service` and `ml.inference.feed_planner`.
- Training, evaluation, preprocessing, and inference modules now obtain active
  filesystem locations from `config.settings`.
- Direct execution fallbacks add `backend/flask_api` to `sys.path` only when
  the configuration package is otherwise unavailable.

## Paths updated

- Raw CSV input paths resolve to `datasets/raw/`.
- Future processed data resolves to `datasets/processed/`.
- Saved models resolve to `backend/flask_api/ml/models/`.
- Generated reports resolve to `backend/flask_api/ml/reports/`.
- The runtime milk-yield model loader resolves the retained model from
  `ml/models/milk_yield_model.joblib`.

## Unresolved issues

- No accepted genuine feed-output model currently exists.
- The rejected `Feed_Quantity_kg` model artifact is absent; only its report is
  retained.
- Dataset provenance, licensing, and real-world validity remain unverified.
- Preserved historical reports contain their original absolute paths. They were
  not regenerated because this migration must not train or reevaluate models.
- The existing local `backend/flask_api/venv/` remains on disk and ignored by
  Git; it was not moved or added to source control.

## Validation results

- Python 3.12.10 syntax compilation passed for backend source files, excluding
  `venv/` and cache folders.
- Imports resolved for `app`, API, configuration, inference, preprocessing,
  training, evaluation, and validation modules.
- Both configured raw dataset paths exist.
- `milk_yield_model.joblib` loaded successfully as a scikit-learn `Pipeline`;
  no retraining was performed.
- The retained model and all four moved report files match their original Git
  blob hashes, confirming that their contents were preserved.
- The Flask application imported successfully and registered
  `/api/health` and `/api/ai/feed-recommendation`.
- Seven backend tests passed, including a retained-model prediction and the
  existing feed-recommendation response-field contract.
- `npm run build` passed for the independent frontend. Vite emitted its existing
  warning that one production chunk is larger than 500 kB after minification.
