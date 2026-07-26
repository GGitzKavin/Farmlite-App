# Phase 5 nutrition isolation verification

Result: PASS.

The v2 Bangladesh path imports no feed-planning or nutrition-rule module.
`bangladesh_model_service.py` returns a fixed null-only
`rule_recommendation` object and exposes DMI only as
`ml_predictions.dmi_kg_day` with unit `kg dry matter/cow/day`.

No DMI-to-roughage, DMI-to-concentrate, dry-matter-to-as-fed conversion,
ingredient allocation, moisture inference, mineral recommendation, water
advice, or feeding-frequency calculation is present.

Focused test 37 mocks `ml.inference.feed_planner.generate_feed_plan` and
confirms it is never called by an enabled eligible v2 request. Tests 35 and
36 confirm no `totalFeedKg` field exists and all rule fields remain null.

Protected SHA-256 values remained:

- `ml/inference/feed_planner.py`:
  `27C17A8DBDF8111FC961DD4DF06CB51201C7C480600494AA52D871C777B72F2A`
- `ml/validation/nutrition_rules.py`:
  `3D7A4448EF66409C2D53B9EA97DE725915E53060D71A9DF619E28B9F6DADEC4C`

Phase 5 did not modify the frontend or PDF source.
