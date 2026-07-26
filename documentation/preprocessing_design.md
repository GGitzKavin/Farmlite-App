# FarmLite Preprocessing Design

## Status

**PHASE_3_IMPLEMENTED_AND_VALIDATED_WITH_LIMITATIONS**

The reusable preprocessing layer, compact split manifest, and training-only
fold manifest were implemented in Phase 3. No prediction model was trained,
evaluated, tuned, fitted, or persisted. No full-data preprocessor was fitted
or saved.

Implemented modules:

- `data_loader.py`: read-only CSV loading and source metadata;
- `column_mapper.py`: deterministic approved-alias mapping;
- `schema_validator.py`: training, inference, and fixture validation modes;
- `data_cleaner.py`: transparent normalization and row-level issues;
- `feature_builder.py`: exact model-specific logical feature views;
- `split_data.py`: deterministic base splits and training-only fold assignment;
- `preprocessing_factory.py`: unfitted sklearn preprocessing factories;
- `preprocessing_types.py`: typed, serializable result structures;
- `validate_preprocessing.py`: end-to-end Phase 3 validation command.

## Principles

1. Read raw files without modifying them.
2. Use the primary milk-yield CSV only for the three proposed tasks.
3. Do not merge the disease CSV.
4. Apply one canonical naming contract from
   `backend/flask_api/config/column_aliases.json`.
5. Fit every learned preprocessing value on training data only.
6. Preserve exact feature order with the saved pipeline.
7. Treat all targets and relationships as synthetic prototype data.

## Dataset Loading

- Resolve the primary path through central project configuration.
- Verify the expected SHA-256 before preprocessing:
  `26D6D08FE463893253A9923FEFEFC99642438934817F554BFE9E08DEEA2AD1B3`.
- Read the CSV with explicit expected columns and stable data types.
- Fail clearly on missing, duplicated, or unexpected required columns.
- Record row/column counts, source checksum, parser version, and contract
  version.
- Do not write cleaned data over the raw CSV.

## Canonical Column Mapping

- Load aliases from `backend/flask_api/config/column_aliases.json`.
- Rename only exact approved aliases.
- Reject ambiguous duplicate matches, such as two source columns mapping to one
  canonical field.
- Apply transformations separately from aliasing. For example, birth date is
  not a direct alias for `age_months`; it requires an explicit calculation.
- Save the applied source-to-canonical mapping in preprocessing metadata.

## Model-Specific Tables

Create logical feature/target views:

- Model 1: nine selected features plus synthetic target `feed_type`;
- Model 2 Design A: the same nine features plus synthetic target
  `feed_quantity_kg`;
- Model 2 Design B: Design A plus out-of-fold `predicted_feed_type`;
- Model 3: the same nine features plus synthetic target `milk_yield_l`.

Identifiers and observation dates may remain in a split manifest but never in
the predictive feature matrix.

## Numeric Processing

Selected numeric features:

- `age_months`;
- `weight_kg`;
- `days_in_milk`;
- `previous_week_avg_yield_l`;
- `body_condition_score`;
- `ambient_temperature_c`;
- `humidity_percent`.

### Required numeric fields

`age_months` and `weight_kg`:

- coerce only well-formed finite numeric values;
- reject invalid/missing inference requests;
- flag training rows outside contract ranges;
- do not silently clip during preprocessing.

### Optional numeric fields

- Fit median imputation on the training partition only.
- Add or retain a missingness indicator for every imputed optional feature.
- Apply the fitted training median to validation, test, and inference.
- Store imputation values in pipeline metadata.
- Never use whole-dataset statistics before splitting.

## Categorical Processing

Selected categorical features:

- `breed`;
- `lactation_stage`.

Rules:

- trim surrounding whitespace;
- apply only documented category mappings;
- map `Early Lactation`, `Mid Lactation`, and `Late Lactation` to the dataset
  categories `Early`, `Mid`, and `Late`;
- do not silently map application `Dry`, because no matching dataset category
  exists;
- represent missing optional categories with `__MISSING__`;
- configure inference encoders to handle unseen otherwise-valid categories
  using `__UNKNOWN__`;
- store fitted category order.

`breed` is required in the current contract. An unseen valid breed may be
encoded as `__UNKNOWN__` only if the final pipeline was fitted with that
category and the request still passes application-scope validation.

## Encoding

- Use one-hot encoding for nominal categories.
- Do not impose numeric ordering on breed, feed type, season, climate, or
  management labels.
- For Model 1, persist target class order with the classifier and output
  probability names in that order.
