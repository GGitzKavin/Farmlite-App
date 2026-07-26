# Bangladesh Cross-Workbook Join Report

## Approved Key Basis

The audited in-memory key is `Animal ID + normalized THI Range + Replication No`. Metadata explicitly defines all three fields. Normalization only maps documented label variants (`T0` and `T0 (≤75)`, for example). Row order is not a key.

## `DMI, milk yield and composition.xlsx` ↔ `physiological responses.xlsx`

- Join safety: `POSSIBLE_WITH_LIMITATIONS`.
- Cardinality: `ONE_TO_ONE`.
- Match: 675 keys (90.0% left; 90.0% right).
- Missing keys: left 0; right 0.
- Duplicate-key rows: left 0; right 0.
- Left-only/right-only keys: 75/75.
- Left-only cows: ['111', '211', '311', '411', '511'].
- Right-only cows: ['101', '201', '301', '401', '501'].
- Many-to-many risk: False.

## `DMI, milk yield and composition.xlsx` ↔ `Blood metabolites.xlsx`

- Join safety: `SAFE_ONE_TO_ONE`.
- Cardinality: `ONE_TO_ONE`.
- Match: 750 keys (100.0% left; 100.0% right).
- Missing keys: left 0; right 0.
- Duplicate-key rows: left 0; right 0.
- Left-only/right-only keys: 0/0.
- Left-only cows: none.
- Right-only cows: none.
- Many-to-many risk: False.

## `physiological responses.xlsx` ↔ `Blood metabolites.xlsx`

- Join safety: `POSSIBLE_WITH_LIMITATIONS`.
- Cardinality: `ONE_TO_ONE`.
- Match: 675 keys (90.0% left; 90.0% right).
- Missing keys: left 0; right 0.
- Duplicate-key rows: left 0; right 0.
- Left-only/right-only keys: 75/75.
- Left-only cows: ['101', '201', '301', '401', '501'].
- Right-only cows: ['111', '211', '311', '411', '511'].
- Many-to-many risk: False.

## Decision

DMI/milk and blood can be joined one-to-one on the composite key. Physiology joins require source-owner resolution of the five-ID-per-group boundary mismatch. No joined data was saved.
