# FarmLite Current Feed-Recommendation Input Inventory

## Inspected Flow

The current flow is:

```text
Firestore livestock + healthRecords
  -> FeedRecommendation.tsx normalization and editable form
  -> inline Axios POST /api/ai/feed-recommendation
  -> api/routes.py
  -> ml/inference/model_service.py
  -> ml/inference/feed_planner.py
  -> React results and browser-generated jsPDF report
```

There is no separate frontend API service for this feature. The Axios call,
request payload, response interface, form, and PDF mapping are all in
`frontend/src/pages/FeedRecommendation.tsx`.

## Current Request Fields

| UI field | API field | Backend field | Dataset column | Type | Unit | Example | Required | Available at prediction time | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Selected animal | Not sent (`selectedAnimalId` is UI-only) | None | None | String ID | None | Firestore document ID | Required by UI | Yes | Selects the Firestore record; never a predictive feature |
| Animal ID/tag | `animalId` | `data.get("animalId")` | `Cattle_ID` only as metadata | String | None | `TEST-001` | Optional to backend | Yes | Loaded from `animalId`, `tagId`, `tagID`, or document ID; returned in response, not used by current model |
| Animal name | `animalName` | `data.get("animalName")` | None | String | None | `Luna` | Optional to backend | Yes | Display/PDF metadata only |
| Breed | `breed` | `input_data["breed"]` | `Breed` | String/categorical | None | `Holstein-Friesian` | Required | Yes | Firestore field and editable text input; one of four runtime-required model fields |
| Age (months) | `ageMonths` | `input_data["ageMonths"]` | `Age_Months` | Number | Months | `48` | Required, positive | Yes | May be derived from birth date, read directly in months, or converted from years; UI stores text and payload converts to number |
| Weight | `weightKg` | `input_data["weightKg"]` and route calculation | `Weight_kg` | Number | kg | `420` | Required, positive | Yes | Firestore accepts `weightKg` or `weight`; interface does not independently verify the original `weight` unit |
| Lactation stage | `lactationStage` | `input_data["lactationStage"]` | `Lactation_Stage` | String/categorical | None | `Mid Lactation` | Required | Yes | UI values are `Early Lactation`, `Mid Lactation`, `Late Lactation`, `Dry`; dataset values are `Early`, `Mid`, `Late`. `Dry` has no dataset category |
| Days in milk | `daysInMilk` | `input_data["daysInMilk"]` | `Days_in_Milk` | Number | Days | `120` | Optional with current default `0` | Yes | Editable form field; current model service silently defaults missing values to 0 |
| Previous-week average yield | `previousWeekAvgYield` | `input_data["previousWeekAvgYield"]` | `Previous_Week_Avg_Yield` | Number | Litres; historical window named previous week | `14` | Optional with current default `0` | Yes | Intended historical value available before prediction; dataset target period is synthetic and not independently validated |
| Body-condition score | `bodyConditionScore` | `input_data["bodyConditionScore"]` | `Body_Condition_Score` | Number | Current UI scale 1-5 | `3.0` | Optional with current default `3.0` | Yes | Dataset observed range is 2.0-5.0 |
| Ambient temperature | `ambientTemperatureC` | `input_data["ambientTemperatureC"]` | `Ambient_Temperature_C` | Number | Degrees Celsius | `28` | Optional with current default `28` | Yes | Editable rather than currently read from a weather service |
| Humidity | `humidityPercent` | `input_data["humidityPercent"]` | `Humidity_percent` | Number | Percent | `75` | Optional with current default `70` | Yes | UI constrains 0-100 |
| Health status | `healthStatus` | `data.get("healthStatus", "Healthy")` | None in primary dataset | String/categorical | None | `Healthy` | Optional with current default `Healthy` | Yes | Derived from latest related Firestore health record or edited; `Disease_Status` is not a valid alias |
| Production stage | No separate UI control; copied from lactation stage | `productionStage` | `data.get("productionStage")` | String | None | `Mid Lactation` | Optional | Yes | Sent as a duplicate of `lactationStage`; current feed planner reports it in explanation but applies no extra rule |

