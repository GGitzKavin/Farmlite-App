# Rwanda Dairy Nutrition Dataset Audit

## Executive Summary

The source contains 96 cross-sectional lactating-cow observations, daily measured/recorded feed, milk, and water fields, composite feed laboratory characteristics, calculated nutrient intake and requirement fields, and 97 observed fodder-mixture descriptions.
It does not contain cow or farm identifiers, observation dates, a true feed recommendation label, optimized rations, concentrate quantities, mineral data, environmental measurements, or a lactating-cow ration-selection rule.
DMI is documented as served DM minus next-morning leftovers, but 28 negative leftover values block an unqualified DMI target until the authors clarify the source column. Milk and water fields are daily, but any model design remains limited by the small cross-sectional sample and absent grouping identifiers.

Final audit decision: **PARTIAL_OPTION_B_SUPPORT**. No training occurred.

## Source Files

| File | Size bytes | SHA-256 | Opens | Sheets/tables |
|---|---:|---|---|---|
| `Metadata.xlsx` | 12680 | `DD3001D696D217C19A6C3198A46F262BFD849BBCD061B62CDF974FE4E778E068` | True | 1 |
| `Specific data recorded on individual cows under lactation in Rwanda 2020-2021.xlsx` | 46769 | `4DADD19810DEA87E1EC2CAE915369E59AB71BF396893496151D8B2F50CF6C876` | True | 1 |
| `Different fodders components in the samples.xlsx` | 14417 | `BA5F9180494FDE7DBC58B95EA4018A08915AE023719D4D453F09D18C25F79D0A` | True | 2 |
| `Bucket feeding plan (Supplemental Table).docx` | 15953 | `B3192EEC974B2599C8607B4458825DA19C7919C87E2FEF263821A584D587493B` | True | 1 |

All source archives remained in place and were read without conversion.

## Licence and Citation

- Dataset: Energy, protein, dry matter and water gap analysis in dairy cows kept under cut and carry fodder-based feeding system. (Mendeley Data, V1).
- Dataset DOI: `10.17632/6jf28ftxrr.1`.
- Dataset licence: `CC BY 4.0`.
- Related article DOI: `10.1016/j.anopes.2025.100097`.
- The supplied files contain authorship/citation text but no licence statement; licence evidence comes from the Mendeley record.

## Study Design

- Cross-sectional; 66 lowland and 30 highland smallholder farms were purposively selected for having at least one lactating dairy cow.
- The related publication reports 96 dairy cows from 96 smallholder farms.
- Sampling was purposive at the cow/farm stage, not a randomized feeding trial.
- Data collection was observational and cross-sectional.
- Feeding system was cut-and-carry fodder based across the study.

## Metadata Workbook

- Sheets: `Metadata`
- Populated rows: 73
- Populated columns: 3
- Definition-table columns: `Number`, `Variables`, `explanations/definitions`
- Parsed definitions: 48
- Missing-value codes: none documented.
- Category definitions: sites, broad breed, lactation period, and calf age bands are documented.
- Formula descriptions: DMI, water, milk, ME, and CP equations are documented.
- Measurement-status counts: CALCULATED=22, DIRECTLY_MEASURED=7, IDENTIFIER=2, MODEL_DERIVED=7, OBSERVED=9, OWNER_REPORTED=1

| Variable | Exact definition | Unit | Period | Status |
|---|---|---|---|---|
| `sites` | Sites; 1=lowlands; 2=highlands | category code | UNCLEAR | `OBSERVED` |
| `LabN°` | Laboratory sample identification number: each lab number corresponds to mixture of fodder fed to each selected cow | identifier | UNCLEAR | `IDENTIFIER` |
| `cowbreed` | Cow breed: exotic and cross | category | UNCLEAR | `OBSERVED` |
| `cowageinyears` | Cow  age (years) | years | UNCLEAR | `OBSERVED` |
| `parity` | Cow parity; Number of birth that the cow has (number) | birth count | UNCLEAR | `OBSERVED` |
| `Bodyweight` | Cow body weight, (kg) | kg | UNCLEAR | `DIRECTLY_MEASURED` |
| `MW` | Cow metabolical weight=BW^0.75 (kg) | kg^0.75 | UNCLEAR | `CALCULATED` |
| `DMIR kg` | Dry matter intake requirement (kg) | kg DM/cow/day | per cow per day | `MODEL_DERIVED` |

