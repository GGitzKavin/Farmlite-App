# FarmLite

FarmLite keeps its Flask backend and React frontend as independent top-level
applications. Shared cattle datasets live at the project root under
`datasets/`.

## Backend

```powershell
cd backend/flask_api
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The API runs on `http://127.0.0.1:5000` by default. Detailed backend and ML
layout notes are in `backend/flask_api/README.md`.

## Frontend

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend remains an independent Vite application with its own dependencies
and build configuration.

### Controlled collected-data DMI UI

The Phase 6 research-prediction UI is disabled by default. For local,
controlled development only, both processes must be enabled:

```powershell
# Backend terminal
$env:BANGLADESH_CANDIDATE_MODELS_ENABLED = "true"

# Frontend terminal, before npm run dev
$env:VITE_BANGLADESH_CANDIDATE_UI_ENABLED = "true"
```

Each flag accepts `1`, `true`, `yes`, or `on`; missing or malformed values
remain false. Neither flag is enabled in a committed environment file.

When enabled, the UI accepts a deliberate genetic-group selection from
`Local`, `HF50`, `HF62.5`, `HF75`, or `HF87.5`, plus a farmer-facing
`Unknown / Not sure` choice that is never submitted as a fabricated model
category. It never derives genetic group from breed.

Farmers see one milk result from the FarmLite milk prediction model. The
unified recommendation may also show DMI in kg DM/cow/day and
backend-calculated THI. DMI is not total feed, fresh-feed weight, roughage,
concentrate, or an as-fed ration quantity; the advisory ration remains owned
by the FarmLite nutrition rule engine.

Technical source note: the collected DMI research data is from Mendeley Data,
DOI `10.17632/954f6g36sb.2`.

## Data and ML outputs

- Raw source datasets: `datasets/raw/`
- Interim data: `datasets/interim/`
- Processed training data: `datasets/processed/`
- External reference data: `datasets/external/`
- Trained models: `backend/flask_api/ml/models/`
- Model and evaluation reports: `backend/flask_api/ml/reports/`

Do not treat the current milk-yield model as a genuine feed-output model. The
current ML scope and discovered limitations are documented under `notes/`.