## Current Application Data Sources

### Firestore `livestock`

The page reads these local aliases:

- animal type: `species`, `animalType`, `type`;
- animal ID: `animalId`, `tagId`, `tagID`;
- animal name: `animalName`, `name`;
- breed: `breed`;
- age: `birthDate`, `dateOfBirth`, `dob`, `ageMonths`, `ageInMonths`,
  `ageYears`, `ageInYears`, `age`;
- weight: `weightKg`, `weight`;
- ownership: `userId`.

The page filters selected records using dairy-cattle-like text labels before
showing them. The resolved species is not included in the current API payload.

### Firestore `healthRecords`

The latest matching record may supply health text from:

- `status`;
- `healthStatus`;
- `condition`;
- `recoveryStatus`.

Record linkage uses `livestockId` or `animalId`, and recency uses `updatedAt`,
`createdAt`, or `date`.

## Runtime Required/Optional Difference

`api/schemas.py` declares a `TypedDict` with `total=False`, so it does not
enforce required fields. Runtime validation in `model_service.py` requires:

- `breed`;
- `ageMonths`;
- `weightKg`;
- `lactationStage`.

The current optional numeric defaults are:

- `daysInMilk`: 0;
- `ambientTemperatureC`: 28;
- `humidityPercent`: 70;
- `previousWeekAvgYield`: 0;
- `bodyConditionScore`: 3.0.

Phase 2 proposes explicit optional-field handling and warning metadata rather
than treating defaults as measured facts.

## Current Model and Feed-Planning Use

The retained milk-yield model consumes:

- `Breed`;
- `Age_Months`;
- `Weight_kg`;
- `Lactation_Stage`;
- `Days_in_Milk`;
- `Ambient_Temperature_C`;
- `Humidity_percent`;
- `Previous_Week_Avg_Yield`;
- `Body_Condition_Score`.

The route then calculates:

```text
weightKg * 0.025 + predictedMilkYieldL * 0.30
```

The feed planner bounds that rule-derived quantity and creates roughage,
concentrate, mineral, water, frequency, warning, confidence, and explanation
values. No current ML model predicts feed type or feed quantity.

## Current PDF Mapping

The PDF includes:

- animal ID/name;
- all nine retained model inputs plus health status;
- predicted milk yield, model name, and target;
- total feed, roughage, concentrate, mineral mix, water advice, feeding
  frequency, confidence, explanations, warnings, limitations, and disclaimer.

The PDF currently labels predicted milk yield as `L/day`, although the
synthetic dataset's measurement period is not independently validated. Phase 2
records this mismatch but does not modify the PDF.

## Existing Test Evidence

`backend/flask_api/tests/test_api.py` sends the complete current payload and
asserts the existing top-level, prediction, and recommendation response keys.
Its example includes `Holstein-Friesian`, 48 months, 420 kg, `Mid`, 120 days in
milk, prior yield 14, body-condition score 3.0, 28 C, and 75% humidity.

`backend/flask_api/tests/test_model_service.py` supplies the same nine current
model inputs and confirms that the retained artifact predicts
`Milk_Yield_L`. These tests document current behaviour only; they do not
authorize or validate the proposed three-model contract.

## Fields Not Available in the Current Request

| Canonical field | Dataset availability | Current request availability | Contract implication |
|---|---|---|---|
| `parity` | Present as `Parity` | Absent | Exclude from current models |
| `season` | Present as `Season` | Absent | Exclude from current models |
| `climate_zone` | Present as `Climate_Zone` | Absent | Exclude from current models |
| `management_system` | Present as `Management_System` | Absent | Exclude from current models |
| `animal_type` | No dataset column | Available in selected Firestore record but not sent | Proposed derived scope field, not predictive input |
| `health_status` | No primary-dataset column | Present | Rule input only; exclude from ML features |
| `feed_type` | Target column | Farmer does not provide it | Correct: must remain a model output, never a farmer input |

No application fields were modified during this inventory.
