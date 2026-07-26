# Bangladesh Model Design Options

No model was trained in Phase 4.5C.

## Effective Sample Size

There are 750 rows but only 50 independent cow groups. Within-cow correlation reduces effective information, and uncertainty estimates must use cows—not rows—as the primary independent unit.

## Future Validation Designs

- GroupKFold by cow for repeated grouped comparison.
- Leave-one-cow-out for a high-variance sensitivity analysis.
- GroupShuffleSplit or complete-cow train/validation/test holds.
- Environmental-condition holdout as a robustness test, not a substitute for cow grouping.
- Source-specific external validation only after target, feature, population, and timing harmonization.

## Future Baseline Families

Start, if separately approved, with transparent mean/group baselines, linear regression, and ridge. Consider tightly controlled shallow tree models and limited boosting only after leakage-safe grouped baselines. This document does not authorize any estimator fitting.

## Candidate Features

- DMI: genetic group and a prediction-time THI/environment feature. Same-day milk and physiology remain leakage-unclear.
- Milk yield: genetic group and prediction-time THI/environment. DMI is usable only if temporal ordering and farmer availability are proven.
- Missing high-value features: weight, parity, DIM, lactation stage, BCS, prior yield, ambient temperature, and humidity.

## Metrics and Uncertainty

Report MAE/RMSE and bias overall, per cow, genetic group, and THI category. Include cow-grouped bootstrap or other group-aware confidence intervals. Report worst-condition and per-condition performance, not only pooled row metrics.
