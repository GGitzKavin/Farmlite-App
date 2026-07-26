# Bangladesh DMI and FarmLite Nutrition-Rule Boundary Review

## Inspected Rule Surfaces

- `ml/inference/feed_planner.py` — active advisory feed-planning rules.
- `ml/validation/nutrition_rules.py` — future feed-prediction completeness
  boundary.
- `api/routes.py` — current weight/milk total-feed calculation.

No file was modified.

## Current Calculation Chain

The current route calculates:

```text
base_feed_kg = weight_kg * 0.025
milk_support_feed_kg = predicted_milk_yield_l * 0.30
estimated_total_feed_kg = base_feed_kg + milk_support_feed_kg
```

The feed planner then:

- bounds total feed to 1.5–4.0% of body weight;
- chooses roughage/concentrate ratios from milk-yield bands;
- moves 10% of concentrate to roughage for selected health states;
- assigns 0.05 or 0.10 kg mineral mix from a body-weight threshold;
- returns generic free-access water advice;
- chooses two or three feedings from milk yield.

The future validation module lists both `total_feed_kg` and
`dry_matter_intake_kg` as distinct required fields. This supports, rather than
removes, the material-basis distinction.

## Rule Dependency Matrix

| Current output/rule | Depends on total feed | Depends on predicted milk | Independent inputs | Unit/basis finding |
|---|---:|---:|---|---|
| `totalFeedKg` | It is the bounded total | Yes, current route adds `0.30 × milk` | Body weight | Label is kg; dry-matter versus as-fed basis is `UNRESOLVED` |
| Roughage kg | Yes, ratio of total | Yes, milk chooses ratio | Health can reallocate | Same unresolved basis as total |
| Concentrate kg | Yes, ratio of total | Yes, milk chooses ratio | Health can reallocate | Same unresolved basis as total |
| Mineral mix kg | No | No | Body-weight threshold | Numeric unit is kg, but nutritional adequacy is not validated |
| Water advice | No | No | None | General text only, not a calculated water requirement |
| Feeding frequency | No direct quantity dependency | Yes, >25 L selects three feedings | None | Rule-generated schedule text |
| Warnings/confidence | Uses clamping/fallback/health state | Indirectly | Weight and health | Rule/system metadata |

## Can Predicted DMI Replace `totalFeedKg`?

`NO`.

Bangladesh DMI is kg of dry matter per cow per day. Current `totalFeedKg`,
roughage kg, and concentrate kg do not declare whether they are dry matter or
fresh/as-fed mass. Substitution would silently change material basis.

At minimum, conversion from dry matter to as-fed mass requires:

```text
as_fed_kg = dry_matter_kg / dry_matter_fraction
```

That requires an approved dry-matter fraction (or moisture percentage) for
each feed/ingredient and a ration allocation. FarmLite currently has neither
in this request/model contract.

## Required Conversions and Missing Inputs

| Desired result | Required conversion or rule | Missing/unclear input | Current status |
|---|---|---|---|
| Total as-fed feed from DMI | Divide allocated DM by each ingredient's DM fraction | Feed ingredients, amount shares, moisture/DM percentage, loss/refusal basis | `BLOCKED` |
| Roughage as-fed kg | Allocate DMI to roughage DM, then divide by roughage DM fraction | Approved roughage ratio on DM basis and roughage moisture | `BLOCKED` |
| Concentrate as-fed kg | Allocate DMI to concentrate DM, then divide by concentrate DM fraction | Approved concentrate ratio on DM basis and concentrate moisture | `BLOCKED` |
| Mineral inclusion | Decide whether mineral is inside or additional to DMI and specify DM contribution | Mineral formulation, unit, inclusion rule | `UNRESOLVED` |
| Water requirement | Use an independently validated formula and inputs | Intake basis, temperature/production inputs, formula approval | Current output is advice only |
| Milk-adjusted ration | Define whether DMI already reflects milk-associated intake before adding milk support | Causal/temporal nutrition design and formula | `BLOCKED` |
| Feed/ration category | Expert-approved ration selection logic or labels | Feed inventory composition and nutrition targets | `BLOCKED` |

## Double-Counting Risks

Double counting occurs if:

- predicted DMI is treated as base total feed and the current
  `weight × 0.025` quantity is added again;
- `milk × 0.30` is added to a DMI prediction that already reflects the study's
  milk-associated intake;
- mineral quantities are added without defining whether they are included in
  total dry matter;
- roughage and concentrate are computed from DMI and then also added to DMI as
  separate totals.

No such combination is approved.

## Safe Phase 5 Boundary

- Return Bangladesh DMI only as `dmi_kg_day` with explicit dry-matter units.
- Do not feed it into the current `estimated_total_feed_kg` chain.
- Keep rule fields in a separate object with explicit value sources.
- Return null/unavailable for a new DMI-dependent ration until the conversion
  contract is approved.
- Existing legacy rule results, if preserved temporarily, must name their
  existing milk/weight source and must not be described as derived from the
  Bangladesh DMI model.

## Final Nutrition Decision

`DMI_TO_CURRENT_TOTAL_FEED_INTEGRATION_BLOCKED`

The Bangladesh DMI model can support a standalone research prediction design,
but it does not provide full Option B feed/ration support.
