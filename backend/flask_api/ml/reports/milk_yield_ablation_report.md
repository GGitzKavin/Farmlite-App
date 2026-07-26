# FarmLite Milk-Yield Previous-Week-Yield Ablation

## Controlled Comparison

| Version | Validation MAE | Validation RMSE | Validation R² | Test MAE | Test RMSE | Test R² |
|---|---:|---:|---:|---:|---:|---:|
| Full nine features | 1.080926 | 1.352556 | 0.944781 | 1.075882 | 1.347188 | 0.945218 |
| Without `previous_week_avg_yield_l` | 2.616395 | 3.403136 | 0.650431 | 2.621518 | 3.393895 | 0.652322 |

## Interpretation

- Validation MAE increases by 1.535469 without the historical feature.
- Test MAE increases by 1.545636 without the historical feature.
- The difference shows how much predictive performance depends on previous-week yield within this synthetic dataset.
- A large difference is consistent with possible formula linkage in the undocumented synthetic generator; it does not prove leakage because the feature is temporally historical.
- Remaining ablation performance indicates how much signal the other eight features contain in these synthetic records.
- Strong full-model results do not establish real-world dairy, veterinary, or nutritional validity.
