# FarmLite Option B Implementation Plan

## Purpose

Option B is the proposed genuine ML pipeline for dairy cattle:

1. predict a feed-type class;
2. predict the observed `Feed_Quantity_kg` target if its meaning is verified;
3. predict `Milk_Yield_L`;
4. apply clearly identified nutrition validation rules;
5. return traceable ML-predicted and rule-derived values through the existing
   Flask endpoint, React page, and PDF.

This plan is conditional. Model training must stop if the dataset audit cannot
establish target meaning, dairy-cattle suitability, safe leakage controls, and
usable deployment features.

## Phase 0 discovery status

Phase 0 inspected the reorganized repository without changing application
behaviour or training models.

### Current architecture

```text
React FeedRecommendation page
  -> reads dairy-cattle-like livestock and health records from Firebase
  -> sends an inline Axios request to POST /api/ai/feed-recommendation
  -> displays the response and creates the PDF in the browser

Flask app.py
  -> registers api.routes.api_blueprint
  -> /api/health
  -> /api/ai/feed-recommendation

Current recommendation route
  -> ml.inference.model_service predicts Milk_Yield_L
  -> route estimates feed as weight * 0.025 + predicted milk * 0.30
  -> ml.inference.feed_planner clamps and splits that estimate
  -> API returns milk prediction plus rule-generated feed outputs
```

The backend and frontend are already separate top-level applications. Dataset,
model, report, training, inference, preprocessing, validation, API, config, and
test directories are already organized, so another structural migration is not
needed.

### Current API contract

The frontend calls:

```text
POST /api/ai/feed-recommendation
```

Current request fields:

- `animalId`
- `animalName`
- `breed`
- `ageMonths`
- `weightKg`
- `lactationStage`
- `daysInMilk`
- `ambientTemperatureC`
- `humidityPercent`
- `previousWeekAvgYield`
- `bodyConditionScore`
- `healthStatus`
- `productionStage`

The current request does not include `animalType`, `parity`, `season`,
`climateZone`, or `managementSystem`.

Current response sections:

- `success`
- `animalId`
- `animalName`
- `prediction`
  - `predictedMilkYieldL`
  - `modelUsed`
  - `target`
  - optional feature and limitation information
- `recommendation`
  - `totalFeedKg`
  - `roughageKg`
  - `concentrateKg`
  - `mineralMixKg`
  - `waterAdvice`
  - `feedingFrequency`
  - `confidenceLevel`
  - `explanation`
  - `warnings`
  - `disclaimer`
- `limitations`

The response does not yet contain a recommended feed type, model version,
validation status, raw predictions, or value-source information.

### Current dairy-cattle restriction

The React page filters Firebase records using species labels such as
`Dairy Cattle`, `Dairy Cow`, `Cattle (Dairy)`, and `Cow`. It rejects clearly
unsuitable frontend labels such as beef cattle, sheep, goats, poultry, and
swine.

The Flask endpoint itself does not currently receive or validate an animal type.
Backend dairy-cattle validation is therefore still required before deploying a
new unified inference service.

### Current ML assets

The only deployed model is:

```text
backend/flask_api/ml/models/milk_yield_model.joblib
```

It is a saved scikit-learn `Pipeline` with `preprocessing` and `model` steps.
Its input columns are:

- `Breed`
- `Age_Months`
- `Weight_kg`
- `Lactation_Stage`
- `Days_in_Milk`
- `Ambient_Temperature_C`
- `Humidity_percent`
- `Previous_Week_Avg_Yield`
- `Body_Condition_Score`

It predicts `Milk_Yield_L`. The historical report records a
`HistGradientBoostingRegressor`, MAE `1.0801 L`, RMSE `1.3532 L`, and R²
`0.9446`. These are historical values from the preserved report, not metrics
rerun during Phase 0.

The retained model SHA-256 at Phase 0 is:

```text
B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA
```

There is no accepted feed-type classifier or feed-quantity model. The existing
feed-quantity report records R² `-0.0065`, so that experiment failed to beat a
mean prediction and is not deployed.

### Current nutrition logic

`ml/inference/feed_planner.py` contains the working FarmLite rules that must be
preserved unless a later change is explicitly approved:

