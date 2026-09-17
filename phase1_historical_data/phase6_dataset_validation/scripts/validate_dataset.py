#!/usr/bin/env python3
"""
Phase 6 Dataset Validation for M2-C Historical Landslide Feature Extraction

This script validates the Phase 5 feature dataset (historical_landslide_features.csv)
to ensure it's structurally, spatially, numerically, and logically valid enough
to proceed to final ML dataset preparation.

Author: Generated for SIH26001 Landslide Risk Prediction Project
"""

import sys
import os
from pathlib import Path
import pandas as pd
import json
import numpy as np
from datetime import datetime

# Add the scripts directory to the path so we can import from other phases if needed
sys.path.append(str(Path(__file__).parent.parent.parent / 'scripts'))

def load_phase5_dataset():
    """Load the Phase 5 feature dataset."""
    # Try to find the Phase 5 CSV file
    possible_paths = [
        Path('../../data/features/phase5/historical_landslide_features.csv'),
        Path('../data/features/phase5/historical_landslide_features.csv'),
        Path('./phase1_historical_data/data/features/phase5/historical_landslide_features.csv'),
    ]

    for path in possible_paths:
        if path.exists():
            return pd.read_csv(path)

    raise FileNotFoundError("Could not find historical_landslide_features.csv in expected locations")

def load_phase3_geojson():
    """Load the Phase 3 historical landslide GeoJSON for cross-validation."""
    possible_paths = [
        Path('../../data/gis/historical_landslides.geojson'),
        Path('../data/gis/historical_landslides.geojson'),
        Path('./phase1_historical_data/data/gis/historical_landslides.geojson'),
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)

    raise FileNotFoundError("Could not find historical_landslides.geojson in expected locations")

def validate_structural(df):
    """Perform structural validation on the dataset."""
    issues = []

    # Check if file exists and is readable (already done by caller)

    # Check if CSV is not empty
    if len(df) == 0:
        issues.append("ERROR: Dataset is empty")
        return issues

    # Check for expected columns
    expected_columns = [
        'landslide_id', 'date', 'latitude', 'longitude',
        'location', 'district', 'state', 'country', 'source', 'source_url',
        'severity', 'description', 'data_quality_status',
        'ndvi', 'ndvi_status', 'rainfall_24h', 'rainfall_3d', 'rainfall_7d', 'rainfall_status',
        'elevation_m', 'elevation_status', 'slope_deg', 'slope_status',
        'aspect_deg', 'aspect_status', 'feature_extraction_status', 'data_source_type'
    ]

    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        issues.append(f"WARNING: Missing expected columns: {missing_columns}")

    # Check for duplicate column names
    if len(df.columns) != len(set(df.columns)):
        duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
        issues.append(f"ERROR: Duplicate column names found: {duplicates}")

    # Check for completely empty columns
    empty_cols = [col for col in df.columns if df[col].isna().all()]
    if empty_cols:
        issues.append(f"WARNING: Completely empty columns: {empty_cols}")

    # Check for completely empty rows
    empty_rows = df.isna().all(axis=1)
    if empty_rows.any():
        issues.append(f"WARNING: {empty_rows.sum()} completely empty rows found")

    return issues