The complete 48-field register is in `rwanda_variable_dictionary.csv`.

## Individual-Cow Workbook

- Sheet: `Raw data`; rows: 96; columns: 43.
- Header row: Excel row 11; source data rows: 12-107.
- Duplicate complete rows: 0.
- Excel formula cells: 8; most calculated values are stored constants.

### Observation Structure

The repository describes one cross-sectional lactating-cow observation from each of 96 farms. The workbook has 96 rows but does not contain a cow_id or farm_id, so row-level identity and repeated-cow absence cannot be independently proven from the file.

### Cow and Farm Identifiers

- `LabN°` is a composite feed laboratory/sample key, not a cow identifier.
- Workbook cow_id: `NOT_AVAILABLE`.
- Workbook farm_id: `NOT_AVAILABLE`.
- Publication-reported farms: 96; workbook-verifiable farm count: `UNCLEAR`.
- `LabN°` unique values: 90.

### Repeated Measurements

- Status: `UNCLEAR`.
- Reason: No cow identifier is present. LabN° is a composite feed sample identifier and must not be treated as cow_id.
- Future splitting rule: If a future source supplies repeated cow IDs, split by cow, never randomly by row.

### Candidate Features

- Evidenced fields: `breed`, `age_years`, `weight_kg`, `parity`, `lactation_stage`, `days_in_milk`, `current_milk_yield`, `location`, `water_access`.
- Current milk must be excluded from X when milk yield is the target.
- DMI, water, CP, ME, and gap outcomes must not enter pre-outcome features.
- `LabN°` and source row are identifiers only.

### Candidate Targets

- DMI: calculated source field, blocked pending negative-leftover clarification.
- Milk: verified daily hand-milk and calculated total daily milk, ready with limitations.
- Water: daily jerry-can-recorded intake, ready with limitations.
- CP and ME: calculated intakes/requirements, more defensible for rule validation than ML labels.
- Feed/ration category: no expert or optimized label.

### Missing Values

