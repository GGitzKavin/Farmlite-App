# Phase 6 PDF validation

Date: 2026-07-26
Result: PASS

## Checks

| Requirement | Result | Evidence |
|---|---|---|
| Existing v1-only PDF still generates | PASS | Focused test 31 |
| Candidate section is optional | PASS | Guarded helper call |
| Candidate DMI has exact dry-matter unit | PASS | Focused tests 32, 47 |
| Candidate milk has exact daily unit | PASS | Focused test 32 |
| THI uses backend response | PASS | Helper reads `environment.calculated_thi` |
| Genetic group supplied is included | PASS | Helper data-shape test |
| Model source and scope included | PASS | Helper rows and test 34 |
| Warnings/limitations included | PASS | Catalogue/backend list iteration |
| Research prototype / not veterinary advice | PASS | Introductory research text |
| Null/NaN/undefined not printed | PASS | Formatter and test 47 |
| No DMI-to-ration conversion | PASS | Source inspection and test 33 |
| Existing ML/rule sources labelled separately | PASS | Test 48 |
| Margins/wrapping/page breaks retained | PASS | Existing shared writer helpers |
| Real PDF bytes produced | PASS | jsPDF tests 31 and 41 |

No PDF rendering dependency is installed. The manual check therefore used a
real jsPDF output buffer, page-aware writer source inspection, and
deterministic data-shape assertions. Visual inspection with authenticated
sample data remains a Phase 7 check.
