# Rwanda Protein and Energy Rule Assessment

## Field and Equation Register

| Field | Classification | Unit | Formula/source | Required inputs | Reproducibility | Decision |
|---|---|---|---|---|---|---|
| %Protein | Laboratory composition | percent of DM | Kjeldahl method in repository | %Protein | YES for 87 rows | READY_AFTER_UNIT_CLARIFICATION |
| Protein/content/gr/kg | Calculated composition conversion | g/kg DM | %Protein × 10 | %Protein | PARTIALLY_REPRODUCIBLE | READY_AFTER_UNIT_CLARIFICATION |
| Cpintakeingr | Calculated intake | g/cow/day | CP g/kg × DMI | CP composition; DMI | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |
| CPmaint=6.27*MW | Model-derived requirement | g/cow/day | 6.27 × MW | body weight; metabolic weight | REPRODUCIBLE_WITH_TOLERANCE | RESEARCH_REFERENCE_ONLY |
| CPmilk | Model-derived requirement | g/cow/day | 82 × potential milk | potential milk | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |
| TotalreqCP | Model-derived requirement | g/cow/day | maintenance CP + milk CP | stored requirement components | REPRODUCIBLE_WITH_TOLERANCE | READY_AFTER_FORMULA_CLARIFICATION |
| gapCP | Calculated gap | g/cow/day | total requirement - current CP intake | requirement; intake | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |
| MEfeeds | Unreproducible calculated composition | MJ/kg DM | 2.2 + 0.136G24 + 0.057CP + 0.0029CP² | G24; CP | NOT_REPRODUCIBLE_MISSING_INPUT | NOT_REPRODUCIBLE |
| MEIntake | Calculated intake | MJ/cow/day | MEfeeds × DMI | ME composition; DMI | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |
| MW*0.589=Energyformaintenance | Model-derived requirement | MJ/cow/day | MW × 0.589 | body weight; MW | PARTIALLY_REPRODUCIBLE | RESEARCH_REFERENCE_ONLY |
| 5.023*peakMilk | Model-derived requirement | MJ/cow/day | 5.023 × potential milk | potential milk | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |
| MEmaint+peakmilk | Model-derived requirement | MJ/cow/day | maintenance ME + milk ME | stored requirement components | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |
| gapME | Calculated gap | MJ/cow/day | total ME requirement - ME intake | requirement; intake | PARTIALLY_REPRODUCIBLE | READY_AFTER_FORMULA_CLARIFICATION |

## Equation Detail

| Field | Formula | Source/citation | Required inputs | Available inputs | Unit | Reproducibility | Applicable to FarmLite | Safe for prototype rule use | Remaining limitation |
|---|---|---|---|---|---|---|---|---|---|
| `%Protein` | Laboratory Kjeldahl result | AOAC method named in repository (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Composite feed sample | Composite sample and 87 stored results | percent of DM | Laboratory source value; not recalculated | Potentially | Only after unit/sample linkage review | Nine missing values; not ingredient-specific |
| `Protein/content/gr/kg` | `%Protein × 10` | Workbook metadata/stored arithmetic | `%Protein` | 87 CP-percent values | g/kg DM | `PARTIALLY_REPRODUCIBLE` | Yes | Only after unit approval | Nine missing upstream values |
| `Cpintakeingr` | `CP g/kg × DMI` | Mendeley reproduction notes (https://data.mendeley.com/datasets/6jf28ftxrr/1) | CP composition; DMI | 87 comparable rows | g/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | DMIcapacity semantics unresolved |
| `CPmaint=6.27*MW` | `6.27 × BW^0.75` | Van der Linden et al. named in repository (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Body weight | 96 body weights/MW values | g/cow/day | `REPRODUCIBLE_WITH_TOLERANCE` | Potentially | Only after guideline applicability review | Equation version and population applicability need confirmation |
| `CPmilk` | `82 × potential milk` | Van der Linden et al. named in repository (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Potential milk | 96 potential-milk values | g/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | 22 stored mismatches; potential milk is model-derived |
| `TotalreqCP` | `maintenance CP + milk CP` | Workbook metadata | Stored CP components | 96 stored components | g/cow/day | `REPRODUCIBLE_WITH_TOLERANCE` | Potentially | NO currently | Reproduces internally but inherits CPmilk conflicts |
| `gapCP` | `total CP requirement - current CP intake` | Mendeley reproduction notes (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Requirement; intake | 87 comparable rows | g/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | Metadata gives a conflicting formula |
| `%CP gap` | `gapCP × 100 / TotalreqCP` | Workbook metadata | CP gap; total requirement | 87 comparable rows | percent | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | Nine stored values missing; inherits upstream conflicts |
| `MEfeeds` | `2.2 + 0.136G24 + 0.057CP + 0.0029CP²` | Groot and Oomen named in repository (https://data.mendeley.com/datasets/6jf28ftxrr/1) | G24; CP | CP is partial; G24 absent | MJ/kg DM | `NOT_REPRODUCIBLE_MISSING_INPUT` | Potentially | NO | G24 and CP equation basis/version must be supplied |
| `MEIntake` | `MEfeeds × DMI` | Mendeley reproduction notes (https://data.mendeley.com/datasets/6jf28ftxrr/1) | ME composition; DMI | 78 comparable rows | MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | Inherits missing G24 and DMI ambiguity |
| `MW*0.589=Energyformaintenance` | `0.589 × BW^0.75` | Van der Linden et al. named in repository (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Body weight/MW | Inputs available for 96 rows | MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | Only after guideline review | 16 stored outputs missing |
| `5.023*peakMilk` | `5.023 × potential milk` | Van der Linden et al. named in repository (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Potential milk | Input available for 96 rows | MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | 20 mismatches and 16 stored outputs missing |
| `MEmaint+peakmilk` | `maintenance ME + milk ME` | Workbook metadata | Stored requirement components | Components available together for 80 rows | MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | Inherits inconsistent/missing component values |
| `gapME` | `total ME requirement - ME intake` | Mendeley reproduction notes (https://data.mendeley.com/datasets/6jf28ftxrr/1) | Requirement; intake | 78 comparable rows | MJ/cow/day | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | Inherits composition, DMI and requirement limitations |
| `%MEgap` | `gapME × 100 / total ME requirement` | Workbook metadata | ME gap; total requirement | 80 comparable rows | percent | `PARTIALLY_REPRODUCIBLE` | Potentially | NO currently | Inherits every upstream ME limitation |

## Applicability to FarmLite

Deterministic equations should be implemented transparently as versioned rules rather than learned by a model only when their sources, units, inputs, and target-population applicability are approved.

- CP intake is blocked by DMI semantics.
- CP requirements need equation provenance and correction of inconsistent `CPmilk` rows.
- CP gap needs an explicit owner decision resolving metadata.
- ME composition is not reproducible without G24.
- ME intake inherits both ME composition and DMI limitations.
- ME requirements need correction of inconsistent/missing rows.

## Overall Decisions

- CP: `READY_AFTER_FORMULA_CLARIFICATION`
- ME: `NOT_REPRODUCIBLE` for composition; requirements are `READY_AFTER_FORMULA_CLARIFICATION`
- Current use: `RESEARCH_REFERENCE_ONLY`; no production rule change is authorized.
