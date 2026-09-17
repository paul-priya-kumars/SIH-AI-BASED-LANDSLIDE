# Phase 7: Final ML Dataset Preparation

This directory contains the Phase 7 final ML dataset preparation implementation for the M2-C Historical Landslide Data Collection & Integration component of the SIH26001 Landslide Risk Prediction Project.

## Purpose

Phase 7 prepares a clean, documented, ML-ready dataset from the validated Phase 5/Phase 6 data (`historical_landslide_features.csv`) for use in M1's ML pipeline.

## ML-Ready Dataset Output

The preparation produces two main output files:

1. **ml_features.csv**: Contains the core features for machine learning:
   - landslide_id (for traceability)
   - latitude, longitude (spatial coordinates, longitude=X, latitude=Y)
   - ndvi, elevation_m, slope_deg, aspect_deg (environmental features)
   - data_source_type (to distinguish synthetic vs real data)

2. **ml_metadata.csv**: Contains historical and contextual metadata:
   - landslide_id (for traceability)
   - date, location, district, state, country, source, source_url, severity, description
   - data_quality_status
   - ndvi_status, rainfall_24h, rainfall_3d, rainfall_7d, rainfall_status
   - elevation_status, slope_status, aspect_status
   - feature_extraction_status

Additionally, a feature manifest documents the ML features:

3. **ml_feature_manifest.json**: Machine-readable documentation of each ML feature.

## Important Notes

- The current environmental values are synthetic/demo data (data_source_type = SYNTHETIC_DEMO) and must not be used as real-world measurements.
- Rainfall data is non-spatial (tabular only) and is not included as an ML feature.
- No missing values have been imputed; they are preserved as NaN with appropriate status codes.
- No target labels have been fabricated; the dataset is target-free (unlabeled) for supervised learning.
- Historical provenance is preserved via landslide_id in both output files.
- Source data files remain unchanged (read-only access only).

## How to Run

### Run the Preparation Script

```bash
python scripts/prepare_ml_dataset.py
```

This will:
1. Load the validated Phase 5 dataset
2. Validate required columns
3. Select and document ML features
4. Standardize data types
5. Preserve missing values and synthetic-data markers
6. Produce the ML-ready feature dataset and metadata dataset
7. Produce the feature manifest
8. Generate a preparation report

### Run the Test Suite

```bash
python scripts/test_ml_dataset.py
```

This runs unit tests for the preparation functions.

## Dependencies

- Python 3.13 or later
- pandas>=2.0.0
- numpy>=1.20.0

Dependencies are already installed as part of the M2-C project requirements.