# FarmLite Dairy-Cattle Filter Definition Register

## Current Status

**BLOCKED — no documented dairy-only filtering rule exists.**

The main CSV has `Breed` and `Lactation_Stage`, but no `Species`,
`Production_Type`, `Cattle_Type`, or equivalent authoritative scope field. The
repository does not contain an original breed-purpose mapping or dataset data
dictionary.

The names of some breeds may look familiar, but Phase 1.5 permits only
repository-documented classifications. Therefore every breed remains
`UNKNOWN`, and none is currently safe to include in a claimed dairy-only
training subset.

## Breed Register

| Breed | Record count | Known purpose from dataset | Proposed category | Evidence source | Safe to include |
|---|---:|---|---|---|---|
| Africander | 6,310 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Ankole | 6,330 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Australian_Friesian_Sahiwal | 6,230 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Australian_Milking_Zebu | 6,297 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Ayrshire | 6,206 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Boran | 6,245 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Brown_Swiss | 6,244 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Butana | 6,242 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Danish_Red | 6,422 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Deoni | 6,026 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Exotic_Local_Cross | 6,250 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Fleckvieh | 6,410 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Gangatiri | 6,340 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Gir | 6,251 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Girolando | 6,387 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Guernsey | 6,246 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Hariana | 6,201 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Holstein-Friesian | 6,227 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Holstein_Zebu_Cross | 6,253 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Illawarra_Shorthorn | 6,142 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Jersey | 6,149 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Jersey_Zebu_Cross | 6,240 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Kankrej | 6,173 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Kenana | 6,341 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Krishna_Valley | 6,291 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Milking_Shorthorn | 6,119 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Montbeliarde | 6,282 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| NDama | 6,189 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Normande | 6,130 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Norwegian_Red | 6,214 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Ongole | 6,286 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Rathi | 6,164 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Red_Poll_Africa | 6,439 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Red_Sindhi | 6,146 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Sahiwal | 6,283 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Simmental | 6,196 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Tharparkar | 6,361 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Tipo_Carora | 6,311 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| White_Fulani | 6,112 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |
| Zebu_Cross_Brazil | 6,315 | `NOT_PROVIDED` | `UNKNOWN` | No repository-local breed-purpose definition | No |

Record counts total 250,000.

`Safe to include: No` means “not yet justified for a documented dairy-only
subset.” It does not claim that the breed is non-dairy.

## Lactation Evidence

The dataset contains only these `Lactation_Stage` labels:

- `Early`
- `Mid`
- `Late`

Every row has one of these values, but there is no locally documented
`Dry`, `Non_Lactating`, or equivalent category. The labels therefore do not
prove that all animals were genuinely lactating or that non-lactating records
were excluded.

## Candidate Filtering Strategies

### 1. Include all records

- Benefit: preserves all 250,000 rows.
- Problem: contradicts a dairy-only claim because production purpose is not
  documented.
- Current acceptability: **Not acceptable for a final dairy-only model.**

### 2. Include only documented dairy breeds

- Benefit: would provide the clearest dairy-only subset.
- Problem: there are currently zero breeds with repository-local documentary
  evidence sufficient for classification.
- Required evidence: an authoritative dataset data dictionary, creator-provided
  breed-purpose mapping, or a separately approved scholarly mapping.
- Current acceptability: **Cannot yet be applied.**

### 3. Include dairy and dual-purpose breeds

- Benefit: could increase sample size while keeping a milk-production scope.
- Problem: neither dairy nor dual-purpose classifications are documented
  locally, and the inclusion policy would require a defensible dissertation
  rationale.
- Current acceptability: **Cannot yet be applied.**

### 4. Add a production-purpose input

- Benefit: could enforce dairy scope directly in future data and in the
  application.
- Problem: the current CSV and FarmLite feed-recommendation request do not
  provide an authoritative production-purpose value. Adding an application
  field would not retrospectively label these rows.
- Current acceptability: **Possible future design, not a current filter.**

### 5. Obtain a different dairy-only dataset

- Benefit: avoids uncertain breed inference if the replacement has documented
  dairy scope, collection method, target definitions, and license.
- Problem: requires dataset discovery and a new audit.
- Current acceptability: **Viable resolution path; no replacement selected.**

## Evidence Required to Approve a Filter

1. A documented production-purpose field or a source-backed mapping for all
   included breeds.
2. A rule for crossbred, local, dual-purpose, and unknown categories.
3. Confirmation that `Lactation_Stage` and `Days_in_Milk` are genuine and
   consistently defined.
4. A decision on whether dry or non-lactating cattle are supported.
5. The same scope rule implemented consistently during training, backend
   validation, frontend selection, and evaluation.

No filtering strategy is selected or applied in Phase 1.5.
