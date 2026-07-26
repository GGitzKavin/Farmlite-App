# FarmLite Final API Reference

Date: 2026-07-26

Base URL in local development: `http://127.0.0.1:5000`

## General behavior

- Requests and responses are JSON except the health `GET`.
- API v1 and v2 contracts remain unchanged.
- Unexpected failures return controlled generic messages; internal exception
  details are not returned to the client.
- CORS is currently enabled application-wide. A production host must apply an
  explicit allowlist.

## GET `/api/health`

Successful response, HTTP 200:

```json
{
  "status": "healthy",
  "service": "FarmLite AI API"
}
```

## POST `/api/ai/feed-recommendation`

API v1 returns the retained FarmLite milk prediction and the separate
rule-generated ration.

### Request

```json
{
  "animalId": "COW-001",
  "animalName": "Luna",
  "breed": "Holstein-Friesian",
  "ageMonths": 48,
  "weightKg": 420,
  "healthStatus": "Healthy",
  "lactationStage": "Mid",
  "daysInMilk": 120,
  "previousWeekAvgYield": 14,
  "bodyConditionScore": 3.0,
  "ambientTemperatureC": 28,
  "humidityPercent": 75,
  "productionStage": "Mid Lactation"
}
```

The model service validates the required retained-model inputs. The route uses
`weightKg`, predicted milk and current health/production context when calling
the nutrition rule engine.

### Successful response

HTTP 200:

```json
{
  "success": true,
  "animalId": "COW-001",
  "animalName": "Luna",
  "prediction": {
    "predictedMilkYieldL": 14.56,
    "modelUsed": "...",
    "target": "...",
    "featuresUsed": [],
    "modelLimitation": "..."
  },
  "recommendation": {
    "totalFeedKg": 14.87,
    "roughageKg": 9.67,
    "concentrateKg": 5.2,
    "mineralMixKg": 0.1,
    "waterAdvice": "...",
    "feedingFrequency": "...",
    "confidenceLevel": "...",
    "explanation": [],
    "warnings": [],
    "disclaimer": "..."
  },
  "limitations": []
}
```

Values above illustrate the shape only; runtime values are dynamic.
`predictedMilkYieldL` is model-owned. Every value under `recommendation` is
owned by the FarmLite nutrition rule engine, not by a feed model and not by
the DMI model.

### Errors

- HTTP 400: invalid/non-object JSON.
- Model-service validation status: controlled `{"success": false, "error":
  "..."}`.
- HTTP 500: `An unexpected recommendation service error occurred.`

## POST `/api/v2/predict`

API v2 is feature-gated by `BANGLADESH_CANDIDATE_MODELS_ENABLED` and has a
16 KiB request limit. It owns eligibility evaluation, backend THI and
collected-data candidate inference. It does not call the nutrition rules.

### Fields

| Field | Type | Required by primitive schema | Notes |
|---|---|---:|---|
| `breed` | string | Yes | Never determines genetic group |
| `genetic_group` | string | No | Required for DMI eligibility; supported values are explicit |
| `age_months` | integer > 0 | Yes | |
| `weight_kg` | finite number > 0 | Yes | |
| `lactation_stage` | string | Yes | Must be within supported production scope |
| `days_in_milk` | integer ≥ 0 or null | No | |
| `previous_week_avg_yield_l` | finite number ≥ 0 or null | No | |
| `body_condition_score` | 1–5 or null | No | |
| `ambient_temperature_c` | finite number or null | No | Required for THI/model eligibility |
| `humidity_percent` | finite number or null | No | Eligibility constrains the valid range |
| `health_status` | string | No | |

Unknown fields are rejected. Strings are trimmed and limited to 256
characters.

### Eligible request

```json
{
  "breed": "Holstein-Friesian",
  "genetic_group": "HF75",
  "age_months": 48,
  "weight_kg": 420,
  "lactation_stage": "Mid Lactation",
  "days_in_milk": 120,
  "previous_week_avg_yield_l": 7.0,
  "body_condition_score": 3.0,
  "ambient_temperature_c": 28,
  "humidity_percent": 75,
  "health_status": "Healthy"
}
```

### Response sections

The stable top-level sections are:

- `schema_version`
- `prediction_status`
- `eligibility`
- `environment`
- `ml_predictions`
- `model_sources`
- `rule_recommendation`
- `warnings`
- `limitations`
- `fallback_reasons`

`environment.calculated_thi` and `environment.thi_category` are backend
derived. `ml_predictions.dmi_kg_day` uses kg dry matter/cow/day. The
`rule_recommendation` fields remain null/unavailable because v2 is forbidden
from producing ration composition.

The response can contain an internal candidate milk value for technical
evaluation. It must not be displayed in the farmer UI or PDF.

### Status behavior

| Condition | HTTP | `prediction_status` |
|---|---:|---|
| Eligible and enabled | 200 | `ELIGIBLE` |
| Flag disabled | 200 | `DISABLED` |
| Missing/unsupported inputs or artifact fallback | 200 | `FALLBACK_REQUIRED` |
| Malformed JSON | 400 | `UNAVAILABLE` |
| Schema/type/size failure | 422 | `UNAVAILABLE` |
| Unexpected service failure | 500 | `UNAVAILABLE` |

Unavailable numeric values are JSON `null`, never zero fallbacks.

## Farmer-facing ownership

API responses are composed by the frontend under these mandatory labels:

- Expected milk yield — FarmLite milk prediction model
- Dry-matter intake — Collected-data DMI model
- Heat Stress Index — Backend THI calculation
- Advisory ration — FarmLite nutrition rule engine

The DMI research-data source is Mendeley Data, DOI
`10.17632/954f6g36sb.2`.
