# FarmLite Synthetic Feed-Category Classifier Report

## Scope

Controlled candidate comparison on the locked training and validation partitions. Feed_Type is a synthetic category, not a veterinarian-selected or nutritionally optimal recommendation.

## Candidate Validation Metrics

| Configuration | Algorithm | Baseline | Accuracy | Balanced accuracy | Macro F1 | Weighted F1 | Predicted classes | Train s | Predict s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `feed_type_dummy_most_frequent` | DummyClassifier | True | 0.126293 | 0.125000 | 0.028033 | 0.028323 | 1 | 0.221 | 0.019 |
| `feed_type_dummy_stratified` | DummyClassifier | True | 0.123920 | 0.123922 | 0.123937 | 0.123935 | 8 | 0.180 | 0.024 |
| `feed_type_logistic_c1` | LogisticRegression | False | 0.125413 | 0.125395 | 0.124809 | 0.124820 | 8 | 0.619 | 0.022 |
| `feed_type_decision_tree` | DecisionTreeClassifier | False | 0.127173 | 0.127385 | 0.102179 | 0.102117 | 8 | 1.899 | 0.023 |
| `feed_type_random_forest` | RandomForestClassifier | False | 0.126960 | 0.126931 | 0.126889 | 0.126899 | 8 | 14.401 | 0.116 |
| `feed_type_hist_gradient_boosting` | HistGradientBoostingClassifier | False | 0.125653 | 0.125397 | 0.111244 | 0.111310 | 8 | 1.092 | 0.048 |

## Locked Validation Selection

- Configuration: `feed_type_random_forest`
- Algorithm: RandomForestClassifier
- Beats baselines on validation: False
- Release status before test: `RESEARCH_ONLY`
- Reason: Highest validation Macro F1 within the controlled candidate set, then balanced accuracy and class coverage; simplicity breaks near-ties. It does not clear the documented baseline margin and remains research-only despite being the strongest candidate.

## Interpretability

- `age_months`: 0.006146 ± 0.001271
- `ambient_temperature_c`: 0.006068 ± 0.003640
- `breed`: 0.004355 ± 0.003365
- `days_in_milk`: 0.004268 ± 0.002699
- `humidity_percent`: 0.004076 ± 0.000465
- `lactation_stage`: 0.002543 ± 0.003365
- `weight_kg`: 0.000886 ± 0.005856
- `previous_week_avg_yield_l`: -0.000105 ± 0.004121
- `body_condition_score`: -0.001791 ± 0.000552

Permutation importance describes validation association in a synthetic dataset. It is not causal or biological evidence.

## Limitations

- Eight classes are approximately balanced, so near-0.125 accuracy is near random.
- A highest-scoring candidate is not automatically useful or deployable.
- Probability output is not scientific confidence.
- The source population is not verified dairy-only.
