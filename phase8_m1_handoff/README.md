# M2-C → M1 Handoff Package

## Phase 8: M1 Integration / Handoff Preparation

This package documents the interface between M2-C (Historical Landslide Data + GIS) and M1 (ML Pipeline) for the SIH26001 Landslide Risk Prediction and Early Alert System.

### Purpose

Phase 8 prepares the M2-C Phase 7 ML-ready dataset for consumption by M1's ML pipeline without:
- Model training
- Feature scaling
- Train/test splitting
- Prediction generation
- Risk scoring
- Any modification of M2-C source data

### M2-C Source Dataset

- **File**: `phase1_historical_data/phase7_final_ml_dataset/data/ml_features.csv`
- **Records**: 4 historical landslide points
- **Features**:
  - `landslide_id`: Unique identifier (string)
  - `latitude`: Latitude coordinate (float, decimal degrees)
  - `longitude`: Longitude coordinate (float, decimal degrees)
  - `ndvi`: Normalized Difference Vegetation Index (float, -1 to 1)
  - `elevation_m`: Elevation above sea level (float, meters)
  - `slope_deg`: Slope angle (float, degrees)
  - `aspect_deg`: Aspect angle (float, degrees)
  - `data_source_type`: Data authenticity marker (string, "SYNTHETIC_DEMO")

### M1 Integration Status

- **M1 implementation found**: NO (not present in this repository)
- **Direct integration performed**: NO
- **Adapter required**: NO (M1 can consume the Phase 7 dataset directly)
- **Adapter created**: NO

### Feature Mapping

| M2-C Feature | M1 Feature (Recommended) | Data Type | Transformation | Status |
|--------------|--------------------------|-----------|----------------|--------|
| landslide_id | landslide_id | string | None | Preserved for traceability |
| latitude | latitude | float | None | Spatial coordinate (Y) |
| longitude | longitude | float | None | Spatial coordinate (X) |
| ndvi | ndvi | float | None | Vegetation health indicator |
| elevation_m | elevation | float | None | Terrain height (meters) |
| slope_deg | slope | float | None | Terrain steepness (degrees) |
| aspect_deg | aspect | float | None | Terrain orientation (degrees) |
| data_source_type | data_source_type | string | None | Synthetic/demo data marker |

### Coordinate Convention

- **Longitude**: X coordinate
- **Latitude**: Y coordinate
- **Datum**: WGS 84
- **CRS**: EPSG:4326
- **Units**: Decimal degrees
- **Valid Ranges**:
  - Latitude: -90.0 to 90.0
  - Longitude: -180.0 to 180.0

### Rainfall Handling

- **Status**: NOT_SPATIALLY_MAPPABLE
- **Handling**: Excluded from ML feature dataset
- **Reason**: Current rainfall demo data lacks spatial coordinates
- **Note**: Rainfall columns preserved in metadata dataset for reference
- **M1 Responsibility**: Obtain rainfall from appropriate spatial rainfall source

### Target / Label Status

- **Target Available**: NO
- **Explanation**: No trustworthy supervised learning target available in synthetic/demo dataset
- **Target Labels Fabricated**: NO
- **Note**: Severity field preserved in metadata but not used as ML target

### Synthetic Data Disclosure

**CRITICAL WARNING**: All environmental feature values (NDVI, elevation, slope, aspect) in this dataset are SYNTHETIC DEMO VALUES created for pipeline development and testing ONLY.

These values MUST NOT:
- Be used as real-world measurements
- Be used to train models for real-world landslide prediction
- Be represented as evidence of model performance
- Be used for operational decision-making

The `data_source_type` column preserves this distinction with value "SYNTHETIC_DEMO".

### Provenance & Traceability

- **Historical IDs Preserved**: YES (landslide_id in both features and metadata)
- **Source Metadata Preserved**: YES (complete metadata dataset)
- **Source URLs Preserved**: YES (in metadata dataset)
- **Synthetic Marker Preserved**: YES (data_source_type column)
- **Coordinates Preserved**: YES (latitude, longitude unchanged)
- **Historical Attributes Preserved**: YES (in metadata dataset)

### Validation & Testing

#### Validation Script
- **Location**: `scripts/validate_m1_handoff.py`
- **Purpose**: Validates M2-C Phase 7 dataset readiness for M1 consumption
- **Checks**: Dataset existence, structure, data types, coordinate validity, synthetic marker preservation, rainfall handling, target absence, provenance protection, leakage prevention

#### Test Suite
- **Location**: `scripts/test_m1_handoff.py`
- **Purpose**: Automated tests for handoff package validity
- **Checks**: Artifact existence, contract validity, dataset validation, validator functionality

#### Usage
```bash
# Run validation
python scripts/validate_m1_handoff.py

# Run test suite
python scripts/test_m1_handoff.py
```

### Known Limitations

1. **Demo Dataset Size**: Only 4 records - NOT sufficient for production model training
2. **Synthetic Data**: All environmental values are synthetic demo values
3. **Rainfall Unavailable**: Spatial rainfall data not available in current demo dataset
4. **No Trustworthy Target**: No supervised learning target available for training
5. **Development Only**: Intended for ML pipeline development and testing only

### M2-C → M1 Architecture Boundary

```
M2-C (Historical Landslide Data + GIS)
        ↓
Phase 7: Final ML Dataset Preparation
        ↓
Validated ML-ready features (ml_features.csv)
        ↓
M2-C → M1 Handoff Contract (this package)
        ↓
M1 ML Pipeline (Feature Ingestion)
```

### Phase 8 Boundary Confirmation

Phase 8 is a data/interface handoff preparation phase. It is NOT:
- Model training
- Feature engineering for model improvement
- Prediction or inference
- Risk assessment or routing
- Any modification of M2-C source datasets
- Proceeding to Phase 9

### Generated Artifacts

- **Handoff Contract**: `phase8_m1_handoff_contract.json`
- **Validation Script**: `scripts/validate_m1_handoff.py`
- **Test Suite**: `scripts/test_m1_handoff.py`
- **README**: `README.md` (this file)
- **Report**: `output/m1_handoff_report.txt` (generated after validation)