| Source column | Missing | Missing % | Unique | Types | Min | Max | Mean |
|---|---:|---:|---:|---|---:|---:|---:|
| `sites` | 0 | 0.00 | 2 | {"integer": 96} | 1.0000 | 2.0000 | 1.3125 |
| `LabN°` | 0 | 0.00 | 90 | {"integer": 96} | 224.0000 | 628.0000 | 372.0521 |
| `cowbreed` | 0 | 0.00 | 2 | {"string": 96} | UNCLEAR | UNCLEAR | UNCLEAR |
| `cowageinyears` | 2 | 2.08 | 27 | {"integer": 56, "number": 8, "string": 30} | 2.5000 | 18.0000 | 6.6312 |
| `parity` | 3 | 3.12 | 8 | {"number": 93} | 1.0000 | 12.0000 | 3.0108 |
| `Bodyweight` | 0 | 0.00 | 59 | {"integer": 96} | 243.0000 | 731.0000 | 431.7083 |
| `MW` | 0 | 0.00 | 59 | {"number": 96} | 61.5467 | 140.5847 | 94.3433 |
| `DMIR kg` | 0 | 0.00 | 59 | {"number": 96} | 8.5050 | 25.5850 | 15.1098 |
| `DM served` | 0 | 0.00 | 91 | {"number": 96} | 3.7020 | 37.2840 | 14.6683 |
| `leftover` | 0 | 0.00 | 96 | {"number": 96} | -8.5307 | 29.8955 | 5.5839 |
| `daysinmilk` | 0 | 0.00 | 24 | {"integer": 96} | 1.0000 | 540.0000 | 143.5104 |
| `lactationperiod` | 0 | 0.00 | 3 | {"string": 96} | UNCLEAR | UNCLEAR | UNCLEAR |
| `Ass.calfmilk` | 0 | 0.00 | 5 | {"integer": 96} | 0.0000 | 6.0000 | 2.7917 |
| `hand-milked yield` | 0 | 0.00 | 33 | {"number": 96} | 1.0000 | 17.0000 | 6.0542 |
| `Total milk performance` | 0 | 0.00 | 44 | {"number": 96} | 1.0000 | 21.0000 | 8.8458 |
| `gapmilk` | 0 | 0.00 | 44 | {"number": 96} | -3.0000 | 16.8000 | 7.6333 |
| `potentialmilk` | 0 | 0.00 | 5 | {"integer": 96} | 15.0000 | 25.0000 | 16.4792 |
| `%gapmilk` | 0 | 0.00 | 61 | {"number": 96} | -20.0000 | 93.3333 | 45.7171 |
| `waterday` | 0 | 0.00 | 13 | {"integer": 96} | 15.0000 | 80.0000 | 35.1042 |
| `waterrequi.` | 7 | 7.29 | 75 | {"number": 89} | 41.9120 | 78.2600 | 56.7442 |
| `gapwater` | 7 | 7.29 | 87 | {"number": 89} | -25.1900 | 49.0020 | 21.6546 |
| `%watergap` | 7 | 7.29 | 87 | {"number": 89} | -45.9588 | 72.2002 | 38.2920 |
| `DMfeeds` | 1 | 1.04 | 88 | {"number": 95} | 9.4400 | 46.7300 | 25.3311 |
| `MEfeeds` | 18 | 18.75 | 75 | {"number": 78} | 2.9338 | 11.0270 | 6.0284 |
| `NDF feeds` | 0 | 0.00 | 89 | {"number": 96} | 26.7700 | 77.9800 | 58.5536 |
| `DMIindex` | 0 | 0.00 | 89 | {"number": 96} | 1.5389 | 4.4826 | 2.1031 |
| `DMIcapacity (kgDM)` | 0 | 0.00 | 95 | {"number": 96} | 4.9231 | 19.6339 | 9.0844 |
| `DMI gap` | 0 | 0.00 | 96 | {"number": 96} | -6.7889 | 11.5401 | 6.0254 |
| `%gapDMI` | 0 | 0.00 | 96 | {"number": 96} | -52.8526 | 66.2293 | 39.3194 |
| `MEIntake` | 18 | 18.75 | 78 | {"number": 78} | 18.1549 | 159.1040 | 55.1737 |
| `MW*0.589=Energyformaintenance` | 16 | 16.67 | 51 | {"number": 80} | 36.2510 | 82.8044 | 55.8634 |
| `5.023*peakMilk` | 16 | 16.67 | 5 | {"number": 80} | 75.3450 | 125.5750 | 81.6238 |
| `MEmaint+peakmilk` | 16 | 16.67 | 66 | {"number": 80} | 112.1540 | 184.6501 | 137.4872 |
| `gapME` | 16 | 16.67 | 80 | {"number": 80} | -34.3718 | 161.9896 | 83.6928 |
| `%MEgap` | 16 | 16.67 | 79 | {"number": 80} | -27.5564 | 100.0000 | 60.7421 |
| `%Protein` | 9 | 9.38 | 78 | {"number": 87} | 3.9500 | 24.5300 | 9.8518 |
| `Protein/content/gr/kg` | 9 | 9.38 | 78 | {"number": 87} | 39.5000 | 245.3000 | 98.5184 |
| `Cpintakeingr` | 9 | 9.38 | 87 | {"number": 87} | 259.2525 | 2941.1610 | 896.7383 |
| `CPmaint=6.27*MW` | 0 | 0.00 | 59 | {"number": 96} | 385.8977 | 881.4660 | 591.5327 |
| `CPmilk` | 0 | 0.00 | 5 | {"integer": 96} | 1230.0000 | 2050.0000 | 1315.4167 |
| `TotalreqCP` | 0 | 0.00 | 76 | {"number": 96} | 1621.8378 | 2678.8644 | 1906.9493 |
| `gapCP` | 0 | 0.00 | 96 | {"number": 96} | -1185.4258 | 2266.3418 | 1094.2802 |
| `%CP gap` | 9 | 9.38 | 87 | {"number": 87} | -67.5173 | 85.5124 | 52.9196 |

