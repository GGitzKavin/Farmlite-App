# Bangladesh DMI Feature Analysis

## Method

Permutation importance on the final complete-cow holdout using negative MAE; descriptive, not causal.

## Permutation Importance

| Feature | Mean MAE increase | SD |
|---|---:|---:|
| `genetic_group` | 1.3816 | 0.0977 |
| `thi_category` | 0.3617 | 0.0340 |

## Findings

- THI-category contribution is `POSITIVE` under holdout permutation (MAE increase 0.3617).
- Genetic-group contribution is `POSITIVE` (MAE increase 1.3816).
- With only two categorical features, predictions primarily represent learned group-level differences. They do not capture individual cow state, ration, weight, DIM, BCS, or numeric weather variation.

## Category Prediction Summary

| Genetic group | THI | Rows | Actual mean | Prediction mean |
|---|---|---:|---:|---:|
| HF50 | T0 | 15 | 9.7400 | 9.7797 |
| HF50 | T1 | 15 | 9.1493 | 9.1654 |
| HF50 | T2 | 15 | 8.6000 | 8.5286 |
| HF62.5 | T0 | 10 | 10.8730 | 10.8845 |
| HF62.5 | T1 | 10 | 10.1300 | 10.2702 |
| HF62.5 | T2 | 10 | 9.6590 | 9.6335 |
| HF75 | T0 | 15 | 12.2487 | 12.0048 |
| HF75 | T1 | 15 | 11.3540 | 11.3905 |
| HF75 | T2 | 15 | 10.7853 | 10.7537 |
| HF87.5 | T0 | 10 | 14.2730 | 13.8656 |
| HF87.5 | T1 | 10 | 13.0650 | 13.2513 |
| HF87.5 | T2 | 10 | 12.6840 | 12.6145 |

## Boundary

Permutation importance is predictive and descriptive, not causal or biological evidence.
