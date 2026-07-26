# Bangladesh DMI Model Report

## Scope

- Target: `dry_matter_intake_kg_day` (kg/cow/day).
- Primary features: `genetic_group`, `thi_category`.
- Group field: `cow_id`; cow ID is not predictive.
- Selection: development-only five-fold GroupKFold.
- Final evaluation: one untouched complete-cow holdout.

## Grouped Baselines

| Baseline | MAE | RMSE | R² | Median AE | Mean residual |
|---|---:|---:|---:|---:|---:|
| `bangladesh_dmi_dummy_mean` | 2.1250 | 2.5850 | -0.0030 | 1.9561 | -0.0000 |
| `bangladesh_dmi_dummy_median` | 2.1177 | 2.5885 | -0.0057 | 1.8475 | -0.1580 |

## Candidate Selection

- Status: `GROUPED_GATE_PASSED`.
- Reason: Lowest grouped-CV RMSE among candidates that meaningfully beat both baselines, had positive R² in every fold, finite predictions, no negative predictions, and stable fold MAE.
- Locked configuration: `bangladesh_dmi_ridge_a0_1`.
- Group-CV MAE/RMSE/R²: 0.3301 / 0.4082 / 0.9750.
- Relative MAE/RMSE improvement: 84.41% / 84.21%.
- Fold MAE CV: 0.0432; all fold R² positive: True.

## Final Holdout

- Unseen cows/rows: 10 / 150.
- MAE/RMSE/R²: 0.3235 / 0.4008 / 0.9413.
- Median AE/mean residual: 0.2684 / 0.0364.
- Prediction range: 8.5286–13.8656; negatives: 0.
- Relative MAE/RMSE improvement: 78.07% / 78.83%.
- Decision: `BEATS_BASELINE`.

## Controlled Leave-One-Cow-Out Analysis

- Folds: 40; aggregate MAE/RMSE/R²: 0.3304 / 0.4086 / 0.9749.

## Holdout Breakdowns

### By THI category

| THI | Rows | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| T0 | 50 | 0.3638 | 0.4588 | 0.9263 |
| T1 | 50 | 0.3406 | 0.4093 | 0.9232 |
| T2 | 50 | 0.2660 | 0.3222 | 0.9540 |

### By genetic group

| Genetic group | Rows | MAE | RMSE | R² |
|---|---:|---:|---:|---:|
| HF50 | 45 | 0.3618 | 0.4509 | 0.5132 |
| HF62.5 | 30 | 0.2781 | 0.3359 | 0.6828 |
| HF75 | 45 | 0.3206 | 0.3946 | 0.6873 |
| HF87.5 | 30 | 0.3156 | 0.3896 | 0.7200 |

## Interpretation Boundary

Performance reflects in-study categorical group signal. It is not a causal effect, commercial validation, veterinary advice, or evidence that individual cow variation is fully captured.
