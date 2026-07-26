# Bangladesh MILK Feature Analysis

## Method

Permutation importance on the final complete-cow holdout using negative MAE; descriptive, not causal.

## Permutation Importance

| Feature | Mean MAE increase | SD |
|---|---:|---:|
| `genetic_group` | 1.1264 | 0.1013 |
| `thi_category` | 0.1777 | 0.0274 |

## Findings

- THI-category contribution is `POSITIVE` under holdout permutation (MAE increase 0.1777).
- Genetic-group contribution is `POSITIVE` (MAE increase 1.1264).
- With only two categorical features, predictions primarily represent learned group-level differences. They do not capture individual cow state, ration, weight, DIM, BCS, or numeric weather variation.

## Category Prediction Summary

| Genetic group | THI | Rows | Actual mean | Prediction mean |
|---|---|---:|---:|---:|
| HF50 | T0 | 15 | 5.4787 | 5.5494 |
| HF50 | T1 | 15 | 5.1720 | 5.1499 |
| HF50 | T2 | 15 | 4.5787 | 4.5853 |
| HF62.5 | T0 | 10 | 6.0740 | 6.0696 |
| HF62.5 | T1 | 10 | 5.3680 | 5.6701 |
| HF62.5 | T2 | 10 | 5.0970 | 5.1055 |
| HF75 | T0 | 15 | 7.2160 | 7.0543 |
| HF75 | T1 | 15 | 6.6213 | 6.6548 |
| HF75 | T2 | 15 | 6.0560 | 6.0901 |
| HF87.5 | T0 | 10 | 9.3580 | 9.4260 |
| HF87.5 | T1 | 10 | 8.9760 | 9.0265 |
| HF87.5 | T2 | 10 | 8.7360 | 8.4619 |

## Boundary

Permutation importance is predictive and descriptive, not causal or biological evidence.
