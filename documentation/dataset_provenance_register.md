# FarmLite Dataset Provenance Register

## Purpose and Evidence Boundary

This register records only evidence available locally in the FarmLite
repository and in filesystem metadata attached to the two local CSV files. No
internet search was performed.

The Windows `Zone.Identifier` streams provide meaningful download-origin
evidence that was not visible to the text-only Phase 1 search. Phase 2 also
records the project owner's verified Kaggle clarification: the dataset is
**Cattle Health and Feeding Data**, published under the Kaggle account
**ShahHet2812**, and the publisher declares it synthetically generated.

The source page is:
`https://www.kaggle.com/datasets/shahhet2812/cattle-health-and-feeding-data`.

This verifies source identity and synthetic status. It does not establish a
detailed generation methodology, scientific validation, real-world
representativeness, target measurement protocols, or license terms.

The signed query strings include temporary credentials and signatures. This
register records the stable storage path and timestamp parameters but does not
copy the expiring signature.

## Dataset Identification

### Milk-yield dataset

- Dataset name: `Cattle Health and Feeding Data`
- Platform: Kaggle
- Publisher/account: `ShahHet2812`
- Current filename:
  `global_cattle_milk_yield_prediction_dataset.csv`
- Original filename if known:
  `global_cattle_milk_yield_prediction_dataset.csv` (confirmed by local
  download metadata)
- Local path:
  `datasets/raw/global_cattle_milk_yield_prediction_dataset.csv`
- SHA-256:
  `26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3`
- File size: 48,805,186 bytes
- Row count: 250,000
- Column count: 37

### Disease dataset

- Dataset name: `Cattle Health and Feeding Data`
- Platform: Kaggle
- Publisher/account: `ShahHet2812`
- Current filename:
  `global_cattle_disease_detection_dataset.csv`
- Original filename if known:
  `global_cattle_disease_detection_dataset.csv` (confirmed by local download
  metadata)
- Local path:
  `datasets/raw/global_cattle_disease_detection_dataset.csv`
- SHA-256:
  `4CEDFA77234FE45B441E303FF051C33123969E37C3B484A03387094A613DC4B9`
- File size: 54,792,252 bytes
- Row count: 250,000
- Column count: 40

## Local Evidence Found

