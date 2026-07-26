# Milk Model Selection Review Plan

## Models Under Future Review

### Phase 4 synthetic milk candidate

Strengths:

- 175,000 training rows plus separate validation/test partitions;
- nine inputs that align better with current FarmLite fields;
- strong synthetic validation/test performance;
- complete preprocessing and reload metadata.

Limitations:

- publisher-declared synthetic target relationships;
- population not verified dairy-only;
- target generation method and real-world validity are unverified;
- no veterinary, commercial, nutritional, or external farm validation.

### Bangladesh real-study milk candidate

Strengths:

- observed daily milk from a real study dataset;
- cow-grouped development validation;
- untouched complete-cow holdout;
- transparent Ridge model with only two features;
- explicit dataset DOI/licence and repeated-observation lineage.

Limitations:

- only 50 cows from one Bangladesh study;
- only genetic group and THI category;
- no weight, DIM, BCS, prior yield, ration, or numeric weather;
- no final-holdout `Local` cow;
- one holdout cow had weak R²;
- no external population validation.

## Comparison Must Not Be Performed on Existing Test Results Alone

The reported metrics use different populations, targets, feature contracts,
data-generating processes, and split designs. Lower MAE or higher R² across the
two reports is not a fair head-to-head comparison.

## Future Evaluation Design

1. Freeze both artifacts, hashes, adapters, and source labels.
2. Acquire an independent, real, dairy/HF-cross dataset containing:
   - Bangladesh-required genetic group and measured environment;
   - the nine synthetic-candidate inputs where possible;
   - directly measured complete daily milk;
   - cow IDs and farm/site lineage.
3. Define a common eligible subset without filling unavailable features with
   invented facts.
4. Evaluate both models without tuning on the same independent cows.
5. Compare MAE, RMSE, R², bias, per-cow/subgroup stability, input coverage,
   rejection rate, calibration, and operational usability.
6. Separately report each model on its broader natural eligibility set.
7. Conduct prospective FarmLite shadow evaluation before user-facing
   selection.

## Possible Decisions

| Decision | Evidence required |
|---|---|
| `BANGLADESH_PRIMARY` | Bangladesh model passes external/prospective criteria and materially outperforms alternatives in its intended scope |
| `SYNTHETIC_PRIMARY` | Synthetic model unexpectedly demonstrates real-world external validity and has acceptable scope/target semantics |
| `CONDITIONAL_ROUTING` | Both pass in different documented populations/input-availability conditions, with deterministic routing |
| `BOTH_RESEARCH_ONLY` | Neither has sufficient external validity for operational use |
| `EXTERNAL_VALIDATION_REQUIRED` | Current state; no fair independent comparison exists |

## Current Decision

`EXTERNAL_VALIDATION_REQUIRED`

No model is declared the production winner. A future conditional route is a
hypothesis, not an approved architecture choice. The existing runtime model
and Phase 4 candidate must not be silently replaced by the Bangladesh
candidate.

## Required Review Outputs

- common and model-specific eligibility counts;
- identical independent-cow metric definitions;
- target/unit compatibility statement;
- subgroup and farm/site results;
- fallback and rejection rates;
- model-source explanations tested with users;
- final selection rationale and rollback plan;
- confirmation that no external target was used for tuning.
