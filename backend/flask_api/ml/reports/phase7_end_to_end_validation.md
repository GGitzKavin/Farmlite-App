# Phase 7 End-to-End Validation

Date: 2026-07-26
Decision: `SYSTEM_READY_WITH_DOCUMENTED_LIMITATIONS`

## Method

Validation combined repository inventory, source inspection, all existing
frontend/backend tests, controlled Flask test-client scenarios, two production
build modes, local Vite runtime smoke, PDF buffer generation, hash checks,
compile/type/lint checks and Git checks.

Firebase configuration and stored data were frozen. No live registration,
login, CRUD mutation, rule retrieval or rule deployment was performed.
Consequently, Firebase conclusions are implementation/test based rather than a
destructive live run.

## Authentication

Result: **PASS WITH LIMITATION**

- registration calls Firebase account creation, profile update and
  `users/{uid}` creation;
- login uses email/password and reports invalid credentials;
- logout uses Firebase `signOut`;
- `ProtectedRoute` guards all application pages;
- `onAuthStateChanged` restores the session;
- profile/empty-state paths are implemented;
- Firebase user-object debug logging was removed.

Limitation: no live account/session was changed.

## Dashboard

Result: **PASS**

Quick Actions, Attention Required, Upcoming Vaccinations, Livestock Overview,
Batch Overview, Recent Activity and Feed Inventory Levels are present.
Phase 6.2 tests verify real Firestore collection sources, distinct due
windows, loading/empty states, navigation, mobile overflow containment and no
duplicated/fabricated summary statistics.

## Individual livestock

Result: **PASS WITH LIVE-DATA LIMITATION**

CRUD handlers, confirmation, search, **All Livestock**, category filtering,
validation, empty states and selected-animal navigation are present.
The Add Animal field is visibly/accessibly **Livestock**. Chicken and Duck are
absent from individual choices. Approved types and historical stored values
remain available during editing. Live CRUD was not executed.

## Batches

Result: **PASS WITH LIVE-DATA LIMITATION**

Phase 6.3 tests verify owned Firestore listener, immediate insertion after a
successful write, no refresh requirement, reconciliation by document ID,
search/filter reset, ownership filtering and visible status text. Edit/delete
and listener error paths are present. Batch choices retain Chicken and Duck.
Responsive FarmLite palette/card contracts pass. Live writes were not made.

## Animal profile

Result: **PASS**

The page is a continuous Animal Profile, Health Status, Medical and
Vaccinations flow. Gender is absent from display but preserved in types/edit
data. Obsolete tabs are absent and existing health/vaccination actions remain
reachable.

## Health and vaccination

Result: **PASS WITH LIVE-DATA LIMITATION**

Create/edit/delete handlers, date parsing, due/overdue/upcoming classification,
history, animals without records, status text and dashboard/notification
integration are present and covered by source/contract tests. Invalid data is
not converted into a fabricated date. Live Firestore mutations were excluded.

## Notifications

Result: **PASS**

List and empty-state behavior, deduplication, relevant navigation and
subtitle removal are present. Notifications are calculated from stored record
conditions rather than placeholder alerts.

## Profile

Result: **PASS**

Profile loading and section saves remain. Farm Type loads as unchanged text,
trims on save, rejects whitespace-only input, enforces 80 characters and
exposes `aria-invalid`/`aria-describedby`. The required About wording is
present.

## Feed and production scenarios

| Scenario | Result | Evidence |
|---|---|---|
| Supported cow | Pass | v1 milk/ration plus v2 DMI/THI; PDF valid |
| Unknown genetic group | Pass | DMI null; valid THI preserved; v1 flow preserved |
| Invalid weather | Pass | Controlled fallback; no frontend THI calculation |
| Candidate backend unavailable | Pass | Partial-artifact and failed-request tests preserve v1 |
| Flags disabled | Pass | No candidate load/request/cards; v1 retained |
| Unsupported production status | Pass | Dry/non-lactating/calf/bull fail closed |
| Local genetic group | Pass with limitation | Explicit `LIMITED_SUPPORT` |

Across all scenarios:

- one milk prediction is farmer-facing;
- internal candidate milk is absent from UI/PDF;
- DMI uses kg DM/cow/day and never zero fallback;
- DMI is not labelled total feed or ration;
- ration quantities come only from the nutrition rule engine;
- THI comes only from the backend;
- displayed fixture outputs were dynamic.

## Output ownership

Result: **PASS**

UI/PDF tests enforce:

- FarmLite milk prediction model — expected milk yield;
- Collected-data DMI model — predicted DMI;
- Backend THI calculation — THI value/category;
- FarmLite nutrition rule engine — ration and feeding advice.

Misleading model-generated ration wording is absent.

## PDF

Result: **PASS WITH VISUAL LIMITATION**

The approved title, selected-animal summary, one milk result, separate
DMI/THI/ration, clarification, ownership labels, DOI note, page numbers,
footer and disclaimer are enforced. Controlled complete, DMI-unavailable,
long-name, long-warning and missing-optional fixtures each produced two
non-empty pages. No installed renderer was available for pixel-level review.

## Responsive

Result: **PASS WITH BROWSER LIMITATION**

Required breakpoint/overflow/wrapping contracts and mobile navigation are
present. No browser automation was available to measure all five widths.

## Accessibility

Result: **PASS WITH LEGACY LIMITATIONS**

Critical Phase 6/7 forms/cards expose labels, focus rings, accessible
validation and alert/status semantics. Text labels accompany color states.
No full axe, contrast tool or screen-reader run was available, and some legacy
forms/spinners do not consistently expose all associations/announcements.

## Security and privacy

Result: **PASS WITH DEPLOYMENT LIMITATIONS**

Raw v1 exception disclosure, Firebase user logging and always-on debug were
corrected. Secrets scan, ignored `.env`, input validation and artifact path
controls pass. Deployed Firestore rules are unavailable, CORS is broad, Flask
does not validate Firebase tokens, and an external npm advisory query was not
authorized.

## Performance and reliability

- v1 mean: 3.297 ms over five warm in-process requests;
- v2 mean: 3.374 ms over five warm in-process requests;
- repeated values: consistent;
- PDF mean: 6.564 ms over five in-process generations;
- production output: 2,018,272 bytes;
- local preview: HTTP 200;
- stale/abort and batch listener contracts: pass;
- crashes/memory symptoms: none observed;
- known warning: 1,567,555-byte main chunk.

## Final automated totals

- frontend: 105 passed, 0 failed;
- backend: 308 passed, 0 failed;
- TypeScript: pass;
- phase-scoped ESLint: pass;
- repository ESLint: six inherited errors;
- feature-enabled build: pass;
- feature-disabled build: pass;
- compileall: pass;
- artifact/metadata/rule integrity: pass.

## Remaining limitations

1. Firestore rules and live authorization behavior require an authorized
   witnessed review.
2. Browser viewport/accessibility and visual PDF inspection remain manual.
3. Repository lint debt and large chunk warning remain.
4. Public deployment needs explicit CORS/API authentication controls.
5. Model claims remain inside the declared limited validation scope.
