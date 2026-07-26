# Rwanda Small-Dataset Model Design Options

## Boundary

This document compares future design options only. It does not approve or run
training. Row independence and the selected target must be confirmed first.

## Dataset Implications

There are only 96 rows. A 15% held-out test partition would contain about 14
records, making metrics highly sensitive to individual observations. Missing
age, parity, CP and ME values further reduce usable samples for some designs.
Feature count must remain low, uncertainty must be reported, and external
validation remains necessary because the sample is cross-sectional and
purposively selected at the final farm/cow stage.

## Candidate Algorithms

| Option | Future role | Main control |
|---|---|---|
| Simple linear regression | Transparent baseline for measured milk or verified water-provided target. | Few pre-outcome features; residual diagnostics. |
| Ridge regression | Preferred regularized linear comparison when correlated features are retained. | Tune only inside validation folds. |
| Lasso | Exploratory only when sparse selection has a clear scientific rationale. | Stability analysis across resamples. |
| Small decision tree | Nonlinear benchmark. | Strict depth and minimum-leaf limits. |
| Random forest | High-overfit-risk sensitivity comparison only. | Very shallow trees, restricted features, nested tuning. |
| Gradient boosting | High-overfit-risk comparison only. | Very limited depth, learning rate and iterations. |

Complex ensembles can memorize 96 rows, especially with identifiers, detailed
ingredient strings, calculated targets or leakage fields.

## Validation Options

| Method | Use condition | Limitation |
|---|---|---|
| Leave-one-out CV | Only after all 96 rows are confirmed independent. | High variance; no protection from hidden farm/cow groups. |
| Repeated K-fold CV | Preferred uncertainty assessment after independence confirmation. | Repeated animals/farms would leak across folds. |
| Grouped CV | Required when cow or farm identifiers become available. | Currently impossible because IDs are absent. |
| Bootstrap confidence intervals | Report metric uncertainty and coefficient stability. | Resampling unit must match cow/farm grouping. |
| Small held-out test | Optional only with sufficient independent external data. | About 14 records at 15%; unstable for current dataset. |

## Recommendation

`WAITING_FOR_DATA_CLARIFICATION`. If independence and target definitions are
confirmed, begin with low-feature linear and ridge baselines using repeated or
grouped validation. Do not approve a final design before that evidence exists.
