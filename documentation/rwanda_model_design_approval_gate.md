# Rwanda Model Design Approval Gate

| Gate | Status | Evidence | Blocking issue | Required action |
|---|---|---|---|---|
| Source licence verified | PASSED | Mendeley Data version 1 declares CC BY 4.0. | None for audit/design use with attribution. | Retain DOI and licence attribution. |
| Measured milk target verified | PASSED_WITH_LIMITATIONS | 96 directly measured hand-milked values, 1-17 L/day. | Completeness across all daily milkings is unclear. | Obtain author confirmation. |
| Row independence verified | BLOCKED | No cow, farm, visit, or date fields. | The 96 rows cannot be proven independent. | Obtain identity/collection documentation. |
| Cow grouping available | BLOCKED | `LabN°` is a composite sample key. | No cow_id is supplied. | Obtain cow/farm grouping identifiers. |
| Water target verified | PASSED_WITH_LIMITATIONS | Repository identifies daily water provided. | Consumption and remaining water are unmeasured. | Limit any future target to water provided. |
| DMI target verified | BLOCKED | Two meanings for DMIcapacity; 28 negative leftovers. | Consumed DMI cannot be defended. | Obtain correction and explicit target definition. |
| Age data repair approved | BLOCKED | 30 breed-text and 2 missing age values. | No deterministic numeric recovery. | Obtain corrected ages or owner missing-value decision. |
| Negative leftovers resolved | BLOCKED | Five interpretations remain unselected. | Sign/collection convention is unknown. | Obtain written author clarification. |
| CP formulas reproducible | BLOCKED | CPmilk mismatches 22 rows; gap metadata conflicts. | Requirement and gap definitions need correction. | Approve formula version and corrected values. |
| ME formulas reproducible | BLOCKED | G24 absent; ME-milk mismatch and missing rows. | Composition and requirement chain are incomplete. | Supply G24, equation version and corrected values. |
| NDF unit verified | BLOCKED | Metadata says kg DM; values/repository indicate percent. | Canonical unit is not owner-confirmed. | Obtain explicit unit and basis. |
| Feed recommendation labels available | BLOCKED | Only observed diets and farmer calf practice. | No expert/optimized target labels. | Collect nutritionist-approved ration labels. |
| Model training not executed | PASSED | Clarification validator contains no estimator operations. | None. | Keep training disabled until a new approval. |

## Final Recommendation

`WAITING_FOR_DATA_CLARIFICATION`

No model design is approved as final, and no training is authorized or started.
