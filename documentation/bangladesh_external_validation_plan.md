# Bangladesh Candidate External-Validation Plan

## Goal

Establish whether the Bangladesh DMI and milk candidates retain useful,
well-calibrated performance on independent cows, farms, seasons, management
systems, and collection procedures before any production claim.

Datasets must remain separate. External validation is evaluation, not
concatenation or retraining.

## Existing Source Assessment

| Potential evidence | DMI validation | Milk validation | Decision |
|---|---|---|---|
| Rwanda dairy dataset | `INCOMPATIBLE_CURRENTLY` | `POTENTIALLY_COMPATIBLE_WITH_MAJOR_LIMITATIONS` | Do not use as current definitive validation |
| Phase 4 synthetic data | `NO` | `NO` for real-world validity | Synthetic targets cannot externally validate a real-study candidate |
| Separate HF-cross farm dataset | `REQUIRED` | `REQUIRED` | Preferred independent retrospective validation |
| Prospective FarmLite records | `REQUIRED_BEFORE_DEPLOYMENT` | `REQUIRED_BEFORE_DEPLOYMENT` | Needed for intended-user and data-entry validation |

## Rwanda Milk

Rwanda `hand-milked yield` is directly measured and reported as L/cow/day,
which is target/unit compatible with Bangladesh milk in principle. It cannot
currently serve as a clean model validation dataset because:

- the 96 rows lack verified cow/farm grouping identifiers;
- completeness across all daily milkings is unclear;
- Bangladesh genetic-group categories are unavailable;
- temperature, humidity, and THI category are unavailable;
- population, farm, breed/cross, management, and study design differ.

Rwanda milk could become supporting external evidence only after identity,
collection completeness, genetic mapping, and environment compatibility are
resolved without invention. It must remain a separate evaluation.

## Rwanda DMI

Rwanda DMI is not compatible. `DMIcapacity` has conflicting intake/capacity
meanings, 28 leftovers are negative, and requirement/intake fields are
calculated or semantically unresolved. It cannot validate Bangladesh measured
DMI until the source authors resolve the target definition and signs.

## Required Independent Dataset

An acceptable external dataset needs:

- independent lactating cows not used in Bangladesh training;
- stable cow identifiers and group-aware evaluation;
- exact or authoritatively documented HF genetic group;
- measured dry-bulb temperature and relative humidity in the required units;
- reproducible THI derivation and category mapping;
- directly measured DMI in kg dry matter/cow/day with documented
  offered/refusal protocol;
- directly measured complete daily milk in L/cow/day;
- dates, farm/site, management system, lactation status, and collection
  quality controls;
- coverage across every intended genetic group and THI category;
- preserved raw lineage, licence, and provenance.

## Minimum Evidence

Numeric sample-size minimum is `UNRESOLVED` until a power/precision analysis is
performed against predeclared error tolerances and between-cow clustering.
Rows must never substitute for independent cows.

At minimum, the external evidence package must include:

1. a preregistered, frozen candidate and hash;
2. no tuning on the external target;
3. cow-grouped metrics and confidence intervals;
4. mean/median baselines evaluated on the same cows;
5. MAE, RMSE, R², median error, bias, residual spread, prediction range, and
   non-finite/negative counts;
6. per-cow, genetic-group, THI-category, site, and season breakdowns;
7. input rejection/fallback rates;
8. calibration/scope analysis for out-of-study target ranges;
9. complete unit and target-definition review;
10. an unchanged-source and no-merge audit.

## Acceptance Criteria

Before viewing external outcomes, owners must approve numeric tolerances for
DMI and milk based on application risk. The candidate must then:

- beat preregistered mean and median baselines on independent cows;
- have finite, biologically interpretable outputs without hidden clamping;
- meet the predeclared MAE/RMSE and bias tolerances;
- show no unacceptable genetic-group, THI, site, or season failure;
- retain documented category coverage;
- expose every rejection and fallback;
- preserve candidate hash and preprocessing contract;
- pass data-quality and target-unit checks.

Any tuning, category remapping, or formula change creates a new candidate and
requires a new untouched validation dataset.

## Reasons Validation May Fail

- incompatible target definition or material basis;
- absent/incorrect genetic proportions;
- numeric environment outside the unknown study range;
- farm/management/population shift;
- missing cow identifiers or repeated-measure leakage;
- DMI measurement-protocol differences;
- incomplete daily milk collection;
- weak per-cow or subgroup performance;
- high fallback/rejection rates;
- changed software or artifact incompatibility.

## Deployment Boundary

Successful Bangladesh internal holdout performance is not external
validation. Production, commercial, and veterinary approval remain blocked
until independent and prospective evidence passes a separately approved gate.
