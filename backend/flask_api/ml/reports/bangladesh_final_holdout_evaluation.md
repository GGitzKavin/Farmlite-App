# Bangladesh Final Complete-Cow Holdout Evaluation

Selections were locked before this evaluation. The holdout contains complete cows never used in candidate selection or development fitting.

| Task | Baseline | Selected model | Group-CV result | Holdout result | Decision |
|---|---|---|---|---|---|
| DMI | Mean + median | `bangladesh_dmi_ridge_a0_1` | MAE 0.3301, R² 0.9750 | MAE 0.3235, R² 0.9413 | `BEATS_BASELINE` |
| MILK | Mean + median | `bangladesh_milk_ridge_a0_1` | MAE 0.4631, R² 0.9549 | MAE 0.4839, R² 0.8590 | `BEATS_BASELINE` |

## Boundary

Positive in-study holdout performance does not establish production, commercial, veterinary, or cross-population validity.
