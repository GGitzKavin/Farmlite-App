# FarmLite Frozen Hybrid Prediction Architecture

## Status

This architecture is frozen as a Phase 4.5E design proposal. No component is
connected to Flask, React, PDF generation, model serving, or nutrition rules.

## Proposed Flow

```text
Cow and measured environment inputs
  -> API v2 schema validation
  -> population/scope classification
  -> exact genetic-group validation
  -> server-side THI calculation and category mapping
  -> deterministic DMI and milk eligibility checks
      -> Bangladesh candidate prediction when eligible
      -> explicit source-specific fallback when ineligible
  -> ML/rule unit and provenance boundary
  -> approved nutrition rules only
  -> final response with value sources, explanations, warnings, limitations
```

Artifact existence, metadata compatibility, and SHA-256 verification occur
before any future `joblib.load`. Unknown categories are rejected before the
fitted encoder, even though it uses `handle_unknown="ignore"`.

## Component Responsibilities

| Component | Responsibility | Must not do |
|---|---|---|
| API v2 validation | Validate types, units, ranges, and conditional fields | Invent missing weather or genetic group |
| Scope classifier | Identify lactating study-like, limited, out-of-scope, or unresolved population | Treat breed as HF percentage |
| THI adapter | Calculate numeric THI and exact category from measured T/RH | Accept arbitrary client category or invent thresholds |
| Eligibility policy | Return deterministic model-specific status | Call an ineligible candidate |
| Candidate loader | Verify trusted path, metadata, and full hash before deserialization | Trust machine-specific path from metadata |
| Bangladesh DMI model | Produce only predicted dry-matter intake | Produce feed type, fresh-feed weight, ration, mineral, or water advice |
| Bangladesh milk model | Produce only predicted daily milk yield | Automatically replace another milk model |
| Fallback selector | Choose a separately eligible source or null | Hide the fallback source |
| Nutrition boundary | Check units, basis, prerequisites, and double counting | Assume DMI equals as-fed total feed |
| Nutrition rules | Produce explicitly rule-owned recommendation fields | Label outputs as ML |
| Explanation layer | Return provenance, limitations, and user warnings | Claim production, commercial, or veterinary readiness |

## Output Ownership

### ML outputs

- `predicted_dmi_kg_day` — Bangladesh DMI candidate only when eligible; kg
  dry matter/cow/day.
- `predicted_milk_yield_l_day` — the explicitly selected eligible milk source;
  L/cow/day.

No roughage, concentrate, feed category, mineral, water, or frequency value is
an output of either Bangladesh pipeline.

### Rule outputs

- feed/ration category;
- roughage quantity;
- concentrate quantity;
- mineral mix;
- water advice;
- nutrition warnings;
- feeding frequency if retained by a future approved contract.

Every numeric rule output must state its unit and whether it is dry matter or
as-fed.

### Derived or display outputs

- prediction status;
- DMI and milk eligibility;
- population scope classification;
- calculated numeric THI;
- derived THI category;
- model/fallback source;
- fallback reason;
- value-source map;
- confidence/scope warning;
- artifact and contract versions;
- limitations and disclaimers.

## DMI-to-Nutrition Boundary

The current rule path cannot consume Bangladesh DMI safely. Before that
connection can exist, an approved nutrition design must define:

- whether ration quantities are on dry-matter or as-fed basis;
- per-feed dry-matter fractions or moisture content;
- ingredient/ration allocation;
- whether mineral amounts are included in or additional to total DMI;
- how predicted milk affects requirements without double counting;
- acceptable adjustment and refusal behavior.

Until those requirements are resolved, predicted DMI may be displayed only as
a standalone research signal and all dependent rule fields must be null,
unchanged legacy outputs with separate provenance, or unavailable.

## Milk-Source Boundary

No permanent primary milk model is frozen. A future selector may consider:

1. Bangladesh candidate when its narrow scope and inputs are satisfied.
2. Phase 4 synthetic candidate when separately approved for research.
3. Existing retained legacy model while the current route remains unchanged.
4. User-provided historical milk as non-ML evidence.
5. No prediction.

The source must be returned. External validation is required before a stronger
selection.

## Frozen Failure Behavior

- Missing/unknown model input: candidate not called, null output, explicit
  fallback.
- Invalid environment: validation result, candidate not called.
- Out-of-scope population: candidate not called.
- Artifact missing/hash mismatch: refuse deserialization.
- Model error/non-finite output: discard candidate value and fall back.
- Rule prerequisite missing or unit basis unresolved: rule output null or
  legacy output clearly separated; never fabricate.

## Architecture Approval Boundary

The frozen design supports the Phase 5 recommendation
`CONDITIONAL_INTEGRATION_REQUIRES_NEW_INPUT`. It does not authorize
implementation. The new input is an explicit, documented `genetic_group`;
measured temperature/humidity must also stop using silent candidate defaults.
