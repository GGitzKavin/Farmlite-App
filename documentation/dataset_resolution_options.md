# FarmLite Dataset Resolution Options

## Decision Status

**Phase 2 resolution path: Option 5 — documented synthetic prototype, with
limitations.**

The verified Kaggle clarification identifies the dataset, publisher account,
source page, and publisher-declared synthetic status. FarmLite may use it to
demonstrate an ML pipeline, but may not claim real-farm observations,
veterinary validation, nutrition-trial validation, commercial safety, or
real-world accuracy.

This selection authorizes contract design only. It does not authorize training.
The applicable gates in
`documentation/ml_training_approval_gate.md` must pass first.

## Option 1 — Current Dataset Fully Verified

Use the current data for:

- feed-type classification;
- feed-quantity regression;
- milk-yield regression.

Required evidence:

- verified creator, source, license, and academic-use permission;
- authoritative definitions for all three targets;
- defensible label timing without leakage;
- a documented dairy-only filter;
- a prediction-time feature set available in FarmLite.

Main benefit:

- supports the intended three-model pipeline using one documented record base.

Main risk:

- this option is invalid if any target is merely a generated/observed field
  that cannot be defended as the proposed FarmLite output.

Current status: **POSSIBLE BUT ALL TARGET-SPECIFIC GATES ARE BLOCKED**

## Option 2 — Feed Type Unsuitable, Quantities Verified

Use ML for:

- feed quantity;
- milk yield.

Use documented nutrition rules to select or explain feed categories.

Required evidence:

- `Feed_Quantity_kg` material basis and period are verified;
- `Milk_Yield_L` period and zero meaning are verified;
- feed type is formally rejected as a recommendation target;
- nutrition rules have suitable published or expert sources;
- dairy scope and feature availability are resolved.

Important presentation rule:

- the system must not claim that feed category came from ML if it came from
  nutrition rules.

Current status: **POSSIBLE IF QUANTITY AND MILK TARGETS ARE VERIFIED**

## Option 3 — Feed Quantity Unsuitable, Feed Type Verified

Use ML for:

- feed type;
- milk yield.

Use documented nutrition equations for quantities.

Required evidence:

- `Feed_Type` is verified as a defensible recommendation target;
- `Milk_Yield_L` is verified;
- `Feed_Quantity_kg` is formally rejected;
- quantity equations, units, assumptions, and sources are documented;
- dairy scope and feature availability are resolved.

Important presentation rule:

- every equation-derived quantity must be labelled as rule/equation-derived,
  not model-predicted.

Current status: **POSSIBLE IF FEED TYPE AND MILK TARGETS ARE VERIFIED**

## Option 4 — Only Milk Yield Verified

Keep the milk-yield model and obtain a new feed-recommendation dataset.

Required evidence:

- `Milk_Yield_L` period, zero meaning, generation/measurement method, license,
  and dairy scope are verified;
- current feed targets are formally rejected;
- a replacement feed dataset is documented and audited before use.

System implication:

- until a suitable feed dataset is available, FarmLite may expose milk-yield
  prediction only as a supporting signal and must describe feed outputs as
  rule-derived.

Current status: **POSSIBLE IF ONLY MILK YIELD PASSES**

## Option 5 — Dataset Confirmed Synthetic but Documented

Use the data as a prototype or proof-of-concept dataset.

Required evidence:

- the creator or source confirms that the dataset is synthetic or simulated;
- the generation rules, distributions, assumptions, and limitations are
  documented;
- the license permits the intended academic use;
- target meanings and units are still defined;
- synthetic scope and any dairy filter are explicit.

Dissertation limitation:

- state clearly that results demonstrate implementation feasibility on
  synthetic/simulated data;
- do not claim real-world clinical, veterinary, nutritional, or commercial
  reliability;
- do not present synthetic evaluation scores as evidence of real-farm
  effectiveness.

Current status: **SELECTED FOR THE UNDERGRADUATE PROTOTYPE**

Verified:

- source dataset and publisher account;
- publisher-declared synthetic status;
- prototype/ML-demonstration interpretation.

Still limited:

- detailed generation formulas and target definitions are absent;
- license confirmation is pending;
- the raw cattle records are not verified dairy-only;
- all UI, report, and dissertation claims must state that the predictions are
  synthetic-target prototype outputs.

## Option 6 — Dataset Unverified

Do not train the final dissertation model from the current data.

Then either:

1. obtain a documented dataset with suitable targets, scope, and license; or
2. construct a transparent synthetic dataset from published nutrition
   equations, clearly label it synthetic, cite every equation, and describe its
   limitations.

A newly obtained or constructed dataset requires a new audit before training.

Current status: **POSSIBLE IF THE BLOCKERS CANNOT BE RESOLVED**

## Comparison

| Option | Feed type | Feed quantity | Milk yield | Additional requirement |
|---|---|---|---|---|
| 1 | ML | ML | ML | All provenance, target, dairy, and feature gates pass |
| 2 | Documented rules | ML | ML | Quantity and milk targets verified |
| 3 | ML | Documented equations | ML | Feed type and milk targets verified |
| 4 | New dataset/rules only | New dataset/rules only | Existing ML path may remain | Milk target verified; obtain feed data |
| 5 | Prototype only as defined | Prototype only as defined | Prototype only as defined | Synthetic generation and license documented |
| 6 | No final training | No final training | No final training from current data | Replace data or transparently construct and reaudit |

## Information Needed Before Selection

1. License and required citation.
2. Detailed synthetic generation method or formulas.
3. Authoritative `Feed_Type` definition and assignment process.
4. `Feed_Quantity_kg` material basis, period, inclusions, and generation
   method.
5. `Milk_Yield_L` period, zero meaning, and generation method.
6. Source-backed dairy-only filtering rule.
7. Confirmation of any unpublished constraints on academic use.

Options 1-4 remain possible only if later evidence verifies the relevant target
semantics. Option 6 remains the fallback if license or prototype-use
constraints cannot be resolved.
