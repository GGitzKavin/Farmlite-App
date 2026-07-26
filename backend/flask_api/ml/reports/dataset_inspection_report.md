# FarmLite Dataset Inspection Report

## Executive Summary

Phase 1 audited both original CSV files without modifying or merging them. Each contains 250,000 rows; the milk file has 37 columns and the disease file has 40 columns. Both have unique, perfectly sequential `Cattle_ID` values, no parsed missing cells, no exact duplicate rows, the same 40 breed labels, the same eight near-balanced feed categories, and identical shared record values. These are strong generated-data indicators, but no local metadata explicitly confirms synthetic generation.

`Feed_Type`, `Feed_Quantity_kg`, and `Milk_Yield_L` all remain blocked for genuine-model training. Feed type is not documented as recommended rather than observed; feed quantity has no documented material basis or period; and milk yield has no documented period. Provenance and reliable dairy-only filtering are also unresolved.

No model was trained, evaluated, replaced, or loaded by this audit.

## Dataset Inventory

| Dataset | Relative path | Bytes | Rows | Columns | Duplicates | Empty rows | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global_cattle_milk_yield_prediction_dataset.csv | datasets/raw/global_cattle_milk_yield_prediction_dataset.csv | 48805186 | 250000 | 37 | 0 | 0 | 26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3 |
| global_cattle_disease_detection_dataset.csv | datasets/raw/global_cattle_disease_detection_dataset.csv | 54792252 | 250000 | 40 | 0 | 0 | 4CEDFA77234FE45B441E303FF051C33123969E37C3B484A03387094A613DC4B9 |

### Milk-yield dataset exact columns

`Cattle_ID`, `Breed`, `Region`, `Country`, `Climate_Zone`, `Management_System`, `Age_Months`, `Weight_kg`, `Parity`, `Lactation_Stage`, `Days_in_Milk`, `Feed_Type`, `Feed_Quantity_kg`, `Feeding_Frequency`, `Water_Intake_L`, `Walking_Distance_km`, `Grazing_Duration_hrs`, `Rumination_Time_hrs`, `Resting_Hours`, `Ambient_Temperature_C`, `Humidity_percent`, `Season`, `Housing_Score`, `FMD_Vaccine`, `Brucellosis_Vaccine`, `HS_Vaccine`, `BQ_Vaccine`, `Anthrax_Vaccine`, `IBR_Vaccine`, `BVD_Vaccine`, `Rabies_Vaccine`, `Previous_Week_Avg_Yield`, `Body_Condition_Score`, `Milking_Interval_hrs`, `Date`, `Farm_ID`, `Milk_Yield_L`

Missing values and inferred types are included in the column-profile tables below. Total parsed missing cells: 0.

### Disease dataset exact columns

`Cattle_ID`, `Breed`, `Region`, `Country`, `Climate_Zone`, `Management_System`, `Age_Months`, `Weight_kg`, `Parity`, `Lactation_Stage`, `Days_in_Milk`, `Feed_Type`, `Feed_Quantity_kg`, `Water_Intake_L`, `Walking_Distance_km`, `Grazing_Duration_hrs`, `Rumination_Time_hrs`, `Resting_Hours`, `Body_Temperature_C`, `Heart_Rate_bpm`, `Respiratory_Rate`, `Ambient_Temperature_C`, `Humidity_percent`, `Season`, `Housing_Score`, `Milk_Yield_L`, `FMD_Vaccine`, `Brucellosis_Vaccine`, `HS_Vaccine`, `BQ_Vaccine`, `Anthrax_Vaccine`, `IBR_Vaccine`, `BVD_Vaccine`, `Rabies_Vaccine`, `Previous_Week_Avg_Yield`, `Body_Condition_Score`, `Milking_Interval_hrs`, `Date`, `Farm_ID`, `Disease_Status`

Missing values and inferred types are included in the column-profile tables below. Total parsed missing cells: 0.

## Dataset Provenance

Status: **NOT_DOCUMENTED**.

Repository notes explicitly state that publisher, source URL, license, collection protocol, data dictionary, representativeness, and measurement validity are not documented. No authoritative local evidence was found.

Repository search: 43 eligible text files searched; 20 relevant files inspected. License files found: none. Citation files found: none.

Files inspected:

- `backend/flask_api/config/__init__.py`
- `backend/flask_api/config/settings.py`
- `backend/flask_api/ml/preprocessing/__init__.py`
- `backend/flask_api/ml/preprocessing/feature_pipeline.py`
- `backend/flask_api/ml/preprocessing/inspect_datasets.py`
- `backend/flask_api/ml/reports/candidate_model_evaluation_report.txt`
- `backend/flask_api/ml/reports/dataset_inspection_report.txt`
- `backend/flask_api/ml/reports/feed_model_report.txt`
- `backend/flask_api/ml/reports/milk_yield_model_report.txt`
- `backend/flask_api/ml/training/evaluate_candidate_models.py`
- `backend/flask_api/ml/training/train_feed_model.py`
- `backend/flask_api/ml/training/train_milk_yield_model.py`
- `backend/flask_api/README.md`
- `datasets/README.md`
- `frontend/README.md`
- `notes/current_ml_status.md`
- `notes/dataset_sources.md`
- `notes/migration_notes.md`
- `notes/option_b_implementation_plan.md`
- `README.md`

The audit did not browse the web.

## Dairy-Cattle Suitability

### Milk-yield dataset

Status: **PARTIALLY_SUITABLE**.

- Unique breeds (40): `Africander`, `Ankole`, `Australian_Friesian_Sahiwal`, `Australian_Milking_Zebu`, `Ayrshire`, `Boran`, `Brown_Swiss`, `Butana`, `Danish_Red`, `Deoni`, `Exotic_Local_Cross`, `Fleckvieh`, `Gangatiri`, `Gir`, `Girolando`, `Guernsey`, `Hariana`, `Holstein-Friesian`, `Holstein_Zebu_Cross`, `Illawarra_Shorthorn`, `Jersey`, `Jersey_Zebu_Cross`, `Kankrej`, `Kenana`, `Krishna_Valley`, `Milking_Shorthorn`, `Montbeliarde`, `NDama`, `Normande`, `Norwegian_Red`, `Ongole`, `Rathi`, `Red_Poll_Africa`, `Red_Sindhi`, `Sahiwal`, `Simmental`, `Tharparkar`, `Tipo_Carora`, `White_Fulani`, `Zebu_Cross_Brazil`
- Dairy indicators: `Australian_Friesian_Sahiwal`, `Australian_Milking_Zebu`, `Ayrshire`, `Brown_Swiss`, `Danish_Red`, `Girolando`, `Guernsey`, `Holstein-Friesian`, `Holstein_Zebu_Cross`, `Illawarra_Shorthorn`, `Jersey`, `Jersey_Zebu_Cross`, `Milking_Shorthorn`, `Montbeliarde`, `Norwegian_Red`, `Tipo_Carora`
- Beef/non-specialized indicators: `Africander`, `Ankole`, `Boran`, `NDama`, `Ongole`, `White_Fulani`
- Unclassified or dual-purpose names: `Butana`, `Deoni`, `Exotic_Local_Cross`, `Fleckvieh`, `Gangatiri`, `Gir`, `Hariana`, `Kankrej`, `Kenana`, `Krishna_Valley`, `Normande`, `Rathi`, `Red_Poll_Africa`, `Red_Sindhi`, `Sahiwal`, `Simmental`, `Tharparkar`, `Zebu_Cross_Brazil`
- Other species: not observed, but No species column exists. All observed Breed labels look cattle-related, but absence of a species field prevents an authoritative species check.
- Dairy-only filtering: Breed can support a documented allow-list, but the file has no authoritative species or dairy-production-purpose field. A reliable dairy-only filter requires source documentation for every breed category.
- Lactation: Early, Mid, and Late stages are distinguishable and all rows have a stage, but no Dry or Non_Lactating category proves whether non-lactating cattle were excluded.

