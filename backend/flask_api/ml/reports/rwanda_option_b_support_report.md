# Rwanda Option B Support Report

## Decision: `PARTIAL_OPTION_B_SUPPORT`

### 1. Better feed-quantity or DMI model?

`BLOCKED_UNCLEAR_DEFINITION`. Daily DMI is documented, but negative leftovers and dual capacity/intake semantics need author correction.

### 2. Daily milk-yield model?

`READY_WITH_LIMITATIONS` using measured hand-milked L/day; small cross-sectional data and missing grouping IDs remain.

### 3. Water-intake prediction?

`READY_WITH_LIMITATIONS`; waterday is L/cow/day but based on jerry cans provided rather than metered drinking.

### 4. CP intake/requirement?

Supports documented calculations/rule validation; not a direct learned requirement.

### 5. Energy intake/requirement?

Supports documented calculations/rule validation with missing G24 reproduction input.

### 6. Roughage/concentrate quantities?

No. Ingredient lists have neither quantities nor validated categories.

### 7. True feed recommendation label?

No. Only observed composite fodders and farmer calf practice.

### 8. Bucket plan ration-selection rule?

No for lactating cows; it is observed calf milk-allocation practice.

### 9. Fodder workbook nutrient calculations?

Partially. It supplies ingredient text; composite nutrient values are in the cow workbook and require a limited LabN join.

### 10. Can files be joined safely?

Cow-to-fodder is `POSSIBLE_WITH_LIMITATIONS`; metadata is semantic; DOCX has no join key.

### 11. Repeated cow observations?

UNCLEAR because cow_id is absent; source methodology says cross-sectional.

### 12. Missing FarmLite inputs?

previous-week yield, body-condition score, ambient temperature, and humidity; numeric age is incomplete.

### 13. Potential future inputs?

parity, site, served DM, leftovers, water intake, and observed ingredient list, subject to timing and quality controls.

### 14. Keep synthetic data in training?

Do not merge it with Rwanda records. Retain it only as a separate historical prototype benchmark.

### 15. Phase 4 redesign priorities?

Redesign milk and water candidates separately; investigate DMI after correction; do not rebuild feed classification without expert recommendation labels.

## Boundary

This is an audit decision only. It does not authorize model training, preprocessing, source merging, frontend changes, nutrition-rule changes, integration, or deployment.
