# Rwanda Age Column Analysis

## Counts

- Cow rows: 96
- Numeric ages: 64
- Breed-text entries: 30
- Missing entries: 2
- Unique text entries: 10

## Text Entries

`fresian*jersey`; `fresian*jersey*fresian`; `fresian*sahiwal*fresian`; `fresian*sahiwal*jersey`; `local*fresian`; `local*fresian*fresian*jersey`; `local*fresian*jersey*fresian`; `local*fresian*jersey*jersey`; `local*jersey`; `sahiwal*jersey`

## Repair Investigation

- Other age column: `NONE`
- Displaced age values found elsewhere: `NO`
- Broad row-shift evidence: `NOT_FOUND`
- Exact duplicates of the existing `cowbreed` categories: `NO`
- Existing `cowbreed` values: `Cross; exotic`
- Deterministic repair possible: `NO`
- Values modified: `NO`

The contaminated entries are more detailed cross-breed descriptions than the
broad `Cross/exotic` field. No evidence-supported numeric age can be recovered
from another supplied column.

## Result

Final status: `SOURCE_CORRECTION_REQUIRED`.
