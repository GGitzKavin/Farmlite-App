# FarmLite Datasets

Dataset files are kept outside both applications so the backend and frontend
remain independent.

## Directories

- `raw/`: original, immutable source CSV files.
- `interim/`: temporary cleaned or merged data.
- `processed/`: validated features and model-ready datasets.
- `external/`: third-party reference datasets.

The current raw files are:

- `global_cattle_milk_yield_prediction_dataset.csv`
- `global_cattle_disease_detection_dataset.csv`

Each current CSV contains 250,000 rows. Their provenance, licensing,
representativeness, and real-world measurement validity have not been
independently verified. Keep raw files unchanged and record any transformations
used to create interim or processed files.

Raw CSV files are local data and are ignored by Git because of their size.
Directory placeholders and this documentation remain versioned.