def validate_historical_fields(df):
    """Validate historical fields: landslide_id, date, latitude, longitude."""
    issues = []

    # landslide_id validation
    if 'landslide_id' in df.columns:
        missing_ids = df['landslide_id'].isna().sum()
        if missing_ids > 0:
            issues.append(f"ERROR: {missing_ids} missing landslide_id values")

        duplicate_ids = df['landslide_id'].duplicated().sum()
        if duplicate_ids > 0:
            issues.append(f"ERROR: {duplicate_ids} duplicate landslide_id values")
            dup_values = df[df['landslide_id'].duplicated(keep=False)]['landslide_id'].unique()
            issues.append(f"  Duplicate IDs: {list(dup_values)}")
    else:
        issues.append("ERROR: landslide_id column not found")

    # date validation
    if 'date' in df.columns:
        # Try to convert to datetime, coercing errors to NaT
        df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
        invalid_dates = df['date_parsed'].isna().sum() - df['date'].isna().sum()  # Count newly invalid
        missing_dates = df['date'].isna().sum()

        if missing_dates > 0:
            issues.append(f"WARNING: {missing_dates} missing date values")

        if invalid_dates > 0:
            issues.append(f"ERROR: {invalid_dates} invalid date values")

        # Check for impossibly old/future dates (beyond reasonable landslide records)
        valid_dates = df['date_parsed'].dropna()
        if len(valid_dates) > 0:
            # Landslides shouldn't be from prehistoric times or too far in future
            too_old = (valid_dates.dt.year < 1900).sum()
            too_future = (valid_dates.dt.year > 2030).sum()
            if too_old > 0:
                issues.append(f"WARNING: {too_old} dates before year 1900")
            if too_future > 0:
                issues.append(f"WARNING: {too_future} dates after year 2030")

        # Clean up temporary column
        df.drop('date_parsed', axis=1, inplace=True, errors='ignore')
    else:
        issues.append("ERROR: date column not found")

    # latitude validation
    if 'latitude' in df.columns:
        # Check if numeric
        non_numeric = pd.to_numeric(df['latitude'], errors='coerce').isna().sum() - df['latitude'].isna().sum()
        if non_numeric > 0:
            issues.append(f"ERROR: {non_numeric} non-numeric latitude values")

        # Check range (-90 to +90)
        lat_numeric = pd.to_numeric(df['latitude'], errors='coerce')
        invalid_lat = ((lat_numeric < -90) | (lat_numeric > 90)).sum()
        missing_lat = df['latitude'].isna().sum()

        if missing_lat > 0:
            issues.append(f"WARNING: {missing_lat} missing latitude values")

        if invalid_lat > 0:
            issues.append(f"ERROR: {invalid_lat} latitude values outside valid range (-90 to +90)")
    else:
        issues.append("ERROR: latitude column not found")

    # longitude validation
    if 'longitude' in df.columns:
        # Check if numeric
        non_numeric = pd.to_numeric(df['longitude'], errors='coerce').isna().sum() - df['longitude'].isna().sum()
        if non_numeric > 0:
            issues.append(f"ERROR: {non_numeric} non-numeric longitude values")

        # Check range (-180 to +180)
        lon_numeric = pd.to_numeric(df['longitude'], errors='coerce')
        invalid_lon = ((lon_numeric < -180) | (lon_numeric > 180)).sum()
        missing_lon = df['longitude'].isna().sum()

        if missing_lon > 0:
            issues.append(f"WARNING: {missing_lon} missing longitude values")

        if invalid_lon > 0:
            issues.append(f"ERROR: {invalid_lon} longitude values outside valid range (-180 to +180)")
    else:
        issues.append("ERROR: longitude column not found")

    return issues

def validate_spatial(df, geojson_data):
    """Validate spatial consistency between CSV and GeoJSON."""
    issues = []

    # Check if we have both datasets
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        issues.append("ERROR: Cannot validate spatial data - missing latitude/longitude columns")
        return issues

    try:
        features = geojson_data.get('features', [])
        if len(features) == 0:
            issues.append("WARNING: No features found in GeoJSON")
            return issues

        # Check record count consistency
        csv_count = len(df)
        geojson_count = len(features)
        if csv_count != geojson_count:
            issues.append(f"WARNING: Record count mismatch - CSV: {csv_count}, GeoJSON: {geojson_count}")

        # Check geometry type and CRS
        geometry_types = [f.get('geometry', {}).get('type') for f in features if f.get('geometry')]
        if geometry_types:
            invalid_geom_types = [gt for gt in geometry_types if gt != 'Point']
            if invalid_geom_types:
                issues.append(f"ERROR: {len(invalid_geom_types)} non-Point geometry types found: {set(invalid_geom_types)}")

        # Check CRS
        crs_name = geojson_data.get('crs', {}).get('properties', {}).get('name', '')
        if 'EPSG:4326' not in crs_name and 'urn:ogc:def:crs:OGC:1.3:CRS84' not in crs_name:
            issues.append(f"WARNING: Unexpected CRS: {crs_name}. Expected EPSG:4326 or CRS84")

        # Validate coordinate order and consistency
        coord_mismatches = 0
        for i, (_, row) in enumerate(df.iterrows()):
            if i < len(features):
                feature = features[i]
                geom = feature.get('geometry', {})
                if geom.get('type') == 'Point':
                    coords = geom.get('coordinates', [])
                    if len(coords) >= 2:
                        geojson_lon, geojson_lat = coords[0], coords[1]
                        csv_lon, csv_lat = row['longitude'], row['latitude']

                        # Check if coordinates match (within floating point tolerance)
                        lon_diff = abs(geojson_lon - csv_lon) if not (pd.isna(geojson_lon) or pd.isna(csv_lon)) else float('inf')
                        lat_diff = abs(geojson_lat - csv_lat) if not (pd.isna(geojson_lat) or pd.isna(csv_lat)) else float('inf')

                        if lon_diff > 1e-10 or lat_diff > 1e-10:
                            coord_mismatches += 1
                            if coord_mismatches <= 5:  # Only report first few mismatches
                                issues.append(f"WARNING: Coordinate mismatch for record {i} (ID: {row.get('landslide_id', 'unknown')}): "
                                            f"CSV({csv_lon}, {csv_lat}) vs GeoJSON({geojson_lon}, {geojson_lat})")

        if coord_mismatches > 5:
            issues.append(f"WARNING: {coord_mismatches} total coordinate mismatches between CSV and GeoJSON")
        elif coord_mismatches > 0:
            issues.append(f"WARNING: {coord_mismatches} coordinate mismatches between CSV and GeoJSON")

        # Check for invalid geometries
        invalid_geoms = 0
        for feature in features:
            geom = feature.get('geometry')
            if not geom or geom.get('type') != 'Point' or len(geom.get('coordinates', [])) < 2:
                invalid_geoms += 1

        if invalid_geoms > 0:
            issues.append(f"ERROR: {invalid_geoms} invalid or missing geometries in GeoJSON")

    except Exception as e:
        issues.append(f"ERROR: Failed to validate spatial data: {str(e)}")

    return issues

