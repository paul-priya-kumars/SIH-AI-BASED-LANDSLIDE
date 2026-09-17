#!/usr/bin/env python3
"""
Tests for Phase 7 Final ML Dataset Preparation
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import json

# Add the scripts directory to the path so we can import the preparation script
sys.path.append(str(Path(__file__).parent))
from prepare_ml_dataset import (
    load_phase5_dataset,
    validate_input_columns,
    prepare_ml_features,
    prepare_ml_metadata,
    create_feature_manifest
)

def test_load_phase5_dataset():
    """Test that we can load the Phase 5 dataset."""
    try:
        df = load_phase5_dataset()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        print("PASS: test_load_phase5_dataset")
        return True
    except Exception as e:
        print(f"FAIL: test_load_phase5_dataset - {str(e)}")
        return False

def test_validate_input_columns():
    """Test input column validation."""
    try:
        df = load_phase5_dataset()
        # This should not raise an exception
        validate_input_columns(df)
        print("PASS: test_validate_input_columns")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_input_columns - {str(e)}")
        return False

def test_prepare_ml_features():
    """Test ML features preparation."""
    try:
        df = load_phase5_dataset()
        ml_features = prepare_ml_features(df)

        # Check that we have the expected columns
        expected_columns = ['landslide_id', 'latitude', 'longitude', 'ndvi', 'elevation_m', 'slope_deg', 'aspect_deg', 'data_source_type']
        assert list(ml_features.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(ml_features.columns)}"

        # Check that we have the same number of records
        assert len(ml_features) == len(df), f"Record count mismatch: {len(ml_features)} vs {len(df)}"

        # Check that landslide_id is string
        assert ml_features['landslide_id'].dtype == 'object', "landslide_id should be string"

        # Check that data_source_type is string
        assert ml_features['data_source_type'].dtype == 'object', "data_source_type should be string"

        # Check that environmental features are numeric
        for col in ['ndvi', 'elevation_m', 'slope_deg', 'aspect_deg']:
            assert pd.api.types.is_numeric_dtype(ml_features[col]), f"{col} should be numeric"

        # Check that coordinates are numeric
        assert pd.api.types.is_numeric_dtype(ml_features['latitude']), "latitude should be numeric"
        assert pd.api.types.is_numeric_dtype(ml_features['longitude']), "longitude should be numeric"

        print("PASS: test_prepare_ml_features")
        return True
    except Exception as e:
        print(f"FAIL: test_prepare_ml_features - {str(e)}")
        return False

def test_prepare_ml_metadata():
    """Test ML metadata preparation."""
    try:
        df = load_phase5_dataset()
        ml_metadata = prepare_ml_metadata(df)

        # Check that we have landslide_id
        assert 'landslide_id' in ml_metadata.columns, "landslide_id should be in metadata"

        # Check that we have historical columns
        expected_historical = ['date', 'location', 'district', 'state', 'country', 'source', 'source_url', 'severity', 'description']
        for col in expected_historical:
            if col in df.columns:  # Only check if it exists in input
                assert col in ml_metadata.columns, f"{col} should be in metadata"

        # Check that we have status columns
        expected_status = ['data_quality_status', 'ndvi_status', 'rainfall_24h', 'rainfall_3d', 'rainfall_7d', 'rainfall_status',
                          'elevation_status', 'slope_status', 'aspect_status', 'feature_extraction_status']
        for col in expected_status:
            if col in df.columns:  # Only check if it exists in input
                assert col in ml_metadata.columns, f"{col} should be in metadata"

        # Check that we have the same number of records
        assert len(ml_metadata) == len(df), f"Record count mismatch: {len(ml_metadata)} vs {len(df)}"

        # Check that landslide_id is string
        assert ml_metadata['landslide_id'].dtype == 'object', "landslide_id should be string"

        print("PASS: test_prepare_ml_metadata")
        return True
    except Exception as e:
        print(f"FAIL: test_prepare_ml_metadata - {str(e)}")
        return False

def test_create_feature_manifest():
    """Test feature manifest creation."""
    try:
        manifest = create_feature_manifest()

        # Check that we have the expected structure
        assert 'ml_features' in manifest, "Manifest should have ml_features key"
        assert 'ml_metadata' in manifest, "Manifest should have ml_metadata key"

        # Check that we have the expected features
        expected_features = ['landslide_id', 'latitude', 'longitude', 'ndvi', 'elevation_m', 'slope_deg', 'aspect_deg', 'data_source_type']
        for feature in expected_features:
            assert feature in manifest['ml_features'], f"Feature {feature} should be in manifest"

        # Check that landslide_id has the expected properties
        landslide_id_info = manifest['ml_features']['landslide_id']
        assert landslide_id_info['data_type'] == 'string', "landslide_id should be string type"
        assert 'Traceability' in landslide_id_info['purpose'], "landslide_id purpose should mention traceability"

        # Check that ndvi has the expected properties
        ndvi_info = manifest['ml_features']['ndvi']
        assert ndvi_info['data_type'] == 'float', "ndvi should be float type"
        assert ndvi_info['valid_range'] == [-1.0, 1.0], "ndvi should have valid range [-1, 1]"
        assert 'Synthetic' in ndvi_info['notes'], "ndvi notes should mention synthetic"

        print("PASS: test_create_feature_manifest")
        return True
    except Exception as e:
        print(f"FAIL: test_create_feature_manifest - {str(e)}")
        return False

def test_output_files_exist():
    """Test that the output files are created correctly."""
    try:
        # Run the preparation script to generate output files
        import subprocess
        result = subprocess.run([sys.executable, 'prepare_ml_dataset.py'],
                              capture_output=True, text=True, cwd=Path(__file__).parent)

        # Check that the script ran successfully
        assert result.returncode == 0, f"Preparation script failed with return code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"

        # Check that the output files exist
        features_path = Path('../data/ml_features.csv')
        metadata_path = Path('../data/ml_metadata.csv')
        manifest_path = Path('../metadata/ml_feature_manifest.json')
        report_path = Path('../output/ml_dataset_preparation_report.txt')

        assert features_path.exists(), f"ML features file not found at {features_path}"
        assert metadata_path.exists(), f"ML metadata file not found at {metadata_path}"
        assert manifest_path.exists(), f"Manifest file not found at {manifest_path}"
        assert report_path.exists(), f"Report file not found at {report_path}"

        # Check that the files have content
        assert features_path.stat().st_size > 0, "ML features file is empty"
        assert metadata_path.stat().st_size > 0, "ML metadata file is empty"
        assert manifest_path.stat().st_size > 0, "Manifest file is empty"
        assert report_path.stat().st_size > 0, "Report file is empty"

        # Check that the CSV files have the expected number of records (should match input)
        input_df = load_phase5_dataset()
        ml_features_df = pd.read_csv(features_path)
        ml_metadata_df = pd.read_csv(metadata_path)

        assert len(ml_features_df) == len(input_df), f"ML features record count mismatch: {len(ml_features_df)} vs {len(input_df)}"
        assert len(ml_metadata_df) == len(input_df), f"ML metadata record count mismatch: {len(ml_metadata_df)} vs {len(input_df)}"

        print("PASS: test_output_files_exist")
        return True
    except Exception as e:
        print(f"FAIL: test_output_files_exist - {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_load_phase5_dataset,
        test_validate_input_columns,
        test_prepare_ml_features,
        test_prepare_ml_metadata,
        test_create_feature_manifest,
        test_output_files_exist
    ]

    passed = 0
    failed = 0

    print("Running Phase 7 ML Dataset Preparation Tests...")
    print("=" * 50)

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("=" * 50)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests:  {len(tests)}")

    if failed == 0:
        print("\nAll tests passed!")
        return True
    else:
        print("\nSome tests failed!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)