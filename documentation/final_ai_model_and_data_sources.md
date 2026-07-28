# FarmLite Final AI Model and Data Sources

Date: 2026-07-26

## Output ownership

FarmLite is a hybrid decision-support system, not one model that generates a
complete feeding plan.

| Output | Owner | Method |
|---|---|---|
| Expected milk yield | FarmLite milk prediction model | Retained scikit-learn joblib pipeline |
| Predicted dry-matter intake | Collected-data DMI model | Feature-gated scikit-learn joblib pipeline |
| THI value and category | Backend THI calculation | Frozen deterministic backend calculation and boundaries |
| Advisory ration and composition | FarmLite nutrition rule engine | Frozen deterministic rules |

The FarmLite nutrition rule engine calculates advisory ration, roughage,
concentrate, mineral mix, water advice, feeding frequency and ration
warnings. No Hugging Face or generative model supplies the complete feeding
plan.

## FarmLite milk prediction model

Artifact:

`backend/flask_api/ml/models/milk_yield_model.joblib`

SHA-256:

`B9AD64E0EC62C75D70568D9D4F9136F240CD223DCC8851EC545D67B909C52BFA`

The retained model predicts one expected milk-yield value. It does not predict
feed type, DMI, ration composition, water advice or feeding frequency.

The associated existing source is **Kaggle Cattle Health and Feeding Data**.
The publisher declares the dataset synthetic. That status supports system and
pipeline demonstration, but not unrestricted real-farm accuracy or
scientific validation. Dataset generation formulas, measurement protocols
and some target semantics remain limited.

## Collected-data DMI model

Artifact:

`backend/flask_api/ml/models/candidates/bangladesh/bangladesh_dmi_regressor_candidate_v1.joblib`

Metadata:

`backend/flask_api/ml/models/candidates/bangladesh/bangladesh_dmi_regressor_candidate_v1.metadata.json`

Hashes:

- artifact:
  `312DDBAADA9A92A8B52E4ED95B254ACE0FD3EBEE1C6DD0B12BB003562EDD035B`
- metadata:
  `86077E3529CEC215F2C6C827E81881FD73C4B1DE7551C451084369C1061041EE`

Target: `dry_matter_intake_kg_day`
Unit: kg dry matter/cow/day
Exact feature order: `genetic_group`, `thi_category`

Research-data source:

> Mendeley Data, DOI: 10.17632/954f6g36sb.2

The artifact remains candidate-only and feature-gated. Its source-study
population and environmental reconstruction do not establish universal,
commercial, veterinary or multi-farm validation.

DMI is not total feed, fresh-feed mass or a ration. FarmLite never converts
the DMI prediction into roughage, concentrate or as-fed quantities.

## Internal second milk candidate

Artifact:

`backend/flask_api/ml/models/candidates/bangladesh/bangladesh_milk_yield_regressor_candidate_v1.joblib`

Metadata:

`backend/flask_api/ml/models/candidates/bangladesh/bangladesh_milk_yield_regressor_candidate_v1.metadata.json`

Hashes:

- artifact:
  `AA650EA16D4E89BB6A660778854138BEECCCCBEA9B3C589E2E549EF823D5F56E`
- metadata:
  `FCE8EA9956996A010D6AD1665E482786BDCBD497359FA018825106119FC0E46B`

This candidate may remain in the technical v2 response for evaluation, but
it is internal. It is not combined or averaged with the FarmLite result and
is absent from the farmer UI and farmer PDF.

## Phase 4 milk candidate

Artifact:

`backend/flask_api/ml/models/candidates/phase4/milk_yield_regressor_candidate_v1.joblib`

Metadata:

`backend/flask_api/ml/models/candidates/phase4/milk_yield_regressor_candidate_v1.metadata.json`

Hashes:

- artifact:
  `5FDA66E3D9879FD6CF49D83B3235781545E5784781509BCC340FBFE03BBA286E`
- metadata:
  `D1D90A9D2BD817B8F91F81665B92F371806F8F7DF1CC98ACE1C8B50768DD4069`

This is an evaluation artifact, not another farmer-facing result.

## Backend THI calculation

THI is calculated in the Flask backend from submitted temperature and
humidity. The frontend contains no THI formula or category calculation.

Phase 7 did not change:

- the THI formula;
- category boundaries;
- mapping contract;
- source label.

Invalid or missing environment inputs produce a controlled unavailable or
fallback result. No fabricated THI and no zero fallback are permitted.

## FarmLite nutrition rule engine

Rule file:

`backend/flask_api/ml/validation/nutrition_rules.py`

SHA-256:

`3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C`

Phase 7 did not change nutrition formulas, allocation boundaries, water
advice or feeding-frequency rules.

The correct farmer statement is:

> The FarmLite nutrition rule engine calculated an advisory ration quantity
> of {value} kg/day.

## Eligibility and safe failure

- Genetic group is supplied explicitly; breed never determines it.
- Supported groups are handled only inside the declared model contract.
- Missing/unknown group preserves milk, ration and valid backend THI while
  DMI remains unavailable.
- Unsupported production status fails closed.
- `Local` is reported as limited support, not full support.
- Artifact/hash/metadata failure keeps the affected value unavailable and
  preserves independent successful outputs.
- Disabled feature flags prevent candidate artifact loading and requests.

## Validation claim

FarmLite has passed repository integration, contract, controlled-scenario and
deterministic consistency tests. It has not received unrestricted external
clinical, commercial or universal validation. Future validation must use
independent farms, documented measurement protocols, prospective outcomes
and qualified veterinary/nutrition review without changing the meaning of
the current targets.