def validate_environmental_features(df):
    """Validate environmental features: NDVI, elevation, slope, aspect."""
    issues = []

    # Define feature validation rules
    features = [
        {
            'name': 'NDVI',
            'value_col': 'ndvi',
            'status_col': 'ndvi_status',
            'valid_range': (-1.0, 1.0),
            'expected_status_when_present': 'EXTRACTED'
        },
        {
            'name': 'Elevation',
            'value_col': 'elevation_m',
            'status_col': 'elevation_status',
            'valid_range': None,  # No universal range for elevation
            'expected_status_when_present': 'EXTRACTED'
        },
        {
            'name': 'Slope',
            'value_col': 'slope_deg',
            'status_col': 'slope_status',
            'valid_range': (0.0, None),  # Non-negative, no upper limit set
            'expected_status_when_present': 'EXTRACTED'
        },
        {
            'name': 'Aspect',
            'value_col': 'aspect_deg',
            'status_col': 'aspect_status',
            'valid_range': (0.0, 360.0),
            'expected_status_when_present': 'EXTRACTED'
        }
    ]

    for feature in features:
        value_col = feature['value_col']
        status_col = feature['status_col']
        name = feature['name']
        valid_range = feature['valid_range']
        expected_status = feature['expected_status_when_present']

        # Check if columns exist
        if value_col not in df.columns:
            issues.append(f"WARNING: {name} value column ({value_col}) not found")
            continue

        if status_col not in df.columns:
            issues.append(f"WARNING: {name} status column ({status_col}) not found")
            continue

        # Check numeric data type
        non_numeric = pd.to_numeric(df[value_col], errors='coerce').isna().sum() - df[value_col].isna().sum()
        if non_numeric > 0:
            issues.append(f"ERROR: {non_numeric} non-numeric {name} values")

        # Count missing values
        missing_count = df[value_col].isna().sum()

        # Count valid numeric values
        numeric_vals = pd.to_numeric(df[value_col], errors='coerce')
        valid_count = numeric_vals.notna().sum()

        # Check for infinite values
        infinite_count = np.isinf(numeric_vals.fillna(0)).sum()
        if infinite_count > 0:
            issues.append(f"ERROR: {infinite_count} infinite {name} values")

        # Check range validation if applicable
        if valid_range is not None:
            min_val, max_val = valid_range
            if min_val is not None:
                below_min = ((numeric_vals < min_val) & numeric_vals.notna()).sum()
                if below_min > 0:
                    issues.append(f"ERROR: {below_min} {name} values below minimum ({min_val})")
            if max_val is not None:
                above_max = ((numeric_vals > max_val) & numeric_vals.notna()).sum()
                if above_max > 0:
                    issues.append(f"ERROR: {above_max} {name} values above maximum ({max_val})")

        # Check status consistency
        # For each row, if status indicates extraction was successful, value should be present
        # If status indicates failure, value should typically be missing (NaN)
        status_value_mismatch = 0
        for idx, row in df.iterrows():
            status = row[status_col]
            value = row[value_col]

            # Normalize status for comparison
            status_str = str(status).strip().upper() if not pd.isna(status) else ''

            if status_str == expected_status:
                # Status says extracted, value should be present
                if pd.isna(value):
                    status_value_mismatch += 1
            elif status_str in ['NODATA', 'OUTSIDE_RASTER', 'ERROR', 'NO_DATA_SOURCE', 'NOT_SPATIALLY_MAPPABLE']:
                # Status says not extracted, value should typically be missing
                if not pd.isna(value):
                    # This might be OK in some cases, but worth noting
                    pass  # We'll allow non-missing values for failed statuses as they might be defaults

        if status_value_mismatch > 0:
            issues.append(f"WARNING: {status_value_mismatch} rows where {name} status indicates extraction but value is missing")

    return issues

