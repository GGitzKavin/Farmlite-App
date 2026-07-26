# FarmLite Dairy-Cattle Scope Strategy

## Scope Statement

> The FarmLite interface is scoped to dairy-cattle use, while the synthetic
> training dataset includes cattle records whose production purpose is not
> fully documented.

This statement must accompany prototype-model documentation. It distinguishes
the application's intended users from the synthetic training-data population.

## Current Evidence

- FarmLite's feed-recommendation page filters selected Firestore records using
  dairy-cattle-like application labels.
- The API currently does not receive or validate `animalType`.
- The primary CSV has 40 `Breed` values and lactation fields.
- It has no verified `Species`, `Production_Type`, or equivalent dairy-purpose
  field.
- No source-backed breed-purpose map is currently approved.
- The publisher declares the data synthetic.

## Strategy A — Use All Synthetic Cattle Records

Use all 250,000 primary rows for the synthetic prototype while the application
continues to accept dairy-cattle records only.

### Assessment

- Academic honesty: acceptable only with the scope statement above and no
  dairy-only training-data claim.
- Reproducibility: strongest; no undocumented breed filtering.
- Data availability: retains the full sample.
- Model sample size: largest.
- False-classification risk: avoids guessing which breeds are dairy or
  dual-purpose.
- Scope mismatch: remains explicit and must be treated as a limitation.

### Current recommendation

**Recommended as the Phase 3 interim prototype strategy.**

This recommendation applies only to preprocessing and future synthetic
prototype experiments. It does not validate dairy nutrition or approve
real-world deployment.

## Strategy B — Add a Documented External Breed-Purpose Map Later

Obtain a credible source that classifies every included breed as `DAIRY`,
`DUAL_PURPOSE`, `BEEF`, `NON_SPECIALIZED`, or `UNKNOWN`, then version and cite
the mapping.

### Assessment

- Academic honesty: strong if sources and ambiguous/crossbred decisions are
  documented.
- Reproducibility: good when the mapping is a versioned artifact.
- Data availability: reduces rows depending on inclusion policy.
- False-classification risk: lower than guessing, but crossbred and local
  categories still require rules.
- Current feasibility: blocked because web/source-backed breed research was not
  authorized in Phases 1.5-2.

### Recommendation

**Preferred later refinement if a defensible source is approved.**

## Strategy C — Add a Production-Purpose Field

Add a reliable `productionPurpose` field to future FarmLite livestock records
and the future canonical API request.

### Assessment

- Academic honesty: improves application-scope enforcement.
- Reproducibility: requires controlled values and validation.
- Data availability: helps future collected data but does not retrospectively
  label the current synthetic CSV.
- False-classification risk: depends on who supplies and validates the field.
- Current feasibility: design candidate only; no frontend or database change is
  approved.

### Recommendation

**Useful for future application data, not a solution for the current CSV.**

## Strategy D — Obtain a Dairy-Only Replacement Dataset

Replace or supplement the current data with a documented dairy-only dataset
whose targets, license, collection/generation method, and population are clear.

### Assessment

- Academic honesty: strongest route for future real-world relevance.
- Reproducibility: depends on source access and versioning.
- Data availability: uncertain and requires a new audit.
- Model sample size: unknown.
- False-classification risk: lowest if dairy scope is explicit.
- Current feasibility: not available in the repository.

### Recommendation

**Best long-term path for claims beyond a synthetic prototype.**

## Strategy Comparison

| Strategy | Honesty | Reproducibility | Sample size | Breed-guessing risk | Current status |
|---|---|---|---|---|---|
| A — All synthetic records | High with explicit limitation | High | 250,000 | None | Recommended interim strategy |
| B — Documented breed map | High with cited mapping | High | Reduced/unknown | Moderate to low | Pending external evidence |
| C — Production-purpose field | High for future app data | Medium-high | Does not relabel current CSV | Depends on data entry | Future design |
| D — Dairy-only replacement | Highest potential | Source-dependent | Unknown | Low | Not currently available |

## Enforcement Requirements

For interim Strategy A:

1. Do not label the training dataset dairy-only.
2. Keep `animalType` as application scope metadata, not an ML feature.
3. Add backend dairy-category validation only in a separately approved API
   phase.
4. Include the synthetic/data-scope limitation in reports, model metadata, API
   responses, React results, PDFs, and dissertation text when those phases are
   approved.
5. Do not filter breeds during Phase 2 or Phase 3 unless Strategy B receives
   explicit approval.

No dataset filter is applied in Phase 2.