| Evidence ID | File | Location | Evidence | Interpretation | Confidence |
|---|---|---|---|---|---|
| PE-001 | `datasets/raw/global_cattle_milk_yield_prediction_dataset.csv` | `Zone.Identifier`, lines 1-4 | `ZoneId=3`; `ReferrerUrl=https://www.kaggle.com/`; host path contains `kagglesdsdata/datasets/8274233/13065532/global_cattle_milk_yield_prediction_dataset.csv`; `X-Goog-Date=20260722T215322Z` | A signed download URL was generated through Kaggle infrastructure on 2026-07-22. Dataset storage ID `8274233` and object/version ID `13065532` are locally evidenced. The human-readable dataset page and creator are not present. | HIGH |
| PE-002 | `datasets/raw/global_cattle_disease_detection_dataset.csv` | `Zone.Identifier`, lines 1-4 | `ZoneId=3`; `ReferrerUrl=https://www.kaggle.com/`; host path contains `kagglesdsdata/datasets/8274233/13065532/global_cattle_disease_detection_dataset.csv`; `X-Goog-Date=20260722T215205Z` | The second signed URL uses the same Kaggle storage dataset/object IDs and was generated approximately 77 seconds earlier. This strongly connects the two files to one Kaggle download source. | HIGH |
| PE-003 | Both raw CSV files | NTFS alternate-stream inventory | The only non-default stream on each dataset is `Zone.Identifier` (948 and 944 bytes respectively). | Browser/download metadata exists, but no sidecar README, citation, license, or archive manifest is attached to the files. | HIGH |
| PE-004 | `datasets/README.md` | lines 13-23 | Names both raw files, records 250,000 rows each, and states that provenance, licensing, representativeness, and measurement validity were not independently verified. | Project documentation preserves the local inventory but is not original publisher documentation. | HIGH |
| PE-005 | `notes/dataset_sources.md` | lines 8-13 | States that no authoritative source URL, publisher, license, collection protocol, or data dictionary was then present. | Confirms that the project did not previously capture source and methodology metadata. The newly discovered Kaggle download metadata partially updates only the source-origin portion. | HIGH |
| PE-006 | `notes/dataset_sources.md` | lines 12-26 | Says regular schemas and sequential identifiers may indicate generated data, but this is unproven; limits use to exploratory or educational development. | Supports a cautious generation status and use restriction; it does not prove synthetic generation or grant academic-use permission. | HIGH |
| PE-007 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 30-36 | Phase 1 reported `NOT_DOCUMENTED`, 43 eligible local text files searched, 20 relevant files inspected, and no license or citation files found. | The text-file conclusion remains correct for author, license, citation, and methodology. Its source-origin conclusion is superseded in part by the Phase 1.5 alternate-stream discovery. | HIGH |
| PE-008 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 178-195 | Lists eight `Feed_Type` values and states that the repository does not define whether they are observed, recommended, or generated. | Establishes the column domain but not the label meaning or assignment process. | HIGH |
| PE-009 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 211-321 | Reports `Feed_Quantity_kg` as `TARGET_UNCLEAR`, with range 3.0-25.0, and states that material basis and period are undocumented. | Statistical evidence cannot identify fresh matter, dry matter, ration component, or measurement period. | HIGH |
| PE-010 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 327-398 | Reports `Milk_Yield_L` range 0.0-36.42 and period `UNCLEAR`. | Litres are named, but daily, weekly, per-milking, or other period is not defined. | HIGH |
| PE-011 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 65-86 | Reports 40 breed values, `PARTIALLY_SUITABLE`, no authoritative species/production-purpose field, and no reliable dairy-only filter. | The project scope says dairy cattle, but the dataset provides no locally documented breed-purpose mapping. | HIGH |
| PE-012 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 569-580 | Reports `POSSIBLY_SYNTHETIC`, citing sequential IDs, complete data, balanced categories, and cross-file duplication. | These are generated-data indicators, not conclusive generation-method evidence. | HIGH |
| PE-013 | `backend/flask_api/ml/reports/dataset_inspection_report.md` | lines 691-709 | Reports all 250,000 `Cattle_ID + Date` keys and all 36 shared columns align, with join status `POSSIBLE_WITH_LIMITATIONS`. | Strongly suggests both files derive from the same record base. It does not prove real-animal identity or observational collection. | HIGH |
| PE-014 | `backend/flask_api/ml/reports/feed_model_report.txt` | lines 45-59 | Historical feed regression had R-squared -0.0065; the report says no validated optimal recommendation labels and provenance was unverified. | This is project-generated evaluation evidence, not a target definition. It reinforces that the existing feed-quantity experiment is unsuitable for deployment. | HIGH |
| PE-015 | `backend/flask_api/ml/reports/candidate_model_evaluation_report.txt` | lines 15, 91, 287, and 294 | Warns that the files do not provide validated optimal feed labels and that real-world quality/provenance is unverified. | Historical internal caution is consistent with Phase 1. It is not original dataset documentation. | HIGH |
| PE-016 | `notes/model_scope.md` | lines 3-36 | Declares FarmLite's intended scope as dairy cattle and lists desired targets. | This is a project requirement, not evidence that the CSV records are dairy-only or that the desired targets are defined. | HIGH |
| PE-017 | Repository-wide Phase 1.5 search | Text and special-file inventory | No relevant DOI, Mendeley record, author, publisher, dataset citation, license file, proposal, contextual report, bibliography, ZIP/7z/RAR archive, extraction note, or dataset-page URL was found. GitHub links found locally belong to frontend tooling, not these datasets. | Required source and permission evidence remains absent. | HIGH |
| PE-018 | Project-owner verified clarification | Phase 2 instruction | Dataset name `Cattle Health and Feeding Data`; Kaggle account `ShahHet2812`; source `https://www.kaggle.com/datasets/shahhet2812/cattle-health-and-feeding-data`; publisher declares the data synthetically generated and potentially unrepresentative of real-world data. | Resolves the source page, publisher account, and high-level generation status. Detailed formulas, measurement protocols, license, and scientific validation remain unresolved. | HIGH |

## Source Information

### Milk-yield dataset

- Publisher/account: `ShahHet2812`
- Author's real-world identity: `NOT_PROVIDED`
- Hosting/download platform: Kaggle (verified through local download metadata)
- Source webpage:
  `https://www.kaggle.com/datasets/shahhet2812/cattle-health-and-feeding-data`
