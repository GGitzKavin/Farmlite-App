# FarmLite Phase 4 One-Time Final Test Evaluation

The selected configurations and both predeclared A/B or ablation variants were written to `locked_model_selection.json` before these test targets were scored. Test results did not change selection.

| Task | Baseline | Selected model | Validation metric | Test metric | Status |
|---|---|---|---:|---:|---|
| Feed type | Dummy stratified Macro F1 | `feed_type_random_forest` | Macro F1 0.126889 | Macro F1 0.122735 | `DOES_NOT_BEAT_BASELINE` |
| Feed quantity Design A | Best dummy MAE | `feed_quantity_hist_gradient_boosting` | MAE 3.178907 | MAE 3.179455 | `DOES_NOT_BEAT_BASELINE` |
| Milk yield | Best dummy MAE | `milk_yield_hist_gradient_boosting` | MAE 1.080926 | MAE 1.075882 | `BEATS_BASELINE` |
