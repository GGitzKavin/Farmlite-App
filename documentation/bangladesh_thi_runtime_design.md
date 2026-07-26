# Bangladesh THI Runtime Design

## Review Decision

The article formula, input units, model labels, and category boundaries are
locally documented. Automatic mapping is therefore
`DESIGN_APPROVED_RUNTIME_NOT_AUTHORIZED`, with limitations. The proposed
machine-readable definition is
`backend/flask_api/config/bangladesh_thi_mapping_contract.json`.

The source workbooks contain only category labels, not numeric temperature,
humidity, or THI. The mapping cannot be reproduced against the 750 historical
rows, and the study's observed numeric environmental ranges are `UNRESOLVED`.

## Proposed Transformation

```text
measured ambient_temperature_c
  + measured humidity_percent
  -> validate units and finite values
  -> calculate unrounded THI
  -> apply exact category boundary
  -> return calculated THI + category + evidence/version
```

Use dry-bulb temperature `T` in degrees Celsius and relative humidity `RH` in
percent:

`THI = (1.8 × T + 32) − [(0.55 − 0.0055 × RH) × (1.8 × T − 26)]`

Source: related article DOI `10.1016/j.anopes.2026.100139`, also recorded in
the Bangladesh dataset inventory and methodology summary.

## Exact Category Policy

| Category | Boundary |
|---|---|
| `T0` | THI ≤ 75 |
| `T1` | 75 < THI < 80 |
| `T2` | THI ≥ 80 |

Calculate and categorize with unrounded values. A display may show a rounded
THI only after category assignment.

- THI exactly 75 is `T0`.
- The next representable value above 75 and every value below 80 is `T1`.
- THI exactly 80 is `T2`.

The client must not choose `thi_category` directly. The server is the only
proposed owner of the derived category.

## Invalid and Missing Inputs

| Condition | Eligibility result | Behavior |
|---|---|---|
| Temperature missing | `MISSING_REQUIRED_INPUT` | Do not calculate or predict; require fallback |
| Humidity missing | `MISSING_REQUIRED_INPUT` | Do not calculate or predict; require fallback |
| Non-numeric/non-finite temperature | `INVALID_ENVIRONMENT_INPUT` | Reject candidate inference |
| Non-numeric/non-finite humidity | `INVALID_ENVIRONMENT_INPUT` | Reject candidate inference |
| Humidity below 0% or above 100% | `INVALID_ENVIRONMENT_INPUT` | Reject candidate inference |
| Calculation failure or non-finite THI | `INVALID_ENVIRONMENT_INPUT` | Reject candidate inference |
| Derived category outside `T0/T1/T2` | `UNKNOWN_THI_CATEGORY` | Reject before pipeline; require fallback |
| Client sends category directly | Validation error | Ignore no value silently; require measured inputs |

The current React and backend defaults of 28 °C and 70% must not be reused for
this adapter. Missing weather is not measured weather.

## Unrealistic Temperature

The study's numeric temperature range is unavailable. A study-derived minimum
or maximum would be invented, so the numeric support boundary is
`UNRESOLVED`. Phase 5 must define product-level physical sensor/input
validation separately and document its authority. Until then:

- require a finite Celsius number;
- never claim that a numeric temperature is inside the study distribution;
- return the categorical-environment limitation on every prediction;
- do not fabricate a study range.

## Unknown Encoder Behavior

Both fitted encoders use `handle_unknown="ignore"`. That only prevents a
technical exception; it does not make an unseen category scientifically
supported. The request adapter must reject unsupported categories before
calling the pipeline.

## Evidence Failure Policy

If a later code version cannot load the formula reference, exact thresholds,
or learned category labels—or if those sources conflict—automatic mapping is
`BLOCKED`. It may not guess thresholds or reuse arbitrary heat-stress bands.

## Traceability Required in Phase 5

A response using the mapping must expose:

- raw validated temperature and humidity;
- unrounded internal THI (returned at documented precision);
- derived `T0`, `T1`, or `T2`;
- mapping-contract version;
- formula DOI;
- warning that historical numeric environment reproduction was impossible.
