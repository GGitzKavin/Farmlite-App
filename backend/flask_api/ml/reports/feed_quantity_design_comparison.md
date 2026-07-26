# FarmLite Feed-Quantity Design A/B Comparison

| Split | Design A MAE | Design B MAE | Design A RMSE | Design B RMSE | Design A R2 | Design B R2 |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 3.178907 | 3.178797 | 3.959567 | 3.959885 | 0.002876 | 0.002716 |
| Test | 3.179455 | 3.179093 | 3.950254 | 3.950620 | 0.002746 | 0.002562 |

## Decision

- Locked design: **Design A**.
- Validation decision: Design B validation changes versus A: MAE +0.00%, RMSE -0.01%, R2 -0.000160. It does not clear all 1% MAE/RMSE and +0.01 R2 requirements; Design A is locked to avoid unjustified classifier dependency.
- Validation B-minus-A effect: MAE improvement +0.000110, RMSE improvement -0.000318, R2 improvement -0.000160.
- Test B-minus-A effect: MAE improvement +0.000362, RMSE improvement -0.000366, R2 improvement -0.000185.
- Validation/test improvement direction consistent: True.
- OOF classifier diagnostic Macro F1: 0.125524. Classifier errors therefore propagate into Design B's categorical input.
- Design B is not preferred for a tiny metric difference; it must justify its extra classifier dependency and OOF complexity.
