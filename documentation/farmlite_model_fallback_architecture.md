# FarmLite Model Fallback Architecture

## Principles

- Fallback is explicit, machine-readable, and visible to the user.
- Ineligibility never calls the Bangladesh pipeline.
- DMI is not silently replaced with a total-feed or feed-quantity model.
- A historical milk value remains historical evidence, not an ML prediction.
- The Bangladesh and synthetic milk candidates remain separate-provenance
  research candidates. Neither is automatically the production winner.
- Rule values are always labelled as rules, even when they consume an ML
  signal.

## DMI Fallback

1. Use `BANGLADESH_DMI_CANDIDATE_V1` only when its deterministic eligibility
   result is `ELIGIBLE`.
2. If ineligible, use an independently approved transparent DMI rule only when
   its required inputs, units, limits, and provenance are satisfied.
3. Otherwise return DMI prediction unavailable with the exact fallback reason.
4. Never substitute the rejected synthetic `Feed_Quantity_kg` experiment, the
   current `totalFeedKg` formula, or any unrelated milk model.

No current FarmLite rule is approved as a DMI fallback. The current weight and
milk formula produces an ambiguously based total-feed quantity, not verified
dry-matter intake.

## Milk Fallback

Milk source selection remains a future policy decision:

- Bangladesh candidate: observed study target, two categorical inputs, small
  population, grouped validation, limited external scope.
- Phase 4 synthetic candidate: large sample and better FarmLite feature
  compatibility, but publisher-declared synthetic target relationships and no
  real-world validity.
- Existing retained FarmLite milk model: current legacy runtime behavior; it
  must remain explicitly labelled and unchanged during Phase 4.5E.
- User-entered prior milk: historical observation, never a model prediction.
- No-ML: null prediction plus unavailable/fallback explanation.

The current review decision is `EXTERNAL_VALIDATION_REQUIRED`; it does not
select a permanent primary milk model.

## Decision Matrix

| Situation | DMI source | Milk source | Explanation | Warning |
|---|---|---|---|---|
| Supported HF genetic group, valid environment, lactating cow, valid artifacts | `BANGLADESH_DMI_CANDIDATE_V1` | `BANGLADESH_MILK_CANDIDATE_V1` for controlled research route only | Both candidates are eligible from the same two input categories | Candidate-only, 50-cow Bangladesh scope, no external validation |
| `Local` study category with valid environment | Bangladesh DMI candidate with `LIMITED_SUPPORT` | Bangladesh milk candidate with `LIMITED_SUPPORT` | Known training category, grouped development evidence | No Local cow in locked final holdout |
| Unknown genetic group | `NONE` unless a separately approved DMI rule exists | Legacy/synthetic source only if separately eligible and explicitly named; otherwise user history or `NONE` | Bangladesh pipeline is not called | Genetic group cannot be inferred from breed |
| Missing temperature or humidity | `NONE` unless approved DMI rule exists | Explicit non-Bangladesh source if separately eligible; otherwise user history or `NONE` | THI cannot be calculated without measured inputs | Weather defaults are prohibited |
| Invalid humidity or environment calculation | `NONE` | Explicit non-Bangladesh source or `NONE` | Candidate eligibility is `INVALID_ENVIRONMENT_INPUT` | Correct the environmental input |
| Non-HF breed without verified `Local` study-equivalent record | `NONE` | User history or non-Bangladesh model only if its own scope permits | Study population equivalence is absent | Out-of-scope population |
| Dry lactation stage | `NONE` | `NONE` as Bangladesh prediction; historical value may be displayed only | Bangladesh population was lactating | Do not treat a dry cow as study-like |
| Calf, bull, or non-lactating cow | `NONE` | `NONE` | Target population is incompatible | Out-of-scope population |
| Candidate artifact unavailable | Approved transparent DMI rule or `NONE` | Existing explicitly named model if separately available, user history, or `NONE` | Artifact availability check fails before loading | Candidate artifact unavailable; fallback source shown |
| Candidate hash mismatch | `NONE` | Non-Bangladesh source or `NONE` | Refuse deserialization | Integrity failure; administrator action required |
| Model prediction failure/non-finite output | Approved transparent DMI rule or `NONE` | Non-Bangladesh source, user history, or `NONE` | `MODEL_ERROR`, then explicit fallback | Candidate result was not used |

## Fallback Response Requirements

Every fallback response must provide:

- eligibility result for DMI and milk separately;
- stable fallback reason code;
- requested and selected model source;
- null for every unavailable ML output;
- source label for historical or rule-derived values;
- warning explaining why the candidate was not called;
- no fabricated zero value.

## No Double Counting

If a future nutrition layer consumes predicted DMI, it must not also add the
current weight-based base feed and milk-support quantity as though all three
were independent feed requirements. The rule owner must define one explicit
material basis and computation chain.
