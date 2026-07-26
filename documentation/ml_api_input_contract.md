# FarmLite Proposed ML API Input Contract

## Status

Design only. The current Flask route and React request are unchanged.

The proposed request uses fields already available in the current application
or derivable from the selected Firestore record. It does not require fields
merely because they exist in the synthetic CSV.

## Proposed Request

```json
{
  "animalType": "Dairy Cattle",
  "animalId": "TEST-001",
  "animalName": "Luna",
  "breed": "Holstein-Friesian",
  "ageMonths": 48,
  "weightKg": 420,
  "healthStatus": "Healthy",
  "lactationStage": "Mid Lactation",
  "daysInMilk": 120,
  "previousWeekAvgYield": 14,
  "bodyConditionScore": 3.0,
  "ambientTemperatureC": 28,
  "humidityPercent": 75
}
```

`Feed_Type`/`feedType` is deliberately absent. The farmer must not submit the
value the classifier is intended to predict.

## Field Contract

| API field | Classification | Type | Unit | Validation | Missing behaviour | Dataset mapping | Model usage |
|---|---|---|---|---|---|---|---|
| `animalType` | `DERIVED` | String | None | Must resolve to an approved dairy-cattle label | Reject unsupported or unknown animal scope before inference | None | Scope validation only |
| `animalId` | `OPTIONAL` | String | None | Non-empty when present; length-limited and treated as opaque | Omit from prediction but allow response/PDF metadata | `Cattle_ID` only as metadata | Never predictive |
| `animalName` | `OPTIONAL` | String | None | Trim; length-limited | Display as unnamed animal | None | Never predictive |
| `breed` | `REQUIRED` | String | Category | Non-empty; documented normalization only | Reject request | `Breed` | Models 1, 2A, 2B, 3 |
| `ageMonths` | `REQUIRED` | Number/integer | Months | Finite integer, proposed range 1-300 | Reject request | `Age_Months` | Models 1, 2A, 2B, 3 |
| `weightKg` | `REQUIRED` | Number | kg | Finite, proposed range 50-1,200 | Reject request | `Weight_kg` | Models 1, 2A, 2B, 3 and rule validation |
| `healthStatus` | `OPTIONAL` | String | Category | Normalize known current statuses; preserve unknown explicitly | Use `Unknown` and emit warning | No primary-dataset equivalent | Rule validation/warnings only |
| `lactationStage` | `REQUIRED` | String | Category | Map Early/Mid/Late Lactation to dataset Early/Mid/Late | Reject missing; reject or defer UI `Dry` because the dataset has no matching class | `Lactation_Stage` | Models 1, 2A, 2B, 3 |
| `daysInMilk` | `OPTIONAL` | Number/integer | Days | Finite integer, proposed range 0-730 | Pipeline training-median imputation plus missing flag | `Days_in_Milk` | Models 1, 2A, 2B, 3 |
| `previousWeekAvgYield` | `OPTIONAL` | Number | Litres; historical window named previous week | Finite, proposed range 0-100 | Pipeline training-median imputation plus missing flag | `Previous_Week_Avg_Yield` | Models 1, 2A, 2B, 3 |
| `bodyConditionScore` | `OPTIONAL` | Number | Score | Finite, current scale 1-5 | Pipeline training-median imputation plus missing flag | `Body_Condition_Score` | Models 1, 2A, 2B, 3 |
| `ambientTemperatureC` | `OPTIONAL` | Number | Degrees Celsius | Finite, proposed range -20 to 55 | Pipeline training-median imputation plus missing flag | `Ambient_Temperature_C` | Models 1, 2A, 2B, 3 |
| `humidityPercent` | `OPTIONAL` | Number | Percent | Finite, range 0-100 | Pipeline training-median imputation plus missing flag | `Humidity_percent` | Models 1, 2A, 2B, 3 |
| `productionStage` | `NOT_SUPPORTED` | String | Category | None | Do not include in the canonical request | No separate column | Current duplicate of `lactationStage`; rule explanation only |
| `parity` | `NOT_SUPPORTED` | Integer | Count | Dataset observed 1-6 | Do not require or invent | `Parity` | Excluded because current application does not supply it |
| `season` | `NOT_SUPPORTED` | String | Category | None | Do not require or infer | `Season` | Excluded because current application does not supply it |
| `climateZone` | `NOT_SUPPORTED` | String | Category | None | Do not require or infer | `Climate_Zone` | Excluded because current application does not supply it |
| `managementSystem` | `NOT_SUPPORTED` | String | Category | None | Do not require or infer | `Management_System` | Excluded because current application does not supply it |
| `feedType` | `NOT_SUPPORTED` | String | Category | Must not be accepted as farmer input | Ignore/reject as an unexpected prediction field | `Feed_Type` target | Model 1 output; true value forbidden at inference |
| `feedQuantityKg` | `NOT_SUPPORTED` | Number | kg, basis/period unvalidated | Must not be accepted as prediction input | Ignore/reject as an unexpected target field | `Feed_Quantity_kg` target | Model 2 output |
| `milkYieldL` | `NOT_SUPPORTED` | Number | Litres, period unvalidated | Must not be accepted as current outcome input | Ignore/reject as an unexpected target field | `Milk_Yield_L` target | Model 3 output |

## Required-Field Rationale

The required model inputs match the current runtime requirements:

- breed;
- age in months;
- weight in kilograms;
- lactation stage.

The other selected model features are present in the current form but remain
optional so the contract does not pretend that default values were measured.
Future inference should expose which optional values were missing and imputed.

## Prediction-Time Rules

1. Validate `animalType` before loading a model.
2. Convert the application lactation labels through an explicit mapping.
3. Do not accept a farmer-supplied feed type.
4. Do not accept current target values as hidden model inputs.
5. Preserve `previousWeekAvgYield` as a historical value.
6. Keep identifiers and names outside the predictive feature frame.
7. Record missing-value, normalization, and imputation actions.
8. Return a clear validation error for unsupported `Dry` stage until that
   application/dataset mismatch has an approved resolution.

## Synthetic-Data Notice

Every accepted request produces only a prototype prediction from models trained
on publisher-declared synthetic cattle data. Input validation does not make the
training data observational, veterinarian-validated, nutritionally validated,
or suitable for commercial feeding decisions.