- body-weight feed bounds of 1.5% to 4.0%;
- roughage/concentrate splits selected from milk-yield bands;
- a 10% concentrate reduction for specified health statuses;
- mineral mix selected from a 350 kg body-weight threshold;
- two or three feedings based on milk yield;
- water-access advice, warnings, confidence, and advisory disclaimer.

The route currently creates the feed estimate using:

```text
weightKg * 0.025 + predictedMilkYieldL * 0.30
```

That feed estimate is formula-derived, not directly predicted by ML. The
existing explanation calls it a model-supplied estimate, which is a traceability
risk to correct only after the new response design is approved.

`ml/validation/nutrition_rules.py` currently defines only a future required-field
check. It does not yet validate ranges, record value sources, or produce
validation actions.

### Current frontend and PDF

`frontend/src/pages/FeedRecommendation.tsx` contains:

- dairy-cattle record loading and filtering;
- the complete input form;
- inline Axios API access;
- loading, validation, connection, and backend-error handling;
- response rendering;
- browser-side PDF generation with jsPDF.

The farmer does not currently choose a feed type. This should remain true.

The page and PDF display milk yield, total feed, roughage, concentrate, mineral
mix, water advice, feeding frequency, confidence, explanations, warnings, and
limitations. They do not display a recommended feed type or model version.

There is no separate frontend API service for this feature; its API call and
response type are local to `FeedRecommendation.tsx`.

### Current datasets

Primary candidate:

```text
datasets/raw/global_cattle_milk_yield_prediction_dataset.csv
```

- recorded size: 48,805,186 bytes;
- existing inspection report: 250,000 rows, 37 columns;
- SHA-256:
  `26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3`.

Secondary dataset:

```text
datasets/raw/global_cattle_disease_detection_dataset.csv
```

- recorded size: 54,792,252 bytes;
- existing inspection report: 250,000 rows, 40 columns;
- SHA-256:
  `4CEDFA77234FE45B441E303FF051C33123969E37C3B484A03387094A613DC4B9`.

Both headers contain `Cattle_ID`, `Date`, `Feed_Type`,
`Feed_Quantity_kg`, and `Milk_Yield_L`. This does not prove that rows can be
joined. The secondary dataset will stay separate unless Phase 1 proves a unique,
genuine shared key using both animal and observation date.

The current repository documentation does not establish:

- whether every row is dairy cattle;
- whether either dataset is observational, simulated, or synthetic;
- whether `Feed_Type` is a recommendation or simply what was used;
- what period `Feed_Quantity_kg` covers;
- whether feed quantity is fresh matter, dry matter, concentrate, or another
  quantity;
- whether `Milk_Yield_L` is a daily value;
- authoritative source, license, or data-collection methodology.

These meanings are currently **UNCLEAR** and are critical audit gates.

### Current dependencies and tests

Backend requirements include Flask, Flask-CORS, pandas, scikit-learn, joblib,
and related application packages. The existing backend virtual environment is
present and uses Python 3.12.10, pandas 3.0.2, scikit-learn 1.8.0, joblib 1.5.3,
and NumPy 2.4.4.

The environment does not currently contain pytest, matplotlib, seaborn,
openpyxl, pyarrow, or xgboost. No package is required to be installed for the
CSV-only Phase 1 audit. Later plot generation and the requested pytest command
will require either permission to add suitable packages or an approved
dependency-free alternative.

Seven standard-library `unittest` checks currently cover:

- health endpoint;
- invalid API body;
- existing response-field contract;
- retained model presence and prediction format;
- future nutrition-field completeness checks.

The frontend has Vite build and ESLint commands. The AI page is routed at
`/ai-feed`.

## Existing files to reuse

| File | Reuse |
|---|---|
| `backend/flask_api/config/settings.py` | Extend central pathlib paths. |
| `backend/flask_api/ml/preprocessing/inspect_datasets.py` | Expand into the Phase 1 multi-format audit. |
| `backend/flask_api/ml/inference/feed_planner.py` | Preserve current formulas while separating source labels and validation actions. |
| `backend/flask_api/ml/inference/model_service.py` | Retain as the old milk-model baseline until release approval. |
| `backend/flask_api/ml/models/milk_yield_model.joblib` | Preserve and back up before any approved replacement. |
| `backend/flask_api/api/routes.py` | Preserve the existing endpoint and integrate only approved services. |
| `backend/flask_api/api/schemas.py` | Extend request/response documentation and validation. |
| `frontend/src/pages/FeedRecommendation.tsx` | Preserve layout, error states, dairy filtering, response UI, and PDF. |
| `backend/flask_api/tests/` | Extend rather than replace existing tests. |
| Existing reports and notes | Treat as historical evidence; do not rewrite them as new results. |

