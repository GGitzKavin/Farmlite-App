# Phase 5 Bangladesh backend integration design

## Decision

Phase 5 implements a backend-only, disabled-by-default prototype at
`POST /api/v2/predict`. It does not change v1 behavior, frontend requests,
PDF generation, nutrition logic, or model training. Both Bangladesh models
remain `CANDIDATE_ONLY`.

## Request flow

1. Flask rejects a body over 16 KiB, malformed JSON, or non-object JSON.
2. The dynamic feature flag is read. False returns a structured disabled
   response before schema, THI, eligibility, or artifact loading.
3. Enabled requests are validated against the frozen snake-case v2 fields.
4. Temperature and humidity are validated without defaults. Server-side THI
   and T0/T1/T2 are derived from the approved contract.
5. Lactating-cow scope and explicit `genetic_group` are checked fail-closed.
   Breed is never an adapter for genetic group.
6. For eligible input, DMI and milk artifacts are verified and loaded
   independently. The feature frame is exactly
   `genetic_group, thi_category`.
7. Each scalar is checked for numeric, finite, nonnegative, and
   study-observed-range sanity without clipping.
8. A failure leaves that prediction null. An independently valid peer
   prediction is retained as `PARTIAL`; no alternate model is invoked.

## Component ownership

| Component | Responsibility |
|---|---|
| `api/v2_schemas.py` | Primitive JSON schema and size-related constants |
| `api/v2_routes.py` | HTTP policy, feature gate, controlled exceptions |
| `bangladesh_thi.py` | Exact formula, boundaries, trace metadata |
| `bangladesh_eligibility.py` | Population/category fail-closed decisions |
| `bangladesh_artifact_loader.py` | Trusted paths, hashes, metadata, safe cache |
| `bangladesh_model_service.py` | Independent predictions and structured provenance |

Successful loads are cached under a reentrant lock. Failed verification and
failed deserialization are never cached. The path is resolved under
`ml/models/candidates/bangladesh`; metadata absolute locator text is never
used to select a runtime artifact.

## Response semantics

The response separates `ml_predictions`, `model_sources`,
`model_provenance`, and null-only `rule_recommendation`. DMI remains kg dry
matter/cow/day; milk remains L/cow/day. THI includes the unrounded value,
separate two-decimal display value, category, mapping version, verification
status, and source. Warnings and limitations identify candidate status,
external-validation absence, environmental overlap uncertainty, and study
range semantics.

HTTP 200 is used for predictions, disabled state, ineligibility, artifact
fallback, and partial results. Malformed JSON uses 400, primitive/schema
failures use 422, and unexpected server failures use 500.
