# Bangladesh Candidate versus Current FarmLite Runtime Input Gap

## Review Boundary

This is a read-only audit of the current React request, Flask route, retained
model service, feed planner, response, and browser-generated PDF. Nothing in
that flow was modified in Phase 4.5E.

The current flow remains:

```text
Firestore livestock and health records
  -> FeedRecommendation.tsx form and camelCase JSON
  -> POST /api/ai/feed-recommendation
  -> retained synthetic milk-yield model
  -> weight-and-milk total-feed formula
  -> rule-based feed planner
  -> React result and browser-generated PDF
```

## Current Frontend and JSON Request

`FeedRecommendation.tsx` owns the form, validation, Axios request, response
typing, rendering, and PDF generation.

| Frontend field | Current JSON field | Type/unit | UI status | Existing default or enum |
|---|---|---|---|---|
| Selected animal | Not sent | Firestore document ID | Required by UI | None |
| Animal ID/tag | `animalId` | String metadata | Optional to backend | Selected record ID fallback |
| Animal name | `animalName` | String metadata | Optional | Empty |
| Breed | `breed` | Free-text category | Required | No enum |
| Age | `ageMonths` | Number, months | Required, positive | Derived from birth date/age aliases when possible |
| Weight | `weightKg` | Number, kg | Required, positive | None |
| Lactation stage | `lactationStage` | Category | Required | `Early Lactation`, `Mid Lactation`, `Late Lactation`, `Dry`; initial `Mid Lactation` |
| Days in milk | `daysInMilk` | Number, days | Optional | `0` |
| Ambient temperature | `ambientTemperatureC` | Number, °C | Optional | `28` |
| Relative humidity | `humidityPercent` | Number, % | Optional | `70`; UI min/max 0/100 |
| Previous-week average yield | `previousWeekAvgYield` | Number, L in named historical window | Optional | `0` |
| Body-condition score | `bodyConditionScore` | Number, score 1–5 | Optional | `3.0` |
| Health status | `healthStatus` | Category | Optional | `Healthy`; enum also includes `Sick`, `Under Treatment`, `Recovering`, `Critical` |
| Production stage | `productionStage` | Duplicate category | Sent but no separate control | Copy of `lactationStage` |

The page recognizes multiple Firestore aliases for animal species, ID, age,
weight, and health status. Breed remains an editable free-text value.
`genetic_group` is not stored, displayed, or sent.

## Current Validation and Defaults

Frontend validation requires a selected dairy-cattle record, non-empty breed,
positive age, positive weight, and non-empty lactation stage. It does not
require measured temperature or humidity because blank/invalid values are
replaced during payload construction with 28 °C and 70%.

The Flask model service currently requires:

- `breed`;
- `ageMonths`;
- `weightKg`;
- `lactationStage`.

It converts numeric fields to finite floats. Missing optional numeric values
receive these backend defaults:

- `daysInMilk`: `0`;
- `ambientTemperatureC`: `28`;
- `humidityPercent`: `70`;
- `previousWeekAvgYield`: `0`;
- `bodyConditionScore`: `3.0`.

Those defaults are acceptable only as documentation of current behavior. They
must not be treated as measured environmental inputs for a Bangladesh
candidate.

## Current Backend Transformations and Model Inputs

The retained model service maps current camelCase fields to:

`Breed`, `Age_Months`, `Weight_kg`, `Lactation_Stage`, `Days_in_Milk`,
`Ambient_Temperature_C`, `Humidity_percent`, `Previous_Week_Avg_Yield`, and
`Body_Condition_Score`.

The route then calculates:

```text
estimated_total_feed_kg =
    weightKg * 0.025
    + predictedMilkYieldL * 0.30
```

The feed planner clamps that value to 1.5–4.0% of body weight, selects a
roughage/concentrate ratio from predicted-milk bands, optionally shifts 10% of
concentrate to roughage for specified health states, selects a fixed mineral
amount by weight threshold, and selects two or three feedings from milk yield.

No current model consumes `genetic_group` or `thi_category`.

## Current Response

The current response contains:

- `success`, `animalId`, and `animalName`;
- `prediction.predictedMilkYieldL`, `modelUsed`, `target`, `featuresUsed`, and
  `modelLimitation`;
- `recommendation.totalFeedKg`, `roughageKg`, `concentrateKg`,
  `mineralMixKg`, `waterAdvice`, `feedingFrequency`, `confidenceLevel`,
  `explanation`, `warnings`, and `disclaimer`;
- top-level `limitations`.

The current response does not contain eligibility status, THI traceability,
DMI prediction, per-output value source, artifact hash, or fallback reason.

## Current PDF Fields

The browser-generated PDF includes:

- report date/time and animal ID/name;
- breed, age, weight, health, lactation stage, days in milk, historical milk,
  BCS, temperature, and humidity;
- predicted milk, model name, and target;
- total feed, roughage, concentrate, mineral mix, water advice, frequency,
  confidence, explanations, warnings, limitations, and disclaimer.

There is no genetic-group field, calculated THI, THI category, DMI value,
eligibility result, model provenance hash, or explicit ML-versus-rule
ownership.

## Required Candidate Field Comparison

| Candidate field | Current FarmLite source | Direct match | Mapping required | Safe | Decision |
|---|---|---|---|---|---|
| `genetic_group` | No field. Only free-text `breed` exists. | `NO` | New explicit input or verified record required | `NO` for breed inference | `NEW_EXPLICIT_INPUT_REQUIRED`; never infer silently from breed |
| `thi_category` | `ambientTemperatureC` and `humidityPercent`, currently optional/defaulted | `NO` | Server-side THI formula and category mapping | `CONDITIONAL` only with measured finite values and verified boundaries | `SERVER_CALCULATION_REQUIRED_NO_DEFAULTS`; missing/invalid environment forces fallback |

## Additional Compatibility Findings

- Cow ID is metadata and must not enter either candidate feature frame.
- Blood, physiology, and milk-composition variables are not ordinary FarmLite
  request fields and remain prohibited.
- Breed is not automatically equivalent to percent HF inheritance.
- Current temperature and humidity field names are compatible in meaning but
  incompatible in missing-value behavior.
- Both candidates require only two categorical features. The current nine
  retained-model features must not be silently passed as substitutes.
- Current `Dry` lactation stage is outside the Bangladesh study population of
  lactating cows.

## Gap Decision

Current FarmLite requests are not directly eligible for Bangladesh inference.
Phase 5 requires a new explicit `genetic_group` input and a separate,
fail-closed environment adapter. Until both are present and valid, the
Bangladesh models must return an ineligibility/fallback result without loading
or calling the pipeline.
