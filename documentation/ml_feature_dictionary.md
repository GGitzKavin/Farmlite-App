# FarmLite ML Feature Dictionary

## Beginner Guide

A **feature** is information given to a model, such as a cow's weight. A
**target** is the value the model learns to predict, such as the synthetic feed
category.

**Leakage** happens when a model is given information that reveals the answer
or would not exist when a real prediction is requested. Leakage can create
excellent-looking test scores that fail in actual use.

An **identifier**, such as `Cattle_ID`, may help track or split records but
should not normally be used for prediction. The model could memorize IDs
instead of learning reusable patterns.

All source data in this dictionary is publisher-declared synthetic. Feature
meaning is suitable for an undergraduate ML demonstration, not proof of
real-world biological relationships.

## Animal Features

| Canonical name | Dataset column | Application field | Meaning | Unit/type | Example | Model usage | Required | Validation | Missing handling | Synthetic-data caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| `animal_type` | None | Firestore `species`/`animalType`/`type`; not currently sent | Application animal-category scope | Category | `Dairy Cattle` | Scope validation only; never predictive | Derived | Must match approved dairy-cattle labels | Reject unsupported category | Raw dataset has no verified animal-purpose field |
| `breed` | `Breed` | `breed` | Synthetic breed label | Category/string | `Holstein-Friesian` | Included in Models 1, 2A, 2B, and 3 | Yes | Non-empty; normalize only documented spelling variants; unseen valid values require explicit unknown handling | Reject missing request | Breed-purpose meaning and dairy suitability are not verified |
| `age_months` | `Age_Months` | `ageMonths` | Synthetic animal age | Months/integer | `48` | Included in all models | Yes | Proposed 1-300; dataset observed 24-143 | Reject missing request | Value is generated rather than verified farm age |
| `weight_kg` | `Weight_kg` | `weightKg` | Synthetic body weight | kg/number | `420.0` | Included in all models and later rule validation | Yes | Proposed 50-1,200; dataset observed 250-750 | Reject missing request | Real measurement process and calibration do not exist |
| `parity` | `Parity` | None | Synthetic calving/lactation count | Count/integer | `3` | Excluded from current models | No | Dataset observed 1-6 if later supported | Not available; do not invent or silently default | Present in data but absent from FarmLite prediction flow |

## Production Features

| Canonical name | Dataset column | Application field | Meaning | Unit/type | Example | Model usage | Required | Validation | Missing handling | Synthetic-data caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| `lactation_stage` | `Lactation_Stage` | `lactationStage` | Synthetic production-stage category | Category | Dataset `Mid`; UI `Mid Lactation` | Included in all models | Yes | Map Early/Mid/Late explicitly; UI `Dry` is unsupported by the dataset | Reject missing or unsupported stage | Stage assignment method is not documented |
| `days_in_milk` | `Days_in_Milk` | `daysInMilk` | Synthetic time since lactation began | Days/integer | `120` | Included in all models | Optional | Proposed 0-730; dataset observed 1-364 | Training-median imputation plus missing flag | Not a verified farm timeline |
| `previous_week_avg_yield_l` | `Previous_Week_Avg_Yield` | `previousWeekAvgYield` | Historical synthetic production value intended to precede prediction | Litres/number; exact aggregation semantics limited | `14.0` | Included in all models | Optional | Proposed 0-100; dataset observed 0-38.67 | Training-median imputation plus missing flag | Strong relationship may reflect generation formula; it must remain a lagged input |
| `body_condition_score` | `Body_Condition_Score` | `bodyConditionScore` | Synthetic body-condition rating | Score/number | `3.0` | Included in all models | Optional | Current application scale 1-5; dataset observed 2-5 | Training-median imputation plus missing flag | Assessment protocol and scorer reliability are not documented |

## Environmental Features

| Canonical name | Dataset column | Application field | Meaning | Unit/type | Example | Model usage | Required | Validation | Missing handling | Synthetic-data caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| `ambient_temperature_c` | `Ambient_Temperature_C` | `ambientTemperatureC` | Synthetic ambient temperature | Degrees Celsius/number | `28.0` | Included in all models | Optional | Proposed -20 to 55; dataset observed -10 to 45 | Training-median imputation plus missing flag | Manually entered; not linked to a verified observation source |
| `humidity_percent` | `Humidity_percent` | `humidityPercent` | Synthetic relative humidity | Percent/number | `70.0` | Included in all models | Optional | 0-100; dataset observed 10-100 | Training-median imputation plus missing flag | Manually entered; not linked to a verified observation source |
| `season` | `Season` | None | Synthetic seasonal category | Category | `Summer` | Excluded from current models | No | Dataset values: Autumn, Monsoon, Spring, Summer, Winter | Not available; do not default | Adding it from CSV would create a frontend/model mismatch |
| `climate_zone` | `Climate_Zone` | None | Synthetic climate category | Category | `Tropical` | Excluded from current models | No | Dataset has six categories | Not available; do not infer from location | No current request or verified location-to-climate service |

