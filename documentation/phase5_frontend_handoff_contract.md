# Phase 5 frontend handoff contract

This is a handoff specification only. Phase 5 made no frontend or PDF change,
and frontend work requires separate authorization.

## Request

Future controlled clients would call `POST /api/v2/predict` with snake-case
JSON. The new field is `genetic_group`, using one exact value:

- `Local`
- `HF50`
- `HF62.5`
- `HF75`
- `HF87.5`

It must be a deliberate user/data-source selection. Never infer it from
`breed`, never convert a breed name to an HF percentage, and never accept an
approximate inheritance percentage.

Bangladesh prediction also needs measured `ambient_temperature_c` and
`humidity_percent`; humidity is 0-100 inclusive. There are no weather
defaults. `lactation_stage` must describe a supported early, mid, or late
lactating cow. Dry, non-lactating, calf, bull, unknown genetic group, or
invalid/missing environment inputs yield explicit null/fallback results.

The backend flag `BANGLADESH_CANDIDATE_MODELS_ENABLED` is false by default.
Frontend code must not assume that a registered endpoint means candidates
are enabled.

## Response handling

Read these sections independently:

- `prediction_status`: `DISABLED`, `ELIGIBLE`, `PARTIAL`, or
  `FALLBACK_REQUIRED`.
- `eligibility.dmi` and `eligibility.milk`: status, scope, fallback reason.
- `environment`: calculated and display THI, category, mapping version and
  verification.
- `ml_predictions`: nullable DMI and milk values.
- `model_sources` and `model_provenance`: explicit candidate identity,
  hashes, target, unit, contract and dataset.
- `warnings`, `limitations`, and `fallback_reasons`: never suppress these.
- `rule_recommendation`: all values remain null in this phase.

Do not render null as zero. Do not substitute a previous, synthetic, legacy,
or rule value unless a future approved contract names it explicitly. `Local`
must display its `LIMITED_SUPPORT` warning.

Any DMI display must say `kg dry matter/cow/day` and explain that it is not
total feed or fresh/as-fed weight. Milk uses `L/cow/day`. Candidate-only,
external-validation, environmental-overlap, and advisory limitations must be
shown with eligible output. There is no DMI-to-ration conversion, roughage,
concentrate, ingredient, mineral, or water calculation yet.
