# Phase 5 API v2 validation

Status: PASS for the controlled backend prototype.

## Route and HTTP policy

- Route: `POST /api/v2/predict`.
- HTTP 200: eligible prediction, candidate disabled, documented ineligibility,
  artifact/model fallback, or partial model availability.
- HTTP 400: malformed JSON or a JSON value that is not an object.
- HTTP 422: primitive/schema errors, unknown fields, or a body over 16 KiB.
- HTTP 500: unexpected server failures only, with private exception text
  excluded from the response.

The existing `/api/health` and `/api/ai/feed-recommendation` routes retain
their prior behavior and response formats.

## Controlled Flask-client results

| Case | HTTP | Result |
|---|---:|---|
| Flag false, empty JSON object | 200 | `DISABLED`; both predictions null; `FEATURE_DISABLED`; no loader call |
| Flag true, HF75, T=28 C, RH=75% | 200 | Both candidates predicted; THI 79.045, category T1 |
| Flag true, unknown genetic group | 200 | Both predictions null; `GENETIC_GROUP_UNKNOWN` |
| Flag true, humidity 100.1% | 200 | Both predictions null; `ENVIRONMENT_INVALID` |
| Flag true, malformed JSON | 400 | `INVALID_JSON` |
| Flag true, invalid primitive type | 422 | Controlled field errors |
| Flag true, oversized body | 422 | `REQUEST_TOO_LARGE` |
| Simulated DMI hash mismatch | 200 | DMI null; valid milk preserved; explicit partial result |

The eligible controlled request returned DMI
`11.390466994631726 kg dry matter/cow/day` and milk
`6.654754896938108 L/cow/day`. These are deterministic candidate outputs for
the categorical input and are not production claims.

## Response ownership

ML values appear only under `ml_predictions`. Model names and reviewed
hash/contract/dataset provenance are explicit. `rule_recommendation` remains
entirely null. No legacy or synthetic fallback model is called by v2.

Validation evidence: 56 focused Phase 5 tests and 307 complete backend tests,
all passing on 2026-07-26.