In addition to explicit blanks, `cowageinyears` has 30 nonnumeric highland breed descriptions. Effective usable numeric age is 64/96, not the apparent 94/96 nonblank count.

### Data-Quality Issues

- Total issue records: 253 (ERROR=63, INFO=1, WARNING=189).
- Leading issue types: MISSING_VALUE=179, TEXT_IN_NUMERIC_AGE_COLUMN=30, NEGATIVE_LEFTOVER=28, REPEATED_INGREDIENT_IN_SAMPLE=4, DUPLICATE_SAMPLE_IDENTIFIER=3, INCONSISTENT_INGREDIENT_SPELLING=1, NO_COMPONENT_NUTRIENT_COLUMNS=1, DOCUMENTED_FORMULA_MISMATCH=1, MISLEADING_PERCENT_NAME=1, INCONSISTENT_UNIT_DEFINITION=1.
- No source record was removed, filled, standardized, or corrected.

## Fodder Components Workbook

- Sheets: `Composites feeds` (97 data rows) and `Sheet2` (2 definitions).
- Each row is a composite daily fodder-ingredient list keyed by `Lab N°`.
- Duplicate complete rows: 0; duplicate `Lab N°`: 0.

### Feed Ingredients

- Raw ingredient tokens: 473; case-sensitive unique raw tokens: 74.
- No standardized feed names or inferred categories were created.

### Dry Matter

No DM values are stored in this workbook. Composite-sample DM percentage is in cow-workbook column `DMfeeds` and requires the limited `Lab N°` relationship.

### Crude Protein

No CP values are stored in this workbook. Composite CP percentage is in `%Protein` in the cow workbook.

### Energy

No energy values are stored in this workbook. Calculated `MEfeeds` is in the cow workbook.

### Fibre

`NDF feeds` is stored in the cow workbook. Its metadata unit conflicts with the percentage-like values/equation and is UNCLEAR.

### Nutrient-Lookup Suitability

Decision: `PARTIALLY_COMPATIBLE`. It supports observed composite ingredient lookup after the limited Lab N° relationship, but not ingredient-specific nutrient lookup, direct ration validation, mineral calculations, or recommendation labels.

## Bucket Feeding Plan

### Purpose

One supplemental table describes a calf milk bucket-feeding program reported as followed by farmers in Rwanda's highlands and lowlands.

### Inputs

- Calf age bands from birth through weaning.

### Outputs

- Milk consumption per calf per day and contextual cow milk production per day.

### Units and Period

- Litres per day; some cells show morning/evening allocations such as `2L-2L`.

### Recommendation Status

Status: `VERIFIED_OBSERVED_PRACTICE`. The document says the plan was followed by farmers and cites farmer-field-school promoters; it does not establish an optimized or expert-approved ration.

### Rule-Engine Suitability

Supporting calf milk-allocation evidence only. It does not provide a lactating-cow roughage, concentrate, water, mineral, or ration-selection rule.

## Dry-Matter Intake Assessment

| Field | Source definition | Unit | Period | Measurement | Status |
|---|---|---|---|---|---|
| `DMIR kg` | Dry matter intake requirement (kg) | kg DM/cow/day | per cow per day | `MODEL_DERIVED` | `UNSUITABLE` |
| `DM served` | DM of served feeds(kgDM) | kg DM/cow/day | per cow per day | `DIRECTLY_MEASURED` | `PARTIALLY_DEFINED` |
| `leftover` | leftovers(kgDM) | kg DM/cow/day | per cow per day | `DIRECTLY_MEASURED` | `PARTIALLY_DEFINED` |
| `DMfeeds` | Dry matter in feeds. The DM content was determined by oven drying the samples at 60 degree Celcius for three days.(%) | percent | UNCLEAR | `DIRECTLY_MEASURED` | `UNSUITABLE` |
| `DMIindex` | Dry matter intake index: it is a value obtained by the DM intake of a given feed per 100 kg BW =120/NDF (%DM) | percent of body weight | UNCLEAR | `CALCULATED` | `UNSUITABLE` |
| `DMIcapacity (kgDM)` | Dry matter intake capacity:  dry matter intake of feeds per body weight=120/NDF x BW/100 (kg) | kg DM/cow/day | per cow per day | `CALCULATED` | `CALCULATED_DMI` |
| `DMI gap` | Dry matter intake gap=dry matter intake requirement minus dry matter intake capacity(kg) | kg DM/cow/day | per cow per day | `CALCULATED` | `PARTIALLY_DEFINED` |
| `%gapDMI` | Percentage of the dry matter intake gap=DM intake*100/DM intake requirement(%) | percent | UNCLEAR | `CALCULATED` | `PARTIALLY_DEFINED` |

