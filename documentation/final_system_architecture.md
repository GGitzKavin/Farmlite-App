# FarmLite Final System Architecture

Date: 2026-07-26
Release review: Phase 7

## System statement

FarmLite is an implemented AI-assisted livestock management and
decision-support system. It combines livestock records, vaccination
management, milk-yield estimation, dry-matter-intake estimation,
environmental heat-stress calculation and rule-based ration guidance. The
current release operates within a declared supported model scope and fails
safely when required inputs or supported conditions are unavailable.

## Runtime architecture

```text
Farmer browser
  |
  +-- React 19 + TypeScript + Vite
  |     |
  |     +-- Firebase Authentication
  |     +-- Cloud Firestore records
  |     +-- jsPDF farmer reports
  |     +-- feature-gated request to Flask API v2
  |
  +-- Flask API
        |
        +-- API v1: retained milk model + nutrition rule engine
        +-- API v2: eligibility + backend THI + collected-data candidates
        +-- verified joblib artifacts and metadata
```

The frontend and backend are independent top-level applications. The frontend
does not contain model artifacts, a THI formula, or nutrition allocation
logic. The backend does not read or write Firebase data.

## Frontend

The frontend is in `frontend/` and uses:

- React 19, TypeScript and React Router;
- Vite 8 and Tailwind CSS;
- the Firebase Web SDK for Authentication and Firestore;
- Axios for Flask API calls;
- jsPDF for farmer-facing report generation;
- Lucide icons and Recharts for presentation.

`AuthProvider` observes the Firebase session. `ProtectedRoute` redirects an
unauthenticated visitor to `/login`. `MainLayout` provides the responsive
navigation shell and the logout action.

### Frontend routes

| Route | Protection | Purpose |
|---|---|---|
| `/login` | Public | Firebase email/password login |
| `/register` | Public | Firebase account and profile creation |
| `/forgot-password` | Public | Password-reset request |
| `/` | Protected | Dashboard |
| `/livestock` | Protected | Individual and batch livestock |
| `/livestock/:id` | Protected | Single-page animal profile |
| `/livestock/edit/:id` | Protected | Edit an animal |
| `/vaccinations` | Protected | Vaccination management |
| `/feed` | Protected | Feed inventory |
| `/ai-feed` | Protected | Feed and production recommendation |
| `/health` | Protected | Health records |
| `/health-tracking` | Protected | Alias for health records |
| `/notifications` | Protected | Due and status notifications |
| `/profile` | Protected | Farmer and farm settings |
| `/settings` | Protected | Existing non-functional placeholder route |

### Firebase integration

The configured Firebase application is initialized only from `VITE_FIREBASE_*`
environment variables. The source-observable collection paths are:

- `users`
- `livestock`
- `batches`
- `healthRecords`
- `vaccinations`
- `feedInventory`

Farm records use the existing `userId` ownership field. User profile documents
use the authenticated UID as the document ID. Several screens apply `userId`
filters in Firestore queries; some legacy screens fetch a collection and apply
the ownership filter in application code. Both patterns still depend on
server-enforced Firestore Security Rules for actual isolation.

No Firebase rules or deployment artifact is present in the repository. The
deployed temporary rule configuration was not read, changed, or deployed
during Phase 7.

## Flask backend

The Flask application is in `backend/flask_api/`. `create_app()` registers two
blueprints:

- `api/routes.py` for API v1;
- `api/v2_routes.py` for API v2.

The routes are:

| Method and path | Owner | Purpose |
|---|---|---|
| `GET /api/health` | Flask | Health check |
| `POST /api/ai/feed-recommendation` | API v1 | Milk estimate and rule-based ration |
| `POST /api/v2/predict` | API v2 | Eligibility, backend THI and feature-gated candidates |

API v1 retains its request and response contracts. API v2 validates a maximum
16 KiB JSON object, rejects unknown fields, checks primitive types and fails
closed at the eligibility layer.

Unexpected API errors return generic client messages. Development debug mode
is disabled unless `FLASK_DEBUG` is explicitly enabled.

## Recommendation orchestration

The farmer workflow has four independent owners:

| Farmer-facing output | Exact owner |
|---|---|
| Expected milk yield | FarmLite milk prediction model |
| Predicted dry-matter intake | Collected-data DMI model |
| THI value and category | Backend THI calculation |
| Advisory ration, roughage, concentrate, mineral mix, water advice, feeding frequency and ration warnings | FarmLite nutrition rule engine |

The frontend first obtains the existing v1 milk and ration result. When both
candidate flags are enabled, it independently requests API v2. A v2 failure
does not clear a successful v1 result. The internal second milk candidate may
exist in the v2 response for controlled evaluation, but the React UI and
farmer PDF never render it.

DMI is displayed in `kg DM/cow/day`. It is not total feed, fresh-feed weight or
an as-fed ration, and it is never converted into roughage or concentrate. THI
is calculated only by the backend. Breed never supplies or infers genetic
group.

## Model and rule assets

| Asset | Repository path |
|---|---|
| Retained FarmLite milk model | `backend/flask_api/ml/models/milk_yield_model.joblib` |
| Collected-data DMI candidate | `backend/flask_api/ml/models/candidates/bangladesh/bangladesh_dmi_regressor_candidate_v1.joblib` |
| DMI metadata | `backend/flask_api/ml/models/candidates/bangladesh/bangladesh_dmi_regressor_candidate_v1.metadata.json` |
| Internal collected-data milk candidate | `backend/flask_api/ml/models/candidates/bangladesh/bangladesh_milk_yield_regressor_candidate_v1.joblib` |
| Internal milk metadata | `backend/flask_api/ml/models/candidates/bangladesh/bangladesh_milk_yield_regressor_candidate_v1.metadata.json` |
| Nutrition rules | `backend/flask_api/ml/validation/nutrition_rules.py` |

Artifact paths are resolved under repository-controlled trusted roots, hashes
are verified before deserialization, feature order is checked against
metadata, and successful loads are cached.

## Reliability boundaries

- The v2 backend and frontend flags default to disabled independently.
- Unknown genetic group leaves DMI unavailable but preserves a valid backend
  THI result.
- Invalid weather produces a controlled fallback and no fabricated THI.
- Unsupported production status produces no unsafe model prediction.
- The `Local` genetic group is explicitly marked limited support.
- Abort and stale-response handling prevents an older v2 response from
  replacing current form state.
- Batch records use an owned Firestore listener and optimistic reconciliation
  by document ID.
- Error boundaries isolate route-level React failures.

## Deployment boundaries

The current release is appropriate for academic submission and controlled
decision-support evaluation. It is not unrestricted veterinary, commercial,
universal or multi-farm validation. Production deployment additionally
requires source-controlled and reviewed Firestore rules, an explicit CORS
policy, authenticated/API-gateway controls appropriate to the hosting model,
external dependency advisory review, browser accessibility testing and
external model validation.
