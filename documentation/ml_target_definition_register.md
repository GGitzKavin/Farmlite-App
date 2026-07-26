# FarmLite ML Target Definition Register

## Purpose

This register separates what the CSV columns demonstrably contain from what
FarmLite would like them to mean. A name, plausible numeric range, or historical
training script is not an authoritative target definition.

The publisher declares the source dataset synthetic. These columns may be
specified as prototype ML targets, but their detailed assignment formulas and
real-world measurement interpretations remain unverified. No training is
approved during Phase 2.

## Target 1 — Feed_Type

| Field | Current evidence |
|---|---|
| Exact dataset column | `Feed_Type` |
| Data type | String/categorical |
| Unique values | `Concentrates`, `Crop_Residues`, `Dry_Fodder`, `Green_Fodder`, `Hay`, `Mixed_Feed`, `Pasture_Grass`, `Silage` |
| Proposed ML task | Multiclass classification for an ML demonstration |
| Who assigned the label | `NOT_PROVIDED` |
| When the label was assigned | `NOT_PROVIDED` |
| Represents feed supplied | `NOT_ESTABLISHED` |
| Represents expert recommendation | **No verified evidence** |
| Represents an optimal feed | **No verified evidence** |
| Represents a broad category | Yes for the prototype contract; the values are broad category labels |
| Multiple feed types can occur simultaneously | `UNCLEAR` |
| Categories are mutually exclusive in reality | `UNCLEAR`; the table stores one value per row, but storage format does not prove real-world exclusivity |
| Farmer would know this before prediction | `UNCLEAR`; the current FarmLite form does not request feed type |
| System is expected to recommend it | The prototype may predict the synthetic category, but must not call it veterinarian-recommended or nutritionally optimal |
| Definition source | Kaggle publisher declaration establishes synthetic origin; detailed label-generation definition is `NOT_PROVIDED` |
| Current status | **CATEGORY_ONLY** |

### Evidence and decision

Every row has exactly one of eight near-balanced class labels, and no duplicate
spellings were found. The verified source clarification permits these values to
be treated as **synthetic feed-type labels** for prototype classification. It
does not show how the label was generated or establish expert recommendation.

`VERIFIED_RECOMMENDATION_TARGET` and `VERIFIED_OBSERVED_USAGE_TARGET` remain
unsupported. `CATEGORY_ONLY` is selected to prevent the prototype prediction
from being misrepresented as a nutritional prescription.

Information required to change the status:

1. an original data dictionary or creator statement defining `Feed_Type`;
2. the label assignment process and timing;
3. confirmation of whether labels are observations or recommendations;
4. confirmation of whether multiple categories may apply to one animal at the
   same time;
5. evidence that the categories are nutritionally defensible outputs for
   FarmLite's intended dairy-cattle scope.

## Target 2 — Feed_Quantity_kg

| Field | Current evidence |
|---|---|
| Exact dataset column | `Feed_Quantity_kg` |
| Data type | Floating-point numeric |
| Proposed ML task | Regression against a synthetic feed-quantity target |
| Observed range | 3.0-25.0 |
| Material represented | `NOT_PROVIDED` |
| Fresh-matter or dry-matter basis | `UNCLEAR` |
| Daily, weekly, per-meal, or other period | `UNCLEAR` |
| Includes roughage | `UNCLEAR` |
| Includes concentrate | `UNCLEAR` |
| Includes mineral supplements | `UNCLEAR` |
| Measurement method | Synthetic generation; detailed formula `NOT_PROVIDED` |
| Definition source | Kaggle publisher declaration establishes synthetic origin; detailed target definition is `NOT_PROVIDED` |
| Current status | **UNCLEAR** |

### Evidence and decision

The column has 250,000 non-missing values, 221 unique values, no zero or
negative values, mean 12.0152, median 12.0, and range 3.0-25.0. Its Pearson
correlations are approximately -0.0022 with `Weight_kg`, 0.0416 with
`Milk_Yield_L`, and 0.0407 with `Previous_Week_Avg_Yield`.

The publisher declaration establishes that this is a **synthetic
feed-quantity target**. The statistics do not reveal whether the value is total fresh feed, dry
matter intake, concentrate, roughage, another ration component, feed per meal,
or another quantity. The `kg` suffix establishes only a mass unit, not its
material basis or period.

Information required to change the status:

1. the exact material included in the measurement;
2. the time period;
3. fresh-matter versus dry-matter basis;
4. treatment of roughage, concentrate, minerals, refusals, and wastage;
5. measurement or generation method;
6. whether the value is an observed quantity, prescribed quantity, or
   optimized quantity;
7. the label's availability and timing relative to all proposed features.

## Target 3 — Milk_Yield_L

| Field | Current evidence |
|---|---|
| Exact dataset column | `Milk_Yield_L` |
| Data type | Floating-point numeric |
| Proposed ML task | Regression against a synthetic milk-yield target |
| Observed range | 0.0-36.42 |
| Daily, weekly, per-milking, or other period | `UNCLEAR` |
| Zero means genuinely no production | `UNCLEAR`; 5,940 rows contain zero |
| Measurement method | Synthetic generation; detailed formula `NOT_PROVIDED` |
| Definition source | Kaggle publisher declaration establishes synthetic origin; detailed target definition is `NOT_PROVIDED` |
| Current status | **UNCLEAR** |

### Evidence and decision

The publisher declaration establishes that this is a **synthetic milk-yield
target**. The name establishes litres but not a period. The column contains 250,000
non-missing values, mean 8.7226, median 7.62, 5,940 zero values, and no negative
values. Its Pearson correlation with `Previous_Week_Avg_Yield` is approximately
0.9684.

The strong lag relationship does not define the period or prove observational
collection. Zero could mean no production, a dry animal, a censored value, a
clipped generated result, or another condition.

Information required to change the status:

1. daily, weekly, per-milking, or other measurement period;
2. meaning of zero;
3. measurement instrument or generation formula;
4. whether `Previous_Week_Avg_Yield` uses the same unit and period;
5. outcome timing relative to feed, disease, and physiological fields;
6. proof that the selected records represent the intended dairy-cattle
   population.

## Current Decision

| Target | Current status | Training implication |
|---|---|---|
| `Feed_Type` | `CATEGORY_ONLY` | Contract may define prototype classification; no Phase 2 training |
| `Feed_Quantity_kg` | `UNCLEAR` | Contract may define synthetic-target regression with explicit unit-basis limitation; no Phase 2 training |
| `Milk_Yield_L` | `UNCLEAR` | Contract may define synthetic-target regression with explicit period limitation; no Phase 2 training |

The source and synthetic status are now verified. The registers should be
updated again if the publisher supplies generation formulas, label assignment,
measurement-period definitions, a data dictionary, or license clarification.
