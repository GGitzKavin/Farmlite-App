# FarmLite Proposed ML API Output Contract

## Status

Design only. The existing Flask response, React rendering, and PDF are not
modified in Phase 2.

The proposed structure keeps current FarmLite camelCase conventions while
making synthetic targets, rule-derived values, validation actions, and model
versions traceable.

## Proposed Success Response

```json
{
  "success": true,
  "animalId": "TEST-001",
  "animalName": "Luna",
  "scope": {
    "animalCategory": "Dairy Cattle",
    "prototype": true,
    "syntheticTrainingData": true,
    "trainingDataScope": "SYNTHETIC_CATTLE_WITH_UNRESOLVED_PRODUCTION_PURPOSE"
  },
  "predictions": {
    "recommendedFeedType": "Silage",
    "classProbabilities": {
      "Silage": 0.31
    },
    "predictedFeedQuantityKg": 12.4,
    "predictedMilkYieldL": 14.2
  },
  "recommendation": {
    "totalFeedKg": 12.4,
    "roughageKg": 7.44,
    "concentrateKg": 4.96,
    "mineralMixKg": 0.1,
    "waterAdvice": "Provide clean water with free access throughout the day.",
    "feedingFrequency": "2 feedings per day",
    "confidenceLevel": "Prototype",
    "explanation": [],
    "warnings": []
  },
  "validation": {
    "status": "ACCEPTED",
    "adjustments": [],
    "imputedInputs": [],
    "normalizedInputs": []
  },
  "valueSources": {
    "recommendedFeedType": "ML_PREDICTED_SYNTHETIC_TARGET",
    "predictedFeedQuantityKg": "ML_PREDICTED_SYNTHETIC_TARGET",
    "predictedMilkYieldL": "ML_PREDICTED_SYNTHETIC_TARGET",
    "totalFeedKg": "ML_PREDICTED_SYNTHETIC_TARGET_RULE_VALIDATED",
    "roughageKg": "RULE_DERIVED",
    "concentrateKg": "RULE_DERIVED",
    "mineralMixKg": "RULE_DERIVED",
    "waterAdvice": "RULE_DERIVED",
    "feedingFrequency": "RULE_DERIVED",
    "warnings": "RULE_VALIDATED"
  },
  "modelVersions": {
    "feedTypeClassifier": "string",
    "feedQuantityRegressor": "string",
    "milkYieldRegressor": "string",
    "contractVersion": "1.0.0"
  },
  "limitations": [
    "Predictions are learned from publisher-declared synthetic cattle data.",
    "The synthetic feed-quantity material basis and period are not independently validated.",
    "The synthetic milk-yield period is not independently validated.",
    "The training data is not verified dairy-only."
  ],
  "disclaimer": "FarmLite is an undergraduate prototype using synthetic cattle data. Outputs demonstrate an ML and rule pipeline and are not veterinary, nutritional, commercial, or real-world feeding guidance."
}
```

Example numbers are structural placeholders only. They are not model results,
nutrition recommendations, or approved formula outputs.

## Prediction Fields

| Field | Type | Source | Interpretation |
|---|---|---|---|
| `recommendedFeedType` | String | Model 1 | Synthetic prototype feed-category prediction; not expert recommendation |
| `classProbabilities` | Optional object | Model 1 | Per-class prototype probabilities in saved class order |
| `predictedFeedQuantityKg` | Number | Model 2 | Raw synthetic feed-quantity prediction |
| `predictedMilkYieldL` | Number | Model 3 | Raw synthetic milk-yield prediction; period not independently validated |

## Recommendation Fields

| Field | Type | Source | Interpretation |
|---|---|---|---|
| `totalFeedKg` | Number | Model 2 prediction after validation/bounds | Compatibility label mapping to synthetic `Feed_Quantity_kg`; real-world material basis and period remain unvalidated |
| `roughageKg` | Number | Rules | Rule-derived feeding breakdown |
| `concentrateKg` | Number | Rules | Rule-derived feeding breakdown |
| `mineralMixKg` | Number | Rules | Rule-derived value |
| `waterAdvice` | String | Rules | General rule-derived advice |
| `feedingFrequency` | String | Rules | Rule-derived schedule text |
| `confidenceLevel` | String | System metadata | Must describe prototype/system conditions, not biological certainty |
| `explanation` | String array | Models plus rules | Must identify synthetic ML values separately from rules |
| `warnings` | String array | Validation rules | Must include missing, adjustment, health-review, scope, and synthetic-data warnings |

## Validation Contract

Allowed `validation.status` values:

- `ACCEPTED`: passed without numeric adjustment;
- `ADJUSTED`: one or more model values were changed by approved validation
  rules;
- `REJECTED`: request or predictions cannot be safely processed;
- `FALLBACK_USED`: a documented prototype fallback was required.

Each adjustment should contain:

```json
{
  "field": "totalFeedKg",
  "rawValue": 0,
  "validatedValue": 0,
  "rule": "string",
  "reason": "string"
}
```

No adjustment may be hidden inside explanation text only.

## Value-Source Vocabulary

- `ML_PREDICTED_SYNTHETIC_TARGET`
- `ML_PREDICTED_SYNTHETIC_TARGET_RULE_VALIDATED`
- `RULE_DERIVED`
- `RULE_VALIDATED`
- `REQUEST_METADATA`
- `FALLBACK_DERIVED`

The frontend and PDF should eventually use these values to state where every
number came from.

## Model-Version Contract

Each model version must identify:

- model artifact version;
- contract version;
- training dataset checksum/version;
- selected design (`DESIGN_A` or `DESIGN_B` for feed quantity);
- feature-order/schema version.

An empty, missing, or incompatible version should fail model loading rather
than silently using a different feature contract.

## Current-to-Future Mapping

| Current response | Proposed response | Change |
|---|---|---|
| `prediction.predictedMilkYieldL` | `predictions.predictedMilkYieldL` | Adds explicit synthetic interpretation and version |
| No feed-type prediction | `predictions.recommendedFeedType` | New prototype output |
| No feed-quantity prediction | `predictions.predictedFeedQuantityKg` | New raw synthetic target output |
| `recommendation.totalFeedKg` | `recommendation.totalFeedKg` | Preserved user-facing label; source becomes explicit |
| Rule breakdown fields | Same names | Preserved with `RULE_DERIVED` source |
| Text-only limitations | `scope`, `valueSources`, `modelVersions`, `limitations` | Adds machine-readable traceability |

## Error Response

The future error shape should preserve current conventions while including
validation details:

```json
{
  "success": false,
  "error": "Human-readable message",
  "validation": {
    "status": "REJECTED",
    "fieldErrors": {}
  },
  "prototype": true
}
```

No response implementation is authorized in Phase 2.