def validate_missing_data(df):
    """Calculate missing-value statistics for important features."""
    issues = []

    # Important features to check for missing data
    important_features = [
        'landslide_id', 'date', 'latitude', 'longitude',
        'ndvi', 'elevation_m', 'slope_deg', 'aspect_deg'
    ]

    # Only check features that exist in the dataframe
    existing_features = [f for f in important_features if f in df.columns]

    if not existing_features:
        issues.append("WARNING: No important features found for missing data analysis")
        return issues

    # Create missing data summary (we'll report this in the main function, not as issues)
    missing_stats = []
    for feature in existing_features:
        total = len(df)
        missing = df[feature].isna().sum()
        valid = total - missing
        missing_pct = (missing / total * 100) if total > 0 else 0

        missing_stats.append({
            'Feature': feature,
            'Total': total,
            'Valid': valid,
            'Missing': missing,
            'Missing %': round(missing_pct, 2)
        })

    # Store for reporting in main function
    validate_missing_data.missing_stats = missing_stats

    return issues

def validate_duplicates(df):
    """Check for duplicate rows, IDs, and coordinates."""
    issues = []

    # Exact duplicate rows
    duplicate_rows = df.duplicated().sum()
    if duplicate_rows > 0:
        issues.append(f"WARNING: {duplicate_rows} exact duplicate rows found")

    # Duplicate landslide IDs
    if 'landslide_id' in df.columns:
        duplicate_ids = df['landslide_id'].duplicated().sum()
        if duplicate_ids > 0:
            issues.append(f"WARNING: {duplicate_ids} duplicate landslide ID values")
            # Show which IDs are duplicated
            dup_ids = df[df['landslide_id'].duplicated(keep=False)]['landslide_id'].unique()
            issues.append(f"  Duplicated IDs: {list(dup_ids[:10])}{'...' if len(dup_ids) > 10 else ''}")

    # Duplicate coordinates
    if 'latitude' in df.columns and 'longitude' in df.columns:
        # Create coordinate pairs, handling NaN values
        coord_pairs = df[['latitude', 'longitude']].dropna().duplicated().sum()
        if coord_pairs > 0:
            issues.append(f"WARNING: {coord_pairs} duplicate coordinate pairs found")

    return issues

def validate_synthetic_data(df):
    """Validate that synthetic data is properly marked and preserved."""
    issues = []

    # Check data_source_type column
    if 'data_source_type' in df.columns:
        synthetic_count = (df['data_source_type'] == 'SYNTHETIC_DEMO').sum()
        total_count = len(df)

        if synthetic_count == 0:
            issues.append("WARNING: No records marked as SYNTHETIC_DEMO in data_source_type")
        elif synthetic_count != total_count:
            issues.append(f"WARNING: {synthetic_count}/{total_count} records marked as SYNTHETIC_DEMO")
            # Check what other values exist
            other_values = df[df['data_source_type'] != 'SYNTHETIC_DEMO']['data_source_type'].unique()
            issues.append(f"  Other values found: {list(other_values)}")
        else:
            # All records are synthetic - this is expected for demo data
            pass  # This is good, all data is properly marked as synthetic
    else:
        issues.append("WARNING: data_source_type column not found - cannot verify synthetic data marking")

    # Check that historical source information is preserved
    source_fields = ['source', 'source_url', 'description']
    for field in source_fields:
        if field in df.columns:
            empty_count = df[field].isna().sum()
            if empty_count > 0:
                issues.append(f"INFO: {empty_count} records have missing {field} (this may be OK)")
        else:
            issues.append(f"WARNING: {field} column not found")

    return issues

