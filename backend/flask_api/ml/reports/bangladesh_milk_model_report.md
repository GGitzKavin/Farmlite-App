# Bangladesh MILK Model Report

## Scope

- Target: `milk_yield_l_day` (L/cow/day).
- Primary features: `genetic_group`, `thi_category`.
- Group field: `cow_id`; cow ID is not predictive.
- Selection: development-only five-fold GroupKFold.
- Final evaluation: one untouched complete-cow holdout.

## Grouped Baselines

| Baseline | MAE | RMSE | R² | Median AE | Mean residual |
|---|---:|---:|---:|---:|---:|
| `bangladesh_milk_dummy_mean` | 2.1913 | 2.7196 | -0.0038 | 1.7812 | -0.0000 |
| `bangladesh_milk_dummy_median` | 2.1625 | 2.7444 | -0.0222 | 1.6475 | -0.3691 |

## Candidate Selection

- Status: `GROUPED_GATE_PASSED`.
- Reason: Lowest grouped-CV RMSE among candidates that meaningfully beat both baselines, had positive R² in every fold, finite predictions, no negative predictions, and stable fold MAE.
- Locked configuration: `bangladesh_milk_ridge_a0_1`.
- Group-CV MAE/RMSE/R²: 0.4631 / 0.5765 / 0.9549.
- Relative MAE/RMSE improvement: 78.58% / 78.80%.
- Fold MAE CV: 0.0835; all fold R² positive: True.

## Final Holdout

- Unseen cows/rows: 10 / 150.
- MAE/RMSE/R²: 0.4839 / 0.6031 / 0.8590.
- Median AE/mean residual: 0.3978 / -0.0062.
- Prediction range: 4.5853–9.4260; negatives: 0.
- Relative MAE/RMSE improvement: 63.17% / 66.06%.
- Decision: `BEATS_BASELINE`.

## Controlled Leave-One-Cow-Out Analysis

- Folds: 40; aggregate MAE/RMSE/R²: 0.4647 / 0.5780 / 0.9547.

## Holdout Breakdowns

### By THI category

| THI | Rows | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| T0 | 50 | 0.5123 | 0.6134 | 0.8397 |
| T1 | 50 | 0.4477 | 0.5541 | 0.8662 |
| T2 | 50 | 0.4916 | 0.6385 | 0.8466 |

### By genetic group

| Genetic group | Rows | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| HF50 | 45 | 0.4448 | 0.5426 | 0.3187 |
| HF62.5 | 30 | 0.4594 | 0.5790 | 0.2933 |
| HF75 | 45 | 0.5503 | 0.6806 | 0.3168 |
| HF87.5 | 30 | 0.4673 | 0.5887 | 0.0992 |

## Interpretation Boundary

Performance reflects in-study categorical group signal. It is not a causal effect, commercial validation, veterinary advice, or evidence that individual cow variation is fully captured.
