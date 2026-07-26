# FarmLite Phase 4.5E Bangladesh Integration Review

## Scope and Decision

Phase 4.5E is an integration review only. It did not load either Bangladesh
candidate from a Flask route, replace the retained milk model, change the feed
planner or nutrition rules, change the React application or PDF, or promote an
artifact.

Final recommendation:

`CONDITIONAL_INTEGRATION_REQUIRES_NEW_INPUT`

This recommendation permits a later, separately approved implementation phase
to build a disabled-by-default prototype inference path under the controls in
`backend/flask_api/config/bangladesh_integration_review.json`. It is not
runtime, production, commercial, veterinary, deployment, or automatic
integration approval. Both artifacts remain `CANDIDATE_ONLY`.

## Review Gate

| Check | Status | Evidence | Phase 4.5E decision |
|---|---|---|---|
| Candidate identity and integrity | `PASS` | DMI SHA-256 `312DDB...035B`; milk SHA-256 `AA650E...F56E`; metadata and artifact targets/features agree | A later loader must verify the full hash and metadata before deserialization. |
| Grouped development validation | `PASS` | Cow-grouped validation passed for DMI and milk | Preserve the candidate metrics and grouping limitations. |
| Locked unseen-cow holdout | `PASS_WITH_SCOPE_LIMIT` | DMI MAE/R² `0.3235/0.9413`; milk MAE/R² `0.4839/0.8590` | Valid only as in-study prototype evidence. |
| Genetic-group coverage in final holdout | `PASS_WITH_LIMITATIONS` | Holdout covered `HF50`, `HF62.5`, `HF75`, and `HF87.5`; it contained no `Local` cows | Treat `Local` as `LIMITED_SUPPORT` with a warning; reject only unknown categories. |
| Current FarmLite genetic input compatibility | `BLOCKED_IN_CURRENT_RUNTIME` | FarmLite stores free-text breed, not an exact `% HF` genetic group | Require a separate exact `genetic_group` field. Never infer it from breed text. |
| THI input compatibility | `READY_AFTER_ADAPTER` | FarmLite has temperature and humidity fields, but currently permits silent defaults | Make both measured inputs required and derive THI server-side. |
| Unknown-category handling | `BLOCKED_IN_CURRENT_RUNTIME` | The fitted encoders use `handle_unknown="ignore"` | The adapter must reject unknown values before the pipeline sees them. |
| DMI meaning versus feed recommendation | `BLOCKED_FOR_RATION_USE` | Target is dry-matter intake in kg/cow/day; it is not an as-fed ration, feed type, or ingredient quantity | Expose only as `predicted_dmi_kg_day`; never map it to legacy `totalFeedKg` or nutrition outputs. |
| Milk candidate replacement | `NOT_AUTHORIZED` | Bangladesh milk is a separate-provenance two-category-feature candidate | A future prototype may expose it separately; it must not silently replace the retained model. |
| Reproducible model loading | `READY_AFTER_HARDENING` | Artifacts reload under scikit-learn 1.8.0; requirements are not version-pinned and metadata contains a machine-specific absolute path | Pin compatible dependencies, locate from trusted project settings, and verify hashes. |
| External/population validation | `BLOCKED` | Only the 50-cow study population has been evaluated | Keep production, commercial, and veterinary approval false. |
| Runtime integration in Phase 4.5E | `PASS` | Runtime baseline hashes are recorded in the review contract | No runtime integration occurred. |

## Artifact and Pipeline Review

Both serialized artifacts are scikit-learn pipelines with:

- feature order `genetic_group`, then `thi_category`;
- a `OneHotEncoder(handle_unknown="ignore")`;
- trained genetic categories `HF50`, `HF62.5`, `HF75`, `HF87.5`, and
  `Local`;
- trained THI categories `T0`, `T1`, and `T2`;
- Ridge regression with `alpha=0.1`.

The encoder's ability to produce a number for an unknown category is a
technical fallback, not validation evidence. A future request adapter must
fail closed before prediction.

The locked holdout manifest has 150 rows from ten cows:

| Genetic group | Holdout rows | Approximate holdout cows |
|---|---:|---:|
| `HF50` | 45 | 3 |
| `HF62.5` | 30 | 2 |
| `HF75` | 45 | 3 |
| `HF87.5` | 30 | 2 |
| `Local` | 0 | 0 |

The original overall unseen-cow holdout result remains valid, but it must not
be interpreted as locked holdout evidence for `Local`.

## Guarded Request Adapter

A future prototype request must require:

```json
{
  "genetic_group": "HF75",
  "ambient_temperature_c": 28,
  "humidity_percent": 75
}
```

Accepted genetic-group values are exactly `Local`, `HF50`, `HF62.5`, `HF75`,
and `HF87.5`. `Local` must receive a limited-support warning. Free-text breed
substitutions, missing values, and unknown categories must be rejected. The UI must explain that this value is known
Holstein-Friesian genetic proportion, not an ordinary breed name.

Use farmer-provided dry-bulb temperature `T` in degrees Celsius and relative
humidity `RH` in percent:

`THI = (1.8 × T + 32) - [(0.55 - 0.0055 × RH) × (1.8 × T - 26)]`

Map the result exactly:

- `T0` when THI is at most 75;
- `T1` when THI is greater than 75 and less than 80;
- `T2` when THI is at least 80.

The server must require finite temperature, require finite relative humidity
from 0 through 100, calculate THI itself, and return the numeric THI and
derived category for traceability. It must not accept a client-selected THI
category, invent weather defaults, or back-calculate historical weather.

## Guarded Output Boundary

A later prototype may return two separate signals:

- `predicted_dmi_kg_day`: predicted dry-matter intake in kg/cow/day;
- `predicted_milk_yield_l_day`: predicted milk yield in L/cow/day.

Every response must identify both outputs as `CANDIDATE_ONLY`, include model
and contract versions, artifact hashes, dataset DOI/licence, derived THI,
value sources, and the study/population limitations.

The DMI value must not become:

- `totalFeedKg`;
- an as-fed feed quantity;
- a roughage or concentrate amount;
- a mineral or water recommendation;
- a feeding frequency;
- a feed type or ration prescription.

The milk value must not automatically replace the existing synthetic
milk-yield route. Side-by-side prototype evaluation requires a later explicit
implementation decision.

## Required Controls Before Any Runtime Enablement

1. Add a separate candidate inference service and route behind a
   disabled-by-default feature flag.
2. Pin compatible Python, scikit-learn, pandas, and joblib versions.
3. Resolve artifacts from trusted repository settings, not the absolute path
   recorded by the training machine.
4. Verify artifact SHA-256 and metadata before calling `joblib.load`.
5. Implement and boundary-test the fail-closed genetic-group and THI adapter.
6. Keep the candidate endpoint separate from feed-planning and nutrition
   outputs.
7. Preserve explicit candidate/prototype warnings in API, UI, and any later
   export.
8. Add monitoring for validation rejects, category distribution, non-finite
   predictions, and model-loading failures before enabling the feature flag.

## Remaining Evidence Needed for Stronger Claims

- external or cross-population validation;
- locked holdout or external evidence for `Local` cows before stronger than
  limited-support use;
- a fully documented DMI offered/refusal measurement protocol;
- validated mapping from FarmLite cattle records to exact genetic proportions;
- validation of farmer-entered weather and THI-category derivation in the
  intended deployment context;
- a nutrition dataset and expert labels before any feed-ration claim.
