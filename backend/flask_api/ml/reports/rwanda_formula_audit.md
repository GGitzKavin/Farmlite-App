# Rwanda Formula Reconstruction Audit

## Scope and Method

Stored values were compared in memory with every documented formula and with explicitly labelled alternative interpretations. Exact tolerance is 1e-9; rounding tolerance is 0.01. No result replaced a source value.

## Status Summary

| Status | Formula interpretations |
|---|---:|
| `FULLY_REPRODUCIBLE` | 8 |
| `REPRODUCIBLE_WITH_TOLERANCE` | 5 |
| `PARTIALLY_REPRODUCIBLE` | 15 |
| `NOT_REPRODUCIBLE_MISSING_INPUT` | 1 |
| `NOT_REPRODUCIBLE_CONFLICT` | 1 |
| `FORMULA_NOT_DOCUMENTED` | 1 |
| `UNCLEAR` | 0 |

## Formula Results

| ID | Domain | Target | Formula | Exact | Tolerance | Mismatch | Missing inputs | Stored missing | Status | Ambiguous |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| `RW-FORM-MILK-001` | MILK | `Ass.calfmilk` | 6 L through day 60; 4 L days 61-90; 2 L days 91-120; 1 L days 121-200; 0 L from day 201 | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | NO |
| `RW-FORM-MILK-002` | MILK | `Total milk performance` | Ass.calfmilk + hand-milked yield | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | NO |
| `RW-FORM-MILK-003` | MILK | `gapmilk` | potentialmilk - Total milk performance | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | NO |
| `RW-FORM-MILK-004` | MILK | `%gapmilk` | gapmilk * 100 / potentialmilk | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | NO |
| `RW-FORM-MILK-005` | MILK | `potentialmilk` | Estimated from similar breed in the same village | 0 | 0 | 0 | 0 | 0 | `FORMULA_NOT_DOCUMENTED` | YES |
| `RW-FORM-ANIMAL-001` | ANIMAL | `MW` | Bodyweight ** 0.75 | 17 | 79 | 0 | 0 | 0 | `REPRODUCIBLE_WITH_TOLERANCE` | NO |
| `RW-FORM-LACTATION-001` | LACTATION | `lactationperiod` | Peak: days 1-100; middle: days 101-200; late: day 201+ | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | NO |
| `RW-FORM-DMI-001` | DMI | `DMIR kg` | Bodyweight * 0.035 | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | YES |
| `RW-FORM-DMI-002A` | DMI | `DMIcapacity (kgDM)` | DM served - leftover | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | YES |
| `RW-FORM-DMI-002B` | DMI | `DMIcapacity (kgDM)` | (120 / NDF feeds) * Bodyweight / 100 | 55 | 14 | 27 | 0 | 0 | `PARTIALLY_REPRODUCIBLE` | YES |
| `RW-FORM-DMI-003` | DMI | `DMIindex` | 120 / NDF feeds | 96 | 0 | 0 | 0 | 0 | `FULLY_REPRODUCIBLE` | YES |
| `RW-FORM-DMI-004` | DMI | `DMI gap` | DMIR kg - DMIcapacity (kgDM) | 76 | 20 | 0 | 0 | 0 | `REPRODUCIBLE_WITH_TOLERANCE` | YES |
| `RW-FORM-DMI-005` | DMI | `%gapDMI` | DMI gap * 100 / DMIR kg | 19 | 77 | 0 | 0 | 0 | `REPRODUCIBLE_WITH_TOLERANCE` | YES |
| `RW-FORM-WATER-001` | WATER | `waterrequi.` | 12.3 + 2.15 * DMIR kg + 0.73 * potentialmilk | 6 | 60 | 23 | 0 | 7 | `PARTIALLY_REPRODUCIBLE` | YES |
| `RW-FORM-WATER-002` | WATER | `gapwater` | waterrequi. - waterday | 19 | 69 | 1 | 7 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-WATER-003` | WATER | `%watergap` | gapwater * 100 / waterrequi. | 25 | 64 | 0 | 7 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-CP-001` | PROTEIN | `Protein/content/gr/kg` | %Protein * 10 | 87 | 0 | 0 | 9 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-CP-002` | PROTEIN | `Cpintakeingr` | Protein/content/gr/kg * DMIcapacity (kgDM) | 2 | 85 | 0 | 9 | 0 | `PARTIALLY_REPRODUCIBLE` | YES |
| `RW-FORM-CP-003` | PROTEIN | `CPmaint=6.27*MW` | 6.27 * MW | 0 | 96 | 0 | 0 | 0 | `REPRODUCIBLE_WITH_TOLERANCE` | NO |
| `RW-FORM-CP-004` | PROTEIN | `CPmilk` | 82 * potentialmilk | 74 | 0 | 22 | 0 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-CP-005` | PROTEIN | `TotalreqCP` | CPmaint=6.27*MW + CPmilk | 8 | 88 | 0 | 0 | 0 | `REPRODUCIBLE_WITH_TOLERANCE` | NO |
| `RW-FORM-CP-006A` | PROTEIN | `gapCP` | TotalreqCP - Cpintakeingr | 9 | 78 | 0 | 9 | 0 | `PARTIALLY_REPRODUCIBLE` | YES |
| `RW-FORM-CP-006B` | PROTEIN | `gapCP` | TotalreqCP - CPmaint=6.27*MW | 0 | 0 | 96 | 0 | 0 | `NOT_REPRODUCIBLE_CONFLICT` | YES |
| `RW-FORM-CP-007` | PROTEIN | `%CP gap` | gapCP * 100 / TotalreqCP | 6 | 81 | 0 | 0 | 9 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-ME-001` | ENERGY | `MEfeeds` | 2.2 + 0.136 * G24 + 0.057 * CP + 0.0029 * CP**2 | 0 | 0 | 0 | 96 | 0 | `NOT_REPRODUCIBLE_MISSING_INPUT` | YES |
| `RW-FORM-ME-002` | ENERGY | `MEIntake` | MEfeeds * DMIcapacity (kgDM) | 12 | 66 | 0 | 18 | 0 | `PARTIALLY_REPRODUCIBLE` | YES |
| `RW-FORM-ME-003` | ENERGY | `MW*0.589=Energyformaintenance` | MW * 0.589 | 15 | 65 | 0 | 0 | 16 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-ME-004` | ENERGY | `5.023*peakMilk` | 5.023 * potentialmilk | 60 | 0 | 20 | 0 | 16 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-ME-005` | ENERGY | `MEmaint+peakmilk` | MW*0.589=Energyformaintenance + 5.023*peakMilk | 11 | 69 | 0 | 16 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-ME-006` | ENERGY | `gapME` | MEmaint+peakmilk - MEIntake | 9 | 69 | 0 | 18 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |
| `RW-FORM-ME-007` | ENERGY | `%MEgap` | gapME * 100 / MEmaint+peakmilk | 3 | 77 | 0 | 16 | 0 | `PARTIALLY_REPRODUCIBLE` | NO |

## Key Conflicts

- `DMIcapacity (kgDM)`: served-minus-leftover reproduces all 96 stored values; the documented NDF/body-weight capacity equation is only partial. Neither arithmetic result proves actual consumed DMI.
- `waterrequi.`: the documented equation matches 66 of 89 stored values within tolerance, conflicts in 23, and has seven source blanks despite available inputs.
- `gapwater`: 88 of 89 comparable values match; source row 77 is materially inconsistent.
- `CPmilk` and `5.023*peakMilk`: stored source subsets do not use the current row's potential-milk value.
- `gapCP`: the repository formula reproduces stored values; the workbook metadata alternative conflicts in all rows.
- `MEfeeds`: G24 is absent, so the composition equation is not independently reproducible.

## Decision

`WAITING_FOR_DATA_CLARIFICATION`. Reproducible arithmetic is not automatically a measured target or approved rule.
