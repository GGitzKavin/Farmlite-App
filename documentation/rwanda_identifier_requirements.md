# Rwanda Identifier and Grouping Requirements

## Required Future Identifiers

| Identifier | Why it is required | Current availability |
|---|---|---|
| `cow_id` | Detect repeated animals and prevent animal-level leakage. | `NOT_AVAILABLE` |
| `farm_id` | Group shared management, diet and environmental conditions. | `NOT_AVAILABLE` |
| observation/collection date | Establish temporal order, season and repeat visits. | `NOT_AVAILABLE` |
| sample identifier | Trace laboratory and composite-feed evidence. | `LabN°` / `Lab N°` |
| repeated-visit identifier | Distinguish visits when the same animal is sampled again. | `NOT_AVAILABLE` |

## Existing Field Assessment

| Existing field | Permitted role | Prohibited role |
|---|---|---|
| `LabN°` / `Lab N°` | Composite feed/laboratory sample identifier with limitations. | Cow or farm identifier without written confirmation. |
| `sites` | Lowland/highland site category only. | Farm, household or animal identifier. |
| source row number | Traceability within the supplied workbook. | Biological identity. |

The cow workbook contains 90 unique `LabN°` values for 96 rows. Three sample
numbers repeat, producing six duplicate occurrences. The fodder workbook has
97 unique sample keys, including seven without a cow-workbook match. These
patterns cannot establish whether samples are shared diets, duplicated animals,
or repeated collections.

## Consequences if IDs Remain Unavailable

- Row-level random splitting may leak repeated-animal or farm information.
- Grouped validation cannot be guaranteed.
- External-validity and performance claims must be limited.
- The study-reported 96 cows and 96 farms cannot be independently verified.
- Leave-one-out or repeated cross-validation is acceptable only after row
  independence is confirmed; neither method repairs hidden grouping.

## Specific Information Request

Please confirm whether each row is one distinct cow, whether each cow belongs
to a distinct farm, whether any cow appears more than once, whether `LabN°`
identifies a cow/farm/sample/composite feed, and whether the six duplicate
occurrences represent duplicated animals, shared diets, or repeated samples.

## Status

`WAITING_FOR_DATA_CLARIFICATION`
