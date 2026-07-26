# FarmLite Phase 4 Model Comparison

| Task | Baseline | Best candidate | Validation result | Test result | Release decision |
|---|---|---|---|---|---|
| Feed type | Stratified dummy | `feed_type_random_forest` | Macro F1 0.126889 | Macro F1 0.122735 | REJECTED_NO_LEARNABLE_SIGNAL |
| Feed quantity Design A | Best dummy | `feed_quantity_hist_gradient_boosting` | MAE 3.178907 | MAE 3.179455 | REJECTED_NO_LEARNABLE_SIGNAL |
| Milk yield | Best dummy | `milk_yield_hist_gradient_boosting` | MAE 1.080926 | MAE 1.075882 | CANDIDATE_ACCEPTED_WITH_LIMITATIONS |

## Required Conclusions

1. Feed_Type meaningfully predictable: **False** (DOES_NOT_BEAT_BASELINE).
2. Feed_Quantity_kg meaningfully predictable: **False** (DOES_NOT_BEAT_BASELINE).
3. Predicted feed type selected: **False**. Design B validation changes versus A: MAE +0.00%, RMSE -0.01%, R2 -0.000160. It does not clear all 1% MAE/RMSE and +0.01 R2 requirements; Design A is locked to avoid unjustified classifier dependency.
4. Milk_Yield_L meaningfully predictable: **True** (BEATS_BASELINE).
5. Previous-week dependence: removing it changes test MAE by +1.545636; see ablation report.
6. Validation/test stability statuses: DOES_NOT_BEAT_BASELINE; DOES_NOT_BEAT_BASELINE; BEATS_BASELINE.
7. Tasks beating baselines: milk yield.
8. Integration-review candidates: milk_yield. Integration remains unapproved.
9. Tasks without eligible artifacts require target/data redesign or a better-scoped, expert-validated dataset.
10. Complete Option B architecture supported: **False**. All dependent components must independently clear their gates.
