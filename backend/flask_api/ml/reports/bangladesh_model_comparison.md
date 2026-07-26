# Bangladesh Model Comparison

## 1

Does DMI beat its grouped baseline? **Yes**.
## 2

Does milk yield beat its grouped baseline? **Yes**.
## 3

Are results stable across cows? **Grouped-fold stability passed**; LOCO and per-cow metrics remain part of the uncertainty record.
## 4

Does THI add signal? See the task feature reports; importance is predictive, not causal.
## 5

Does genetic group add signal? See the task feature reports; much of the model is group-average structure.
## 6

Do results generalize to unseen cows? **Within this study holdout, yes**; external populations are untested.
## 7

Suitable for integration review? **Candidate review only**; never automatic integration.
## 8

Feed-quantity restoration? **Prototype DMI prediction restored with limitations**; ration selection and ingredient quantities remain absent.
## 9

Limitations: 50 cows, categorical THI only, incomplete DMI protocol, two categorical inputs, no commercial validation, and no expert feed labels.
## 10

Synthetic milk candidate: retain unchanged and compare further as a separate-provenance prototype; do not replace it automatically.

## Recommendation

`READY_FOR_DMI_AND_MILK_INTEGRATION_REVIEW`

No existing or candidate synthetic model was replaced. No integration was performed.
