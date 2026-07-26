# Rwanda Interim Data-Cleaning Specification

This is a proposal only. No cleaned dataset, corrected cell, imputed value, normalized label, or processed Rwanda file was created.

| Field | Issue | Proposed action | Evidence required | Reversible | Data-loss risk | Approval required |
|---|---|---|---|---|---|---|
| cowageinyears | 30 breed-text values; 2 missing | Preserve original. Set cleaned numeric value missing only after approval if corrected ages cannot be supplied. | Corrected workbook or author response | YES | MEDIUM | YES |
| leftover | 28 negative values | Preserve signed source value; do not transform. | Author-defined sign and collection convention | YES | HIGH | YES |
| LabN° | Three repeated keys; six duplicate occurrences | Preserve. Add occurrence index only after record/sample meaning is confirmed. | Sample-sharing and row-identity clarification | YES | MEDIUM | YES |
| DMIcapacity (kgDM) | Conflicting capacity/intake formulas | Preserve source. Add separately named recalculated fields and formula-validation status only after approval. | Approved target definition and formula | YES | HIGH | YES |
| waterday | Consumed versus provided wording | Preserve source; provisional canonical mapping only to water_provided_l_cow_day. | Owner confirmation of collection scope | YES | MEDIUM | YES |
| waterrequi.; gapwater | Missing and inconsistent calculated values | Preserve source and add recalculated value plus validation status separately. | Formula approval and corrected rows | YES | LOW | YES |
| NDF feeds | Unit conflict | Do not convert or rename until unit is approved. | Author/data dictionary confirmation | YES | HIGH | YES |
| CPmilk; gapCP | Formula mismatches and metadata contradiction | Preserve source; version any future recalculation. | Approved CP equations and corrected values | YES | MEDIUM | YES |
| MEfeeds; ME requirement fields | Missing G24 plus inconsistent/missing calculated values | Preserve source; do not impute or recompute as final. | G24 data, formula provenance and corrected workbook | YES | HIGH | YES |
| SAMPLE ID | Raw ingredient spelling and no quantities | Preserve text. Create expert-reviewed vocabulary only in a later approved phase. | Expert mapping and ingredient quantities | YES | MEDIUM | YES |

## Required Future Audit Columns

- `source_file`
- `source_sheet`
- `source_row_number`
- `original_value`
- `cleaned_value`
- `cleaning_reason`
- `approval_reference`

Source values must remain immutable, and recalculated fields must never overwrite them.