The repository verifies daily DMI as served DM minus leftovers. The source column named `DMIcapacity (kgDM)` matches that equation, but it also matches a BW/NDF capacity equation and 28 leftover values are negative. Target status: `CALCULATED_DMI`; model-design decision: `BLOCKED_UNCLEAR_DEFINITION` until clarified.

## Milk-Yield Assessment

| Field | Source definition | Unit | Period | Measurement | Status |
|---|---|---|---|---|---|
| `Ass.calfmilk` | Assumed milk suckled by calf: from birth to 60 days of age= 6litres; from 61 days to 90 days=4 litres; from 91 days to 120 days=2 litres; 121 days to 200 days=1 litres; from 201 days on ward=0 litres (litres) | L/cow/day | per cow per day | `MODEL_DERIVED` | `PARTIALLY_DEFINED` |
| `hand-milked yield` | Hand milked yield, measured using graduated plastic measuring jugs of 1 litre, 2 litres and 5 litres capacity after each milking session.(litres) | L/cow/day | per cow per day | `DIRECTLY_MEASURED` | `VERIFIED_MILK_YIELD_L_DAY` |
| `Total milk performance` | Total milk performance: it is the addition of assumed milk suckled by the calf and the observed milk yield(litres) | L/cow/day | per cow per day | `CALCULATED` | `VERIFIED_MILK_YIELD_L_DAY` |
| `gapmilk` | Gap milk in litres: it is obtained by subtracting the total milk performance that include assumed milk suckled by the calf from the potential milk yields.(litres) | L/cow/day | per cow per day | `CALCULATED` | `PARTIALLY_DEFINED` |
| `potentialmilk` | Potential milk of the cow:potential milk production was estimated based on the information on potential milk yield achieved by similar breed of the same village(litres) | L/cow/day | per cow per day | `MODEL_DERIVED` | `PARTIALLY_DEFINED` |
| `%gapmilk` | Percentage of gap in milk yield=the total milk performance*100/potential milk value (%) | percent | UNCLEAR | `CALCULATED` | `PARTIALLY_DEFINED` |
| `Milk consumption/day` | Gradual milk consumption of a calf from birth to weaning time : 6litres, 6L,6L,4L,4L,2L,2L, weaning time | L/calf/day | per calf per day | `OBSERVED` | `PARTIALLY_DEFINED` |
| `Milk production/day` | Cow m milk performance from calving to weaning:Colostrum production from calving to 8th day post calving, normal milk production from 9th day onward | L/cow/day | per cow per day | `OBSERVED` | `PARTIALLY_DEFINED` |

`hand-milked yield` is the directly measured daily candidate (96 usable; 1-17 L/day; mean 6.0542). `Total milk performance` adds model-assumed calf suckling and is calculated. Model decision: `READY_WITH_LIMITATIONS`, especially due absent grouping keys.

## Water Assessment

