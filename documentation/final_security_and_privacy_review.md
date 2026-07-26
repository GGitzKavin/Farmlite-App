# FarmLite Final Security and Privacy Review

Date: 2026-07-26

## Outcome

The source review found and corrected two concrete leaks:

1. API v1 returned raw unexpected exception text to the client.
2. `AuthProvider` logged the complete Firebase user object in the browser.

API v1 now returns a generic 500 message, a regression test proves private
exception text is absent, Firebase user logging is removed, and Flask debug
mode is disabled by default.

No Firebase configuration, user, data, provider, collection path, ownership
field or Security Rule was changed.

## Authentication and routes

- Firebase Authentication owns registration, login, logout, password reset
  and session restoration.
- All application routes other than login, registration and password reset
  are nested under `ProtectedRoute`.
- Frontend route protection is a user-experience control, not a substitute
  for Firestore Security Rules.
- The Flask prediction APIs do not currently enforce Firebase tokens. If
  exposed publicly, use an authenticated API gateway/token-validation layer
  and rate limits without changing the current JSON contracts.

## Firestore privacy

Farm records use `userId`; profile documents use the Firebase UID.
Vaccination, feed and batch queries include ownership predicates. Some legacy
screens fetch broader collection snapshots and filter returned data by
`userId` in application code.

This is safe only when deployed Firestore rules independently prevent
cross-user reads/writes. Frontend filtering must not be treated as the
security boundary.

The repository contains no `firestore.rules`, `firebase.json`,
`.firebaserc` or rules deployment snapshot. The exact current temporary rule
configuration could not be verified. This is the principal deployment
security limitation. It was documented without retrieving, editing or
deploying any rule.

## Secrets and environment

- Firebase client settings are loaded from `frontend/.env`.
- The `.env` file is ignored by Git.
- Phase 7 read only environment variable names, not their values.
- No tracked `.env`, PEM/key or service-account JSON file was found.
- A repository pattern scan found no private-key header, service-account
  identity or obvious Firebase key literal outside ignored dependencies/data.
- Model and report files contain no Firebase tokens or passwords.

Firebase web client configuration is not a substitute for Security Rules and
must not be treated as a server credential.

## Flask input and error handling

API v1:

- rejects a non-object/non-JSON body with HTTP 400;
- delegates retained-model field validation to `model_service`;
- preserves its success contract;
- returns a generic unexpected-error message.

API v2:

- limits requests to 16 KiB;
- requires a JSON object;
- rejects unknown fields;
- validates primitive types, finite values, text lengths and basic ranges;
- applies explicit eligibility rules;
- returns controlled 400, 422 and 500 responses;
- does not return an internal exception string.

Server logs can contain stack traces for unexpected faults. Logs must be
access-controlled, retained minimally and never returned to the browser.

## CORS

`CORS(flask_app)` currently enables a broad policy. This is acceptable only
for the current controlled development context. Configure an explicit trusted
origin allowlist at Flask or the deployment gateway before public exposure.
This was documented instead of changed because the target production origin
was not supplied and a guess could break API compatibility.

## Model artifact safety

- Candidate paths are resolved under a trusted repository root.
- Escaping the trusted root is rejected.
- Artifact and metadata SHA-256 values are checked before joblib loading.
- Metadata and exact feature order are validated.
- Hash mismatch, missing artifact and invalid metadata fail closed.
- No model, coefficient, metadata, feature order or nutrition rule changed.

Joblib artifacts are executable serialization formats. Only repository-owned,
hash-verified artifacts may be deployed.

## PDF content

- PDF text comes from the authenticated farmer’s selected records and
  prediction results.
- Dynamic text uses jsPDF text functions rather than HTML interpretation.
- Missing numeric values are normalized to **Unavailable**.
- Filenames are sanitized by the existing helper.
- PDFs can contain personal farm/animal information; users must store and
  share them accordingly.
- The internal candidate milk value is not included.

## Dependency review

- `python -m pip check`: pass, no broken requirements.
- `npm.cmd ls --omit=dev --depth=0`: pass, dependency tree resolves.
- A live `npm audit` could not be performed because sending the dependency
  manifest to the external registry was not authorized by the execution
  environment.

Run an approved dependency advisory/SBOM scan in the submission or deployment
pipeline before public release.

## Findings

| Severity | Finding | Disposition |
|---|---|---|
| High deployment | Deployed temporary Firestore rules are not source-visible | Documented; production gate requires review |
| Medium | Flask CORS is unrestricted | Configure trusted origins before public exposure |
| Medium | Flask APIs have no Firebase token enforcement | Protect at deployment boundary |
| Medium | Some frontend collection reads rely on client filtering | Requires strict server rules; no Firebase change made |
| Medium | Live npm advisory scan unavailable | Run in authorized pipeline |
| Low | Legacy console errors remain in non-auth UI flows | Avoid sensitive objects; future logging policy |
| Fixed | Raw v1 exception disclosure | Generic response plus regression test |
| Fixed | Full Firebase user-object console logging | Removed |
| Fixed | Flask development debug always enabled | Explicit opt-in only |

## Privacy scope

FarmLite processes farmer profile, contact, farm, animal, health and
vaccination data. The release should apply least privilege, documented
retention, account deletion/export procedures and restricted report sharing.
Those organizational controls are outside this repository and must be
completed by the deployer.
