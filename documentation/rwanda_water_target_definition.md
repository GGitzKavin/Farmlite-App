# Rwanda Water Target Definition

## Source Evidence

- Field: `waterday`
- Metadata wording: "Water consumed per day measured using the number of jeri
  cans of 20, 10 and 5 litres that a farmer provides to a cow per day."
- Repository method: water was recorded from graduated jerry cans provided to
  cows daily.
- Repository gap equation: water required per day minus water provided per day.
- Unit and period: L/cow/day.
- Usable values: 96/96
- Missing values: 0
- Range: 15-80 L/cow/day.
- Collection status: owner/farmer-reported container count.
- Direct metering of drinking: `NOT_VERIFIED`
- Remaining/refused water measured: `NOT_AVAILABLE`
- Household/herd aggregation: `UNCLEAR`; wording says per cow.

Repository evidence supports **provided water**, not verified physiological
consumption. The metadata's use of "consumed" conflicts with its own collection
description. No conversion or semantic relabelling was applied.

## Formula Relationships

- Requirement: `12.3 + 2.15 × DMIR + 0.73 × potential milk`.
- Gap: requirement minus `waterday`.
- Requirement reconstruction: 66/89 stored values match within tolerance,
  23 mismatch, and seven are missing despite available inputs.
- Gap reconstruction: 88/89 comparable values match; source row 77 conflicts.

## Provisional Status

`VERIFIED_WATER_PROVIDED_L_COW_DAY`

A water-consumption/intake regressor is not approved. A future model of
farmer-provided water would still require row independence and target-timing
confirmation.

Primary reproduction evidence: https://data.mendeley.com/datasets/6jf28ftxrr/1
