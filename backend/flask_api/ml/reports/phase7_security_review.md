# Phase 7 Security Review

Date: 2026-07-26
Result: `PASS_WITH_DOCUMENTED_DEPLOYMENT_LIMITATIONS`

## Corrected findings

| Finding | Correction | Verification |
|---|---|---|
| v1 returned raw unexpected exception text | Generic 500 message and server-side log only | Regression test passes |
| Auth provider logged complete Firebase user object | Debug/user-object logging removed | Typecheck and focused lint pass |
| Flask development debug was always enabled | `FLASK_DEBUG` explicit opt-in | Source review and compileall |

## Authentication and authorization

Public frontend routes are login, registration and password reset. All
application pages are nested below `ProtectedRoute`. Firebase owns account
and session behavior.

Firestore records retain `userId`; profiles retain UID document ownership.
Frontend ownership filtering is not a security boundary. The repository has
no deployed-rule snapshot, so cross-user server enforcement cannot be proven.
No rule was retrieved, changed or deployed.

The Flask prediction endpoints do not validate Firebase ID tokens. Apply
gateway/token enforcement and rate limits before public exposure.

## Input/error review

- v1 rejects invalid JSON and uses retained model validation.
- v2 enforces a 16 KiB limit, JSON-object shape, known fields, types, finite
  numbers, text limits and eligibility.
- v1/v2 unexpected responses do not return internal exception text.
- Server stack traces must remain in access-controlled logs.
- CORS is broad and needs an explicit production allowlist.

## Secrets review

- `frontend/.env` is Git-ignored.
- Only Firebase variable names were recorded.
- No tracked env, service-account, PEM/key or obvious private-key material was
  found.
- No password, Firebase token or service credential was added to reports.

## Model/PDF review

- Candidate paths are restricted to a trusted root.
- Artifact and metadata hashes are verified before joblib loading.
- Invalid/missing/mismatched artifacts fail closed.
- PDF values are text-rendered, null-safe and exclude internal candidate milk.
- PDFs contain farmer/animal information and must be handled as private data.

## Dependencies

- Python `pip check`: pass.
- Local npm production dependency tree: pass.
- External npm advisory lookup: not completed because manifest egress was not
  authorized.

## Open findings

| Severity | Finding | Required action |
|---|---|---|
| High deployment | Temporary deployed Firestore rules not source-visible | Export and independently review before deployment |
| Medium | Broad CORS | Configure exact trusted origins |
| Medium | Flask APIs lack Firebase token enforcement | Add deployment-boundary authentication |
| Medium | Some broad Firestore collection reads | Depend on/verify strict rules; later use owned queries |
| Medium | External advisory scan unavailable | Run approved SBOM/advisory pipeline |
| Low | Legacy console error statements | Establish sanitized structured logging |

No frozen Firebase configuration, model artifact, metadata, THI rule or
nutrition rule was changed.