## Management Features

| Canonical name | Dataset column | Application field | Meaning | Unit/type | Example | Model usage | Required | Validation | Missing handling | Synthetic-data caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| `management_system` | `Management_System` | None | Synthetic management category | Category | `Intensive` | Excluded from current models | No | Dataset values: Extensive, Intensive, Mixed, Pastoral, Semi_Intensive | Not available; do not default | Present only in the CSV |
| `health_status` | None in primary CSV | `healthStatus` | Latest current FarmLite health text | Category | `Healthy` | Excluded from ML; retained for rule validation/warnings | Optional | Current UI: Healthy, Sick, Under Treatment, Recovering | Use `Unknown` and warn rather than invent a dataset feature | `Disease_Status` is a synthetic outcome and is not an alias |

## Targets

| Canonical name | Dataset column | Application field | Meaning | Unit/type | Example | Model task | Required/optional | Validation | Missing handling | Synthetic-data caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| `feed_type` | `Feed_Type` | None; future output `recommendedFeedType` | Synthetic feed-category label | Category/string | `Silage` | Model 1 multiclass classification | Required training target | Must be one of eight audited classes | Exclude missing target rows during future preprocessing and report count | Not an expert recommendation or nutritionally optimal label |
| `feed_quantity_kg` | `Feed_Quantity_kg` | None; future output `predictedFeedQuantityKg` | Synthetic feed-quantity target | kg/number | `12.0` | Model 2 regression | Required training target | Dataset observed 3.0-25.0 | Exclude missing target rows and report count | Material basis and period are not independently validated |
| `milk_yield_l` | `Milk_Yield_L` | None; future output `predictedMilkYieldL` | Synthetic milk-yield target | litres/number | `14.06` | Model 3 regression | Required training target | Dataset observed 0.0-36.42 | Exclude missing target rows and report count | Daily/weekly/per-milking period and zero meaning are not independently validated |

Targets are never inputs to their own model.

## Design-B Derived Feature

| Canonical name | Dataset column | Application field | Meaning | Unit/type | Example | Model usage | Required | Validation | Missing handling | Synthetic-data caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| `predicted_feed_type` | None as an input | Future Model 1 output | Model 1's synthetic category prediction | Category/string or probability vector | `Silage` | Included only in Feed Quantity Design B | Yes for Design B | Category order/version must match Model 1 | Design B unavailable if Model 1 fails | Training values must be out-of-fold predictions, never the true `Feed_Type` |

## Excluded Fields

| Canonical name | Dataset/application source | Proposed role | Reason excluded |
|---|---|---|---|
| `cattle_id` | `Cattle_ID` / `animalId` | Metadata only | Unique identifier; memorisation and generated-batch risk |
| `farm_id` | `Farm_ID` | Grouping/metadata only | Not currently supplied and may encode synthetic farm batches |
| `observation_date` | `Date` | Metadata/split audit only | Not currently supplied and may reveal generated time batches |
| `production_stage` | API `productionStage` | Rule metadata only | Current payload duplicates `lactationStage`; no separate dataset column |
| `feed_type` in Models 2A, 2B, and 3 | `Feed_Type` | Excluded input | Same-record timing is unclear; Design B uses predicted rather than true feed type |
| `feed_quantity_kg` outside its target role | `Feed_Quantity_kg` | Excluded input | Target leakage or unavailable same-record outcome |
| `milk_yield_l` outside its target role | `Milk_Yield_L` | Excluded input | Target leakage or unavailable same-record outcome |
| `disease_status` | Secondary CSV `Disease_Status` | Excluded | Separate synthetic outcome, unavailable in the current request, and not merged |
| Vital signs and treatment/outcome fields | Secondary CSV only | Excluded | Potential post-outcome leakage and application mismatch |
| Direct row index | Generated during loading | Excluded | No biological meaning; can reveal row-generation order |

## Missing and Unknown Values

- Required fields are rejected when absent or invalid.
- Optional numeric values are imputed using statistics fitted on the training
  partition only, and a missing-value flag is retained.
- Unknown categorical values use an explicit `__UNKNOWN__` encoder category
  only when they are otherwise valid.
- Unsupported semantic categories are not silently converted. In particular,
  the UI value `Dry` cannot be mapped to the dataset's Early/Mid/Late
  lactation categories.
- Imputation values, feature order, category order, and validation rules must
  be saved with each future pipeline.
