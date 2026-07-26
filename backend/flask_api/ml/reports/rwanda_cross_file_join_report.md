# Rwanda Cross-File Join Audit

No permanent or processed join was created.

| Left file | Right file | Keys | Cardinality evidence | Match | Safety |
|---|---|---|---|---:|---|
| `Specific data recorded on individual cows under lactation in Rwanda 2020-2021.xlsx` | `Different fodders components in the samples.xlsx` | `LabN°` -> `Lab N°` | 90 unique left keys; 97 unique right keys; 6 left duplicate occurrences | 100.00% | `POSSIBLE_WITH_LIMITATIONS` |
| `Metadata.xlsx` | All sources | Semantic definitions only | No record key | N/A | `NO_VALID_JOIN_KEY` |
| `Bucket feeding plan (Supplemental Table).docx` | Cow/fodder sources | No shared key | Separate calf-practice table | 0% | `NO_VALID_JOIN_KEY` |

## Lab Sample Relationship

- Cow rows: 96.
- Fodder rows: 97.
- Matched cow rows: 96.
- Fodder-only keys: 580, 581, 583, 597, 610, 626, 627.
- Many-to-many risk: False.
- Meaning: Links a cow-level observation to the text list of fodder ingredients for its composite laboratory sample. Repeated LabN° values mean multiple cow rows may share one fodder record.

Although every cow row finds a fodder record, repeated LabN° values conflict with a simplistic one-sample-per-cow assumption. Use only after confirming sample-sharing semantics.