- Download URL: an expired signed Kaggle storage URL was locally preserved;
  stable path:
  `https://storage.googleapis.com/kagglesdsdata/datasets/8274233/13065532/global_cattle_milk_yield_prediction_dataset.csv`
- DOI: `NOT_PROVIDED`
- Publication date: `NOT_PROVIDED`
- License: `NOT_PROVIDED`
- Version: Kaggle storage object ID `13065532`; its semantic version meaning is
  `NOT_PROVIDED`
- Download date: 2026-07-22 21:53:22 UTC signed-URL timestamp; exact transfer
  completion time is `NOT_PROVIDED`
- Original archive name: `NOT_PROVIDED`; metadata indicates a direct CSV
  download

### Disease dataset

- Publisher/account: `ShahHet2812`
- Author's real-world identity: `NOT_PROVIDED`
- Hosting/download platform: Kaggle (verified through local download metadata)
- Source webpage:
  `https://www.kaggle.com/datasets/shahhet2812/cattle-health-and-feeding-data`
- Download URL: an expired signed Kaggle storage URL was locally preserved;
  stable path:
  `https://storage.googleapis.com/kagglesdsdata/datasets/8274233/13065532/global_cattle_disease_detection_dataset.csv`
- DOI: `NOT_PROVIDED`
- Publication date: `NOT_PROVIDED`
- License: `NOT_PROVIDED`
- Version: Kaggle storage object ID `13065532`; its semantic version meaning is
  `NOT_PROVIDED`
- Download date: 2026-07-22 21:52:05 UTC signed-URL timestamp; exact transfer
  completion time is `NOT_PROVIDED`
- Original archive name: `NOT_PROVIDED`; metadata indicates a direct CSV
  download

Kaggle is evidenced as the hosting/download platform, not necessarily the
publisher or scientific creator.

## Dataset Generation Method

Status: **SYNTHETIC — PUBLISHER_DECLARED**

The publisher declares that the dataset was synthetically generated and may not
reflect real-world data. The files also have matching local indicators:

- perfectly sequential `Cattle_ID` values;
- no parsed missing cells in 500,000 combined rows;
- unusually balanced categories;
- one observation per animal;
- the same 250,000 composite keys and identical values in all 36 shared
  columns.

The detailed generation formulas, distributions, dependencies, validation
procedure, and measurement protocols are not established. `SYNTHETIC` here
describes publisher-declared origin, not scientific or nutritional validity.

- Scientific validation: **NOT_ESTABLISHED**
- Real-world representativeness: **NOT_ESTABLISHED**
- Intended project use: **PROTOTYPE_AND_ML_PIPELINE_DEMONSTRATION**

## Permitted Academic Use

- License known: **No**
- Attribution requirement: `NOT_PROVIDED`
- Modification permission: `NOT_PROVIDED`
- Redistribution permission: `NOT_PROVIDED`
- Academic-use permission: `NOT_PROVIDED`
- Unresolved restrictions:
  - The Kaggle dataset page and owner must be identified.
  - The license displayed on that page must be captured.
  - Any license conditions for modification, redistribution, model training,
    and dissertation publication must be reviewed.
  - Dataset authorship and required citation must be recorded.

Possession of a downloaded Kaggle file does not itself establish permission to
reuse or redistribute it.

The approved project interpretation permits the data to demonstrate
preprocessing, classification, regression, evaluation, deployment, Flask
inference, React integration, and a hybrid ML/rule architecture. Every such use
must state that the data is synthetic and the system is a prototype. This
project-use decision does not replace confirmation of the Kaggle license for
publication or redistribution.

## Provenance Decision

**VERIFIED_SOURCE_WITH_LIMITATIONS**

Verified:

- both original filenames;
- dataset name `Cattle Health and Feeding Data`;
- Kaggle publisher/account `ShahHet2812`;
- human-readable Kaggle source page;
- Kaggle as the download/hosting platform;
- shared Kaggle storage dataset ID `8274233`;
- shared Kaggle storage object/version ID `13065532`;
- download timestamps;
- publisher-declared synthetic generation status;
- current paths, sizes, checksums, and shapes.

Not verified:

- license and citation;
- author's real-world identity and publication/version description;
- detailed generation methodology;
- population and dairy-only scope;
- label definitions and measurement procedures.

This decision supports a synthetic prototype and ML pipeline demonstration. It
does not authorize real-world claims or model training during Phase 2.
