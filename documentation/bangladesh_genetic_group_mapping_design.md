# Bangladesh Genetic-Group Mapping Design

## Evidence

The study variable dictionary defines genetic group as Holstein-Friesian
inheritance proportion: 0%, 50%, 62.5%, 75%, and 87.5% HF. Both fitted
pipelines learned these exact stored labels:

| Stored model label | Study meaning | Locked final-holdout coverage |
|---|---|---|
| `Local` | 0% HF / study local group | None; development grouped-validation evidence only |
| `HF50` | 50% HF | Yes |
| `HF62.5` | 62.5% HF | Yes |
| `HF75` | 75% HF | Yes |
| `HF87.5` | 87.5% HF | Yes |

FarmLite currently stores breed as free text. A breed name does not establish
an individual cow's HF inheritance percentage, and the same named cross can
represent different pedigrees. Breed must therefore remain separate from
genetic group.

## Option Review

| Option | Scientific defensibility | Farmer usability | Frontend impact | Unknown-value risk | Incorrect-mapping risk | Required documentation | Prototype suitability |
|---|---|---|---|---|---|---|---|
| **A — Ask directly for genetic group** | High only when the user has a pedigree/farm record and selects an exact study category | Medium; labels require explanation | Add a separate enum and “unknown” path | Low if unknown is allowed | Medium if users guess | Definitions, pedigree source, `Local` limitation, no breed equivalence | `APPROVED_PRIMARY_DESIGN` |
| **B — Ask for approximate HF inheritance percentage** | Low for approximate values; rounding to study bins is unsupported | Medium | Add numeric field and mapping UX | Medium | High near 50/62.5/75/87.5 boundaries | A verified binning rule, uncertainty policy, pedigree evidence | `NOT_APPROVED_AS_APPROXIMATE_MAPPING` |
| **C — Map only with an explicitly verified relationship** | High when a trusted pedigree/genomic record states an exact supported percentage | High after records exist | Data-model and provenance field required | Low | Low if evidence is retained | Approved evidence sources and audit trail | `CONDITIONAL_FUTURE_OPTION` |
| **D — Refuse Bangladesh prediction and fall back** | High | High; clear unavailable message required | Eligibility/fallback display only | None | None | Fallback source and warning catalog | `APPROVED_REQUIRED_SAFETY_PATH` |

## Frozen Design

Use Option A plus Option D:

1. Add a separate `genetic_group` input in a later approved phase.
2. Present exactly `Local`, `HF50`, `HF62.5`, `HF75`, and `HF87.5`, plus a UI
   “unknown/not documented” choice that is never sent as a supported model
   category.
3. Require the user to confirm that the value comes from a pedigree, farm
   breeding record, or another documented source. A guess is not verified.
4. When the value is missing, unknown, or outside the exact set, mark both
   Bangladesh models ineligible and use the explicit fallback architecture.
5. Never calculate genetic group from the existing `breed` string.

Option C may later populate the same exact `genetic_group` field only after
the relationship and provenance are independently approved. Option B remains
blocked because no defensible approximate-value binning rule exists.

## `Local` Policy

`Local` is a known training category, not an unknown encoder value. It has
grouped development evidence but no cow from that group appeared in the locked
final holdout. A controlled research prototype may classify it
`LIMITED_SUPPORT`, must show a specific warning, and must not claim the same
holdout coverage as the four HF-cross groups. Production support remains
blocked for every group.

## Fail-Closed Rules

- Empty value: `MISSING_REQUIRED_INPUT`, then `FALLBACK_REQUIRED`.
- Unsupported text: `UNKNOWN_GENETIC_GROUP`, then `FALLBACK_REQUIRED`.
- Breed supplied without genetic group: do not map; use fallback.
- Approximate numeric percentage without an approved exact record: do not
  round; use fallback.
- Conflicting breed and genetic-group text: do not resolve automatically;
  return a validation error for human correction.

## Required Phase 5 Documentation

- Plain-language meaning of every category.
- Evidence source recorded by the user or farm.
- `Local` holdout limitation.
- No automatic breed mapping.
- Candidate-only and Bangladesh study-population warnings.
- Change/audit behavior if a genetic-group value is later corrected.
