# Bangladesh Candidate Scope and Limitations

## Candidate Population

The candidates were developed from one Bangladesh HF-cross study conducted at
the Central Cattle Breeding and Dairy Farm, Savar:

- 50 lactating cows;
- five groups of ten cows: `Local`, `HF50`, `HF62.5`, `HF75`, `HF87.5`;
- three assigned THI categories: `T0`, `T1`, `T2`;
- five replications per cow/category;
- 15 repeated observations per cow and 750 rows;
- study period January–December 2024.

The repeated rows are not 750 independent animals.

## Observed Outcome Scope

| Outcome | Study range | Unit |
|---|---:|---|
| Dry-matter intake | 4.48–14.82 | kg dry matter/cow/day |
| Milk yield | 0.30–10.47 | L/cow/day |

These ranges describe the source records. They are not clinical limits,
clamping bounds, nutrition targets, or evidence that a prediction outside the
range is correct. A future out-of-range prediction must remain unclamped,
receive a scope warning, and be reviewed as `LIMITED_SUPPORT` or `MODEL_ERROR`
under an approved monitoring policy.

## Scope Matrix

| Population or condition | Status | Reason and required behavior |
|---|---|---|
| Lactating cow with exact `HF50`, `HF62.5`, `HF75`, or `HF87.5` and valid THI inputs | `IN_SCOPE` | Matches model category structure and locked holdout category coverage; still only an in-study prototype |
| Study-like cow recorded as `Local` | `LIMITED_SUPPORT` | Known trained category with grouped development evidence, but no Local cow occurred in the locked holdout |
| Other non-HF animal or unverified “local” population | `OUT_OF_SCOPE` | The study's Local group cannot represent every non-HF population |
| Unknown crossbreed percentage | `OUT_OF_SCOPE` | No safe breed-to-percentage mapping |
| Dry cow | `OUT_OF_SCOPE` | Study population was lactating |
| Non-lactating cow | `OUT_OF_SCOPE` | Target relationships were observed in lactating cows |
| Calf | `OUT_OF_SCOPE` | Different physiological and feeding population |
| Bull | `OUT_OF_SCOPE` | Milk target is inapplicable and population is absent |
| Cow outside Bangladesh/study management conditions | `UNRESOLVED` | Cross-population validity has not been established |
| Valid formula result in `T0`, `T1`, or `T2` | `LIMITED_SUPPORT` | Category matches, but numeric T/RH/THI source ranges are absent |
| Missing or invalid environment | `OUT_OF_SCOPE` for candidate call | Candidate must not run; use explicit fallback |
| Prediction outside observed DMI or milk range | `LIMITED_SUPPORT` | Do not clamp; warn and monitor |

## Important Model Limits

- Only `genetic_group` and `thi_category` are predictive features.
- Predictions largely reflect group/category average structure, not individual
  cow state.
- Body weight, parity, DIM, lactation stage, BCS, ration, prior yield, and
  numeric weather variation are absent from the Bangladesh models.
- The DMI offered/refusal protocol is not fully documented.
- Numeric temperature, humidity, and THI are absent from the workbooks.
- Milk sampling details and quality-control procedures remain incomplete.
- One locked holdout cow (`510`) had weak milk R² of approximately `-0.0110`,
  despite good pooled holdout performance.
- The final holdout contained no `Local` cows.
- No external farm or cross-population validation has occurred.
- No feed type, ration ingredient, roughage, concentrate, mineral, water, or
  expert recommendation labels were trained.

## Required Warnings

Every future candidate result must say:

1. It is based on Bangladesh HF-cross research data from 50 cows.
2. It uses only genetic group and a derived THI category.
3. `Local` has limited evidence if that category is used.
4. Numeric environment distribution overlap is unverified.
5. DMI means dry matter/cow/day, not fresh-feed weight or a ration.
6. Rule outputs are not ML predictions.
7. External validation and production approval are absent.
8. The output is decision support, not veterinary or nutritionist advice.

## Approval Boundary

All candidate, production, commercial, and veterinary flags remain false
except the artifact label `CANDIDATE_ONLY`. This scope document does not
authorize runtime loading or deployment.
