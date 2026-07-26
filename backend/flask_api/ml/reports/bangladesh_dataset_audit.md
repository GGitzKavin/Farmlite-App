# Bangladesh HF Cross Dataset Audit

## Executive Decision

**Final decision: `DMI_AND_MILK_SUPPORT`.**

The source verifies a DMI field in kg per cow per day and daily milk yield in L per cow per day, each with 750 usable repeated observations from 50 cows. Both are `READY_WITH_LIMITATIONS` for future model design. This does not establish a feed/ration recommendation label.

## Scope and Audit Order

Audit only. The files were read in the required order: `metadata.docx`, DMI/milk workbook, physiology workbook, then blood workbook. No model was fitted, evaluated, integrated, deployed, or replaced; no joined or processed dataset was saved.

## Source Provenance

- Repository dataset: [Physiological responses, Dry matter Intake, milk yield, composition and blood metabolites of HF Cross cows](https://data.mendeley.com/datasets/954f6g36sb/2).
- Citation: Pehan Eshtiak Ahamed (2026), V2, DOI `10.17632/954f6g36sb.2`.
- Repository licence: `CC BY 4.0`.
- Related article: [Effects of cyclic temperature-humidity index on milk production, physiological and haematobiochemical responses in Holstein-Friesian cows of varied genetic proportions](https://www.sciencedirect.com/science/article/pii/S2772694026000130), DOI `10.1016/j.anopes.2026.100139`.
The repository record is supplemental provenance. Local-file facts and external-record facts are kept distinct.

## Metadata DOCX Audit

- Title: Effects of Cyclic THI on Milk Yield, Composition, Somatic Cell Count, Physiological and Hemato-Biochemical Profile in Holstein-Friesian Cows of Varied Genetic Proportions
- Authors/contributors: Corresponding Author: Md. Rakibul Hassan; Email: mdrakibulhassan@gmail.com | Contributors: Eshtiak Ahamed Pehan (Data curation, analysis, and compilation)Bangladesh Livestock Research Institute (BLRI), Savar, Dhaka, Bangladesh
- Paragraphs/headings/tables: 46/4/0.
- Parsed variable definitions: 33.
- Local study period/cow count/sampling frequency: `UNCLEAR`; repository: January–December 2024, 50 cows, five milk/blood samples per THI category.
- Local DOCX licence: `UNCLEAR`; matched repository record: `CC BY 4.0`.
- Absent/unclear: parity, weight, age, DIM, lactation stage, BCS, missing codes, exact DMI/milk methods, instruments, and laboratory assays.

## Workbook Structure

### `DMI, milk yield and composition.xlsx` / `Sheet1`

- Shape: **750 data rows × 13 columns**.
- Columns: `Animal ID`, `Genetic Group`, `THI Range`, `Replication No`, `DMI (kg)`, `Milk Yield (L/day/cow)`, `SCC cells per mL`, `Fat%`, `SNF%`, `Protein %`, `Salt%`, `Lactose%`, `pH`
- Missing cells by parsed values: 0; exact duplicate rows: 0; duplicate composite keys: 0.
- Cows: 50; records/cow: 15–15.
- Row structure: `ONE_ROW_PER_COW_PER_THI_CATEGORY_PER_REPLICATION`.
- Hidden sheets: 0; formulas: 0; merged ranges: 0; comments: 0.

| Field | n | Min | Max | Mean | Median | SD | Zero | Negative |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Animal ID` | 750 | 102.000 | 511.000 | 306.500 | 306.500 | 141.545 | 0 | 0 |
| `Replication No` | 750 | 1.000 | 5.000 | 3.000 | 3.000 | 1.415 | 0 | 0 |
| `DMI (kg)` | 750 | 4.480 | 14.820 | 10.050 | 10.150 | 2.463 | 0 | 0 |
| `Milk Yield (L/day/cow)` | 750 | 0.300 | 10.470 | 5.529 | 5.805 | 2.572 | 0 | 0 |
| `SCC cells per mL` | 750 | 97000.000 | 364000.000 | 218884.000 | 217500.000 | 48790.784 | 0 | 0 |
| `Fat%` | 750 | 2.870 | 4.310 | 3.565 | 3.560 | 0.282 | 0 | 0 |
| `SNF%` | 750 | 6.330 | 10.380 | 8.445 | 8.420 | 0.686 | 0 | 0 |
| `Protein %` | 750 | 2.460 | 3.600 | 3.096 | 3.090 | 0.211 | 0 | 0 |
| `Salt%` | 750 | 0.589 | 0.820 | 0.689 | 0.687 | 0.044 | 0 | 0 |
| `Lactose%` | 750 | 3.700 | 5.500 | 4.642 | 4.620 | 0.311 | 0 | 0 |
| `pH` | 750 | 6.670 | 7.160 | 6.910 | 6.900 | 0.096 | 0 | 0 |

### `physiological responses.xlsx` / `Sheet1`

- Shape: **750 data rows × 7 columns**.
- Columns: `Animal ID`, `Genetic group`, `THI Range`, `Replication No`, `Rectal Temp (F)`, `Pulse Rate (bpm)`, `Respiration Rate (bpm)`
- Missing cells by parsed values: 0; exact duplicate rows: 0; duplicate composite keys: 0.
- Cows: 50; records/cow: 15–15.
- Row structure: `ONE_ROW_PER_COW_PER_THI_CATEGORY_PER_REPLICATION`.
- Hidden sheets: 0; formulas: 0; merged ranges: 0; comments: 0.

| Field | n | Min | Max | Mean | Median | SD | Zero | Negative |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Animal ID` | 750 | 101.000 | 510.000 | 305.500 | 305.500 | 141.545 | 0 | 0 |
| `Replication No` | 750 | 1.000 | 5.000 | 3.000 | 3.000 | 1.415 | 0 | 0 |
| `Rectal Temp (F)` | 750 | 101.230 | 103.460 | 102.391 | 102.410 | 0.372 | 0 | 0 |
| `Pulse Rate (bpm)` | 750 | 58.800 | 72.500 | 65.122 | 65.100 | 2.464 | 0 | 0 |
| `Respiration Rate (bpm)` | 750 | 25.000 | 46.200 | 34.362 | 33.350 | 4.761 | 0 | 0 |

### `Blood metabolites.xlsx` / `Sheet1`

- Shape: **750 data rows × 13 columns**.
- Columns: `Animal ID`, `Genetic Group`, `THI Range`, `Replication No`, `Glucose (mmol/L)`, `Total Protein (g/dL)`, `Uric Acid (mg/dL)`, `Cholesterol (mg/dL)`, `Calcium (mg/dL)`, `HDL (mg/dL)`, `AST (U/I)`, `ALT (U/I)`, `Cortisol (µg/dL)`
- Missing cells by parsed values: 0; exact duplicate rows: 0; duplicate composite keys: 0.
- Cows: 50; records/cow: 15–15.
- Row structure: `ONE_ROW_PER_COW_PER_THI_CATEGORY_PER_REPLICATION`.
- Hidden sheets: 0; formulas: 0; merged ranges: 0; comments: 0.

| Field | n | Min | Max | Mean | Median | SD | Zero | Negative |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Animal ID` | 750 | 102.000 | 511.000 | 306.500 | 306.500 | 141.545 | 0 | 0 |
| `Replication No` | 750 | 1.000 | 5.000 | 3.000 | 3.000 | 1.415 | 0 | 0 |
| `Glucose (mmol/L)` | 750 | 2.490 | 3.780 | 3.147 | 3.150 | 0.221 | 0 | 0 |
| `Total Protein (g/dL)` | 750 | 5.940 | 9.290 | 7.328 | 7.160 | 0.751 | 0 | 0 |
| `Uric Acid (mg/dL)` | 750 | 0.630 | 1.930 | 1.223 | 1.220 | 0.206 | 0 | 0 |
| `Cholesterol (mg/dL)` | 750 | 80.520 | 284.270 | 168.159 | 149.070 | 57.093 | 0 | 0 |
| `Calcium (mg/dL)` | 750 | 1.910 | 6.250 | 3.992 | 3.890 | 0.914 | 0 | 0 |
| `HDL (mg/dL)` | 750 | 47.850 | 156.120 | 106.656 | 116.805 | 29.769 | 0 | 0 |
| `AST (U/I)` | 750 | 17.930 | 35.190 | 26.420 | 26.210 | 3.355 | 0 | 0 |
| `ALT (U/I)` | 750 | 24.510 | 40.970 | 32.985 | 32.940 | 3.166 | 0 | 0 |
| `Cortisol (µg/dL)` | 750 | 2.620 | 10.870 | 5.610 | 5.290 | 1.852 | 0 | 0 |

## DMI Target Audit

- Exact field: `DMI (kg)`.
- Definition/status: dry matter intake per cow; metadata variable name specifies kg/day. `VERIFIED_DMI_KG_COW_DAY`.
- Usable/missing: 750 / 0.0%.
- Range/mean/median/SD: 4.480–14.820 / 10.050 / 10.150 / 2.463 kg/cow/day.
- Zero/negative: 0/0.
- Feed offered/refused fields: absent. The source presents DMI as measured intake, not estimated requirement, but the exact offered/refusal protocol is `UNCLEAR`.
- Repeats: five observations in each of T0/T1/T2 for every cow; cow grouping is possible. Variation is non-zero, but adequacy must be assessed with cow-grouped validation.
- ML decision: `READY_WITH_LIMITATIONS`.

## Milk-Yield Target Audit

- Exact field: `Milk Yield (L/day/cow)`.
- Definition/status: daily milk yield per cow in litres; `VERIFIED_MILK_YIELD_L_COW_DAY`.
- Usable/missing: 750 / 0.0%.
- Range/mean/median/SD: 0.300–10.470 / 5.529 / 5.805 / 2.572 L/cow/day.
- Zero/negative: 0/0.
- Exact recording instrument/time-of-day protocol is `UNCLEAR`. Litres were not converted to kilograms.
- ML/external-validation decision: `READY_WITH_LIMITATIONS`; external validation requires compatible features, timing, population, and units.

## Milk-Composition Audit

Verified fields: `SCC cells per mL`, `Fat%`, `SNF%`, `Protein %`, `Salt%`, `Lactose%`, and `pH`. All have 750 non-missing repeated records. Total solids and density are not present.
Roles: composition fields are `ML_TARGET_CANDIDATE` or `OPTIONAL_DIAGNOSTIC`; as prediction-time inputs they are `POSSIBLE_LEAKAGE` because same-record timing and farmer availability are not established. Exact laboratory or instrument methods are `UNCLEAR`.

## Physiological and Environmental Audit

Verified physiology: `Rectal Temp (F)` (101.23–103.46 °F), `Pulse Rate (bpm)` (58.8–72.5 beats/min), and `Respiration Rate (bpm)` (25.0–46.2 breaths/min). The last header uses bpm, while metadata defines breaths/min.
No ambient temperature, relative humidity, numeric THI, date, or time is stored in the supplied workbooks. `THI Range` is an assigned categorical environmental group.
The related article documents `THI = (1.8 × T + 32) − [(0.55 − 0.0055 × RH) × (1.8 × T − 26)]` with T = dry-bulb temperature (°C); RH = relative humidity (%). Reproduction cannot be checked because numeric T, RH, and THI are absent.
Repository provenance says physiological readings were taken twice daily on milk/blood sampling dates and averaged; whether the averages precede DMI/milk prediction is `UNCLEAR`.

## Blood-Metabolite Audit

Verified fields: glucose, total protein, uric acid, cholesterol, calcium, HDL, AST, ALT, and cortisol (750 non-missing records each). AST/ALT units conflict: workbook `U/I`, metadata `U/L`.
Roles: all are `RESEARCH_OUTCOME` and `NOT_AVAILABLE_AT_FARM_INFERENCE`; cortisol may be a `POSSIBLE_HEAT_STRESS_TARGET`. None is approved as a FarmLite prediction-time input.

## Identifier and Repeated-Measure Audit

Each workbook has 50 cow IDs and exactly 15 records/cow: 3 THI categories × 5 replication numbers. Within each workbook, `Animal ID + THI Range + Replication No` is unique.
No standalone observation ID, date, or sampling timestamp exists. `Animal ID` is safe for future grouped validation. All rows from a cow must remain in one partition/fold.
DMI/blood cow IDs are 102–111, 202–211, …, 502–511; physiology uses 101–110, 201–210, …, 501–510. Thus only 45 cow IDs are shared with physiology.

## Cross-Workbook Join Audit

| Left | Right | Key matches | Match % | Cardinality | Decision |
|---|---|---:|---:|---|---|
| `DMI, milk yield and composition.xlsx` | `physiological responses.xlsx` | 675 | 90.0% | ONE_TO_ONE | `POSSIBLE_WITH_LIMITATIONS` |
| `DMI, milk yield and composition.xlsx` | `Blood metabolites.xlsx` | 750 | 100.0% | ONE_TO_ONE | `SAFE_ONE_TO_ONE` |
| `physiological responses.xlsx` | `Blood metabolites.xlsx` | 675 | 90.0% | ONE_TO_ONE | `POSSIBLE_WITH_LIMITATIONS` |

DMI/milk ↔ blood is `SAFE_ONE_TO_ONE` (750/750). Joins involving physiology are `POSSIBLE_WITH_LIMITATIONS` (675/750; 90%). No row-order join is valid, and no joined dataset was saved.

## Data-Quality Analysis

- Issue rows: 169 (HIGH=155, MEDIUM=10, LOW=4).
- 150 rows describe the cross-workbook physiology cow-ID coverage mismatch (75 on each side), not 150 independent defect types.
- No parsed missing values, exact duplicate rows, duplicate composite keys, formulas, negative/zero DMI, or negative/zero milk yield were detected.
- Other findings: mixed blood-ID cell types (2 cells), genetic/THI label formatting differences, AST/ALT unit conflicts, missing dates/environmental inputs, and undocumented methods. No source value was corrected.
- Biological plausibility of physiological/laboratory values was not asserted without a source-specific clinical reference and protocol.

## Leakage Audit

| Candidate field | DMI model | Milk model | Reason |
|---|---|---|---|
| Genetic group | `SAFE` | `SAFE` | Stable source attribute. |
| THI category | `UNCLEAR` | `UNCLEAR` | Available only if future conditions are measured and categorized consistently. |
| Same-day milk/DMI | `POSSIBLE_LEAKAGE` | `POSSIBLE_LEAKAGE` | Timing/order is not established. |
| Physiology | `UNCLEAR` | `UNCLEAR` | Averaged on sampling dates; pre-prediction availability is not established. |
| Milk composition | `POSSIBLE_LEAKAGE` | `POSSIBLE_LEAKAGE` | Same-record outcomes. |
| Blood metabolites | `RESEARCH_ONLY` | `RESEARCH_ONLY` | Laboratory outcomes unavailable to typical farmers. |

## FarmLite Compatibility

Only 1/9 current inputs are present or partially mappable: `breed` is only represented by genetic group. Age, weight, lactation stage, DIM, previous-week yield, BCS, numeric ambient temperature, and humidity are missing.
Potential future inputs: genetic group and measured temperature/humidity or numeric THI. Physiology could be an optional research input only after timing and farmer availability are justified. No frontend was changed.

## Model-Support Assessment

| Proposed model | Decision |
|---|---|
| A — DMI regression | `READY_WITH_LIMITATIONS`: target verified; very limited practical feature set and grouped validation required. |
| B — milk-yield regression | `READY_WITH_LIMITATIONS`: target verified; very limited feature set and timing gaps. |
| C — heat-stress-aware milk | `READY_WITH_LIMITATIONS`: categorical THI only; numeric T/RH/THI absent. |
| D — heat-stress-aware DMI | `READY_WITH_LIMITATIONS`: categorical THI only; numeric T/RH/THI absent. |
| E — physiological response | `READY_WITH_LIMITATIONS` as optional research, not core FarmLite. |
| F — feed/ration category | `NOT_SUPPORTED`: no expert or optimized ration labels. |

## Limitations and Blockers

- Exact DMI feed-offered/refusal protocol is `UNCLEAR`.
- Numeric temperature, humidity, THI, dates, and timestamps are absent.
- Physiology cow-ID coverage conflicts with DMI/milk and blood.
- Eight of nine current FarmLite inputs are absent.
- Same-day outcome timing creates unresolved leakage risks.
- No ration ingredients, quantities, or expert recommendations exist.
- Rwanda DMI semantics remain unclear, preventing DMI external validation.

## Audit-Only Boundary

No training, estimator fitting, prediction, model evaluation, preprocessing output, permanent join, dataset concatenation, unit conversion, source edit, route edit, frontend edit, PDF edit, nutrition-rule edit, model replacement, or deployment occurred.
