#!/usr/bin/env python3
"""
Tests for Phase 6 Dataset Validation
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import json
import tempfile

# Add the scripts directory to the path so we can import the validation script
sys.path.append(str(Path(__file__).parent))
from validate_dataset import (
    load_phase5_dataset,
    load_phase3_geojson,
    validate_structural,
    validate_historical_fields,
    validate_spatial,
    validate_environmental_features,
    validate_missing_data,
    validate_duplicates,
    validate_synthetic_data,
    validate_cross_dataset_consistency,
    validate_feature_extraction_status,
    validate_rainfall_handling,
    validate_no_data_leakage
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

def test_load_phase3_geojson():
    """Test that we can load the Phase 3 GeoJSON."""
    try:
        geojson_data = load_phase3_geojson()
        assert isinstance(geojson_data, dict)
        assert 'type' in geojson_data
        assert geojson_data['type'] == 'FeatureCollection'
        assert 'features' in geojson_data
        print("PASS: test_load_phase3_geojson")
        return True
    except Exception as e:
        print(f"FAIL: test_load_phase3_geojson - {str(e)}")
        return False

def test_validate_structural():
    """Test structural validation function."""
    try:
        df = load_phase5_dataset()
        issues = validate_structural(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found structural errors: {error_issues}"
        print("PASS: test_validate_structural")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_structural - {str(e)}")
        return False

def test_validate_historical_fields():
    """Test historical fields validation."""
    try:
        df = load_phase5_dataset()
        # Work on a copy to avoid modifying the original
        issues = validate_historical_fields(df.copy())
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found historical field errors: {error_issues}"
        print("PASS: test_validate_historical_fields")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_historical_fields - {str(e)}")
        return False

def test_validate_spatial():
    """Test spatial validation."""
    try:
        df = load_phase5_dataset()
        geojson_data = load_phase3_geojson()
        issues = validate_spatial(df, geojson_data)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found spatial errors: {error_issues}"
        print("PASS: test_validate_spatial")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_spatial - {str(e)}")
        return False

def test_validate_environmental_features():
    """Test environmental features validation."""
    try:
        df = load_phase5_dataset()
        issues = validate_environmental_features(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found environmental feature errors: {error_issues}"
        print("PASS: test_validate_environmental_features")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_environmental_features - {str(e)}")
        return False

def test_validate_missing_data():
    """Test missing data analysis."""
    try:
        df = load_phase5_dataset()
        issues = validate_missing_data(df)
        # Missing data validation should not produce errors (it's informational)
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found missing data errors: {error_issues}"
        print("PASS: test_validate_missing_data")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_missing_data - {str(e)}")
        return False

def test_validate_duplicates():
    """Test duplicate validation."""
    try:
        df = load_phase5_dataset()
        issues = validate_duplicates(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found duplicate errors: {error_issues}"
        print("PASS: test_validate_duplicates")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_duplicates - {str(e)}")
        return False

def test_validate_synthetic_data():
    """Test synthetic data validation."""
    try:
        df = load_phase5_dataset()
        issues = validate_synthetic_data(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found synthetic data errors: {error_issues}"
        print("PASS: test_validate_synthetic_data")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_synthetic_data - {str(e)}")
        return False

def test_validate_cross_dataset_consistency():
    """Test cross-dataset consistency validation."""
    try:
        df = load_phase5_dataset()
        geojson_data = load_phase3_geojson()
        issues = validate_cross_dataset_consistency(df, geojson_data)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found cross-dataset consistency errors: {error_issues}"
        print("PASS: test_validate_cross_dataset_consistency")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_cross_dataset_consistency - {str(e)}")
        return False

def test_validate_feature_extraction_status():
    """Test feature extraction status validation."""
    try:
        df = load_phase5_dataset()
        issues = validate_feature_extraction_status(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found feature extraction status errors: {error_issues}"
        print("PASS: test_validate_feature_extraction_status")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_feature_extraction_status - {str(e)}")
        return False

def test_validate_rainfall_handling():
    """Test rainfall handling validation."""
    try:
        df = load_phase5_dataset()
        issues = validate_rainfall_handling(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found rainfall handling errors: {error_issues}"
        print("PASS: test_validate_rainfall_handling")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_rainfall_handling - {str(e)}")
        return False

def test_validate_no_data_leakage():
    """Test data leakage validation."""
    try:
        df = load_phase5_dataset()
        issues = validate_no_data_leakage(df)
        # Should not have critical errors for the real dataset
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) == 0, f"Found data leakage errors: {error_issues}"
        print("PASS: test_validate_no_data_leakage")
        return True
    except Exception as e:
        print(f"FAIL: test_validate_no_data_leakage - {str(e)}")
        return False

def test_create_temp_invalid_dataset():
    """Test validation with an intentionally invalid dataset."""
    try:
        # Create a minimal invalid dataset
        data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,95.0,0.0
TEST-002,2020-01-02,0.0,185.0
"""
        df = pd.read_csv(pd.io.common.StringIO(data))

        # Test historical validation - should catch invalid coordinates
        issues = validate_historical_fields(df)
        error_issues = [issue for issue in issues if issue.startswith('ERROR:')]
        assert len(error_issues) > 0, "Should have found errors in invalid dataset"

        print("PASS: test_create_temp_invalid_dataset")
        return True
    except Exception as e:
        print(f"FAIL: test_create_temp_invalid_dataset - {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_load_phase5_dataset,
        test_load_phase3_geojson,
        test_validate_structural,
        test_validate_historical_fields,
        test_validate_spatial,
        test_validate_environmental_features,
        test_validate_missing_data,
        test_validate_duplicates,
        test_validate_synthetic_data,
        test_validate_cross_dataset_consistency,
        test_validate_feature_extraction_status,
        test_validate_rainfall_handling,
        test_validate_no_data_leakage,
        test_create_temp_invalid_dataset
    ]

    passed = 0
    failed = 0

    print("Running Phase 6 Dataset Validation Tests...")
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