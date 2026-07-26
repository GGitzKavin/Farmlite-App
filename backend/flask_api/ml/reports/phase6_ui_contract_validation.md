# Phase 6 UI contract validation

Date: 2026-07-26
Result: PASS WITH MANUAL VISUAL LIMITATION

## Contract mapping

| Requirement | Result | Evidence |
|---|---|---|
| Frontend flag false by default | PASS | `publicFeatureFlag.ts`; tests 1-4, 38 |
| Exact genetic groups only | PASS | Options constant; tests 6-10 |
| No breed inference/default | PASS | Reset logic; tests 8-9 |
| No silent candidate weather defaults | PASS | Conditional initial values; test 43 |
| Existing v1 remains available | PASS | Independent Axios call; tests 5, 27, 35 |
| v2 isolated at correct path | PASS | Typed client; test 16 |
| Optional fields omitted | PASS | Request builder; test 39 |
| Celsius and humidity validation | PASS | Tests 12-14 |
| THI not calculated in frontend | PASS | Tests 15, 42 |
| Stale/cancel protection | PASS | Abort/sequence logic; test 44 |
| DMI unit/material basis | PASS | Tests 17, 19, 33 |
| Milk unit | PASS | Test 18 |
| Rule/ML visual separation | PASS | Tests 20, 28, 34, 48 |
| Null stays unavailable | PASS | Tests 21, 47 |
| Backend disabled | PASS | Test 22 and controlled Flask response |
| Unknown group | PASS | Test 23 and controlled Flask response |
| Invalid environment | PASS | Test 24 and controlled Flask response |
| Local limited support | PASS | Test 25 and controlled Flask response |
| Partial target | PASS | Test 26 |
| Candidate transport failure | PASS | Tests 27, 46 and loopback-unavailable check |
| Required candidate warnings | PASS | Tests 29-30, 40, 49 |
| No model artifact in frontend | PASS | Test 37 |
| Responsive source patterns | PASS WITH LIMITATION | Responsive grids, wrapping, and `min-w-0`; authenticated visual pass deferred |

## Controlled backend responses

| Scenario | Status | Scope/fallback | Result |
|---|---|---|---|
| Backend disabled | `DISABLED` | `FEATURE_DISABLED` | Null targets retained |
| HF50, 28 C, 75% | `ELIGIBLE` | `IN_SCOPE`, T1 | Separate finite DMI/milk |
| Local, 28 C, 75% | `ELIGIBLE` | `LIMITED_SUPPORT`, T1 | Local warning present |
| Dry cow | `FALLBACK_REQUIRED` | `POPULATION_OUT_OF_SCOPE` | Null targets |
| Unknown group | `FALLBACK_REQUIRED` | `GENETIC_GROUP_UNKNOWN` | Breed not substituted |
| Humidity 101 | `FALLBACK_REQUIRED` | `ENVIRONMENT_INVALID` | No THI/targets |

The frontend does not implement or duplicate these eligibility or THI rules;
the controlled responses are used only to verify rendering behavior.
