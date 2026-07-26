# FarmLite Final Testing and Evaluation

Date: 2026-07-26

## Decision

`SYSTEM_READY_WITH_DOCUMENTED_LIMITATIONS`

The integrated application passed its automated functional, model-integrity,
build, type and runtime-smoke checks. Submission readiness is limited by
unavailable live Firebase/rules verification, unavailable browser-based
viewport/accessibility automation, unavailable visual PDF rendering, six
inherited repository-wide ESLint findings and an external npm advisory query
that was not authorized.

## Final automated results

| Area | Command/evidence | Result |
|---|---|---|
| Phase 6 frontend | `npm.cmd run test:phase6` | 25/25 pass |
| Phase 6.1 frontend/PDF | `npm.cmd run test:phase6.1` | 32/32 pass |
| Phase 6.2 frontend | `npm.cmd run test:phase6.2` | 30/30 pass |
| Phase 6.3 frontend | `npm.cmd run test:phase6.3` | 18/18 pass |
| Frontend aggregate | All existing frontend tests | 105/105 pass |
| Backend | `python -m unittest discover -s tests` | 308/308 pass |
| TypeScript | `npm.cmd exec tsc -- -b` | Pass |
| Phase-scoped ESLint | Phase 6/7 source with inherited effect rule excluded | Pass |
| Repository ESLint | `npm.cmd run lint` | 6 inherited errors |
| Feature-enabled build | `VITE_BANGLADESH_CANDIDATE_UI_ENABLED=true` | Pass |
| Feature-disabled build | default flag | Pass |
| Python compilation | `python -m compileall -q app.py config api ml tests` | Pass |
| Python dependency integrity | `python -m pip check` | Pass |
| Frontend dependency tree | `npm.cmd ls --omit=dev --depth=0` | Pass |
| Runtime preview | Vite preview at `127.0.0.1:4174` | HTTP 200 |

The final backend suite was rerun after advancing authorized Phase 7
route/frontend hash snapshots. No implementation source was changed after the
successful full rerun.

## Recommendation scenarios

### Supported cow

A controlled lactating HF75 cow returned:

- one farmer-facing v1 milk estimate;
- DMI `11.390466994631726 kg DM/cow/day`;
- backend THI `79.045`, display `79.05`, category `T1`;
- the independent v1 advisory ration and composition;
- warnings/limitations;
- a valid two-page PDF buffer.

The measured v1 fixture produced one milk value of `14.56 L/day` and advisory
ration `14.87 kg/day`. These are controlled dynamic outputs, not production
constants.

### Unknown genetic group

API v2 returned `FALLBACK_REQUIRED`, `GENETIC_GROUP_MISSING`, null DMI and a
valid backend THI. Frontend tests verify that the v1 milk/ration result remains
and null is never presented as zero.

### Invalid weather

Invalid humidity produced controlled `FALLBACK_REQUIRED` behavior. Eligibility
tests cover missing, non-numeric and out-of-range weather. The frontend
contains no THI formula, so no THI is fabricated.

### Candidate backend unavailable

Artifact-unavailable and hash-mismatch tests preserve successful independent
outputs. Frontend orchestration tests confirm that a failed v2 request cannot
clear a successful v1 result. No second milk value appears.

### Feature flags disabled

Backend and frontend flags default false. Disabled-mode tests verify no
candidate load/request, no candidate cards and retention of the compatible v1
result/PDF.

### Unsupported production status

Dry, non-lactating, calf and bull cases return out-of-scope/fallback states
without model values.

### Local genetic group

The response remains eligible only with `LIMITED_SUPPORT`. Farmer-facing
documentation does not claim full support.

## Functional evaluation

### Authentication

Code inspection confirms registration, login, logout, protected routing,
session observation, invalid-login errors, profile loading and new-user empty
states. Phase 7 removed full Firebase user-object console logging. No live
account was created, deleted or changed, and no live login was performed.
Status: pass by implementation review, with live-environment limitation.

### Dashboard

Targeted tests verify all required sections, real collection sources, 7-day
and 30-day vaccination windows, existing navigation, loading/empty states,
mobile overflow guards and no duplicate/fabricated statistics.

### Livestock and batches

Tests and code inspection verify individual CRUD flows, search/filter paths,
the **Livestock** field, excluded poultry choices for individuals, retained
legacy values, batch poultry choices, owned listener, immediate insert,
reconciliation, search/filter reset and visible statuses. Live destructive
CRUD was not performed against Firebase.

### Animal profile, health, vaccination and notifications

The single-page animal profile, hidden-but-preserved gender, health/medical
sections, vaccination due/overdue/upcoming handling, empty histories,
deduplicated notifications and relevant links passed source/test contracts.
Live stored data was not mutated.

### Profile

Farm Type load/save compatibility, trimming, whitespace rejection,
80-character maximum and accessible error linkage passed. Required About
wording is present.

## PDF evaluation

Automated jsPDF cases verify:

- approved title;
- one milk value and no internal second milk;
- separate DMI, THI and ration;
- correct ownership labels;
- DMI/ration clarification;
- DOI note;
- footer and page numbers;
- null-safe values;
- two pages and non-empty buffers.

Additional Phase 7 buffers:

| Case | Pages | Bytes |
|---|---:|---:|
| Complete result | 2 | 38,399 |
| DMI unavailable | 2 | 38,392 |
| Long animal name | 2 | 38,479 |
| Long warning | 2 | 39,810 |
| Missing optional values | 2 | 38,418 |

PDF generation over five in-process samples averaged 6.564 ms with a
21.559 ms maximum. No visual PDF renderer was installed, so pixel-level
overflow and heading/value visual inspection remains a manual pre-submission
check.

## Responsive and accessibility evaluation

Responsive class contracts cover 320, 375, 768, 1024 and desktop behavior:
`min-w-0`, `overflow-x-hidden`, single-column mobile grids, breakpoint grids,
wrapped text and full-width mobile actions. Targeted tests pass. No browser
automation was installed, so screenshots and physical horizontal-scroll
measurement at those widths were not performed.

Accessibility tests/source review confirm labels in the Phase 6 recommendation
flow, keyboard-native controls, focus styling, `aria-invalid`,
`aria-describedby`, alert/status roles in changed critical components,
meaningful buttons and text status labels. A full axe/browser audit was not
available. Some legacy forms/loading spinners do not consistently expose all
labels/status announcements and remain documented follow-up work.

## Performance

- Feature-enabled and default-disabled production output: 2,018,272 bytes
  uncompressed.
- Main application chunk: 1,567,555 bytes; Vite large-chunk warning retained.
- Warm in-process API v1 mean: 3.297 ms over five requests.
- Warm in-process API v2 mean: 3.374 ms over five requests.
- Repeated v1 milk and v2 DMI results were consistent.
- Vite preview returned HTTP 200 and a valid React root.
- No runtime crash, memory symptom or unhandled client response was observed.

These are local development measurements, not network or production load
benchmarks.

## Known non-blocking findings

Repository ESLint reports six inherited errors:

- one unused error-boundary parameter;
- five React `set-state-in-effect` findings across recommendation, health,
  livestock and notifications flows.

TypeScript, builds, runtime tests and focused lint pass. The findings are
recorded rather than refactored under the Phase 7 no-broad-rewrite policy.
