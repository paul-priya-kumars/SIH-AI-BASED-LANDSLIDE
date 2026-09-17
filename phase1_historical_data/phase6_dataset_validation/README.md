# Phase 6: Dataset Validation

This directory contains the Phase 6 dataset validation implementation for the M2-C Historical Landslide Data Collection & Integration component of the SIH26001 Landslide Risk Prediction Project.

## Purpose

Phase 6 validates the Phase 5 feature dataset (`historical_landslide_features.csv`) to ensure it is structurally, spatially, numerically, and logically valid enough to proceed to final ML dataset preparation.

## Validation Checks Performed

1. **Structural Validation**
   - File existence and readability
   - Expected column presence
   - Duplicate column detection
   - Empty column/row detection

2. **Historical Field Validation**
   - landslide_id: missing values, duplicates
   - date: valid format, missing values, impossible values
   - latitude: numeric, range (-90 to +90), missing values
   - longitude: numeric, range (-180 to +180), missing values

3. **Spatial Validation**
   - GeoJSON geometry existence and type (Point)
   - Coordinate order (longitude=X, latitude=Y)
   - CRS validation (EPSG:4326)
   - CSV-Geojson coordinate consistency
   - Invalid geometry detection

4. **Environmental Feature Validation**
   - NDVI: range validation (-1 to +1), status consistency
   - Elevation: numeric validation, status consistency
   - Slope: non-negative validation, status consistency
   - Aspect: range validation (0-360 degrees), status consistency
   - Status-feature consistency checking

5. **Missing Data Analysis**
   - Statistics for important features
   - Valid/missing/invalid counts
   - Missing percentage calculation

6. **Duplicate Validation**
   - Exact duplicate rows
   - Duplicate landslide IDs
   - Duplicate coordinate pairs

7. **Synthetic Data Validation**
   - `data_source_type` column verification
   - Synthetic data marker preservation
   - Historical source information verification

8. **Cross-Dataset Consistency**
   - Phase 3 GeoJSON vs Phase 5 CSV consistency
   - Record count matching
   - landslide ID matching
   - Coordinate consistency

9. **Feature Extraction Status Validation**
   - Status value validation (COMPLETE, PARTIAL, etc.)
   - Status-feature availability consistency

10. **Rainfall Handling Validation**
    - Confirmation of `NOT_SPATIALLY_MAPPABLE` status
    - Non-spatial data handling verification

11. **Data Leakage / Target Validation**
    - Check for accidental ML target columns
    - Verification of no prediction/risk/scale columns

## File Structure

```
phase6_dataset_validation/
├── README.md                 # This file
├── scripts/
│   ├── validate_dataset.py   # Main validation script
│   └── test_dataset_validation.py  # Test suite
└── output/
    └── dataset_validation_report.txt  # Generated validation report
```

## How to Run

### Run the Validation Script

```bash
python scripts/validate_dataset.py
```

This will:
1. Load the Phase 5 feature dataset
2. Load the Phase 3 historical landslide GeoJSON for cross-validation
3. Run all validation checks
4. Generate a detailed validation report in `output/dataset_validation_report.txt`

### Run the Test Suite

```bash
python scripts/test_dataset_validation.py
```

This runs unit tests for all validation functions to ensure they work correctly.

## Expected Output

The validation script generates `dataset_validation_report.txt` containing:

1. Dataset Summary
2. Structural Validation Results
3. Historical Field Validation Results
4. Spatial Validation Results
5. Environmental Feature Validation Results
6. Missing Data Statistics
7. Duplicate Validation Results
8. Synthetic Data Validation
9. Cross-Dataset Consistency Results
10. Feature Extraction Status Validation
11. Rainfall Handling Validation
12. Data Leakage / Target Validation
13. Overall Validation Result (PASS/PASS_WITH_WARNINGS/FAIL)
14. Dataset Statistics Summary
15. Important Notes and Warnings

## Important Notes

- This validation does NOT modify any source data files
- Synthetic data is clearly identified and must not be used as real observations
- Rainfall data remains non-spatial (tabular only) in this implementation
- Missing values are preserved as NaN with appropriate status codes
- The validation report clearly indicates whether the dataset is suitable for progression to final ML dataset preparation

## Dependencies

- Python 3.13 or later
- pandas>=2.0.0
- numpy>=1.20.0

Dependencies are already installed as part of the M2-C project requirements.