- For Feed Quantity Design B, either use Model 1 class probabilities in fixed
  order or one encoded predicted class; the selected representation must be
  versioned.

## Scaling

- Scale numeric features for linear, distance-based, or neural candidates when
  required.
- Fit scaling only on training data.
- Do not add unnecessary scaling for tree-based candidates.
- Keep scaling inside the persisted pipeline so training and inference use the
  same transformation.

## Outlier and Range Handling

- Flag values outside documented contract ranges.
- Report counts by split.
- Do not automatically remove or winsorize rows solely because of statistical
  outlier status.
- Biological validation cannot be claimed for publisher-declared synthetic
  records.
- Any approved clipping or removal rule must be fitted/decided using training
  data and documented before application to validation/test.

## Train/Validation/Test Split

Preferred allocation:

- training: 70%;
- validation: 15%;
- test: 15%;
- random seed: 42.

Design requirements:

- create the split before fitting imputers, encoders, scalers, or feature
  selection;
- use one stable split manifest across comparable designs where possible;
- preserve `Feed_Type` class proportions for Model 1 through stratification
  when practical;
- verify that every feed-type class appears in all three partitions;
- keep the final test partition untouched until model/design selection is
  complete;
- do not tune thresholds, preprocessing, hyperparameters, or model choice on
  final-test results.

`Cattle_ID` is currently unique, so animal-group splitting is not required.
If repeated animal identifiers are added later, group-aware splitting becomes
mandatory so one animal cannot appear in multiple partitions.

Because the records are synthetic and dates may encode generation batches,
`Date` must not be a predictor. A later sensitivity check may compare random
and temporal/batch-aware splits, but such evaluation is outside Phase 3
preprocessing implementation unless separately approved.

## Feed Quantity Design B

Ground-truth `Feed_Type` must never be inserted directly as the Design B
feature for validation, test, or inference.

Training design:

1. Split the data.
2. Within training data, produce Model 1 predictions using out-of-fold
   cross-fitting.
3. Use those out-of-fold predictions as the Design B training feature.
4. Fit the final Model 1 only on the allowed training data.
5. Use that fitted Model 1 to create validation and test feed-type predictions.
6. At inference, create the feature from the loaded Model 1.

Persist Model 1 class order/version as a Design B dependency.

## Target Handling

- `feed_type`, `feed_quantity_kg`, and `milk_yield_l` are targets only.
- Remove rows with missing target values only after reporting the count.
- Do not impute targets.
- Never place a target in its own input feature frame.
- Exclude same-record target/output fields whose timing is unavailable.
- Label every report and artifact with its synthetic-target interpretation.

## Pipeline Persistence

Each future persisted pipeline must include or reference:

- contract version;
- alias-map checksum/version;
- source dataset checksum;
- target name and interpretation;
- exact ordered input features;
- fitted imputers and missing flags;
- fitted category mappings/encoders;
- fitted scaler when applicable;
- model class and library versions;
- split seed and split-manifest checksum;
- synthetic-data disclaimer;
- expected output schema.

A runtime service must reject an artifact whose feature schema or contract
version is incompatible.

## Schema Validation

Training-time validation:

- required source columns exist exactly once;
- expected types can be parsed;
- target is present and excluded from inputs;
- identifiers are absent from the predictive frame;
- selected features match the model contract;
- class labels/ranges are reported;
- split proportions and class distributions are recorded.

Inference-time validation:

- required fields are present;
- values are finite and inside contract bounds;
- application categories map explicitly;
- optional missing fields are recorded;
- feature order matches the pipeline;
- no target or forbidden field is accepted as a hidden input.

## Phase 3 Deliverables Proposed

Phase 3 implemented:

- read-only loader;
- canonical mapper;
- schema validator;
- model-specific feature builders;
- split-manifest builder;
- unfitted preprocessing-pipeline factories;
- unit tests for mappings, leakage exclusions, missing handling, and feature
  order.

Generated evidence:

- `backend/flask_api/ml/reports/data_split_manifest.csv`;
- `backend/flask_api/ml/reports/data_split_summary.json`;
- `backend/flask_api/ml/reports/data_split_report.md`;
- `backend/flask_api/ml/reports/feed_type_oof_fold_manifest.csv`;
- `backend/flask_api/ml/reports/feed_type_oof_fold_summary.json`;
- `backend/flask_api/ml/reports/preprocessing_validation_report.md`.

The validation result is `READY_FOR_PHASE_4_WITH_LIMITATIONS`. That result does
not authorize training. Phase 3 stops before any classifier or regressor is
fitted.
