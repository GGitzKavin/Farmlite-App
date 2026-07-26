# Bangladesh Group Split Report

## Design

A fixed-seed `GroupShuffleSplit` creates a final 20% complete-cow holdout. Only the remaining development cows enter `GroupKFold(n_splits=5)`. Every observation from a cow remains in one partition and one validation fold.

- Random seed: `42`.
- Development: 600 rows / 40 cows.
- Final holdout: 150 rows / 10 cows.
- Cow overlap: 0.
- Missing partition/fold assignments: 0/0.

## Fold Inventory

| Fold | Cows | Rows | THI distribution | Genetic distribution |
|---:|---:|---:|---|---|
| 1 | 8 | 120 | T0=40, T1=40, T2=40 | HF50=15, HF62.5=30, HF75=15, HF87.5=30, Local=30 |
| 2 | 8 | 120 | T0=40, T1=40, T2=40 | HF50=15, HF62.5=30, HF75=15, HF87.5=30, Local=30 |
| 3 | 8 | 120 | T0=40, T1=40, T2=40 | HF50=15, HF62.5=30, HF75=15, HF87.5=30, Local=30 |
| 4 | 8 | 120 | T0=40, T1=40, T2=40 | HF50=30, HF62.5=15, HF75=30, HF87.5=15, Local=30 |
| 5 | 8 | 120 | T0=40, T1=40, T2=40 | HF50=30, HF62.5=15, HF75=30, HF87.5=15, Local=30 |

## Final Holdout

- Cow IDs: 205, 209, 211, 307, 308, 402, 404, 411, 507, 510.
- THI: T0=50, T1=50, T2=50.
- Genetic groups: HF50=45, HF62.5=30, HF75=45, HF87.5=30.

## Leakage Checks

- No cow appears in both development and holdout.
- No development cow appears in more than one GroupKFold validation fold.
- Holdout rows have no CV-fold assignment.
- Replication number is lineage only, not a model feature.
- Final holdout metrics are calculated only after the selection lock is written.
