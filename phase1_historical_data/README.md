# M2-C: Historical Landslide Data Collection & Integration

**SIH26001 — Landslide Risk Prediction and Early Alert System with Citizen Closed-Loop Reporting**

## What is M2-C?
M2-C is responsible for Historical Landslide Data + GIS Integration + Final ML Dataset in the project.

## Project Status
- **Phase 1**: Historical Landslide Data Collection + Basic Validation ✅ COMPLETE
- **Phase 2**: Historical Landslide Data Cleaning + Standardization ✅ COMPLETE
- **Phase 3**: Historical Landslide Location Mapping / GIS Layer Creation ✅ COMPLETE
- **Phase 4**: M2-A + M2-B + Historical GIS Layer Integration ✅ COMPLETE
- **Phase 5**: Spatial Join / Feature Extraction ✅ COMPLETE
- **Phase 6**: Dataset Validation ✅ COMPLETE
- **Phase 7**: Final ML Dataset Preparation ✅ COMPLETE (current)

## Folder Structure
```
M2-C/
├── requirements.txt
└── phase1_historical_data/
    ├── README.md                 # This file
    ├── data/
    │   ├── raw/                  # Place for real historical landslide data (to be provided later)
    │   ├── sample/               # Contains sample/demo data (clearly marked as synthetic)
    │   │   └── sample_landslides.csv
    │   ├── cleaned/              # Output of Phase 2 cleaning
    │   │   └── cleaned_sample_landslides.csv
    │   ├── gis/                  # Output of Phase 3 GIS conversion
    │   │   ├── historical_landslides.geojson
    │   │   └── historical_landslides.gpkg (optional)
    │   └── integrated/           # Output of Phase 4 integration
    │       ├── m2a/              # M2-A data (satellite imagery + NDVI)
    │   │   ├── m2b/              # M2-B data (rainfall + DEM + terrain)
    │   │   ├── m2c/              # M2-C data (historical landslide GIS layer)
    │   │   └── integration_metadata/  # Metadata about the integrated datasets
    │       │   ├── dataset_registry.json
    │       │   ├── integration_manifest.csv
    │       │   └── inspection_results.json
    ├── scripts/
    │   ├── create_schema.py      # Script to create folder structure and sample data
    │   ├── validate_input.py     # Script to validate landslide CSV data (Phase 1)
    │   ├── test_validation.py    # Tests for Phase 1 validation
    │   ├── clean_historical_data.py # Script to clean historical landslide CSV (Phase 2)
    │   ├── test_cleaning.py      # Tests for Phase 2 cleaning
    │   ├── create_landslide_layer.py # Script to create GIS point layer (Phase 3)
    │   ├── test_gis_layer.py     # Tests for Phase 3 GIS conversion
    │   ├── inspect_m2_inputs.py  # Script to inspect M2-A and M2-B inputs
    │   ├── integrate_m2_datasets.py # Script to integrate M2-A, M2-B, and M2-C datasets (Phase 4)
    │   └── test_integration.py   # Tests for Phase 4 integration
    └── output/
        ├── validation_report_sample_landslides.txt   # Phase 1 validation report
        ├── cleaning_report_sample_landslides.txt     # Phase 2 cleaning report
        ├── gis_report_sample_landslides.txt          # Phase 3 GIS conversion report
        └── integration_report.txt                    # Phase 4 integration report
```

## CSV Schema (Phases 1 & 2)
The expected schema for historical landslide data is:

| Field          | Description                                                                 | Required? |
|----------------|-----------------------------------------------------------------------------|-----------|
| landslide_id   | Unique identifier for each landslide record                                 | Yes       |
| date           | Date of the landslide occurrence (YYYY-MM-DD format)                        | Yes       |
| latitude       | Latitude coordinate (-90 to 90)                                             | Yes       |
| longitude      | Longitude coordinate (-180 to 180)                                          | Yes       |
| location       | Name of the specific location (e.g., town, village)                         | Recommended |
| district       | District name                                                               | Recommended |
| state          | State or province name                                                      | Recommended |
| country        | Country name                                                                | Recommended |
| source         | Name of the data source (e.g., agency, organization)                        | Recommended |
| source_url     | URL to the original data source                                             | Recommended |
| severity       | Severity level of the landslide (if available)                              | Optional  |
| description    | Additional description or notes about the landslide                         | Optional  |

