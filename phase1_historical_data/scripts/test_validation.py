import sys
import os
from pathlib import Path

# Add the scripts directory to the path so we can import validate_input
sys.path.append(str(Path(__file__).parent))
from validate_input import validate_landslide_csv
import pandas as pd

def test_valid_record():
    """Test a valid record."""
    data = """landslide_id,date,latitude,longitude,location,district,state,country,source,source_url,severity,description
TEST-001,2020-01-01,10.0,20.0,Test Location,Test District,Test State,Test Country,Test Source,http://example.com,Low,A test record
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    # We need to write to a temporary file for the validation function
    temp_file = Path("temp_valid.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        assert results['total_records'] == 1
        assert results['valid_records'] == 1
        assert results['records_with_errors'] == 0
        assert results['records_with_warnings'] == 0
        print("PASS: test_valid_record")
    finally:
        temp_file.unlink()

def test_missing_required_column():
    """Test missing required column."""
    data = """landslide_id,date,latitude
TEST-001,2020-01-01,10.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_missing_col.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        # Expect errors for missing longitude and other required fields
        assert results['records_with_errors'] > 0
        print("PASS: test_missing_required_column")
    finally:
        temp_file.unlink()

def test_invalid_latitude():
    """Test invalid latitude."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,91.0,0.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_lat.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        assert results['invalid_coordinates'] > 0
        assert results['records_with_errors'] > 0
        print("PASS: test_invalid_latitude")
    finally:
        temp_file.unlink()

def test_invalid_longitude():
    """Test invalid longitude."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,0.0,181.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_lon.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        assert results['invalid_coordinates'] > 0
        assert results['records_with_errors'] > 0
        print("PASS: test_invalid_longitude")
    finally:
        temp_file.unlink()

def test_invalid_date():
    """Test invalid date."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-13-01,0.0,0.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_date.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        assert results['invalid_dates'] > 0
        assert results['records_with_errors'] > 0
        print("PASS: test_invalid_date")
    finally:
        temp_file.unlink()

def test_duplicate_landslide_id():
    """Test duplicate landslide ID."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,0.0,0.0
TEST-001,2020-01-02,1.0,1.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_duplicate_id.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        assert results['duplicate_ids'] > 0
        assert results['records_with_errors'] > 0
        print("PASS: test_duplicate_landslide_id")
    finally:
        temp_file.unlink()

def test_missing_required_values():
    """Test missing required values (empty string)."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,,0.0
TEST-002,2020-01-02,0.0,
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_missing_values.csv")
    df.to_csv(temp_file, index=False)
    try:
        results = validate_landslide_csv(temp_file)
        assert results['missing_coordinates'] >= 2  # latitude and longitude missing
        assert results['records_with_errors'] > 0
        print("PASS: test_missing_required_values")
    finally:
        temp_file.unlink()

if __name__ == "__main__":
    test_valid_record()
    test_missing_required_column()
    test_invalid_latitude()
    test_invalid_longitude()
    test_invalid_date()
    test_duplicate_landslide_id()
    test_missing_required_values()
    print("All tests passed!")