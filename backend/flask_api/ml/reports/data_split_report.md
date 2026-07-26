# FarmLite Data Split Report

## Summary

- Total rows: 250,000
- Training: 175,000 (70.000000%)
- Validation: 37,500 (15.000000%)
- Test: 37,500 (15.000000%)
- Random seed: 42
- Split version: `phase3_split_v1`
- Algorithm: Two-stage sklearn train_test_split: 70% train, then equal validation/test halves of the remaining 30%; Feed_Type stratified

## Feed_Type Distribution by Split

| Split | Category | Count | Percentage |
|---|---|---:|---:|
| train | Concentrates | 21897 | 12.512571% |
| train | Crop_Residues | 21891 | 12.509143% |
| train | Dry_Fodder | 22098 | 12.627429% |
| train | Green_Fodder | 21856 | 12.489143% |
| train | Hay | 21794 | 12.453714% |
| train | Mixed_Feed | 21806 | 12.460571% |
| train | Pasture_Grass | 21903 | 12.516000% |
| train | Silage | 21755 | 12.431429% |
| validation | Concentrates | 4693 | 12.514667% |
| validation | Crop_Residues | 4691 | 12.509333% |
| validation | Dry_Fodder | 4736 | 12.629333% |
| validation | Green_Fodder | 4683 | 12.488000% |
| validation | Hay | 4670 | 12.453333% |
| validation | Mixed_Feed | 4672 | 12.458667% |
| validation | Pasture_Grass | 4693 | 12.514667% |
| validation | Silage | 4662 | 12.432000% |
| test | Concentrates | 4692 | 12.512000% |
| test | Crop_Residues | 4691 | 12.509333% |
| test | Dry_Fodder | 4735 | 12.626667% |
| test | Green_Fodder | 4683 | 12.488000% |
| test | Hay | 4670 | 12.453333% |
| test | Mixed_Feed | 4673 | 12.461333% |
| test | Pasture_Grass | 4694 | 12.517333% |
| test | Silage | 4662 | 12.432000% |

## Feed_Quantity_kg Summary by Split

| Split | Count | Mean | Std | Min | P25 | Median | P75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 175000 | 12.023848 | 3.959758 | 3.0 | 9.3 | 12.0 | 14.7 | 25.0 |
| validation | 37500 | 11.993896 | 3.965326 | 3.0 | 9.3 | 12.0 | 14.7 | 25.0 |
| test | 37500 | 11.995979 | 3.955742 | 3.0 | 9.3 | 12.0 | 14.7 | 25.0 |

Material distribution difference detected: **False** (maximum standardized mean difference 0.005373; threshold 0.1).

## Milk_Yield_L Summary by Split

| Split | Count | Mean | Std | Min | P25 | Median | P75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 175000 | 8.729748 | 5.766628 | 0.0 | 4.34 | 7.62 | 12.3 | 36.42 |
| validation | 37500 | 8.709638 | 5.755969 | 0.0 | 4.31 | 7.63 | 12.3 | 36.05 |
| test | 37500 | 8.702181 | 5.755934 | 0.0 | 4.35 | 7.58 | 12.27 | 35.34 |

Material distribution difference detected: **False** (maximum standardized mean difference 0.003542; threshold 0.1).

## Integrity Checks

- Cattle_ID overlap count: 0
- Duplicate source-row count: 0
- Missing assignment count: 0
- Every row assigned once: True
- Manifest fields are traceability-only: True
- Reproducibility SHA-256: `A7C206B058CBD04AED428F9C44228653AF4CBEB6F86D90317A0A847BC02DADFB`

## Limitations

- The source is publisher-declared synthetic data.
- Feed quantity basis and measurement period are not independently validated.
- Milk-yield measurement period and zero meaning are not independently validated.
- The random split is not evidence of real-world generalization.
- Cattle_ID is retained only for traceability and never as a predictive feature.