| Field | Source definition | Unit | Period | Measurement | Status |
|---|---|---|---|---|---|
| `waterday` | Water consumed per day measured using the number of jeri cans of 20, 10 and 5 litres that a farmer provides to a cow per day(litres) | L/cow/day | per cow per day | `OWNER_REPORTED` | `VERIFIED_WATER_INTAKE_L_COW_DAY` |
| `waterrequi.` | The quantity of water that a cow is requiring. That quantity was calculated based on the formula by Erickson and Kalscheur (2019) FWI =12.3+2.15 x DMIR+0.73 x PM.  FWI(free water intake) is a function of dry matter intake requirement (DMIR) and potential milk (PM) (litres) | L/cow/day | per cow per day | `MODEL_DERIVED` | `VERIFIED_WATER_REQUIREMENT` |
| `gapwater` | The gap in water intake=the required water minus the free water intake(Litres) | L/cow/day | per cow per day | `CALCULATED` | `CALCULATED_WATER_GAP` |
| `%watergap` | The precentage of water gap=the gap in water * 100/ the required water (%) | percent | UNCLEAR | `CALCULATED` | `PARTIALLY_DEFINED` |

`waterday` has 96 usable values, 15-80 L/cow/day, mean 35.1042. It is container-based daily water provided/recorded, not a precise metered consumption measurement. Requirement and gaps are calculated. Model decision: `READY_WITH_LIMITATIONS`.

## Protein Assessment

| Field | Source definition | Unit | Period | Measurement | Status |
|---|---|---|---|---|---|
| `%Protein` | Percentage of protein in feeds (%) | percent | UNCLEAR | `DIRECTLY_MEASURED` | `VERIFIED_FEED_CP_PERCENT` |
| `Protein/content/gr/kg` | Protein content (g per kg) | g/kg DM | UNCLEAR | `CALCULATED` | `PARTIALLY_DEFINED` |
| `Cpintakeingr` | CP intake (g/day) | g/cow/day | per cow per day | `CALCULATED` | `VERIFIED_CP_INTAKE_G_DAY` |
| `CPmaint=6.27*MW` | CP for maintenance=6.27*MW (g/day) | g/cow/day | per cow per day | `MODEL_DERIVED` | `VERIFIED_CP_REQUIREMENT_G_DAY` |
| `CPmilk` | CP required for potential milk=82*Milk quantity(g/day) | g/cow/day | per cow per day | `MODEL_DERIVED` | `VERIFIED_CP_REQUIREMENT_G_DAY` |
| `TotalreqCP` | Total required CP for both maintenance and potential milk production=(6.26*MW)+(82*Milk quantity)(g/day) | g/cow/day | per cow per day | `MODEL_DERIVED` | `VERIFIED_CP_REQUIREMENT_G_DAY` |
| `gapCP` | Gap in CP intake=CP required for both maintenance and potential milk minus CP required for maintenance(g/day) | g/cow/day | per cow per day | `CALCULATED` | `CALCULATED_CP_GAP` |
| `%CP gap` | Percentage of gap in crude protein=obtaine value for gap in CP*100/the obtained value of total CP requirement(%) | percent | UNCLEAR | `CALCULATED` | `PARTIALLY_DEFINED` |

CP percentage is laboratory-derived; CP intake, maintenance, milk requirement, total requirement, and gaps are calculated. A metadata formula contradiction exists for `gapCP`. Best use: transparent rule validation after formula confirmation, not a learned requirement target.

## Energy Assessment

| Field | Source definition | Unit | Period | Measurement | Status |
|---|---|---|---|---|---|
| `MEfeeds` | Metabolizable energy in feeds = 2.2 + 0.136 G24 + 0.057CP + 0.0029CP^2. Where GV24 = gas volume generated after 24 h of substrate incubation; CP=crude protein content.(MJ/kg DM) | MJ/kg DM | UNCLEAR | `CALCULATED` | `FEED_ENERGY_COMPOSITION` |
| `MEIntake` | Metabolizable energy intake=ME in feeds x DM intake (MJ) | MJ/cow/day | per cow per day | `CALCULATED` | `VERIFIED_ME_INTAKE_MJ_DAY` |
| `MW*0.589=Energyformaintenance` | Energy for maintenance =BW^0.75 x 0.589 (MJ); where BW is the body weight | MJ/cow/day | per cow per day | `CALCULATED` | `VERIFIED_ME_REQUIREMENT_MJ_DAY` |
| `5.023*peakMilk` | Energy for potential milk=5.023*potential Milk(MJ/day) | MJ/cow/day | per cow per day | `CALCULATED` | `VERIFIED_ME_REQUIREMENT_MJ_DAY` |
| `MEmaint+peakmilk` | Energy for both maintenance and potential milk= energy for maintenance+ energy for potential milk(MJ/day) | MJ/cow/day | per cow per day | `CALCULATED` | `VERIFIED_ME_REQUIREMENT_MJ_DAY` |
| `gapME` | Gap ME= energy requirement minus energy intake(MJ/day) | MJ/cow/day | per cow per day | `CALCULATED` | `CALCULATED_ENERGY_GAP` |
| `%MEgap` | Percentage of ME gap=obtaned value for ME gap*100/obtained value for energy requirement (%) | percent | UNCLEAR | `CALCULATED` | `PARTIALLY_DEFINED` |

