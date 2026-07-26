# FarmLite ML Training Approval Gate

## Purpose

This gate controls authorization for final dissertation-model training. A
technically trainable column is not sufficient: its source, meaning, scope, and
prediction-time availability must also be defensible.

Current overall decision: **TRAINING BLOCKED DURING PHASE 2**

## Gate A — Provenance

Pass only when:

- the dataset source is identified;
- the publisher or creator is known;
- academic-use permission or license is understood.

Current evidence:

- Dataset: `Cattle Health and Feeding Data`
- Platform: Kaggle
- Publisher/account: `ShahHet2812`
- Source:
  `https://www.kaggle.com/datasets/shahhet2812/cattle-health-and-feeding-data`
- The publisher declares the dataset synthetically generated and potentially
  unrepresentative of real-world data.
- Detailed generation methodology and license confirmation remain unresolved.

## Gate B — Feed-Type Meaning

Pass only when:

- `Feed_Type` has an authoritative definition;
- the label-assignment process is known;
- it represents a defensible prediction target.

Current evidence:

- eight broad, near-balanced categories exist;
- the contract can defensibly describe them as synthetic feed-category labels
  for prototype classification;
- label assignment, nutritional meaning, and real-world exclusivity are not
  documented;
- they are not verified expert recommendations.

## Gate C — Feed-Quantity Meaning

Pass only when:

- material basis is known;
- measurement period is known;
- inclusion of roughage and concentrate is known;
- the frontend label can be stated honestly.

Current evidence:

- values range from 3.0 to 25.0 kg;
- the publisher declaration establishes a synthetic feed-quantity target;
- fresh matter versus dry matter, period, ration components, and measurement or
  generation method are unknown.

## Gate D — Milk-Yield Meaning

Pass only when:

- measurement period is known;
- zero values are understood;
- the target is available as a genuine recorded or generated outcome.

Current evidence:

- values range from 0.0 to 36.42 L;
- the publisher declaration establishes a synthetic milk-yield target;
- 5,940 values are zero;
- period, zero meaning, and observation/generation method are unknown.

## Gate E — Dairy-Cattle Filter

Pass only when:

- a documented dairy-only filtering rule exists;
- unsupported records can be removed consistently;
- the same scope can be enforced in the application.

Current evidence:

- 40 breed values exist;
- no local source defines their production purpose;
- no authoritative species or production-purpose field exists;
- all 40 breed classifications therefore remain `UNKNOWN`.

## Gate F — Feature Availability

Pass only when:

- selected model features are available from FarmLite at prediction time;
- no required model input is unavailable in the frontend or database;
- no target leakage is present.

Current evidence:

- the Phase 2 contract selects breed, age, weight, lactation stage, days in
  milk, previous-week yield, body-condition score, ambient temperature, and
  humidity;
- all nine are present in the primary dataset and the current request flow;
- parity, season, climate zone, management system, and health status are
  excluded from model inputs because of application or dataset mismatch;
- targets, identifiers, current outcomes, disease outcomes, and post-outcome
  fields are explicitly excluded;
- predicted feed type in Feed Quantity Design B requires out-of-fold training
  predictions and Model 1 inference output.

## Current Gate Table

| Gate | Status | Evidence | Blocking issue | Required action |
|---|---|---|---|---|
| A — Provenance | `PARTIALLY_PASSED` | Dataset name, Kaggle source, publisher account, and publisher-declared synthetic status are verified | Detailed generation methodology and license remain unresolved | Capture the Kaggle license and any generation/data-dictionary documentation |
| B — Feed-Type Meaning | `PARTIALLY_PASSED` | Eight synthetic category labels support prototype classification | Assignment formula and nutritional meaning are unknown; not an expert recommendation | Preserve `CATEGORY_ONLY` wording and obtain publisher generation details if available |
| C — Feed-Quantity Meaning | `BLOCKED` | A complete synthetic numeric target ranges 3.0-25.0 kg | Material basis, period, included ration components, and generation method are unknown | Use only “synthetic feed-quantity target” internally; obtain detailed definition before stronger claims |
| D — Milk-Yield Meaning | `BLOCKED` | A complete synthetic numeric target ranges 0.0-36.42 L; 5,940 zeros | Period, zero meaning, and generation method are unknown | Use only “synthetic milk-yield target”; obtain detailed definition before stronger claims |
| E — Dairy-Cattle Filter | `BLOCKED` | Breed and lactation fields exist, but all 40 breed purposes remain undocumented | No safe dairy-only rule or enforceable production-purpose field | Provide a source-backed breed mapping or documented production-purpose field, or replace the dataset |
| F — Feature Availability | `PASSED` | Nine selected inputs exist in both the primary dataset and current request flow; mismatched and leakage fields are excluded | Optional inputs still require explicit imputation flags and UI/dataset lactation mapping | Implement only the approved schema and preserve missing/unknown-value metadata |

## Approval Rule

Any future training phase may begin only after:

1. the owner explicitly approves that training phase;
2. Gate F is `PASSED` for the specific model;
3. the selected resolution option and synthetic prototype claim are documented;
4. target-specific blocked/limited gates are accepted explicitly for a
   synthetic demonstration and are never presented as scientific validation;
5. license status is reviewed before publication or redistribution.

`PARTIALLY_PASSED` does not authorize training. Historical model artifacts and
reports do not satisfy these gates.

## Current Decision

- Feed-type classifier training: **NOT APPROVED**
- Feed-quantity regressor training: **NOT APPROVED**
- Final milk-yield regressor training: **NOT APPROVED**
- Existing model replacement: **NOT APPROVED**
- Phase 2 contract documentation: **APPROVED WITH SYNTHETIC-DATA LIMITATIONS**

Next action after Phase 2 approval: implement reusable preprocessing only,
without training, while preserving all synthetic-data and scope limitations.