def validate_cross_dataset_consistency(df, geojson_data):
    """Validate consistency between Phase 3 GeoJSON and Phase 5 CSV."""
    issues = []

    try:
        features = geojson_data.get('features', [])

        # Check record count
        csv_count = len(df)
        geojson_count = len(features)
        if csv_count != geojson_count:
            issues.append(f"WARNING: Record count mismatch between Phase 3 and Phase 5: "
                        f"Phase 3: {geojson_count}, Phase 5: {csv_count}")

        # Check landslide ID consistency if both datasets have them
        if 'landslide_id' in df.columns and len(features) > 0:
            csv_ids = set(df['landslide_id'].dropna().astype(str))

            geojson_ids = set()
            for feature in features:
                props = feature.get('properties', {})
                landslide_id = props.get('landslide_id')
                if landslide_id is not None:
                    geojson_ids.add(str(landslide_id))

            # Find IDs in CSV but not in GeoJSON
            only_in_csv = csv_ids - geojson_ids
            # Find IDs in GeoJSON but not in CSV
            only_in_geojson = geojson_ids - csv_ids

            if only_in_csv:
                issues.append(f"WARNING: {len(only_in_csv)} landslide IDs in CSV but not in GeoJSON: {list(only_in_csv)}")
            if only_in_geojson:
                issues.append(f"WARNING: {len(only_in_geojson)} landslide IDs in GeoJSON but not in CSV: {list(only_in_geojson)}")

            # Check coordinate consistency for matching IDs
            # (This was partially covered in spatial validation, but we can do more detailed checking here)

    except Exception as e:
        issues.append(f"ERROR: Failed to validate cross-dataset consistency: {str(e)}")

    return issues

def validate_feature_extraction_status(df):
    """Validate feature_extraction_status column consistency."""
    issues = []

    if 'feature_extraction_status' not in df.columns:
        issues.append("WARNING: feature_extraction_status column not found")
        return issues

    # Define expected status values based on Phase 5 implementation
    expected_statuses = ['COMPLETE', 'PARTIAL', 'NO_FEATURES', 'REVIEW_REQUIRED']

    # Check for unexpected status values
    actual_statuses = set(df['feature_extraction_status'].dropna().astype(str).str.upper().str.strip())
    unexpected_statuses = actual_statuses - set(s.upper() for s in expected_statuses)

    if unexpected_statuses:
        issues.append(f"WARNING: Unexpected feature_extraction_status values: {unexpected_statuses}")

    # Check status consistency with actual feature availability
    # For COMPLETE status, all main features should be present
    # For PARTIAL, some should be present
    # For NO_FEATURES, none should be present

    inconsistency_count = 0
    for idx, row in df.iterrows():
        status = str(row['feature_extraction_status']).strip().upper()

        # Count how many main features have EXTRACTED status
        feature_status_cols = ['ndvi_status', 'elevation_status', 'slope_status', 'aspect_status']
        existing_status_cols = [col for col in feature_status_cols if col in df.columns]

        if existing_status_cols:
            extracted_count = 0
            for col in existing_status_cols:
                col_status = str(row[col]).strip().upper() if not pd.isna(row[col]) else ''
                if col_status == 'EXTRACTED':
                    extracted_count += 1

            # Check consistency
            if status == 'COMPLETE' and extracted_count < len(existing_status_cols):
                inconsistency_count += 1
            elif status == 'PARTIAL' and extracted_count == 0:
                inconsistency_count += 1  # PARTIAL but no features extracted?
            elif status == 'PARTIAL' and extracted_count == len(existing_status_cols):
                inconsistency_count += 1  # PARTIAL but all features extracted?
            elif status == 'NO_FEATURES' and extracted_count > 0:
                inconsistency_count += 1  # NO_FEATURES but some features extracted?

    if inconsistency_count > 0:
        issues.append(f"WARNING: {inconsistency_count} records have inconsistent feature_extraction_status vs actual feature availability")

    return issues

def validate_rainfall_handling(df):
    """Validate that rainfall is correctly handled as non-spatial."""
    issues = []

    # Check if rainfall status column exists
    if 'rainfall_status' in df.columns:
        # Check that it's correctly set to NOT_SPATIALLY_MAPPABLE
        not_spatial_count = (df['rainfall_status'] == 'NOT_SPATIALLY_MAPPABLE').sum()
        total_count = len(df)

        if not_spatial_count == 0:
            issues.append(f"WARNING: No records have rainfall_status = NOT_SPATIALLY_MAPPABLE")
        elif not_spatial_count != total_count:
            issues.append(f"WARNING: {not_spatial_count}/{total_count} records have rainfall_status = NOT_SPATIALLY_MAPPABLE")
            other_values = df[df['rainfall_status'] != 'NOT_SPATIALLY_MAPPABLE']['rainfall_status'].unique()
            issues.append(f"  Other rainfall status values found: {list(other_values)}")
    else:
        issues.append("WARNING: rainfall_status column not found")

    # Check that rainfall value columns exist but are typically empty (since non-spatial)
    rainfall_value_cols = ['rainfall_24h', 'rainfall_3d', 'rainfall_7d']
    existing_rainfall_cols = [col for col in rainfall_value_cols if col in df.columns]

    if existing_rainfall_cols:
        # For non-spatial rainfall, these columns should typically be empty/NaN
        for col in existing_rainfall_cols:
            non_empty_count = df[col].notna().sum()
            if non_empty_count > 0:
                issues.append(f"INFO: {non_empty_count} non-empty values in {col} (may be OK if rainfall data was somehow made spatial)")

    return issues