ME composition, intake, maintenance, potential-milk requirement, and gaps are calculated. `MEfeeds` lacks the row-level gas-volume input required to independently reproduce it. Best use: rule validation with documented equations and provenance.

## Feed-Category Label Assessment

The fodder workbook records ingredients actually served. It does not identify a nutritionist recommendation, optimized ration, treatment optimum, or broad expert label. Status: `OBSERVED_DIET_ONLY`. A genuine feed recommendation classifier is not supported; `EXPERT_FEED_LABELS_REQUIRED`.

## Cross-File Join Assessment

Cow workbook to fodder workbook via LabN°/Lab N°: 96/96 cow rows match (100.00%). Status: `POSSIBLE_WITH_LIMITATIONS`.
The cow table has 6 duplicate key occurrences; the fodder table has none. There is no many-to-many join.
- Metadata links semantically, not by record key.
- The DOCX has no cow/sample/farm key and cannot be row-joined.

## FarmLite Feature Compatibility

- Direct/partial current inputs: breed, age_years, weight, lactation stage, days in milk.
- Missing current inputs: previous-week yield, body-condition score, temperature, humidity.
- Useful future fields: parity, site, daily water, served DM, leftovers, and ingredient list.
- No frontend change was made.

## Leakage Risks

- Current/total milk is target leakage for a milk-yield model.
- DMI, water, CP, ME, requirements, and gaps are same-row outcomes.
- Calculated requirements are deterministic equations and poor ML targets.
- `LabN°` and source row can enable memorization and are identifier-only.
- Random row splitting is not defensible without cow/farm grouping evidence.

## Common Schema

The evidence-only schema is stored at `backend/flask_api/config/rwanda_dairy_common_schema.json`. Unsupported fields were omitted rather than filled with guesses.

## Option B Support Assessment

| Component | Decision |
|---|---|
| DMI regression | `BLOCKED_UNCLEAR_DEFINITION` |
| Milk-yield regression | `READY_WITH_LIMITATIONS` |
| Water-intake regression | `READY_WITH_LIMITATIONS` |
| CP intake/requirement | `READY_WITH_LIMITATIONS` for calculations/rules |
| Energy intake/requirement | `READY_WITH_LIMITATIONS` for calculations/rules |
| Feed/ration category | `NOT_SUPPORTED` without expert labels |
| Bucket ration selection | `NOT_SUPPORTED` for lactating cows |

## Limitations

- Small cross-sectional sample: 96 cow observations.
- No cow_id, farm_id, observation date, repeated-observation key, or treatment period.
- Purposive cow/farm inclusion limits representativeness.
- Thirty highland age cells contain breed text; two more are blank.
- Twenty-eight negative leftover values conflict with the weighing method.
- NDF unit and CP-gap metadata formula require clarification.
- Composite ingredients lack quantities and expert categories.
- No environmental measurements or historical milk yield.

## Final Decision

**PARTIAL_OPTION_B_SUPPORT**

The source can support a later, separately approved design phase for daily milk and water models and transparent nutrient rules. DMI model design is blocked pending source clarification. A genuine feed classifier and full ration recommendation remain unsupported.

No model was trained, evaluated, integrated, replaced, or deployed.
