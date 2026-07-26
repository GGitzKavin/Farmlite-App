# Rwanda Fodder Sample Limitations

## What the Workbook Contains

- 97 rows with unique `Lab N°` keys.
- One raw text field listing fodder ingredients in each composite sample.
- Seven sample keys without a matching cow-workbook row.
- Ingredient spelling, case, and repeated-token inconsistencies.

## What It Does Not Contain

- Ingredient weights, proportions, inclusion percentages or offered quantity.
- Ingredient-specific DM, CP, ME, NDF or mineral values.
- Validated roughage/concentrate categories.
- Farm IDs, cow IDs, dates or collection periods.
- Nutritionist-approved or optimized ration labels.

Ingredient strings can be tokenized for traceability only. Ingredient presence
does not establish amount, and a composite diet cannot be reconstructed without
proportions. Mineral-mix quantity, roughage percentage and concentrate
percentage therefore cannot be derived.

## Cross-File Nutrient Relationship

`Lab N°` can link ingredient-list text to composite nutrient values stored in
the cow workbook. This remains `POSSIBLE_WITH_LIMITATIONS`: all 96 cow rows
match a fodder key, but three cow-side keys repeat and sample-sharing semantics
are unknown. Nutrient values must not be created from ingredient names.

## Status

`PARTIALLY_COMPATIBLE` for observed composite-sample lookup only.
`NOT_COMPATIBLE` for ration reconstruction or recommendation labels.