### Disease dataset

Status: **PARTIALLY_SUITABLE**.

- Unique breeds (40): `Africander`, `Ankole`, `Australian_Friesian_Sahiwal`, `Australian_Milking_Zebu`, `Ayrshire`, `Boran`, `Brown_Swiss`, `Butana`, `Danish_Red`, `Deoni`, `Exotic_Local_Cross`, `Fleckvieh`, `Gangatiri`, `Gir`, `Girolando`, `Guernsey`, `Hariana`, `Holstein-Friesian`, `Holstein_Zebu_Cross`, `Illawarra_Shorthorn`, `Jersey`, `Jersey_Zebu_Cross`, `Kankrej`, `Kenana`, `Krishna_Valley`, `Milking_Shorthorn`, `Montbeliarde`, `NDama`, `Normande`, `Norwegian_Red`, `Ongole`, `Rathi`, `Red_Poll_Africa`, `Red_Sindhi`, `Sahiwal`, `Simmental`, `Tharparkar`, `Tipo_Carora`, `White_Fulani`, `Zebu_Cross_Brazil`
- Dairy indicators: `Australian_Friesian_Sahiwal`, `Australian_Milking_Zebu`, `Ayrshire`, `Brown_Swiss`, `Danish_Red`, `Girolando`, `Guernsey`, `Holstein-Friesian`, `Holstein_Zebu_Cross`, `Illawarra_Shorthorn`, `Jersey`, `Jersey_Zebu_Cross`, `Milking_Shorthorn`, `Montbeliarde`, `Norwegian_Red`, `Tipo_Carora`
- Beef/non-specialized indicators: `Africander`, `Ankole`, `Boran`, `NDama`, `Ongole`, `White_Fulani`
- Unclassified or dual-purpose names: `Butana`, `Deoni`, `Exotic_Local_Cross`, `Fleckvieh`, `Gangatiri`, `Gir`, `Hariana`, `Kankrej`, `Kenana`, `Krishna_Valley`, `Normande`, `Rathi`, `Red_Poll_Africa`, `Red_Sindhi`, `Sahiwal`, `Simmental`, `Tharparkar`, `Zebu_Cross_Brazil`
- Other species: not observed, but No species column exists. All observed Breed labels look cattle-related, but absence of a species field prevents an authoritative species check.
- Dairy-only filtering: Breed can support a documented allow-list, but the file has no authoritative species or dairy-production-purpose field. A reliable dairy-only filter requires source documentation for every breed category.
- Lactation: Early, Mid, and Late stages are distinguishable and all rows have a stage, but no Dry or Non_Lactating category proves whether non-lactating cattle were excluded.

## Identifier and Repeated-Observation Analysis

### Milk-yield dataset

| Cattle rows | Unique Cattle_ID | Repeated IDs | Maximum observations/animal | Date range | Group split required |
| --- | --- | --- | --- | --- | --- |
| 250000 | 250000 | 0 | 1 | 2022-01-01T00:00:00 to 2024-12-30T00:00:00 | False |

Cattle_ID is unique in this file, so no animal currently spans multiple rows. Grouping becomes required if future data introduces repeated animals.

`Farm_ID` repeats, but it identifies farms rather than repeated animal observations. If farm-level generalisation is required later, a grouped farm split should be considered separately.

### Disease dataset

| Cattle rows | Unique Cattle_ID | Repeated IDs | Maximum observations/animal | Date range | Group split required |
| --- | --- | --- | --- | --- | --- |
| 250000 | 250000 | 0 | 1 | 2022-01-01T00:00:00 to 2024-12-30T00:00:00 | False |

Cattle_ID is unique in this file, so no animal currently spans multiple rows. Grouping becomes required if future data introduces repeated animals.

`Farm_ID` repeats, but it identifies farms rather than repeated animal observations. If farm-level generalisation is required later, a grouped farm split should be considered separately.

## Main Milk-Yield Dataset

### Column Profile

| Column | Pandas type | Inferred type | Missing | Missing % | Unique | Sample values |
| --- | --- | --- | --- | --- | --- | --- |
| Cattle_ID | str | identifier | 0 | 0.0 | 250000 | CATTLE_000001, CATTLE_000002, CATTLE_000003, CATTLE_000004, CATTLE_000005 |
| Breed | str | categorical | 0 | 0.0 | 40 | Tharparkar, Africander, Holstein-Friesian, Fleckvieh, Danish_Red |
| Region | str | categorical | 0 | 0.0 | 6 | Africa, South_America, Oceania, Europe_NA, South_Asia |
| Country | str | categorical | 0 | 0.0 | 15 | CA, ET, KE, BR, US |
| Climate_Zone | str | categorical | 0 | 0.0 | 6 | Tropical, Arid, Temperate, Subtropical, Continental |
| Management_System | str | categorical | 0 | 0.0 | 5 | Intensive, Semi_Intensive, Extensive, Mixed, Pastoral |
| Age_Months | int64 | integer | 0 | 0.0 | 120 | 32, 63, 132, 73, 50 |
| Weight_kg | float64 | continuous_numeric | 0 | 0.0 | 5001 | 259.9, 593.9, 675.4, 260.5, 477.8 |
| Parity | int64 | integer | 0 | 0.0 | 6 | 4, 6, 3, 5, 2 |
| Lactation_Stage | str | categorical | 0 | 0.0 | 3 | Late, Early, Mid |
| Days_in_Milk | int64 | integer | 0 | 0.0 | 364 | 352, 325, 79, 249, 339 |
| Feed_Type | str | categorical | 0 | 0.0 | 8 | Hay, Dry_Fodder, Crop_Residues, Concentrates, Pasture_Grass |
| Feed_Quantity_kg | float64 | continuous_numeric | 0 | 0.0 | 221 | 16.8, 8.9, 3.0, 10.6, 14.3 |
| Feeding_Frequency | int64 | integer | 0 | 0.0 | 5 | 3, 1, 2, 5, 4 |
| Water_Intake_L | float64 | continuous_numeric | 0 | 0.0 | 1001 | 58.5, 57.8, 75.3, 90.3, 57.3 |
| Walking_Distance_km | float64 | continuous_numeric | 0 | 0.0 | 1079 | 7.89, 4.01, 2.08, 3.6, 4.09 |
| Grazing_Duration_hrs | float64 | continuous_numeric | 0 | 0.0 | 131 | 1.6, 5.5, 3.8, 6.8, 1.0 |
| Rumination_Time_hrs | float64 | continuous_numeric | 0 | 0.0 | 101 | 4.3, 11.3, 9.8, 7.1, 5.2 |
| Resting_Hours | float64 | continuous_numeric | 0 | 0.0 | 131 | 8.4, 11.1, 12.0, 8.9, 5.9 |
| Ambient_Temperature_C | float64 | continuous_numeric | 0 | 0.0 | 551 | 24.9, 34.0, 45.0, 33.1, 25.3 |
| Humidity_percent | float64 | continuous_numeric | 0 | 0.0 | 901 | 66.9, 46.2, 78.3, 34.9, 100.0 |
| Season | str | categorical | 0 | 0.0 | 5 | Summer, Autumn, Spring, Monsoon, Winter |
| Housing_Score | float64 | continuous_numeric | 0 | 0.0 | 71 | 0.57, 0.77, 0.54, 0.69, 0.83 |
| FMD_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| Brucellosis_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| HS_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| BQ_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| Anthrax_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| IBR_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| BVD_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| Rabies_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| Previous_Week_Avg_Yield | float64 | continuous_numeric | 0 | 0.0 | 3163 | 4.88, 3.52, 11.28, 10.63, 16.99 |
| Body_Condition_Score | float64 | continuous_numeric | 0 | 0.0 | 7 | 3.0, 2.5, 4.0, 2.0, 3.5 |
| Milking_Interval_hrs | int64 | integer | 0 | 0.0 | 4 | 24, 12, 8, 6 |
| Date | str | datetime | 0 | 0.0 | 1095 | 2023-02-06, 2022-10-31, 2024-11-01, 2023-07-07, 2024-09-20 |
| Farm_ID | str | identifier | 0 | 0.0 | 1000 | FARM_0825, FARM_0106, FARM_0201, FARM_0174, FARM_0028 |
| Milk_Yield_L | float64 | continuous_numeric | 0 | 0.0 | 3122 | 3.08, 2.0, 14.06, 12.74, 15.64 |

