# FarmLite Final Installation and Run Guide

Date: 2026-07-26

## Prerequisites

The Phase 7 validation environment used:

- Windows PowerShell;
- Node.js 24.11.0 and npm 11.6.1;
- Python 3.12.10;
- Git 2.51.2.

Use a currently supported Node.js release compatible with Vite 8 and Python
3.12 or a compatible Python 3 release. Model artifacts are already supplied;
do not retrain them to run the application.

## Repository layout

```text
FarmLite/
  backend/flask_api/     Flask API, models, tests and reports
  frontend/              React application and frontend tests
  datasets/              source/processed research material
  documentation/         design and final submission documents
```

## Backend setup

From the repository root:

```powershell
cd backend\flask_api
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

The default address is `http://127.0.0.1:5000`. `PORT` can change the port.
Debug mode is off by default; set `FLASK_DEBUG=true` only for trusted local
development.

Check the backend:

```powershell
Invoke-WebRequest http://127.0.0.1:5000/api/health
```

## Frontend setup

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_FLASK_API_URL` when supplied and otherwise calls
`http://127.0.0.1:5000`.

## Firebase environment

Create `frontend/.env` locally with the existing authorized Firebase web
configuration:

```text
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
```

Do not commit this file. Phase 7 verified that it is ignored. Do not change
Authentication providers, users, collection paths, ownership fields or
Firestore rules as part of installation.

The repository does not include the deployed Firestore rules. Before a real
deployment, obtain and review the exact rules through the authorized Firebase
administration process; do not assume frontend filters enforce access.

## Controlled DMI and backend THI path

The candidate path is disabled by default and requires independent flags in
both processes.

Backend terminal, before `python app.py`:

```powershell
$env:BANGLADESH_CANDIDATE_MODELS_ENABLED = 'true'
```

Frontend terminal, before `npm run dev` or `npm run build`:

```powershell
$env:VITE_BANGLADESH_CANDIDATE_UI_ENABLED = 'true'
```

The accepted true values are `1`, `true`, `yes` and `on`, after trimming and
case normalization. Any other or missing value is false. Do not place either
flag in committed configuration.

## Production build

Default feature-disabled build:

```powershell
cd frontend
Remove-Item Env:\VITE_BANGLADESH_CANDIDATE_UI_ENABLED -ErrorAction SilentlyContinue
npm run build
npm run preview -- --host 127.0.0.1 --port 4174
```

Controlled feature-enabled build:

```powershell
$env:VITE_BANGLADESH_CANDIDATE_UI_ENABLED = 'true'
npm run build
```

Phase 7 left `dist` in the default-disabled mode. Both builds passed. Vite
reports a known non-blocking large-chunk warning.

## Validation commands

Frontend:

```powershell
cd frontend
npm run test:phase6
npm run test:phase6.1
npm run test:phase6.2
npm run test:phase6.3
npm exec tsc -- -b
npm run lint
```

Backend:

```powershell
cd backend\flask_api
python -m unittest discover -s tests
python -m compileall -q app.py config api ml tests
python -m pip check
```

Repository:

```powershell
git status --short
git diff --check
git diff --cached --name-only
```

The final test totals and known lint debt are recorded in
`backend/flask_api/ml/reports/phase7_test_summary.json`.

## Operational checks

- Confirm `/api/health` returns HTTP 200 before opening recommendation pages.
- Enable or disable both candidate flags together for the intended mode.
- Never copy the internal v2 milk candidate into farmer-facing output.
- Preserve the exact model and nutrition-rule hashes in the system inventory.
- Use only a small number of test requests; do not load-test the academic
  deployment.
- Configure an explicit production CORS allowlist and API protection at the
  hosting boundary before public exposure.

## Troubleshooting

- **PowerShell blocks `npm.ps1`:** run `npm.cmd` or use an approved shell
  policy; this is an environment issue, not a FarmLite build failure.
- **Firebase permission error:** stop and record the deployed-rule limitation.
  Do not edit or deploy rules during validation.
- **DMI unavailable:** check both feature flags, genetic group, production
  scope and weather inputs. Do not substitute zero.
- **THI unavailable:** correct temperature/humidity; the frontend must not
  calculate THI.
- **Large chunk warning:** the build is valid. Treat code splitting as future
  performance work rather than a Phase 7 feature change.
