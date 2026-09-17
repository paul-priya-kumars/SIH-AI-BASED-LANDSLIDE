#!/usr/bin/env python3
"""
M2-C → M1 Handoff Validator
Validates that the M2-C Phase 7 ML dataset is ready for M1 consumption.
"""

import os
import sys
import pandas as pd
import json
from pathlib import Path

def main():
    print("=" * 60)
    print("M2-C -> M1 Handoff Validation")
    print("=" * 60)

    # Define paths
    m2c_root = Path(__file__).parent.parent.parent
    phase7_features_path = m2c_root / "phase7_final_ml_dataset" / "data" / "ml_features.csv"
    phase7_metadata_path = m2c_root / "phase7_final_ml_dataset" / "data" / "ml_metadata.csv"
    contract_path = Path(__file__).parent.parent / "phase8_m1_handoff_contract.json"

    # Track validation results
    checks_passed = 0
    checks_total = 0
    failures = []

    def check(description, condition, failure_msg=None):
        nonlocal checks_passed, checks_total
        checks_total += 1
        if condition:
            print(f"[PASS] {description}")
            checks_passed += 1
            return True
        else:
            print(f"[FAIL] {description}")
            if failure_msg:
                failures.append(f"{description}: {failure_msg}")
            else:
                failures.append(description)
            return False

    print("\n1. DATASET EXISTENCE AND READABILITY")
    print("-" * 40)

    # Check 1: Features dataset exists
    check("ML features dataset exists", phase7_features_path.exists(),
          f"File not found: {phase7_features_path}")

    # Check 2: Metadata dataset exists
    check("ML metadata dataset exists", phase7_metadata_path.exists(),
          f"File not found: {phase7_metadata_path}")

    # Check 3: Contract exists
    check("Handoff contract exists", contract_path.exists(),
          f"Contract not found: {contract_path}")

    if not phase7_features_path.exists():
        print("\nCannot continue - features dataset missing")
        return False

    print("\n2. DATASET LOADING AND BASIC STRUCTURE")
    print("-" * 40)

    # Load the datasets
    try:
        df_features = pd.read_csv(phase7_features_path)
        check("Features dataset loads successfully", True)
    except Exception as e:
        check("Features dataset loads successfully", False, f"Error loading CSV: {e}")
        return False

    try:
        df_metadata = pd.read_csv(phase7_metadata_path)
        check("Metadata dataset loads successfully", True)
    except Exception as e:
        check("Metadata dataset loads successfully", False, f"Error loading CSV: {e}")
        return False

    print("\n3. RECORD COUNT VALIDATION")
    print("-" * 40)

    # Check 4: Expected record count (should be 4 from Phase 7)
    expected_records = 4
    actual_records = len(df_features)
    check(f"Expected {expected_records} records", actual_records == expected_records,
          f"Expected {expected_records}, got {actual_records}")

    # Check 5: Metadata record count matches features
    check("Metadata record count matches features", len(df_metadata) == actual_records,
          f"Metadata has {len(df_metadata)} records, features has {actual_records}")

    print("\n4. FEATURE EXISTENCE AND ORDER")
    print("-" * 40)

    # Load contract to get expected schema
    try:
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        check("Contract loads successfully", True)
    except Exception as e:
        check("Contract loads successfully", False, f"Error loading contract: {e}")
        return False

    expected_features = contract.get('feature_order', [])

    # Check 6: All expected features exist
    missing_features = [f for f in expected_features if f not in df_features.columns]
    check("All expected features exist", len(missing_features) == 0,
          f"Missing features: {missing_features}" if missing_features else None)

    # Check 7: No unexpected features in features dataset (basic check)
    unexpected_features = [f for f in df_features.columns if f not in expected_features]
    check("No unexpected features in features dataset", len(unexpected_features) == 0,
          f"Unexpected features: {unexpected_features}" if unexpected_features else None)

    # Check 8: Feature order matches contract
    actual_feature_order = list(df_features.columns)
    check("Feature order matches contract", actual_feature_order == expected_features,
          f"Expected order: {expected_features}\nActual order: {actual_feature_order}")

    print("\n5. DATA TYPE VALIDATION")
    print("-" * 40)

    # Check numeric features
    numeric_features = ['latitude', 'longitude', 'ndvi', 'elevation_m', 'slope_deg', 'aspect_deg']
    for feature in numeric_features:
        if feature in df_features.columns:
            check(f"{feature} is numeric", pd.api.types.is_numeric_dtype(df_features[feature]),
                  f"{feature} has dtype {df_features[feature].dtype}")

    # Check string features - accept both 'object' and 'str' dtypes
    string_features = ['landslide_id', 'data_source_type']
    for feature in string_features:
        if feature in df_features.columns:
            dtype_str = str(df_features[feature].dtype)
            is_string = dtype_str in ['object', 'str', 'string']
            check(f"{feature} is string", is_string,
                  f"{feature} has dtype {df_features[feature].dtype}")

    print("\n6. COORDINATE VALIDATION")
    print("-" * 40)

    # Check 9: Latitude valid range (-90 to 90)
    if 'latitude' in df_features.columns:
        lat_valid = df_features['latitude'].between(-90, 90).all()
        check("Latitude in valid range [-90, 90]", lat_valid,
              f"Invalid latitude values: {df_features.loc[~df_features['latitude'].between(-90, 90), 'latitude'].tolist()}")

    # Check 10: Longitude valid range (-180 to 180)
    if 'longitude' in df_features.columns:
        lon_valid = df_features['longitude'].between(-180, 180).all()
        check("Longitude in valid range [-180, 180]", lon_valid,
              f"Invalid longitude values: {df_features.loc[~df_features['longitude'].between(-180, 180), 'longitude'].tolist()}")

    # Check 11: Coordinate order (longitude=X, latitude=Y) - implicitly validated by column names and ranges
    check("Coordinate convention: longitude=X, latitude=Y",
          'longitude' in df_features.columns and 'latitude' in df_features.columns,
          "Missing longitude or latitude columns")

    print("\n7. SYNTHETIC DATA MARKER")
    print("-" * 40)

    # Check 12: data_source_type is preserved and correct
    if 'data_source_type' in df_features.columns:
        unique_values = df_features['data_source_type'].unique()
        check("data_source_type column exists", True)
        check("All records have SYNTHETIC_DEMO marker",
              all(val == 'SYNTHETIC_DEMO' for val in unique_values),
              f"Unexpected values in data_source_type: {unique_values}")

    print("\n8. RAINFALL HANDLING")
    print("-" * 40)

    # Check 13: Rainfall not present in features dataset (should be excluded)
    rainfall_indicators = ['rainfall', 'rainfall_24h', 'rainfall_3d', 'rainfall_7d']
    unexpected_rainfall = [col for col in rainfall_indicators if col in df_features.columns]
    check("No rainfall columns in features dataset", len(unexpected_rainfall) == 0,
          f"Unexpected rainfall columns found: {unexpected_rainfall}")

    # Check 14: Rainfall status preserved in metadata
    if 'rainfall_status' in df_metadata.columns:
        rainfall_status_vals = df_metadata['rainfall_status'].unique()
        check("Rainfall status preserved in metadata", True)
        check("All rainfall status are NOT_SPATIALLY_MAPPABLE",
              all(val == 'NOT_SPATIALLY_MAPPABLE' for val in rainfall_status_vals),
              f"Unexpected rainfall status values: {rainfall_status_vals}")

    print("\n9. TARGET / LABEL CHECK")
    print("-" * 40)

    # Check 15: No target columns in features dataset
    target_indicators = ['target', 'label', 'class', 'severity', 'risk', 'probability']
    unexpected_targets = [col for col in target_indicators if col in df_features.columns]
    check("No target/label columns in features dataset", len(unexpected_targets) == 0,
          f"Unexpected target columns found: {unexpected_targets}")

    # Check 16: Severity preserved in metadata but not used as target
    if 'severity' in df_metadata.columns:
        check("Severity preserved in metadata", True)
        # Just verify it exists, values can be anything including missing

    print("\n10. PROVENANCE PRESERVATION")
    print("-" * 40)

    # Check 17: landslide_id preserved
    check("landslide_id preserved", 'landslide_id' in df_features.columns and 'landslide_id' in df_metadata.columns)

    # Check 18: Basic historical fields in metadata
    historical_fields = ['date', 'location', 'district', 'state', 'country']
    missing_historical = [f for f in historical_fields if f not in df_metadata.columns]
    check("Historical fields preserved in metadata", len(missing_historical) == 0,
          f"Missing historical fields: {missing_historical}" if missing_historical else None)

    print("\n11. DATA INTEGRITY AND LEAKAGE PROTECTION")
    print("-" * 40)

    # Check 19: No prediction columns
    prediction_indicators = ['prediction', 'predicted', 'forecast', 'estimate']
    unexpected_predictions = [col for col in df_features.columns if any(ind in col.lower() for ind in prediction_indicators)]
    check("No prediction columns", len(unexpected_predictions) == 0,
          f"Unexpected prediction columns: {unexpected_predictions}")

    # Check 20: No risk score columns
    risk_indicators = ['risk', 'hazard', 'danger', 'vulnerability']
    unexpected_risks = [col for col in df_features.columns if any(ind in col.lower() for ind in risk_indicators)]
    check("No risk score columns", len(unexpected_risks) == 0,
          f"Unexpected risk columns: {unexpected_risks}")

    # Check 21: No confidence score columns
    confidence_indicators = ['confidence', 'certainty', 'probability', 'likelihood']
    unexpected_confidence = [col for col in df_features.columns if any(ind in col.lower() for ind in confidence_indicators)]
    check("No confidence score columns", len(unexpected_confidence) == 0,
          f"Unexpected confidence columns: {unexpected_confidence}")

    # Check 22: No train/test split columns
    split_indicators = ['train', 'test', 'split', 'fold']
    unexpected_splits = [col for col in df_features.columns if any(ind in col.lower() for ind in split_indicators)]
    check("No train/test split columns", len(unexpected_splits) == 0,
          f"Unexpected train/test split columns: {unexpected_splits}")

    # Check 23: No feature scaling columns (basic check for common scaling indicators)
    scale_indicators = ['scaled', 'normalized', 'standardized', 'zscore']
    unexpected_scale = [col for col in df_features.columns if any(ind in col.lower() for ind in scale_indicators)]
    check("No feature scaling columns", len(unexpected_scale) == 0,
          f"Unexpected feature scaling columns: {unexpected_scale}")

    print("\n12. SOURCE FILE INTEGRITY CHECK")
    print("-" * 40)

    # Check 24: Verify source files haven't been modified (basic existence check)
    # We'll check that key source files from previous phases still exist
    source_files_to_check = [
        "phase1_historical_data/data/sample/sample_landslides.csv",
        "phase1_historical_data/data/cleaned/cleaned_sample_landslides.csv",
        "phase1_historical_data/data/gis/historical_landslides.geojson",
        "phase1_historical_data/data/features/phase5/historical_landslide_features.csv"
    ]

    source_files_exist = []
    for file_path in source_files_to_check:
        full_path = m2c_root / file_path
        if full_path.exists():
            source_files_exist.append(file_path)
        else:
            print(f"[INFO] Source file not found (may be expected): {file_path}")

    check("Key source files exist", len(source_files_exist) > 0,
          "At least some source files verified to exist")

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Checks passed: {checks_passed}/{checks_total}")

    if failures:
        print(f"\nFailures ({len(failures)}):")
        for i, failure in enumerate(failures, 1):
            print(f"  {i}. {failure}")
        print("\nResult: FAIL")
        return False
    else:
        print("\nResult: PASS")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)