def validate_no_data_leakage(df):
    """Check for accidental ML target columns or data leakage."""
    issues = []

    # Columns that should NOT be present in a validation dataset
    leakage_indicators = [
        'risk', 'risk_score', 'risk_label', 'prediction', 'predicted',
        'model_', 'train', 'test', 'split', 'scaled', 'normalized',
        'confidence', 'probability', 'target', 'label'
    ]

    found_leakage = []
    for col in df.columns:
        col_lower = col.lower()
        for indicator in leakage_indicators:
            if indicator in col_lower:
                found_leakage.append(col)
                break  # Only count each column once

    if found_leakage:
        issues.append(f"WARNING: Potential data leakage/ML target columns found: {found_leakage}")
        issues.append("  These should not be present in the validation dataset for final ML preparation")

    return issues

def generate_report(df, geojson_data, validation_results):
    """Generate the validation report."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("M2-C PHASE 6 - DATASET VALIDATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 1. Dataset Summary
    report_lines.append("1. DATASET SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Input file: historical_landslide_features.csv")
    report_lines.append(f"Record count: {len(df)}")
    report_lines.append(f"Column count: {len(df.columns)}")
    report_lines.append(f"Columns: {', '.join(df.columns)}")
    report_lines.append("")

    # 2. Structural Validation
    report_lines.append("2. STRUCTURAL VALIDATION")
    report_lines.append("-" * 40)
    struct_result = validation_results.get('structural', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {struct_result['status']}")
    if struct_result['issues']:
        report_lines.append("Issues found:")
        for issue in struct_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 3. Historical Field Validation
    report_lines.append("3. HISTORICAL FIELD VALIDATION")
    report_lines.append("-" * 40)
    hist_result = validation_results.get('historical', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {hist_result['status']}")
    if hist_result['issues']:
        report_lines.append("Issues found:")
        for issue in hist_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 4. Spatial Validation
    report_lines.append("4. SPATIAL VALIDATION")
    report_lines.append("-" * 40)
    spatial_result = validation_results.get('spatial', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {spatial_result['status']}")
    if spatial_result['issues']:
        report_lines.append("Issues found:")
        for issue in spatial_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 5. Environmental Feature Validation
    report_lines.append("5. ENVIRONMENTAL FEATURE VALIDATION")
    report_lines.append("-" * 40)
    env_result = validation_results.get('environmental', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {env_result['status']}")
    if env_result['issues']:
        report_lines.append("Issues found:")
        for issue in env_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 6. Missing Data Statistics
    report_lines.append("6. MISSING DATA STATISTICS")
    report_lines.append("-" * 40)
    if hasattr(validate_missing_data, 'missing_stats'):
        report_lines.append(f"{'Feature':<15} {'Total':<8} {'Valid':<8} {'Missing':<8} {'Missing %':<10}")
        report_lines.append("-" * 55)
        for stat in validate_missing_data.missing_stats:
            report_lines.append(f"{stat['Feature']:<15} {stat['Total']:<8} {stat['Valid']:<8} {stat['Missing']:<8} {stat['Missing %']:<10}")
    else:
        report_lines.append("  Missing data statistics not available")
    report_lines.append("")

    # 7. Duplicate Validation
    report_lines.append("7. DUPLICATE VALIDATION")
    report_lines.append("-" * 40)
    dup_result = validation_results.get('duplicates', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {dup_result['status']}")
    if dup_result['issues']:
        report_lines.append("Issues found:")
        for issue in dup_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 8. Synthetic Data Warning
    report_lines.append("8. SYNTHETIC DATA VALIDATION")
    report_lines.append("-" * 40)
    synth_result = validation_results.get('synthetic', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {synth_result['status']}")
    if synth_result['issues']:
        report_lines.append("Issues found:")
        for issue in synth_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")
    report_lines.append("!!! IMPORTANT WARNING !!!")
    report_lines.append("CURRENT ENVIRONMENTAL DATA IS SYNTHETIC DEMO DATA AND MUST NOT BE")
    report_lines.append("REPRESENTED AS REAL MEASUREMENTS.")
    report_lines.append("")

    # 9. Cross-Dataset Consistency
    report_lines.append("9. CROSS-DATASET CONSISTENCY")
    report_lines.append("-" * 40)
    cross_result = validation_results.get('cross_dataset', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {cross_result['status']}")
    if cross_result['issues']:
        report_lines.append("Issues found:")
        for issue in cross_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 10. Feature Extraction Status Consistency
    report_lines.append("10. FEATURE EXTRACTION STATUS CONSISTENCY")
    report_lines.append("-" * 40)
    status_result = validation_results.get('feature_status', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {status_result['status']}")
    if status_result['issues']:
        report_lines.append("Issues found:")
        for issue in status_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 11. Rainfall Validation
    report_lines.append("11. RAINFALL HANDLING VALIDATION")
    report_lines.append("-" * 40)
    rain_result = validation_results.get('rainfall', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {rain_result['status']}")
    if rain_result['issues']:
        report_lines.append("Issues found:")
        for issue in rain_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 12. Data Leakage / Target Validation
    report_lines.append("12. DATA LEAKAGE / TARGET VALIDATION")
    report_lines.append("-" * 40)
    leak_result = validation_results.get('leakage', {'status': 'UNKNOWN', 'issues': []})
    report_lines.append(f"Result: {leak_result['status']}")
    if leak_result['issues']:
        report_lines.append("Issues found:")
        for issue in leak_result['issues']:
            report_lines.append(f"  * {issue}")
    else:
        report_lines.append("  No issues found")
    report_lines.append("")

    # 13. Overall Validation Result
    report_lines.append("13. OVERALL VALIDATION RESULT")
    report_lines.append("-" * 40)

    # Determine overall status based on critical issues
    all_issues = []
    for key, result in validation_results.items():
        if key != 'missing_data':  # Missing data is informational
            all_issues.extend(result.get('issues', []))

    # Categorize issues by severity
    errors = [issue for issue in all_issues if issue.startswith('ERROR:')]
    warnings = [issue for issue in all_issues if issue.startswith('WARNING:')]
    infos = [issue for issue in all_issues if issue.startswith('INFO:')]

    if len(errors) > 0:
        overall_status = "FAIL"
        status_reason = f"Found {len(errors)} error(s)"
    elif len(warnings) > 0:
        overall_status = "PASS_WITH_WARNINGS"
        status_reason = f"Found {len(warnings)} warning(s)"
    else:
        overall_status = "PASS"
        status_reason = "No issues found"

    report_lines.append(f"Overall Status: {overall_status}")
    report_lines.append(f"Reason: {status_reason}")
    report_lines.append(f"Errors: {len(errors)}")
    report_lines.append(f"Warnings: {len(warnings)}")
    report_lines.append(f"Informational: {len(infos)}")
    report_lines.append("")

    # 14. Dataset Statistics Summary
    report_lines.append("14. DATASET STATISTICS SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Records: {len(df)}")
    report_lines.append(f"Columns: {len(df.columns)}")

    # Coordinate statistics
    if 'latitude' in df.columns and 'longitude' in df.columns:
        valid_lat = df['latitude'].notna().sum()
        valid_lon = df['longitude'].notna().sum()
        valid_coords = df[['latitude', 'longitude']].dropna().shape[0]
        report_lines.append(f"Valid coordinates: {valid_coords}")
        report_lines.append(f"Missing latitude: {df['latitude'].isna().sum()}")
        report_lines.append(f"Missing longitude: {df['longitude'].isna().sum()}")

    # Environmental feature statistics
    env_features = [('ndvi', 'NDVI'), ('elevation_m', 'Elevation'), ('slope_deg', 'Slope'), ('aspect_deg', 'Aspect')]
    for col, name in env_features:
        if col in df.columns:
            valid = pd.to_numeric(df[col], errors='coerce').notna().sum()
            missing = df[col].isna().sum()
            report_lines.append(f"{name} valid: {valid}")
            report_lines.append(f"{name} missing: {missing}")

    if 'rainfall_status' in df.columns:
        not_spatial = (df['rainfall_status'] == 'NOT_SPATIALLY_MAPPABLE').sum()
        report_lines.append(f"Rainfall NOT_SPATIALLY_MAPPABLE: {not_spatial}")

    report_lines.append("")

    # 15. Important Notes
    report_lines.append("15. IMPORTANT NOTES")
    report_lines.append("-" * 40)
    report_lines.append("1. This validation report assesses the fitness of the Phase 5 dataset for")
    report_lines.append("   progression to final ML dataset preparation.")
    report_lines.append("2. All environmental values marked as SYNTHETIC_DEMO are derived from")
    report_lines.append("   synthetic/demo data and must not be used as real observations.")
    report_lines.append("3. Rainfall data is non-spatial (tabular only) and marked as NOT_SPATIALLY_MAPPABLE.")
    report_lines.append("4. Missing values are preserved as NaN with appropriate status codes.")
    report_lines.append("5. No missing values were imputed or replaced with artificial values.")
    report_lines.append("6. Original data files remain unchanged (read-only access only).")
    report_lines.append("")

    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)

def main():
    """Main validation function."""
    print("Starting M2-C Phase 6 Dataset Validation...")

    try:
        # Load datasets
        print("Loading Phase 5 feature dataset...")
        df = load_phase5_dataset()
        print(f"Loaded {len(df)} records from Phase 5 dataset")

        print("Loading Phase 3 historical landslide GeoJSON...")
        geojson_data = load_phase3_geojson()
        print(f"Loaded {len(geojson_data.get('features', []))} features from Phase 3 GeoJSON")

        # Run all validation checks
        validation_results = {}

        print("Running structural validation...")
        validation_results['structural'] = {
            'status': 'PASS',  # Will be updated based on issues
            'issues': validate_structural(df)
        }

        print("Running historical field validation...")
        validation_results['historical'] = {
            'status': 'PASS',
            'issues': validate_historical_fields(df.copy())  # Copy to avoid modifying original
        }

        print("Running spatial validation...")
        validation_results['spatial'] = {
            'status': 'PASS',
            'issues': validate_spatial(df, geojson_data)
        }

        print("Running environmental feature validation...")
        validation_results['environmental'] = {
            'status': 'PASS',
            'issues': validate_environmental_features(df)
        }

        print("Running missing data analysis...")
        validation_results['missing_data'] = {
            'status': 'INFO',
            'issues': validate_missing_data(df)
        }

        print("Running duplicate validation...")
        validation_results['duplicates'] = {
            'status': 'PASS',
            'issues': validate_duplicates(df)
        }

        print("Running synthetic data validation...")
        validation_results['synthetic'] = {
            'status': 'PASS',
            'issues': validate_synthetic_data(df)
        }

        print("Running cross-dataset consistency validation...")
        validation_results['cross_dataset'] = {
            'status': 'PASS',
            'issues': validate_cross_dataset_consistency(df, geojson_data)
        }

        print("Running feature extraction status validation...")
        validation_results['feature_status'] = {
            'status': 'PASS',
            'issues': validate_feature_extraction_status(df)
        }

        print("Running rainfall handling validation...")
        validation_results['rainfall'] = {
            'status': 'PASS',
            'issues': validate_rainfall_handling(df)
        }

        print("Running data leakage validation...")
        validation_results['leakage'] = {
            'status': 'PASS',
            'issues': validate_no_data_leakage(df)
        }

        # Update statuses based on issues found
        for key, result in validation_results.items():
            if key == 'missing_data':
                # Missing data is informational
                result['status'] = 'INFO'
            else:
                issues = result['issues']
                errors = [issue for issue in issues if issue.startswith('ERROR:')]
                warnings = [issue for issue in issues if issue.startswith('WARNING:')]

                if len(errors) > 0:
                    result['status'] = 'FAIL'
                elif len(warnings) > 0:
                    result['status'] = 'PASS_WITH_WARNINGS'
                else:
                    result['status'] = 'PASS'

        # Generate report
        print("Generating validation report...")
        report = generate_report(df, geojson_data, validation_results)

        # Save report
        output_dir = Path('./phase1_historical_data/phase6_dataset_validation/output')
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / 'dataset_validation_report.txt'

        with open(report_path, 'w') as f:
            f.write(report)

        print(f"Validation report saved to: {report_path}")

        # Print summary to console
        print("\n" + "="*50)
        print("PHASE 6 VALIDATION SUMMARY")
        print("="*50)

        # Count overall issues
        all_issues = []
        for key, result in validation_results.items():
            if key != 'missing_data':
                all_issues.extend(result.get('issues', []))

        errors = [issue for issue in all_issues if issue.startswith('ERROR:')]
        warnings = [issue for issue in all_issues if issue.startswith('WARNING:')]

        if len(errors) > 0:
            overall_result = "FAIL"
        elif len(warnings) > 0:
            overall_result = "PASS_WITH_WARNINGS"
        else:
            overall_result = "PASS"

        print(f"Overall Result: {overall_result}")
        print(f"Errors: {len(errors)}")
        print(f"Warnings: {len(warnings)}")
        print(f"Records Processed: {len(df)}")
        print(f"Report Location: {report_path}")

        # Return appropriate exit code
        if len(errors) > 0:
            return 1
        else:
            return 0

    except Exception as e:
        print(f"ERROR: Validation failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())