### Candidate Features

| Candidate | Present | Source | Type | Missing % | Unique | Form | Prediction-time assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Breed | True | Breed | str | 0.0 | 40 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Age_Months | True | Age_Months | int64 | 0.0 | 120 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Weight_kg | True | Weight_kg | float64 | 0.0 | 5001 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Health_Status | False |  |  |  |  | PROVIDED_BUT_DATASET_EQUIVALENCE_UNCLEAR | AVAILABILITY_MISMATCH |
| Parity | True | Parity | int64 | 0.0 | 6 | NOT_PROVIDED | AVAILABILITY_MISMATCH |
| Lactation_Stage | True | Lactation_Stage | str | 0.0 | 3 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Days_in_Milk | True | Days_in_Milk | int64 | 0.0 | 364 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Previous_Week_Avg_Yield | True | Previous_Week_Avg_Yield | float64 | 0.0 | 3163 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Body_Condition_Score | True | Body_Condition_Score | float64 | 0.0 | 7 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Ambient_Temperature_C | True | Ambient_Temperature_C | float64 | 0.0 | 551 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Humidity_percent | True | Humidity_percent | float64 | 0.0 | 901 | PROVIDED | SAFE_WITH_INPUT_VALIDATION |
| Season | True | Season | str | 0.0 | 5 | NOT_PROVIDED | AVAILABILITY_MISMATCH |
| Climate_Zone | True | Climate_Zone | str | 0.0 | 6 | NOT_PROVIDED | AVAILABILITY_MISMATCH |
| Management_System | True | Management_System | str | 0.0 | 5 | NOT_PROVIDED | AVAILABILITY_MISMATCH |

The disease outcome `Disease_Status` was deliberately not treated as an alias for the form's current `Health_Status`; their meanings and timing differ.

### Feed-Type Analysis

Target status: **TARGET_UNCLEAR**.

Exact unique values: `Concentrates`, `Crop_Residues`, `Dry_Fodder`, `Green_Fodder`, `Hay`, `Mixed_Feed`, `Pasture_Grass`, `Silage`

| Feed type | Count | Percentage |
| --- | --- | --- |
| Dry_Fodder | 31569 | 12.6276% |
| Pasture_Grass | 31290 | 12.5160% |
| Concentrates | 31282 | 12.5128% |
| Crop_Residues | 31273 | 12.5092% |
| Green_Fodder | 31222 | 12.4888% |
| Mixed_Feed | 31151 | 12.4604% |
| Hay | 31134 | 12.4536% |
| Silage | 31079 | 12.4316% |

Missing: 0. Rare classes: none. Spelling duplicates: none.

Feed_Type exists and contains eight broad categories, but repository-local documentation does not define whether it is observed, recommended, or generated.