**Required fields** are essential for basic identification and geolocation.
**Recommended fields** provide important contextual information.
**Optional fields** may be missing in some datasets but are valuable when available.

## Phase 1: Historical Landslide Data Collection
Phase 1 focuses on creating a reliable historical landslide data collection module. It establishes a standard schema for storing historical landslide records and provides tools to validate input data.

### What Phase 1 Does:
- Creates the required folder structure
- Generates a sample CSV with clearly marked synthetic/demo records
- Reads a CSV input file
- Validates required columns exist
- Checks basic coordinate validity (latitude between -90 and 90, longitude between -180 and 180)
- Validates landslide_id presence
- Validates date values can be parsed
- Reports missing important fields
- Reports duplicate landslide IDs
- Produces a validation report
- Does NOT automatically delete questionable records
- Clearly distinguishes warnings from errors

### How to Run Phase 1 Validation:
```bash
python scripts/validate_input.py --input path/to/your/data.csv
```
The script will produce a validation report in the `output/` directory.

## Phase 2: Historical Landslide Data Cleaning & Standardization
Phase 2 focuses on cleaning and standardizing the historical landslide data collected in Phase 1.

### What Phase 2 Does:
- Reads the validated CSV (or sample data)
- Preserves the original raw data (never modifies it)
- Cleans supported fields:
  - Text fields (location, district, state, country, source, source_url, severity, description): removes leading/trailing whitespace, collapses repeated spaces
  - Landslide ID: strips whitespace
  - Dates: standardizes valid dates to YYYY-MM-DD format (where interpretation is unambiguous)
  - Latitude/Longitude: converts to numeric, validates ranges (-90 to 90 for latitude, -180 to 180 for longitude)
- Detects and reports:
  - Exact duplicate rows
  - Duplicate landslide IDs
  - Possible spatial duplicates (same date, latitude, longitude)
  - Missing required values
  - Invalid coordinates
  - Invalid dates
- Standardizes valid data:
  - Dates converted to YYYY-MM-DD
  - Coordinates converted to numeric values
  - Text fields normalized (whitespace)
- Adds a `data_quality_status` column with values:
  - `CLEAN`: record passed all validation checks
  - `REVIEW_REQUIRED`: record has issues requiring human review (e.g., missing required values, invalid coordinates, invalid dates)
- Saves the cleaned dataset to `phase1_historical_data/data/cleaned/`
- Generates a cleaning report detailing actions performed and records requiring review

### How to Run Phase 2 Cleaning:
```bash
python scripts/clean_historical_data.py --input phase1_historical_data/data/sample/sample_landslides.csv
```
The script will save the cleaned CSV to `phase1_historical_data/data/cleaned/` and generate a report in the `output/` directory.

## Phase 3: Historical Landslide Location Mapping / GIS Layer Creation
Phase 3 converts the cleaned historical landslide CSV into a proper geospatial point dataset for use in GIS analysis.

### What Phase 3 Does:
- Reads the cleaned CSV output from Phase 2
- Uses latitude and longitude to create geographic point features
- Assigns the correct coordinate reference system (WGS 84 / EPSG:4326)
- Creates a GeoPoint layer preserving all important historical attributes
- Exports the layer to GeoJSON (and optionally GeoPackage)
- Handles records that require review (from Phase 2):
  - Records with valid latitude and longitude are converted to GIS points
  - Records without valid coordinates are excluded from point creation but reported
  - Does NOT invent coordinates or move missing-coordinate records to 0,0
- Generates a GIS conversion report detailing:
  - Total cleaned records
  - Records converted to GIS points
  - Records excluded due to invalid/missing coordinates
  - Records marked REVIEW_REQUIRED
  - Coordinate reference system used
