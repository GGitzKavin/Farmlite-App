# Phase 6 controlled frontend integration design

Date: 2026-07-26
Status: implemented, disabled by default

## Scope

Phase 6 adds a separate, controlled frontend path for the Phase 5 Bangladesh
DMI and milk candidates. It does not replace or merge with the existing
FarmLite feed-recommendation path. No model, model loader, THI formula,
nutrition rule, dataset, or candidate-selection policy is changed.

The pre-change flow and insertion points are recorded in
`phase6_frontend_existing_flow_audit.md`.

## Feature controls

| Layer | Flag | Default | Accepted enabled values |
|---|---|---|---|
| Frontend build | `VITE_BANGLADESH_CANDIDATE_UI_ENABLED` | false | `1`, `true`, `yes`, `on` |
| Backend runtime | `BANGLADESH_CANDIDATE_MODELS_ENABLED` | false | `1`, `true`, `yes`, `on` |

Missing, empty, malformed, and all other values evaluate to false. No
committed environment file enables either flag. When the frontend flag is
false, the selector and research result section are absent and no v2 request
can start.

## Input ownership

`FeedRecommendation.tsx` continues to own the form. Phase 6 adds only the
controlled `geneticGroup` state and the separate candidate request state.

The genetic-group selector has an unselected placeholder and submits one
exact value:

- `Local`
- `HF50`
- `HF62.5`
- `HF75`
- `HF87.5`

It is reset when a different cow is selected and is never populated from
breed. `hf_inheritance_percent` does not exist in the frontend contract.

The legacy v1 form defaults for temperature and humidity remain available
when candidate UI is disabled. When candidate UI is enabled, those two
fields begin empty so that the candidate path cannot silently reuse the
legacy 28 C and 70% values as measurements. An absent or invalid candidate
weather value suppresses only the v2 request; the existing recommendation
may still proceed.

## Request construction and transport

`src/features/bangladeshCandidate.ts` constructs the v2 payload. It validates:

- an exact supported genetic group;
- a finite Celsius temperature;
- finite humidity in the inclusive range 0-100.

Optional values are included only when present and valid. The frontend never
sends a THI or THI category.

`src/api/bangladeshCandidate.ts` provides the isolated typed client. It:

- uses the existing `VITE_FLASK_API_URL` convention;
- posts JSON to `/api/v2/predict`;
- converts controlled 400, 422, 500, network, cancellation, and malformed
  response cases into `CandidateApiError`;
- validates the response status, eligibility, environment, nullable
  predictions, sources, null-only rule boundary, warnings, limitations, and
  fallback reasons;
- does not call v1 or another model as a candidate fallback;
- does not log cow payloads.

## Orchestration

The existing v1 request remains a direct, independent Axios call to
`/api/ai/feed-recommendation`. When candidate UI is enabled, v2 starts as a
second request only after candidate prerequisites pass.

The two paths have separate response, loading, error, and notice state.
Candidate failure cannot clear a valid v1 result, and a candidate result
does not hide a v1 failure. An `AbortController` plus request sequence
protects against stale responses. Changing any candidate request field
aborts and clears the prior candidate result.

## Result presentation

`ResearchPredictions.tsx` is a distinct research-prototype section after the
existing recommendation. It displays:

- predicted DMI as `kg dry matter/cow/day`;
- predicted milk as `L/cow/day`;
- model source, eligibility, and scope for each value;
- backend-calculated THI, category, mapping version, verification status,
  and backend source;
- concise priority warnings with additional warnings, limitations, and
  fallback reasons in an expandable area.

Null stays distinct from zero and displays as `Unavailable`. The existing
milk result is labelled `Existing FarmLite prediction flow`; ration values
are labelled `Existing FarmLite rule engine`.

## PDF boundary

`appendResearchPredictionsToPdf` appends an optional section only when a v2
response exists. Existing report content remains in its original order.
The research section includes explicit sources, units, supplied genetic
group, eligibility/scope, THI, warnings, limitations, `Research prototype`,
and `Not veterinary advice`.

No DMI-to-ration conversion exists in UI or PDF code.

## Accessibility and responsive behavior

The new selector and candidate weather errors use explicit labels, ids,
`aria-describedby`, `aria-invalid`, and alert roles. Native select behavior
supports keyboard operation. Expandable details have visible focus styling.
The result grid collapses to one column, uses `min-w-0` and wrapped text, and
does not introduce a fixed width or horizontal overflow.

## Phase boundary

This implementation is research-only and production approval remains false.
Phase 7 system validation is not part of this work.