## Existing files expected to need modification

No file below should change until its phase is approved.

- `backend/flask_api/config/settings.py`
- `backend/flask_api/requirements.txt` only if a missing package is approved
- `backend/flask_api/ml/preprocessing/inspect_datasets.py`
- `backend/flask_api/ml/preprocessing/feature_pipeline.py`
- `backend/flask_api/ml/inference/feed_planner.py`
- `backend/flask_api/ml/inference/model_service.py`
- `backend/flask_api/ml/validation/nutrition_rules.py`
- `backend/flask_api/api/routes.py`
- `backend/flask_api/api/schemas.py`
- backend tests
- `frontend/src/pages/FeedRecommendation.tsx`
- root/backend READMEs and requested documentation

## Proposed new files

Creation is phased and conditional on the audit.

### Phase 1: dataset audit

- `backend/flask_api/ml/reports/dataset_audit.json`
- `backend/flask_api/ml/reports/dataset_inspection_report.md`
- `backend/flask_api/ml/reports/dataset_target_matrix.csv`

### Phase 2: model contract

The established project already has `backend/flask_api/config/`, so the
contract should be placed at:

- `backend/flask_api/config/model_contract.json`
- `documentation/ml_feature_dictionary.md`

This avoids adding a second competing config location under `ml/`.

### Phase 3: reusable preprocessing

- `backend/flask_api/ml/preprocessing/data_loader.py`
- `backend/flask_api/ml/preprocessing/column_mapping.py`
- `backend/flask_api/ml/preprocessing/data_cleaner.py`
- `backend/flask_api/ml/preprocessing/feature_builder.py`
- `backend/flask_api/ml/preprocessing/split_data.py`

### Phases 4-8: splitting, training, evaluation, release

- `backend/flask_api/ml/reports/data_split_report.md`
- `backend/flask_api/ml/training/train_feed_type_classifier.py`
- `backend/flask_api/ml/training/train_feed_quantity_regressor.py`
- `backend/flask_api/ml/training/train_milk_yield_regressor.py`
- model joblib files and real metadata JSON files
- real Markdown evaluation reports and generated plots
- `backend/flask_api/ml/reports/final_model_comparison.md`
- `backend/flask_api/ml/models/model_manifest.json`

These files must not be created with placeholder scores or fake metadata.

### Phases 9-11: validation, inference, and API

- `backend/flask_api/ml/validation/input_validator.py`
- `backend/flask_api/ml/validation/nutrition_validator.py`
- `backend/flask_api/ml/validation/recommendation_rules.py`
- `backend/flask_api/ml/validation/warning_generator.py`
- `backend/flask_api/ml/inference/recommendation_service.py`

### Phases 14-16: tests and documentation

- focused preprocessing, validation, inference, model-loading, and API tests;
- `documentation/ai_feed_recommendation.md`
- `documentation/model_training_guide.md`
- `documentation/model_evaluation.md`
- `documentation/api_feed_recommendation.md`
- `documentation/limitations_and_ethics.md`
- `backend/flask_api/ml/reports/final_system_validation.md`

## Risks and decision gates

### Critical audit gates

Final feed-type and feed-quantity training must stop if any of these remain
unresolved:

1. `Feed_Type` is only observed usage rather than a recommended label.
2. `Feed_Quantity_kg` period or material basis remains unclear.
3. the primary data cannot be limited to dairy cattle;
4. target leakage cannot be prevented;
5. required model inputs are unavailable from FarmLite at inference time;
6. the dataset source or validity is too weak for the claimed use.

### Technical and product risks

- `Cattle_ID` may repeat across time. Random row splitting could leak the same
  cow into training and test data.
- The two datasets look structurally related, but joining by row order or
  similar attributes would be unsafe.
- `Previous_Week_Avg_Yield`, current milk yield, feed type, and feed quantity
  may have time or causal relationships that cannot be interpreted without
  documentation.
- The frontend supplies `Mid Lactation`, while the dataset examples use values
  such as `Mid`. Contract-level mapping is needed and must be documented.
- `Health_Status` is not a column in the primary dataset. The secondary
  `Disease_Status` must not be silently substituted or joined.