- Preserves source attribution and all original fields in the GeoJSON properties

### Important GIS Concepts:
- **Coordinate Order**: Longitude → X coordinate, Latitude → Y coordinate (Point(longitude, latitude))
- **Coordinate Reference System**: EPSG:4326 represents WGS 84 geographic coordinates, appropriate for storing the original latitude/longitude coordinates
- **No Automatic Reprojection**: Coordinates are not transformed; they remain in the source CRS
- **Review-Required Records**: Clearly identified in reports; only records with valid coordinates become point features

### How to Run Phase 3 GIS Conversion:
```bash
python scripts/create_landslide_layer.py --input phase1_historical_data/data/cleaned/cleaned_sample_landslides.csv
```
The script will save the GeoJSON to `phase1_historical_data/data/gis/historical_landslides.geojson` and generate a report in the `output/` directory.

### How to View the GeoJSON in QGIS:
1. Install and open QGIS (https://qgis.org)
2. Click "Layer" → "Add Layer" → "Add Vector Layer"
3. Select "File" as the source type
4. Browse to `phase1_historical_data/data/gis/historical_landslides.geojson`
5. Click "Add"
6. The points will appear on the map; you can inspect their attributes by right-clicking the layer and opening the attribute table

## Phase 4: M2-A + M2-B + M2-C Data Integration
Phase 4 integrates the outputs from M2-A (satellite imagery + NDVI), M2-B (rainfall + DEM + terrain), and M2-C (historical landslide GIS layer) to prepare for spatial analysis.

### What Phase 4 Does:
- Inspects available M2-A, M2-B, and M2-C datasets
- Records metadata about each dataset (format, CRS, spatial extent, etc.)
- Checks CRS compatibility and documents any reprojection needed
- Checks spatial extent overlap between datasets
- Creates a machine-readable dataset registry (JSON)
- Creates an integration manifest (CSV) summarizing all datasets
- Generates a human-readable integration report
- Preserves all original data (no modification of source files)
- Provides a foundation for Phase 5 spatial joins and feature extraction

### Important Integration Concepts:
- **CRS Handling**: All datasets are inspected for their native CRS. The integration uses EPSG:4326 (WGS 84) as the common geographic CRS unless otherwise noted. No original data is modified; reprojection is only applied to derived integration layers if needed.
- **Spatial Extent**: The spatial extent (bounding box) of each dataset is recorded to assess overlap.
- **Data Integrity**: Original M2-A, M2-B, M2-C raw data, cleaned CSV, and historical GeoJSON remain unchanged.
- **Synthetic Data**: Any demo/synthetic data used for testing is clearly labeled and must not be used as real observations.

### How to Run Phase 4 Integration:
```bash
python scripts/inspect_m2_inputs.py
```
This script inspects the available datasets and saves inspection results.

```bash
python scripts/integrate_m2_datasets.py
```
This script integrates the datasets, generates metadata, and produces the integration report.

### How to View the Integration Outputs:
- **Dataset Registry**: `phase1_historical_data/data/integrated/integration_metadata/dataset_registry.json`
- **Integration Manifest**: `phase1_historical_data/data/integrated/integration_metadata/integration_manifest.csv`
- **Integration Report**: `phase1_historical_data/output/integration_report.txt`

## Dependencies
- Python 3.13 or later
- pandas>=2.0.0
- geopandas>=0.12.0
- shapely>=2.0.0
- rasterio>=1.3.0

Install dependencies with:
```bash
pip install -r requirements.txt
```

## Important Notes
- The sample data in `data/sample/` is **SYNTHETIC** and for demonstration purposes only.
- **Never use synthetic data as real historical landslide observations.**
- Always verify the provenance and accuracy of real data before use.
- Phase 1 does not alter or delete records; it only reports on data quality.
- Phase 2 does not modify the original raw data; it reads from `data/raw/` or `data/sample/` and writes to `data/cleaned/`.
- Phase 3 does not modify the cleaned CSV; it reads from `data/cleaned/` and writes to `data/gis/`.
- Phase 4 does not modify any original data; it only reads from the existing data directories and writes metadata and reports to the `integrated/` and `output/` directories.
- The pipeline is designed so that you can replace the sample CSV with real data in `data/raw/` and run the validation, cleaning, GIS conversion, and integration scripts sequentially.

## Phase 5 — Spatial Join / Feature Extraction
Phase 5 is responsible for spatially associating historical landslide locations with environmental variables from M2-A and M2-B datasets.

### What Phase 5 Does:
- Loads the historical landslide GeoJSON output from Phase 3
- Extracts NDVI values from the M2-A NDVI raster for each historical landslide point
- Extracts elevation values from the M2-B DEM raster for each historical landslide point
- Extracts slope values from the M2-B slope raster for each historical landslide point
- Extracts aspect values from the M2-B aspect raster for each historical landslide point
- Handles M2-B rainfall data (identified as non-spatial tabular data)
- Preserves all historical landslide attributes
- Adds extraction status fields for each environmental variable
- Adds data source type field to distinguish synthetic vs real data
- Creates an intermediate feature-extraction CSV dataset
- Optionally creates a GeoJSON version of the feature dataset
- Generates a detailed feature extraction report
- Handles coordinate transformations when CRS differs between layers
- Preserves NoData values rather than imputing missing data
- Does NOT modify any original data files (read-only access only)

### How to Run Phase 5 Feature Extraction:
```bash
python scripts/extract_spatial_features.py
```
This script will generate:
- Intermediate CSV: `phase1_historical_data/data/features/phase5/historical_landslide_features.csv`
- Optional GeoJSON: `phase1_historical_data/data/features/phase5/historical_landslide_features.geojson`
- Extraction report: `phase1_historical_data/output/feature_extraction_report.txt`

### Important Outputs:
- **Feature Extraction CSV**: Contains historical attributes + environmental values + status fields
- **Feature Extraction GeoJSON**: Spatial version of the CSV with Point geometry (EPSG:4326)
- **Extraction Report**: Detailed summary of extraction process, statistics, and important notes

### Key Features:
- ✅ Coordinate order validated (longitude=X, latitude=Y)
- ✅ CRS handling and transformation when necessary
- ✅ Proper NoData/nodata handling (preserved as missing, not replaced with 0)
- ✅ Outside-raster point handling (marked appropriately)
- ✅ Historical attribute preservation
- ✅ Synthetic data demarcation (data_source_type field)
- ✅ Comprehensive extraction status tracking
- ✅ No modification of original data files
- ✅ Intermediate dataset clearly labeled as NOT the final ML dataset

## Warning
The synthetic data provided is **not real** and must not be used for training models or making decisions. It is intended solely to illustrate the expected data format, validation, cleaning, GIS conversion, and integration processes.

## Phase 6 — Dataset Validation
Phase 6 is responsible for validating the Phase 5 feature dataset to ensure it is structurally, spatially, numerically, and logically valid enough to proceed to final ML dataset preparation.

### What Phase 6 Does:
- Loads the Phase 5 feature dataset (historical_landslide_features.csv)
- Loads the Phase 3 historical landslide GeoJSON for cross-validation
- Performs structural validation (file existence, column integrity, etc.)
- Validates historical fields (landslide_id, date, latitude, longitude)
- Validates spatial consistency between CSV and GeoJSON
- Validates environmental features (NDVI, elevation, slope, aspect) for range and status consistency
- Analyzes missing data statistics
- Checks for duplicate records, IDs, and coordinates
- Verifies synthetic data is properly marked and preserved
- Validates cross-dataset consistency between Phase 3 and Phase 5
- Validates feature extraction status consistency
- Confirms rainfall data remains correctly marked as non-spatial
- Checks for accidental data leakage or ML target columns
- Generates a detailed validation report
- Does NOT modify any source data files (read-only access only)

### How to Run Phase 6 Dataset Validation:
```bash
python phase1_historical_data/phase6_dataset_validation/scripts/validate_dataset.py
```
This script will generate:
- Validation report: `phase1_historical_data/phase6_dataset_validation/output/dataset_validation_report.txt`

To run the test suite:
```bash
python phase1_historical_data/phase6_dataset_validation/scripts/test_dataset_validation.py
```

### Important Outputs:
- **Validation Report**: Detailed summary of validation process, statistics, issues found, and overall suitability for progression to final ML dataset preparation
- **Test Suite**: Automated tests verifying all validation functions work correctly

### Key Features:
- ✅ Structural validation of CSV file and columns
- ✅ Historical field validation (ID, date, coordinate ranges)
- ✅ Spatial validation (geometry type, coordinate order, CRS, CSV-GeoJSON consistency)
- ✅ Environmental feature validation (range checking, status consistency)
- ✅ Missing data analysis and reporting
- ✅ Duplicate detection (rows, IDs, coordinates)
- ✅ Synthetic data verification and tracking
- ✅ Cross-dataset consistency checking
- ✅ Feature extraction status validation
- ✅ Rainfall handling confirmation (non-spatial data)
- ✅ Data leakage / target verification
- ✅ No modification of source data files
- ✅ Clear reporting of limitations and warnings

## Phase 7 — Final ML Dataset Preparation
Phase 7 prepares a clean, documented, ML-ready dataset from the validated Phase 5/Phase 6 data for use in M1's ML pipeline.

### What Phase 7 Does:
- Loads the validated Phase 5 feature dataset
- Selects and documents core ML features (NDVI, elevation, slope, aspect)
- Preserves historical IDs and coordinates for traceability
- Creates separate ML feature and metadata datasets
- Generates a machine-readable feature manifest
- Preserves synthetic data markings and warnings
- Handles non-spatial rainfall data appropriately (excluded from ML features)
- Does NOT fabricate target labels, rainfall values, or environmental measurements
- Does NOT perform imputation, scaling, or train/test splitting
- Does NOT train any machine learning models
- Maintains read-only access to all source data files

### How to Run Phase 7 ML Dataset Preparation:
```bash
python phase1_historical_data/phase7_final_ml_dataset/scripts/prepare_ml_dataset.py
```
This script will generate:
- ML feature dataset: `phase1_historical_data/phase7_final_ml_dataset/data/ml_features.csv`
- ML metadata dataset: `phase1_historical_data/phase7_final_ml_dataset/data/ml_metadata.csv`
- Feature manifest: `phase1_historical_data/phase7_final_ml_dataset/metadata/ml_feature_manifest.json`
- Preparation report: `phase1_historical_data/phase7_final_ml_dataset/output/ml_dataset_preparation_report.txt`

To run the test suite:
```bash
python phase1_historical_data/phase7_final_ml_dataset/scripts/test_ml_dataset.py
```

### Important Outputs:
- **ML Feature Dataset**: Contains core features for machine learning (landslide_id, latitude, longitude, ndvi, elevation_m, slope_deg, aspect_deg, data_source_type)
- **ML Metadata Dataset**: Contains historical and contextual metadata for traceability
- **Feature Manifest**: Machine-readable documentation of each ML feature's source, type, and limitations
- **Preparation Report**: Detailed summary of the preparation process, feature mapping, and important warnings

### Key Features:
- ✅ Core ML feature selection and documentation
- ✅ Historical ID and coordinate preservation
- ✅ Separate metadata dataset for traceability
- ✅ Machine-readable feature manifest
- ✅ Synthetic data preservation and warning
- ✅ Appropriate handling of non-spatial rainfall data
- ✅ No target label fabrication
- ✅ No data imputation or synthetic value creation
- ✅ No modification of source data files
- ✅ Clear reporting of limitations and intended use

## Warning
The synthetic data provided is **not real** and must not be used for training models or making decisions. It is intended solely to illustrate the expected data format, validation, cleaning, GIS conversion, and integration processes.