Categorical relationships (Cramer's V; 0 means no observed association and 1 means perfect association):

| Related field | Available | Cramer's V |
| --- | --- | --- |
| Breed | True | 0.012253 |
| Lactation_Stage | True | 0.004991 |
| Management_System | True | 0.006244 |
| Season | True | 0.006080 |
| Region | True | 0.005031 |

The full relationship count tables are retained in `dataset_audit.json`.

### Feed-Quantity Analysis

Target status: **TARGET_UNCLEAR**.

| Statistic | Value |
| --- | --- |
| Minimum | 3.0000 |
| Maximum | 25.0000 |
| Mean | 12.0152 |
| Median | 12.0000 |
| Standard deviation | 3.9600 |
| P01 | 3.0000 |
| P05 | 5.4000 |
| P25 | 9.3000 |
| P50 | 12.0000 |
| P75 | 14.7000 |
| P95 | 18.6000 |
| P99 | 21.3000 |
| Missing | 0 |
| Zero | 0 |
| Negative | 0 |
| Unique values | 221 |

Decimal precision counts: `{'0': 27776, '1': 222224}`.

The statistical IQR fence found 0 low and 853 high outliers. This is not a nutrition-validity rule.

Distribution by Feed_Type:

| Group | Count | Min | Max | Mean | Median | Std |
| --- | --- | --- | --- | --- | --- | --- |
| Concentrates | 31282 | 3.0000 | 25.0000 | 12.0600 | 12.1000 | 3.9432 |
| Crop_Residues | 31273 | 3.0000 | 25.0000 | 11.9915 | 12.0000 | 3.9534 |
| Dry_Fodder | 31569 | 3.0000 | 25.0000 | 12.0076 | 12.0000 | 3.9721 |
| Green_Fodder | 31222 | 3.0000 | 25.0000 | 12.0320 | 12.0000 | 3.9766 |
| Hay | 31134 | 3.0000 | 25.0000 | 12.0154 | 12.0000 | 3.9706 |
| Mixed_Feed | 31151 | 3.0000 | 25.0000 | 12.0011 | 12.0000 | 3.9463 |
| Pasture_Grass | 31290 | 3.0000 | 25.0000 | 12.0129 | 12.0000 | 3.9481 |
| Silage | 31079 | 3.0000 | 25.0000 | 12.0009 | 12.0000 | 3.9695 |

Distribution by Lactation_Stage:

| Group | Count | Min | Max | Mean | Median | Std |
| --- | --- | --- | --- | --- | --- | --- |
| Early | 75059 | 3.0000 | 25.0000 | 12.0177 | 12.0000 | 3.9442 |
| Late | 74933 | 3.0000 | 25.0000 | 12.0239 | 12.0000 | 3.9672 |
| Mid | 100008 | 3.0000 | 25.0000 | 12.0068 | 12.0000 | 3.9664 |

Distribution by Weight_kg range:

| Group | Count | Min | Max | Mean | Median | Std |
| --- | --- | --- | --- | --- | --- | --- |
| 200-299 | 24937 | 3.0000 | 25.0000 | 12.0430 | 12.0000 | 3.9570 |
| 300-399 | 50048 | 3.0000 | 25.0000 | 12.0324 | 12.0000 | 3.9636 |
| 400-499 | 49795 | 3.0000 | 25.0000 | 12.0055 | 12.0000 | 3.9636 |
| 500-599 | 50080 | 3.0000 | 25.0000 | 12.0204 | 12.0000 | 3.9349 |
| 600-699 | 49999 | 3.0000 | 25.0000 | 11.9771 | 12.0000 | 3.9817 |
| 700-799 | 25141 | 3.0000 | 25.0000 | 12.0376 | 12.0000 | 3.9552 |

Distribution by Breed:

| Breed | Count | Min | Max | Mean | Median | Std |
| --- | --- | --- | --- | --- | --- | --- |
| Africander | 6310 | 3.0000 | 25.0000 | 12.0986 | 12.1000 | 3.9054 |
| Ankole | 6330 | 3.0000 | 25.0000 | 11.9618 | 12.0000 | 3.9219 |
| Australian_Friesian_Sahiwal | 6230 | 3.0000 | 25.0000 | 11.9907 | 12.0000 | 3.9672 |
| Australian_Milking_Zebu | 6297 | 3.0000 | 25.0000 | 12.0109 | 12.0000 | 3.9443 |
| Ayrshire | 6206 | 3.0000 | 25.0000 | 12.0963 | 12.0000 | 3.9835 |
| Boran | 6245 | 3.0000 | 25.0000 | 12.0352 | 12.0000 | 4.0130 |
| Brown_Swiss | 6244 | 3.0000 | 25.0000 | 12.0043 | 12.0000 | 3.9228 |
| Butana | 6242 | 3.0000 | 25.0000 | 12.0589 | 12.0000 | 4.0520 |
| Danish_Red | 6422 | 3.0000 | 25.0000 | 12.0455 | 12.1000 | 3.9690 |
| Deoni | 6026 | 3.0000 | 25.0000 | 11.9499 | 11.9000 | 3.9774 |
| Exotic_Local_Cross | 6250 | 3.0000 | 25.0000 | 12.0040 | 12.0000 | 3.9848 |
| Fleckvieh | 6410 | 3.0000 | 25.0000 | 11.9468 | 11.9000 | 4.0028 |
| Gangatiri | 6340 | 3.0000 | 25.0000 | 12.0643 | 12.0000 | 3.9255 |
| Gir | 6251 | 3.0000 | 25.0000 | 11.9724 | 11.9000 | 3.9472 |
| Girolando | 6387 | 3.0000 | 25.0000 | 11.9921 | 11.9000 | 3.9396 |
| Guernsey | 6246 | 3.0000 | 25.0000 | 12.0191 | 12.0000 | 3.9324 |
| Hariana | 6201 | 3.0000 | 25.0000 | 12.0080 | 12.0000 | 4.0225 |
| Holstein-Friesian | 6227 | 3.0000 | 25.0000 | 11.8524 | 11.8000 | 3.9797 |
| Holstein_Zebu_Cross | 6253 | 3.0000 | 25.0000 | 12.0201 | 12.0000 | 3.9401 |
| Illawarra_Shorthorn | 6142 | 3.0000 | 25.0000 | 11.9765 | 12.0000 | 3.9474 |
| Jersey | 6149 | 3.0000 | 25.0000 | 11.9255 | 11.9000 | 3.9082 |
| Jersey_Zebu_Cross | 6240 | 3.0000 | 25.0000 | 12.1205 | 12.1000 | 3.8864 |
| Kankrej | 6173 | 3.0000 | 25.0000 | 11.9113 | 11.9000 | 4.0329 |
| Kenana | 6341 | 3.0000 | 25.0000 | 11.9968 | 12.0000 | 3.9150 |
| Krishna_Valley | 6291 | 3.0000 | 25.0000 | 12.0200 | 12.0000 | 3.9171 |
| Milking_Shorthorn | 6119 | 3.0000 | 25.0000 | 12.0951 | 12.1000 | 3.9313 |
| Montbeliarde | 6282 | 3.0000 | 25.0000 | 12.0808 | 12.1000 | 3.9271 |
| NDama | 6189 | 3.0000 | 25.0000 | 11.9324 | 11.9000 | 3.9441 |
| Normande | 6130 | 3.0000 | 25.0000 | 11.9237 | 11.9000 | 3.9665 |
| Norwegian_Red | 6214 | 3.0000 | 25.0000 | 12.0124 | 12.0000 | 3.9255 |
| Ongole | 6286 | 3.0000 | 25.0000 | 12.0877 | 12.1000 | 3.9665 |
| Rathi | 6164 | 3.0000 | 25.0000 | 12.1230 | 12.1000 | 3.9094 |
| Red_Poll_Africa | 6439 | 3.0000 | 25.0000 | 12.0317 | 12.1000 | 3.9752 |
| Red_Sindhi | 6146 | 3.0000 | 25.0000 | 12.0678 | 12.1000 | 3.9721 |
| Sahiwal | 6283 | 3.0000 | 25.0000 | 12.0409 | 12.1000 | 3.9932 |
| Simmental | 6196 | 3.0000 | 25.0000 | 12.0398 | 12.1000 | 3.9705 |
| Tharparkar | 6361 | 3.0000 | 25.0000 | 12.1694 | 12.2000 | 3.9833 |
| Tipo_Carora | 6311 | 3.0000 | 25.0000 | 11.9001 | 11.9000 | 4.0489 |
| White_Fulani | 6112 | 3.0000 | 25.0000 | 12.0454 | 12.1000 | 3.9607 |
| Zebu_Cross_Brazil | 6315 | 3.0000 | 25.0000 | 11.9698 | 11.9000 | 3.9692 |

Pearson correlations:

| Variable | Correlation with Feed_Quantity_kg |
| --- | --- |
| Weight_kg | -0.002220 |
| Milk_Yield_L | 0.041593 |
| Previous_Week_Avg_Yield | 0.040688 |

The kg values can be described statistically, but neither the material basis nor time period is documented. Plausible ranges cannot establish meaning.

### Milk-Yield Analysis

| Statistic | Value |
| --- | --- |
| Minimum | 0.0000 |
| Maximum | 36.4200 |
| Mean | 8.7226 |
| Median | 7.6200 |
| Standard deviation | 5.7634 |
| P01 | 0.0000 |
| P05 | 1.0000 |
| P25 | 4.3400 |
| P50 | 7.6200 |
| P75 | 12.2900 |
| P95 | 19.7200 |
| P99 | 24.6300 |
| Missing | 0 |
| Zero | 5940 |
| Negative | 0 |

Distribution by Lactation_Stage:

| Group | Count | Min | Max | Mean | Median | Std |
| --- | --- | --- | --- | --- | --- | --- |
| Early | 75059 | 0.0000 | 36.4200 | 9.8925 | 8.6500 | 6.3123 |
| Late | 74933 | 0.0000 | 28.4100 | 7.2058 | 6.3800 | 4.7660 |
| Mid | 100008 | 0.0000 | 34.2200 | 8.9811 | 7.9200 | 5.7701 |

Distribution by Breed:

| Breed | Count | Min | Max | Mean | Median | Std |
| --- | --- | --- | --- | --- | --- | --- |
| Africander | 6310 | 0.0000 | 12.7800 | 3.2530 | 3.1400 | 2.1210 |
| Ankole | 6330 | 0.0000 | 10.1300 | 3.2202 | 3.1500 | 2.1109 |
| Australian_Friesian_Sahiwal | 6230 | 0.0000 | 26.2800 | 11.3350 | 11.3400 | 4.5138 |
| Australian_Milking_Zebu | 6297 | 0.0000 | 18.7600 | 7.5302 | 7.5200 | 3.2935 |
| Ayrshire | 6206 | 0.0000 | 30.2300 | 13.7279 | 13.6900 | 5.2762 |
| Boran | 6245 | 0.0000 | 12.5400 | 3.7976 | 3.7300 | 2.2839 |
| Brown_Swiss | 6244 | 0.0000 | 32.9000 | 15.5778 | 15.6100 | 5.9358 |
| Butana | 6242 | 0.0000 | 14.3500 | 4.9862 | 4.9850 | 2.5897 |
| Danish_Red | 6422 | 0.0000 | 31.1500 | 13.7630 | 13.7200 | 5.3073 |
| Deoni | 6026 | 0.0000 | 12.3200 | 3.8277 | 3.7900 | 2.2716 |
| Exotic_Local_Cross | 6250 | 0.0000 | 26.1800 | 11.2570 | 11.3100 | 4.4885 |
| Fleckvieh | 6410 | 0.0000 | 32.1400 | 15.0551 | 15.1000 | 5.6770 |
| Gangatiri | 6340 | 0.0000 | 11.2900 | 3.2524 | 3.1700 | 2.1146 |
| Gir | 6251 | 0.0000 | 17.4800 | 6.2583 | 6.3000 | 2.9609 |
| Girolando | 6387 | 0.0000 | 24.6000 | 9.9342 | 9.9700 | 4.1061 |
| Guernsey | 6246 | 0.0000 | 25.4400 | 11.2057 | 11.2500 | 4.3870 |
| Hariana | 6201 | 0.0000 | 13.2100 | 4.4590 | 4.4400 | 2.4372 |
| Holstein-Friesian | 6227 | 0.0000 | 36.4200 | 17.5137 | 17.5300 | 6.5023 |
| Holstein_Zebu_Cross | 6253 | 0.0000 | 28.1900 | 12.5210 | 12.5400 | 4.9351 |
| Illawarra_Shorthorn | 6142 | 0.0000 | 23.2800 | 9.3599 | 9.3200 | 3.8571 |
| Jersey | 6149 | 0.0000 | 27.9800 | 12.5091 | 12.5900 | 4.8867 |
| Jersey_Zebu_Cross | 6240 | 0.0000 | 24.4600 | 10.0263 | 10.0500 | 4.0551 |
| Kankrej | 6173 | 0.0000 | 14.2200 | 5.0602 | 5.0600 | 2.5974 |
| Kenana | 6341 | 0.0000 | 18.3600 | 5.6555 | 5.6400 | 2.7687 |
| Krishna_Valley | 6291 | 0.0000 | 13.1300 | 4.4358 | 4.3800 | 2.4532 |
| Milking_Shorthorn | 6119 | 0.0000 | 28.3600 | 13.0993 | 13.0400 | 5.0488 |
| Montbeliarde | 6282 | 0.0000 | 29.2000 | 13.2689 | 13.2500 | 5.0689 |
| NDama | 6189 | 0.0000 | 11.5200 | 2.6376 | 2.5200 | 1.9393 |
| Normande | 6130 | 0.0000 | 25.5200 | 11.9360 | 11.9150 | 4.5914 |
| Norwegian_Red | 6214 | 0.0000 | 29.2900 | 14.4587 | 14.4700 | 5.5133 |
| Ongole | 6286 | 0.0000 | 15.6700 | 5.0937 | 5.0800 | 2.6045 |
| Rathi | 6164 | 0.0000 | 16.0400 | 5.6875 | 5.6400 | 2.7466 |
| Red_Poll_Africa | 6439 | 0.0000 | 13.7000 | 5.0113 | 4.9900 | 2.6034 |
| Red_Sindhi | 6146 | 0.0000 | 17.2200 | 6.8953 | 6.9100 | 3.1591 |
| Sahiwal | 6283 | 0.0000 | 19.0500 | 7.5056 | 7.5400 | 3.3056 |
| Simmental | 6196 | 0.0000 | 32.4900 | 15.0213 | 14.9700 | 5.7222 |
| Tharparkar | 6361 | 0.0000 | 19.3800 | 8.1658 | 8.1900 | 3.4790 |
| Tipo_Carora | 6311 | 0.0000 | 18.7200 | 7.4937 | 7.5400 | 3.2896 |
| White_Fulani | 6112 | 0.0000 | 13.3300 | 4.3586 | 4.3750 | 2.4408 |
| Zebu_Cross_Brazil | 6315 | 0.0000 | 20.0600 | 8.7498 | 8.8200 | 3.6430 |

Previous-week yield correlation: 0.968447.

Period: **UNCLEAR**. The column name establishes litres but repository-local documentation does not state whether each value is daily, weekly, per milking, or another period.

### Data-Quality Issues

| Status | Severity | Issue | Column | Affected | Percentage | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | WARNING | Duplicate complete rows | ALL_COLUMNS | 0 | 0.0 | Exact duplicate across all parsed columns. |
| PASS | WARNING | Empty physical CSV rows | ALL_COLUMNS | 0 | 0.0 | Blank physical lines after the header; pandas normally skips these. |
| PASS | WARNING | Negative age | Age_Months | 0 | 0.0 | Age below 0 months. |
| PASS | WARNING | Zero age | Age_Months | 0 | 0.0 | Age exactly 0 months. |
| PASS | WARNING | Implausible age | Age_Months | 0 | 0.0 | Audit threshold: age under 12 months or over 300 months. |
| PASS | WARNING | Negative weight | Weight_kg | 0 | 0.0 | Weight below 0 kg. |
| PASS | WARNING | Zero weight | Weight_kg | 0 | 0.0 | Weight exactly 0 kg. |
| PASS | WARNING | Implausible weight | Weight_kg | 0 | 0.0 | Audit threshold: weight under 50 kg or over 1,200 kg. |
| PASS | WARNING | Negative milk yield | Milk_Yield_L | 0 | 0.0 | Milk_Yield_L below 0. |
| FLAGGED | WARNING | Zero milk yield | Milk_Yield_L | 5940 | 2.376 | Milk_Yield_L exactly 0. |
| PASS | WARNING | Suspiciously high milk yield | Milk_Yield_L | 0 | 0.0 | Conservative audit threshold: Milk_Yield_L over 100; its period is UNCLEAR. |
| PASS | WARNING | Negative feed quantity | Feed_Quantity_kg | 0 | 0.0 | Feed_Quantity_kg below 0. |
| PASS | WARNING | Zero feed quantity | Feed_Quantity_kg | 0 | 0.0 | Feed_Quantity_kg exactly 0. |
| PASS | WARNING | Suspiciously high feed quantity | Feed_Quantity_kg | 0 | 0.0 | Conservative audit threshold: Feed_Quantity_kg over 100; basis/period are UNCLEAR. |
| PASS | WARNING | Negative days in milk | Days_in_Milk | 0 | 0.0 | Days_in_Milk below 0. |
| PASS | WARNING | Suspiciously high days in milk | Days_in_Milk | 0 | 0.0 | Audit threshold: Days_in_Milk over 730. |
| PASS | WARNING | Humidity outside 0-100 | Humidity_percent | 0 | 0.0 | Humidity_percent outside the physical percentage range. |
| PASS | WARNING | Implausible ambient temperature | Ambient_Temperature_C | 0 | 0.0 | Audit threshold: ambient temperature below -20 C or above 55 C. |
| PASS | WARNING | Body-condition score outside detected 1-5 scale | Body_Condition_Score | 0 | 0.0 | Observed values are assessed against the common 1-5 scale; source scale is undocumented. |
| PASS | WARNING | Invalid parity | Parity | 0 | 0.0 | Audit threshold: negative, non-integer, or above 20. |
| PASS | ERROR | Impossible age/lactation combination | Days_in_Milk + Age_Months | 0 | 0.0 | Days_in_Milk exceeds approximate lifetime in days (Age_Months x 31). |
| PASS | ERROR | Impossible young-age/parity combination | Parity + Age_Months | 0 | 0.0 | Positive parity with age below 18 months. |
| PASS | WARNING | Inconsistent categorical spelling | Cattle_ID | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Breed | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Region | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Country | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Climate_Zone | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Management_System | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Lactation_Stage | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Feed_Type | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Season | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Date | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Farm_ID | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| FLAGGED | WARNING | Extremely high-cardinality categorical column | Cattle_ID | 250000 | 100.0 | 250,000 unique values across 250,000 rows. |
| UNCLEAR | WARNING | Mixed or undocumented feed units | Feed_Quantity_kg |  |  | The name states kg but supplies no material basis or time period; mixed units cannot be ruled out. |
| UNCLEAR | WARNING | Mixed or undocumented milk-yield period | Milk_Yield_L |  |  | The name states litres but supplies no daily/weekly/other period metadata. |

### Leakage Risks

#### Feed-type classifier

| Input | Classification | Reason |
| --- | --- | --- |
| Cattle_ID | POSSIBLE_LEAKAGE | Identifier may permit record, farm, or generated-batch memorisation. |
| Breed | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Region | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Country | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Climate_Zone | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Management_System | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Age_Months | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Weight_kg | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Parity | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Lactation_Stage | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Days_in_Milk | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Feed_Type | DEFINITE_LEAKAGE | This is the model target. |
| Feed_Quantity_kg | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Feeding_Frequency | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Water_Intake_L | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Walking_Distance_km | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Grazing_Duration_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Rumination_Time_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Resting_Hours | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Ambient_Temperature_C | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Humidity_percent | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Season | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Housing_Score | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| FMD_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Brucellosis_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| HS_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| BQ_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Anthrax_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| IBR_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| BVD_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Rabies_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Previous_Week_Avg_Yield | SAFE | A lagged value is available in the form, provided its time window is verified. |
| Body_Condition_Score | SAFE | No direct leakage signal identified for feed_type_classifier; validation and timing still apply. |
| Milking_Interval_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Date | POSSIBLE_LEAKAGE | Collection date may encode temporal or generated data batches. |
| Farm_ID | POSSIBLE_LEAKAGE | Identifier may permit record, farm, or generated-batch memorisation. |
| Milk_Yield_L | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |

#### Feed-quantity regressor

| Input | Classification | Reason |
| --- | --- | --- |
| Cattle_ID | POSSIBLE_LEAKAGE | Identifier may permit record, farm, or generated-batch memorisation. |
| Breed | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Region | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Country | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Climate_Zone | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Management_System | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Age_Months | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Weight_kg | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Parity | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Lactation_Stage | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Days_in_Milk | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Feed_Type | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Feed_Quantity_kg | DEFINITE_LEAKAGE | This is the model target. |
| Feeding_Frequency | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Water_Intake_L | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Walking_Distance_km | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Grazing_Duration_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Rumination_Time_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Resting_Hours | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Ambient_Temperature_C | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Humidity_percent | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Season | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Housing_Score | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| FMD_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Brucellosis_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| HS_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| BQ_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Anthrax_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| IBR_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| BVD_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Rabies_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Previous_Week_Avg_Yield | SAFE | A lagged value is available in the form, provided its time window is verified. |
| Body_Condition_Score | SAFE | No direct leakage signal identified for feed_quantity_regressor; validation and timing still apply. |
| Milking_Interval_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Date | POSSIBLE_LEAKAGE | Collection date may encode temporal or generated data batches. |
| Farm_ID | POSSIBLE_LEAKAGE | Identifier may permit record, farm, or generated-batch memorisation. |
| Milk_Yield_L | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |

#### Milk-yield regressor

| Input | Classification | Reason |
| --- | --- | --- |
| Cattle_ID | POSSIBLE_LEAKAGE | Identifier may permit record, farm, or generated-batch memorisation. |
| Breed | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Region | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Country | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Climate_Zone | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Management_System | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Age_Months | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Weight_kg | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Parity | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Lactation_Stage | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Days_in_Milk | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Feed_Type | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Feed_Quantity_kg | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Feeding_Frequency | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Water_Intake_L | POSSIBLE_LEAKAGE | May be a same-record decision, exposure, or post-outcome field; timing is undocumented. |
| Walking_Distance_km | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Grazing_Duration_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Rumination_Time_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Resting_Hours | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Ambient_Temperature_C | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Humidity_percent | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Season | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Housing_Score | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| FMD_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Brucellosis_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| HS_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| BQ_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Anthrax_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| IBR_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| BVD_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Rabies_Vaccine | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Previous_Week_Avg_Yield | SAFE | A lagged value is available in the form, provided its time window is verified. |
| Body_Condition_Score | SAFE | No direct leakage signal identified for milk_yield_regressor; validation and timing still apply. |
| Milking_Interval_hrs | AVAILABILITY_MISMATCH | The current FarmLite request does not provide this exact field. |
| Date | POSSIBLE_LEAKAGE | Collection date may encode temporal or generated data batches. |
| Farm_ID | POSSIBLE_LEAKAGE | Identifier may permit record, farm, or generated-batch memorisation. |
| Milk_Yield_L | DEFINITE_LEAKAGE | This is the model target. |

### Synthetic-Data Indicators

Status: **POSSIBLY_SYNTHETIC**.

Perfectly sequential IDs, complete data, balanced categories, and the cross-file duplication pattern are generated-data indicators. No repository metadata explicitly confirms synthetic generation, so the cautious status is POSSIBLY_SYNTHETIC rather than a definitive claim.

| Indicator | Evidence |
| --- | --- |
| Sequential generated-looking identifiers | {"numeric_suffix_parseable_percentage": 100.0, "row_order_matches_1_to_n_percentage": 100.0, "first_values": ["CATTLE_000001", "CATTLE_000002", "CATTLE_000003", "CATTLE_000004", "CATTLE_000005"], "last_values": ["CATTLE_249996", "CATTLE_249997", "CATTLE_249998", "CATTLE_249999", "CATTLE_250000"]} |
| Missing-data cleanliness | {"total_missing_cells": 0, "total_cells": 9250000, "missing_percentage": 0.0} |
| Breed category balance | {"categories": 40, "minimum_class_count": 6026, "maximum_class_count": 6439, "relative_max_min_spread": 0.06608} |
| Feed_Type category balance | {"categories": 8, "minimum_class_count": 31079, "maximum_class_count": 31569, "relative_max_min_spread": 0.01568} |
| Region category balance | {"categories": 6, "minimum_class_count": 41466, "maximum_class_count": 41837, "relative_max_min_spread": 0.008904} |
| Management_System category balance | {"categories": 5, "minimum_class_count": 49848, "maximum_class_count": 50322, "relative_max_min_spread": 0.00948} |
| Season category balance | {"categories": 5, "minimum_class_count": 49691, "maximum_class_count": 50293, "relative_max_min_spread": 0.01204} |
| Lactation_Stage category balance | {"categories": 3, "minimum_class_count": 74933, "maximum_class_count": 100008, "relative_max_min_spread": 0.3009} |
| Near-perfect numeric correlations | [] |

## Disease Dataset

### Column Profile

| Column | Pandas type | Inferred type | Missing | Missing % | Unique | Sample values |
| --- | --- | --- | --- | --- | --- | --- |
| Cattle_ID | str | identifier | 0 | 0.0 | 250000 | CATTLE_000001, CATTLE_000002, CATTLE_000003, CATTLE_000004, CATTLE_000005 |
| Breed | str | categorical | 0 | 0.0 | 40 | Tharparkar, Africander, Holstein-Friesian, Fleckvieh, Danish_Red |
| Region | str | categorical | 0 | 0.0 | 6 | Africa, South_America, Oceania, Europe_NA, South_Asia |
| Country | str | categorical | 0 | 0.0 | 15 | CA, ET, KE, BR, US |
| Climate_Zone | str | categorical | 0 | 0.0 | 6 | Tropical, Arid, Temperate, Subtropical, Continental |
| Management_System | str | categorical | 0 | 0.0 | 5 | Intensive, Semi_Intensive, Extensive, Mixed, Pastoral |
| Age_Months | int64 | integer | 0 | 0.0 | 120 | 32, 63, 132, 73, 50 |
| Weight_kg | float64 | continuous_numeric | 0 | 0.0 | 5001 | 259.9, 593.9, 675.4, 260.5, 477.8 |
| Parity | int64 | integer | 0 | 0.0 | 6 | 4, 6, 3, 5, 2 |
| Lactation_Stage | str | categorical | 0 | 0.0 | 3 | Late, Early, Mid |
| Days_in_Milk | int64 | integer | 0 | 0.0 | 364 | 352, 325, 79, 249, 339 |
| Feed_Type | str | categorical | 0 | 0.0 | 8 | Hay, Dry_Fodder, Crop_Residues, Concentrates, Pasture_Grass |
| Feed_Quantity_kg | float64 | continuous_numeric | 0 | 0.0 | 221 | 16.8, 8.9, 3.0, 10.6, 14.3 |
| Water_Intake_L | float64 | continuous_numeric | 0 | 0.0 | 1001 | 58.5, 57.8, 75.3, 90.3, 57.3 |
| Walking_Distance_km | float64 | continuous_numeric | 0 | 0.0 | 1079 | 7.89, 4.01, 2.08, 3.6, 4.09 |
| Grazing_Duration_hrs | float64 | continuous_numeric | 0 | 0.0 | 131 | 1.6, 5.5, 3.8, 6.8, 1.0 |
| Rumination_Time_hrs | float64 | continuous_numeric | 0 | 0.0 | 101 | 4.3, 11.3, 9.8, 7.1, 5.2 |
| Resting_Hours | float64 | continuous_numeric | 0 | 0.0 | 131 | 8.4, 11.1, 12.0, 8.9, 5.9 |
| Body_Temperature_C | float64 | continuous_numeric | 0 | 0.0 | 61 | 39.8, 39.1, 40.2, 37.7, 38.3 |
| Heart_Rate_bpm | float64 | continuous_numeric | 0 | 0.0 | 88 | 61.0, 82.0, 60.0, 91.0, 73.0 |
| Respiratory_Rate | float64 | continuous_numeric | 0 | 0.0 | 44 | 30.0, 27.0, 25.0, 16.0, 24.0 |
| Ambient_Temperature_C | float64 | continuous_numeric | 0 | 0.0 | 551 | 24.9, 34.0, 45.0, 33.1, 25.3 |
| Humidity_percent | float64 | continuous_numeric | 0 | 0.0 | 901 | 66.9, 46.2, 78.3, 34.9, 100.0 |
| Season | str | categorical | 0 | 0.0 | 5 | Summer, Autumn, Spring, Monsoon, Winter |
| Housing_Score | float64 | continuous_numeric | 0 | 0.0 | 71 | 0.57, 0.77, 0.54, 0.69, 0.83 |
| Milk_Yield_L | float64 | continuous_numeric | 0 | 0.0 | 3122 | 3.08, 2.0, 14.06, 12.74, 15.64 |
| FMD_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| Brucellosis_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| HS_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| BQ_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| Anthrax_Vaccine | int64 | integer | 0 | 0.0 | 2 | 1, 0 |
| IBR_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| BVD_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| Rabies_Vaccine | int64 | integer | 0 | 0.0 | 2 | 0, 1 |
| Previous_Week_Avg_Yield | float64 | continuous_numeric | 0 | 0.0 | 3163 | 4.88, 3.52, 11.28, 10.63, 16.99 |
| Body_Condition_Score | float64 | continuous_numeric | 0 | 0.0 | 7 | 3.0, 2.5, 4.0, 2.0, 3.5 |
| Milking_Interval_hrs | int64 | integer | 0 | 0.0 | 4 | 24, 12, 8, 6 |
| Date | str | datetime | 0 | 0.0 | 1095 | 2023-02-06, 2022-10-31, 2024-11-01, 2023-07-07, 2024-09-20 |
| Farm_ID | str | identifier | 0 | 0.0 | 1000 | FARM_0825, FARM_0106, FARM_0201, FARM_0174, FARM_0028 |
| Disease_Status | str | categorical | 0 | 0.0 | 45 | Foot_and_Mouth, Ketosis_Subclinical, Healthy, Bovine_Tuberculosis, Mastitis_Clinical |

### Intended Use Assessment

| Use | Decision | Reason |
| --- | --- | --- |
| direct_feed_type_training | NOT_SUPPORTED | Feed_Type meaning remains UNCLEAR and duplicates the milk file's values. |
| direct_feed_quantity_training | NOT_SUPPORTED | Feed_Quantity_kg meaning remains UNCLEAR and adds no independent feed target. |
| milk_yield_training | NOT_RECOMMENDED | Milk_Yield_L duplicates the milk file; disease/vital fields may be post-outcome leakage. |
| health_status_enrichment | POSSIBLE_WITH_LIMITATIONS | Disease_Status is an outcome label, not a proven equivalent of the form's current health status. |
| separate_future_disease_classification | POTENTIALLY_SUPPORTED | Disease_Status exists, but provenance, label timing, leakage, and validity require a separate audit. |
| nutrition_warnings | NOT_DIRECTLY_SUPPORTED | Disease labels and vital signs do not define safe nutrition actions or veterinary rules. |

### Data-Quality Issues

| Status | Severity | Issue | Column | Affected | Percentage | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | WARNING | Duplicate complete rows | ALL_COLUMNS | 0 | 0.0 | Exact duplicate across all parsed columns. |
| PASS | WARNING | Empty physical CSV rows | ALL_COLUMNS | 0 | 0.0 | Blank physical lines after the header; pandas normally skips these. |
| PASS | WARNING | Negative age | Age_Months | 0 | 0.0 | Age below 0 months. |
| PASS | WARNING | Zero age | Age_Months | 0 | 0.0 | Age exactly 0 months. |
| PASS | WARNING | Implausible age | Age_Months | 0 | 0.0 | Audit threshold: age under 12 months or over 300 months. |
| PASS | WARNING | Negative weight | Weight_kg | 0 | 0.0 | Weight below 0 kg. |
| PASS | WARNING | Zero weight | Weight_kg | 0 | 0.0 | Weight exactly 0 kg. |
| PASS | WARNING | Implausible weight | Weight_kg | 0 | 0.0 | Audit threshold: weight under 50 kg or over 1,200 kg. |
| PASS | WARNING | Negative milk yield | Milk_Yield_L | 0 | 0.0 | Milk_Yield_L below 0. |
| FLAGGED | WARNING | Zero milk yield | Milk_Yield_L | 5940 | 2.376 | Milk_Yield_L exactly 0. |
| PASS | WARNING | Suspiciously high milk yield | Milk_Yield_L | 0 | 0.0 | Conservative audit threshold: Milk_Yield_L over 100; its period is UNCLEAR. |
| PASS | WARNING | Negative feed quantity | Feed_Quantity_kg | 0 | 0.0 | Feed_Quantity_kg below 0. |
| PASS | WARNING | Zero feed quantity | Feed_Quantity_kg | 0 | 0.0 | Feed_Quantity_kg exactly 0. |
| PASS | WARNING | Suspiciously high feed quantity | Feed_Quantity_kg | 0 | 0.0 | Conservative audit threshold: Feed_Quantity_kg over 100; basis/period are UNCLEAR. |
| PASS | WARNING | Negative days in milk | Days_in_Milk | 0 | 0.0 | Days_in_Milk below 0. |
| PASS | WARNING | Suspiciously high days in milk | Days_in_Milk | 0 | 0.0 | Audit threshold: Days_in_Milk over 730. |
| PASS | WARNING | Humidity outside 0-100 | Humidity_percent | 0 | 0.0 | Humidity_percent outside the physical percentage range. |
| PASS | WARNING | Implausible ambient temperature | Ambient_Temperature_C | 0 | 0.0 | Audit threshold: ambient temperature below -20 C or above 55 C. |
| PASS | WARNING | Body-condition score outside detected 1-5 scale | Body_Condition_Score | 0 | 0.0 | Observed values are assessed against the common 1-5 scale; source scale is undocumented. |
| PASS | WARNING | Invalid parity | Parity | 0 | 0.0 | Audit threshold: negative, non-integer, or above 20. |
| PASS | ERROR | Impossible age/lactation combination | Days_in_Milk + Age_Months | 0 | 0.0 | Days_in_Milk exceeds approximate lifetime in days (Age_Months x 31). |
| PASS | ERROR | Impossible young-age/parity combination | Parity + Age_Months | 0 | 0.0 | Positive parity with age below 18 months. |
| PASS | WARNING | Inconsistent categorical spelling | Cattle_ID | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Breed | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Region | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Country | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Climate_Zone | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Management_System | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Lactation_Stage | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Feed_Type | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Season | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Date | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Farm_ID | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| PASS | WARNING | Inconsistent categorical spelling | Disease_Status | 0 | 0.0 | No case/spacing/punctuation-only duplicate categories detected. |
| FLAGGED | WARNING | Extremely high-cardinality categorical column | Cattle_ID | 250000 | 100.0 | 250,000 unique values across 250,000 rows. |
| UNCLEAR | WARNING | Mixed or undocumented feed units | Feed_Quantity_kg |  |  | The name states kg but supplies no material basis or time period; mixed units cannot be ruled out. |
| UNCLEAR | WARNING | Mixed or undocumented milk-yield period | Milk_Yield_L |  |  | The name states litres but supplies no daily/weekly/other period metadata. |

### Leakage Risks

The full per-column leakage classifications for all three proposed models are in `dataset_audit.json`. Disease outcome and physiological measurements are especially risky because their timing is undocumented and they are not available from the current FarmLite form.

## Cross-Dataset Join Assessment

Join status: **POSSIBLE_WITH_LIMITATIONS**.

Cattle_ID + Date is unique in both files, all 250,000 composite keys overlap, and shared values align exactly. This is strong file-level evidence that the disease file extends the same generated-looking records. However, provenance does not independently establish real animal identity or collection method. Do not join during Phase 1; any future join must use the composite key, never row order, and must first resolve provenance and intended use.

| Evidence | Value |
| --- | --- |
| preferred_composite_key | ['Cattle_ID', 'Date'] |
| milk_duplicate_composite_keys | 0 |
| disease_duplicate_composite_keys | 0 |
| milk_unique_composite_keys | 250000 |
| disease_unique_composite_keys | 250000 |
| shared_composite_keys | 250000 |
| keys_identical_in_row_order | True |

Shared columns: 36. All shared values identical in row order: True.

The datasets were not merged.

## Target Availability Matrix

| Target | Dataset Column | Availability | Meaning/Unit Status | Training Readiness | Notes |
| --- | --- | --- | --- | --- | --- |
| Recommended Feed Type | Feed_Type | PRESENT | UNCLEAR: broad category; observed/recommended/generated role undocumented | BLOCKED_PENDING_DEFINITION | Eight near-balanced categories; no explicit optimal/recommended label metadata. |
| Total Feed Quantity | Feed_Quantity_kg | PRESENT | UNCLEAR: kg basis and time period undocumented | BLOCKED_PENDING_DEFINITION | Could be fresh matter, dry matter, component intake, per meal, or another quantity. |
| Milk Yield | Milk_Yield_L | PRESENT | PARTIAL: litres stated; time period UNCLEAR | BLOCKED_PENDING_DEFINITION | Provenance is absent and dataset is not reliably dairy-only. |
| Roughage | NONE | ABSENT | NOT_AVAILABLE | NOT_SUPPORTED | Feed_Type category is not a numeric roughage target. |
| Concentrate | NONE | ABSENT | NOT_AVAILABLE | NOT_SUPPORTED | Concentrates is a Feed_Type class, not a quantity target. |
| Mineral Mix | NONE | ABSENT | NOT_AVAILABLE | NOT_SUPPORTED | No direct label. |
| Water Advice | NONE | ABSENT | NOT_AVAILABLE | NOT_SUPPORTED | Water_Intake_L is an observation, not advice. |
| Warnings | NONE | ABSENT | NOT_AVAILABLE | NOT_SUPPORTED | Disease_Status does not encode nutrition warning text or action. |

## Model Readiness Assessment

| Model | Decision | Target status | Reason |
| --- | --- | --- | --- |
| feed_type_classifier | BLOCKED_PENDING_DEFINITION | TARGET_UNCLEAR | Feed_Type is not documented as a recommendation target. |
| feed_quantity_regressor | BLOCKED_PENDING_DEFINITION | TARGET_UNCLEAR | Feed_Quantity_kg material basis and time period are UNCLEAR. |
| milk_yield_regressor | BLOCKED_PENDING_DEFINITION | TARGET_UNCLEAR | Litres are explicit, but the measurement period, provenance, and dairy-only scope are unresolved. |

## Information Required From Project Owner

1. What is the authoritative publisher/download source and license for each CSV?
2. Are the records observed, simulated, synthetic, or a mixture, and how were they generated or collected?
3. Does Feed_Type mean feed supplied, a recommended feed, a dominant ingredient, or another category?
4. Who or what assigned Feed_Type, and was it known before the milk/disease outcome?
5. What does Feed_Quantity_kg measure: total ration, fresh matter, dry matter, concentrate, roughage, or another quantity?
6. What period does Feed_Quantity_kg cover: per day, per meal, per week, or another period?
7. What period does Milk_Yield_L cover: per day, per milking, per week, or another period?
8. Are all records lactating dairy cattle? If not, which documented field or breed mapping defines the dairy-only subset?
9. Do identical Cattle_ID and Date values in both files represent the same real observation, or were both files derived from one generated table?
10. Which fields were available before each target was assigned, so post-outcome leakage can be excluded?
11. What are the category definitions and measurement protocols for lactation stage, parity, body-condition score, and management system?

## Final Decision

**Phase 1 result: PASS as a dataset audit; all three proposed model-training paths remain blocked.**

Do not begin a final feature contract or model training until the project owner supplies authoritative provenance and target definitions. A narrowly scoped Phase 2 draft could document these blockers, but it must not declare Feed_Type, Feed_Quantity_kg, or Milk_Yield_L deployment-ready.