- `Parity`, `Season`, `Climate_Zone`, and `Management_System` are not currently
  provided by the AI form.
- The Flask endpoint currently trusts frontend dairy filtering; unsupported
  animal types are not rejected by the backend.
- Existing optional numeric defaults silently substitute values. This conflicts
  with the new rule against silently continuing when required information is
  missing.
- The current model lacks metadata, a version, and a manifest.
- The current route formula is described too much like a model feed prediction.
- Existing nutrition ratios are working code but do not have a documented
  veterinary or nutrition source in the repository.
- The requested plot and pytest workflow need packages not currently available
  in the backend environment.
- A future API response expansion affects the React type, display, PDF, and
  contract tests together and requires explicit approval before integration.

## Expected implementation phases

1. **Phase 1 — Audit only:** enhance and run the dataset audit; generate real
   audit outputs; decide whether each target passes.
2. **Phase 2 — Contract only:** define fields using the audit and actual
   frontend availability; do not train.
3. **Phase 3 — Preprocessing:** implement reusable loaders, mapping, cleaning,
   feature construction, and leakage-aware split utilities.
4. **Phase 4 — Split:** create reproducible train/validation/test assignments
   with grouping if cattle repeat.
5. **Phases 5-7 — Train separately:** train feed type, feed quantity, and milk
   yield only for targets approved by the audit.
6. **Phase 8 — Release decision:** compare against baselines and reject weak or
   incompatible models.
7. **Phases 9-10 — Validation and inference:** preserve existing formulas,
   identify every value source, load released models once, and expose health
   information.
8. **Phases 11-13 — API, React, and PDF:** expand the existing contract in one
   coordinated, approved change without redesigning the page.
9. **Phases 14-16 — Test, document, and validate:** run backend and frontend
   checks, verify artifacts and checksums, and issue an honest readiness status.

At the end of every phase, update a change log with completed work, files,
commands, results, warnings, blockers, and the next approval gate.

## Phase 0 verification

- Backend: `venv\Scripts\python.exe -m unittest discover -s tests -v`
  completed successfully; all 7 tests passed.
- Frontend: `npm.cmd run build` completed successfully.
- Diff hygiene: `git diff --check` completed successfully. Git reported only
  line-ending conversion notices for pre-existing modified files.
- Build warning: Vite reports an existing minified JavaScript chunk larger than
  500 kB. This does not fail the build and is outside the Option B Phase 0
  scope.
- Phase result: **PASS**. Only this planning document was added for Phase 0;
  application behaviour and model artifacts were not changed.

## Rollback approach

1. Work in small phases and review `git diff` before proceeding.
2. Do not modify files outside the active phase.
3. Keep raw datasets read-only and compare their Phase 0 SHA-256 hashes during
   final validation.
4. Never overwrite `milk_yield_model.joblib` directly. Before any approved
   replacement, copy it to a dated backup location and verify the backup hash.
5. Save new models under new filenames until Phase 8 approves integration.
6. Keep the current Flask route, response contract, React page, and PDF working
   until a coordinated integration phase.
7. If a phase fails, remove only files created by that phase and revert only
   that phase's edits; retain its failure report for review.
8. Do not use destructive Git reset commands. Use explicit file-level review
   and recover from the last approved checkpoint.

## Information needed from the project owner

The following is not present in the repository and becomes important before
final model training:

1. dataset source or download page;
2. dataset README, data dictionary, or license;
3. exact meaning and time period of `Feed_Quantity_kg`;
4. whether `Feed_Quantity_kg` is fresh matter, dry matter, concentrate, or
   another measure;
5. meaning of each `Feed_Type` category and whether it is observed or
   recommended;
6. confirmation or source for the current FarmLite nutrition formulas;
7. later permission to expand the API response and update the React/PDF
   contract;
8. later permission to add pytest and a plotting package if those outputs
   remain required.

Phase 1 can still produce an honest audit without these answers, but unresolved
items will be marked `UNCLEAR` and may block training.

## Exact next action after approval

Modify only `backend/flask_api/ml/preprocessing/inspect_datasets.py` for the
Phase 1 audit, then run it with the existing backend environment:

```powershell
cd backend/flask_api
venv\Scripts\python.exe -m ml.preprocessing.inspect_datasets
```

Validate the three generated audit files, report the decision for each target,
and stop again before Phase 2 or any model training.
