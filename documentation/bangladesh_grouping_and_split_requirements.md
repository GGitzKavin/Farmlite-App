# Bangladesh Grouping and Split Requirements

## Verified Observation Hierarchy

50 cows → 3 THI categories/cow → 5 replications/category → 750 rows.

The 750 records are repeated observations from 50 animals; they are not 750 independent cows.

## Mandatory Group Policy

- Keep every observation from a cow in the same fold or partition.
- Never randomly split repeated cow records by row.
- Use `Animal ID` as the grouping field.
- Use GroupKFold, GroupShuffleSplit, leave-one-cow-out, or another documented cow-grouped method.
- Preserve genetic-group and THI-category representation where practical without breaking cow groups.
- Fit every learned preprocessing step only inside the training fold.
- Report unique-cow counts and condition counts in every partition.

## Observation Key

`Animal ID + THI Range + Replication No` is unique inside each workbook. Replication number is not globally unique. No date, timestamp, or standalone observation ID exists.

## Cross-Workbook Restriction

DMI/milk and blood have a complete one-to-one key match. Physiology has only 45 shared cows and 675 matching keys; do not construct a full cross-workbook training table until the five boundary IDs per source are resolved.
