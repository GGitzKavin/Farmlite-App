# Bangladesh Integration Approval Gate

## Phase 4.5D Evidence Carried into Review

| Check | Status | Evidence | Required action |
|---|---|---|---|
| DMI beats grouped baseline | `PASS` | Holdout R²=0.9413; MAE improvement=78.07% | Review candidate limitations. |
| DMI generalizes to unseen cows | `PASS` | Holdout R²=0.9413; MAE improvement=78.07% | Require external/population validation before production. |
| Milk beats grouped baseline | `PASS` | Holdout R²=0.8590; MAE improvement=63.17% | Review candidate limitations. |
| Milk generalizes to unseen cows | `PASS` | Holdout R²=0.8590; MAE improvement=63.17% | Require external/population validation before production. |
| Cow leakage prevented | `PASS` | GroupShuffleSplit + GroupKFold; zero overlap | Preserve cow grouping in every future run. |
| Feature timing defensible | `PASS_WITH_LIMITATIONS` | Genetic group and derived THI category are pre-prediction concepts | Specify and validate runtime THI derivation before integration. |
| Candidate artifacts reload | `PASS` | Exact prediction equality=True | Do not review a failed artifact. |
| Existing models preserved | `PASS` | Protected hash equality=True | Stop if any protected file differs. |
| Dataset licence documented | `PASS` | CC BY 4.0; DOI 10.17632/954f6g36sb.2 | Retain attribution with artifacts. |
| Integration not performed | `PASS` | No runtime, route, frontend, PDF, or nutrition changes | Require explicit approval for any integration. |

## Future FarmLite THI-Category Derivation

A future, separately approved request adapter may calculate THI from farmer-provided dry-bulb temperature `T` (°C) and relative humidity `RH` (%) using the study article's cited formula:

`THI = (1.8 × T + 32) − [(0.55 − 0.0055 × RH) × (1.8 × T − 26)]`

Map the result to the source categories exactly: `T0` for THI ≤75, `T1` for 75<THI<80, and `T2` for THI ≥80. Validate input units and boundary behavior before use. Do not invent a numeric THI for historical rows and do not back-calculate temperature or humidity from category labels.

Source: Pehan et al., *Effects of cyclic temperature-humidity index on milk production, physiological and haematobiochemical responses in Holstein-Friesian cows of varied genetic proportions*, DOI `10.1016/j.anopes.2026.100139`.

## Phase 4.5D Recommendation Entering Review: `READY_FOR_DMI_AND_MILK_INTEGRATION_REVIEW`

This is an integration-review recommendation only. It is not production, commercial, veterinary, deployment, or automatic integration approval.

## Phase 4.5E Architecture-Freeze Matrix

| Requirement | Status | Evidence | Blocker | Phase 5 action |
|---|---|---|---|---|
| Candidate artifacts valid | `PASS` | Both pipelines reload for structure review; reviewed hashes are DMI `312DDB...035B` and milk `AA650E...F56E` | Dependencies are not pinned in `requirements.txt`; metadata paths are machine-specific | Pin compatible packages, resolve trusted repository paths, and verify metadata/hash before deserialization |
| DMI model passed holdout | `PASS_WITH_LIMITATIONS` | Unseen-cow holdout MAE `0.3235`, RMSE `0.4008`, R² `0.9413`, zero negative predictions | One study, 50 cows, incomplete DMI protocol, no external validation | Preserve candidate label and validate externally before stronger use |
| Milk model passed holdout | `PASS_WITH_LIMITATIONS` | Unseen-cow holdout MAE `0.4839`, RMSE `0.6031`, R² `0.8590`, zero negative predictions | Cow `510` had R² about `-0.0110`; no external validation | Retain per-cow warning and perform fair independent model comparison |
| Genetic-group input resolved | `DESIGN_DEFINED_RUNTIME_INPUT_MISSING` | Exact learned values are `Local`, `HF50`, `HF62.5`, `HF75`, `HF87.5`; direct-input-plus-fallback design is documented | FarmLite currently has only free-text breed | Add an explicit documented `genetic_group`; never infer from breed |
| THI mapping resolved | `VERIFIED_WITH_LIMITATIONS` | Article formula and exact `T0/T1/T2` boundaries are recorded in the THI contract | Source workbooks lack numeric T/RH/THI ranges; current request silently defaults weather | Implement server-side unrounded calculation with measured inputs and no defaults |
| Unknown-category policy defined | `PASS_DESIGN_ONLY` | Eligibility policy rejects unsupported values before `OneHotEncoder(handle_unknown="ignore")` | Not implemented | Add deterministic validation and fallback reason codes |
| Fallback architecture defined | `PASS_DESIGN_ONLY` | DMI, milk, no-ML, user-history, artifact-failure, and out-of-scope paths are documented | No approved current DMI fallback rule | Return DMI unavailable until a transparent DMI rule is independently approved |
| Nutrition boundary verified | `BLOCKED_FOR_DMI_TO_RATION` | DMI is kg dry matter/cow/day; current total/roughage/concentrate basis is unresolved | Feed moisture, ingredient DM fractions, ration allocation, and double-counting policy are missing | Keep DMI standalone; approve conversion/ration contract before connecting rules |
| API v2 contract approved | `PROPOSED_REVIEW_COMPLETE` | Versioned snake_case request/response, errors, nulls, sources, ownership, and fallback codes are defined | Endpoint and implementation are intentionally absent | Obtain owner approval, then implement backend validation behind a disabled flag |
| External validation planned | `PASS_PLAN_ONLY` | Separate HF-cross and prospective FarmLite evidence requirements are documented; Rwanda compatibility assessed | No suitable independent validation has been performed | Acquire independent data; preregister tolerances and evaluate frozen artifacts without merging |
| Production deployment blocked | `PASS` | All artifact/config approval flags remain false; both models remain `CANDIDATE_ONLY` | External validation, new input, unit boundary, monitoring, and runtime hardening remain incomplete | Do not enable production/commercial/veterinary use |

## Frozen Design Decisions

- Genetic group is a new explicit category, not a breed mapping.
- `Local` is a known model category with `LIMITED_SUPPORT` because no Local cow
  appeared in the locked final holdout.
- Temperature and humidity must be measured finite inputs. Missing values
  cannot use the current 28 °C / 70% defaults for Bangladesh inference.
- THI is calculated server-side with the article formula, then mapped as:
  `T0` for THI ≤75, `T1` for 75<THI<80, and `T2` for THI ≥80.
- Unknown categories and invalid/missing inputs refuse candidate prediction and
  require an explicit fallback.
- DMI remains a standalone kg dry matter/cow/day output; it is not
  `totalFeedKg` or a fresh-feed/ration quantity.
- Milk-source selection remains `EXTERNAL_VALIDATION_REQUIRED`; no existing
  or candidate model is automatically replaced.
- Rule outputs and ML outputs remain structurally separate.

## Final Phase 5 Recommendation

`CONDITIONAL_INTEGRATION_REQUIRES_NEW_INPUT`

The required new input is an explicit, documented `genetic_group`. Phase 5
must also implement the no-default THI adapter, eligibility/fallback controls,
artifact integrity checks, and API v2 source separation before a controlled
backend candidate path can be reviewed.

This recommendation is not runtime, production, commercial, veterinary,
deployment, or automatic integration approval. Phase 4.5E performed no model
training, tuning, prediction evaluation, route registration, React/PDF change,
nutrition-rule change, artifact promotion, or Git staging.
