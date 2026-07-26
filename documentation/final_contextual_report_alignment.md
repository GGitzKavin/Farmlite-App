# FarmLite Final Contextual Report Alignment

Date: 2026-07-26

## Purpose

This document supplies the final claim set that the contextual report,
proposal, presentation and submission forms should use. Historical phase
documents remain evidence of earlier decisions; this final alignment
supersedes older high-level descriptions where they conflict.

## Approved system description

> FarmLite is an implemented AI-assisted livestock management and
> decision-support system. It combines livestock records, vaccination
> management, milk-yield estimation, dry-matter-intake estimation,
> environmental heat-stress calculation and rule-based ration guidance. The
> current release operates within a declared supported model scope and fails
> safely when required inputs or supported conditions are unavailable.

Do not describe the complete application as only a prototype or only a model
experiment. It is an implemented integrated system. Individual candidate
models may still be described as candidate-only where technically accurate.

## Claim alignment

| Topic | Final aligned statement |
|---|---|
| Complete feeding plan | FarmLite does not use a Hugging Face or generative model to directly create the complete plan |
| Milk | The FarmLite milk prediction model supplies the one farmer-facing expected milk value |
| DMI | The collected-data DMI model supplies dry-matter intake in kg DM/cow/day |
| THI | The backend calculates THI and its category |
| Ration | The FarmLite nutrition rule engine calculates ration quantity/composition and advice |
| Second milk candidate | Internal evaluation only; absent from farmer UI/PDF and never averaged |
| Genetic group | Supplied explicitly; never inferred from breed |
| DMI conversion | DMI is not converted into total/fresh feed, roughage or concentrate |
| Missing/unsupported inputs | Fail safely; unavailable is not replaced with zero |
| Feature flags | Backend and frontend paths are independently disabled by default |
| Model scope | Supported lactating-cow cases only, with Local marked limited support |
| Validation | Integrated tests passed; external universal/veterinary/commercial validation is not claimed |

## Data-source wording

For the retained synthetic source use:

> Kaggle Cattle Health and Feeding Data; publisher-declared synthetic dataset.

For the collected DMI research source use:

> Mendeley Data, DOI: 10.17632/954f6g36sb.2.

Farmer-facing headings should use **FarmLite milk prediction model**,
**Collected-data DMI model**, **Backend THI calculation** and **FarmLite
nutrition rule engine**. Do not use a country, nationality or region as a
farmer-facing dataset/model name.

## Results and evaluation wording

Acceptable:

- “The integrated repository passed 105 frontend and 308 backend automated
  tests.”
- “Controlled supported inputs produced deterministic milk, DMI, THI and
  advisory-ration outputs.”
- “The PDF contract produced valid non-empty two-page buffers.”
- “The collected-data DMI model requires wider independent multi-farm
  validation.”

Avoid:

- “The AI generates the complete optimal ration.”
- “The model is universally accurate.”
- “The system is veterinary approved.”
- “DMI equals total feed.”
- “Breed automatically identifies genetic group.”
- “The second model confirms or averages the farmer milk result.”
- “The system has complete production security approval.”

## Evaluation numbers

Test and performance numbers belong in the methodology/evaluation chapter,
not as unrestricted accuracy claims:

- frontend tests: 105/105;
- backend tests: 308/308;
- typecheck/build/compileall: pass;
- local warm v1 mean: 3.297 ms over five requests;
- local warm v2 mean: 3.374 ms over five requests;
- farmer PDF generation mean: 6.564 ms over five samples;
- production bundle: 2,018,272 uncompressed bytes;
- repository ESLint: six inherited findings.

These timings are local engineering measurements, not deployment SLAs.

## Limitations paragraph

Use a visible limitations paragraph substantially equivalent to:

> The current release is intended for academic submission and controlled
> decision-support evaluation. The retained milk model uses
> publisher-declared synthetic source data, while the collected-data DMI
> model has limited source-study scope and requires independent multi-farm
> validation. FarmLite does not replace veterinary or qualified nutrition
> advice. Production deployment additionally requires verified Firestore
> Security Rules, authenticated API controls, browser accessibility testing
> and approved dependency-security review.

## Contextual report availability

No completed contextual-report document was present under
`documentation/contextual_report/` during Phase 7. Alignment was therefore
performed against the repository, tests, phase approval records and final
Phase 7 brief. The report author must copy these final claims into the actual
submission document and remove conflicting historical wording.
