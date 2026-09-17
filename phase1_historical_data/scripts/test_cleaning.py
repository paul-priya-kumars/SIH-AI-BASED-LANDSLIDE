import sys
import os
from pathlib import Path
import pandas as pd

# Add the scripts directory to the path so we can import clean_historical_data
sys.path.append(str(Path(__file__).parent))
from clean_historical_data import clean_landslide_data

def test_whitespace_cleaning():
    """Test that leading/trailing whitespace is removed from text fields."""
    data = """landslide_id,date,latitude,longitude,location,district,state,country,source,source_url,severity,description
TEST-001,2020-01-01,10.0,20.0,  Wayanad  ,  Wayanad  ,Kerala,India,Test Source,http://example.com,High,  A test record  """
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_whitespace.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        # Read the cleaned data
        df_clean = pd.read_csv(output_path)
        # Check that whitespace is removed
        assert df_clean.loc[0, 'location'] == 'Wayanad'
        assert df_clean.loc[0, 'district'] == 'Wayanad'
        assert df_clean.loc[0, 'description'] == 'A test record'
        # Check that the text_fields_normalized count is at least 4 (location, district, state, description) but note state and country had no whitespace? Actually state was 'Kerala' (no extra spaces) and country 'India' (no extra spaces). So we expect 4.
        # However, note that we also count landslide_id and source/source_url if they had whitespace? They didn't in this test.
        # We'll just check that the cleaning happened.
        print("PASS: test_whitespace_cleaning")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_date_standardization():
    """Test that various date formats are standardized to YYYY-MM-DD."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020/01/01,10.0,20.0
TEST-002,01-01-2020,10.0,20.0
TEST-003,2020-01-01,10.0,20.0
TEST-004,01/01/2020,10.0,20.0
TEST-005,2020-13-01,10.0,20.0  # invalid date
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_date.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        # Check the first four records are standardized
        assert df_clean.loc[0, 'date'] == '2020-01-01'
        assert df_clean.loc[1, 'date'] == '2020-01-01'
        assert df_clean.loc[2, 'date'] == '2020-01-01'
        assert df_clean.loc[3, 'date'] == '2020-01-01'
        # The invalid date should remain unchanged and be flagged for review (we don't check the review flag here, just that it's not changed to a valid date)
        assert df_clean.loc[4, 'date'] == '2020-13-01'
        print("PASS: test_date_standardization")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_valid_coordinate_handling():
    """Test that valid coordinates are preserved as numeric."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
TEST-002,2020-01-02,-10.5,20.7
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_coord.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        # Check that the values are numeric and unchanged
        assert df_clean.loc[0, 'latitude'] == 10.0
        assert df_clean.loc[0, 'longitude'] == 20.0
        assert df_clean.loc[1, 'latitude'] == -10.5
        assert df_clean.loc[1, 'longitude'] == 20.7
        # Check that coordinates_converted counts the ones that were strings converted to numeric? In our test they were already numeric, so might be 0.
        # We'll just check that the cleaning didn't break them.
        print("PASS: test_valid_coordinate_handling")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_invalid_latitude():
    """Test that invalid latitude is handled (set to NaN and flagged for review)."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,91.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_lat.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        # The invalid latitude should become NaN (or missing) and the record should be flagged for review.
        # In our cleaning, we set invalid latitude to np.nan, which when saved to CSV becomes empty? Actually, pandas writes NaN as empty.
        # Let's check that the value is empty or NaN. We'll read with keep_default_na=False to see the raw string.
        df_clean_raw = pd.read_csv(output_path, keep_default_na=False)
        # The latitude for the invalid record should be empty string.
        assert df_clean_raw.loc[0, 'latitude'] == ''
        # Check that invalid_coordinates count increased
        assert stats['invalid_coordinates'] > 0
        print("PASS: test_invalid_latitude")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_invalid_longitude():
    """Test that invalid longitude is handled."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,181.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_lon.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        df_clean_raw = pd.read_csv(output_path, keep_default_na=False)
        assert df_clean_raw.loc[0, 'longitude'] == ''
        assert stats['invalid_coordinates'] > 0
        print("PASS: test_invalid_longitude")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_missing_required_fields():
    """Test that missing required fields are flagged for review."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,,20.0
TEST-002,2020-01-02,10.0,
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_missing.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        df_clean_raw = pd.read_csv(output_path, keep_default_na=False)
        # First record: missing latitude -> empty
        assert df_clean_raw.loc[0, 'latitude'] == ''
        # Second record: missing longitude -> empty
        assert df_clean_raw.loc[1, 'longitude'] == ''
        # Check that missing_required_values count is 2 (one for each missing)
        assert stats['missing_required_values'] == 2
        print("PASS: test_missing_required_fields")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_duplicate_landslide_id():
    """Test that duplicate landslide IDs are detected and flagged for review."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
TEST-001,2020-01-02,10.0,20.0
TEST-002,2020-01-03,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_duplicate_id.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        # Check that duplicate_landslide_ids count is 2 (both duplicates, because we mark both)
        # Note: our algorithm marks all duplicates (both the second and the first? Actually we mark all that are duplicated, so both rows with TEST-001)
        assert stats['duplicate_landslide_ids'] == 2
        print("PASS: test_duplicate_landslide_id")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_exact_duplicate_rows():
    """Test that exact duplicate rows are detected."""
    data = """landslide_id,date,latitude,longitude,location
TEST-001,2020-01-01,10.0,20.0,Location A
TEST-001,2020-01-01,10.0,20.0,Location A
TEST-002,2020-01-02,10.0,20.0,Location B
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_exact_dup.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        # Check that exact_duplicate_rows count is 1 (the second duplicate)
        assert stats['exact_duplicate_rows'] == 1
        print("PASS: test_exact_duplicate_rows")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_missing_optional_fields():
    """Test that missing optional fields are left as missing and not invented."""
    data = """landslide_id,date,latitude,longitude,severity,description
TEST-001,2020-01-01,10.0,20.0,,
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_missing_optional.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        # Check that severity and description are missing (NaN) in the cleaned data
        assert pd.isna(df_clean.loc[0, 'severity'])
        assert pd.isna(df_clean.loc[0, 'description'])
        # Check that the record is considered cleaned (no errors) because missing optional fields are allowed.
        # In our cleaning, missing optional fields do not trigger review (only missing required fields do).
        # So we expect the record to be cleaned.
        assert stats['records_cleaned'] == 1
        assert stats['records_require_review'] == 0
        print("PASS: test_missing_optional_fields")
    finally:
        temp_file.unlink()
        output_path.unlink()

def test_source_preservation():
    """Test that source and source_url are preserved."""
    data = """landslide_id,date,latitude,longitude,source,source_url
TEST-001,2020-01-01,10.0,20.0,Test Source,http://example.com
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_source.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_path = clean_landslide_data(temp_file)
        df_clean = pd.read_csv(output_path)
        assert df_clean.loc[0, 'source'] == 'Test Source'
        assert df_clean.loc[0, 'source_url'] == 'http://example.com'
        print("PASS: test_source_preservation")
    finally:
        temp_file.unlink()
        output_path.unlink()

if __name__ == "__main__":
    test_whitespace_cleaning()
    test_date_standardization()
    test_valid_coordinate_handling()
    test_invalid_latitude()
    test_invalid_longitude()
    test_missing_required_fields()
    test_duplicate_landslide_id()
    test_exact_duplicate_rows()
    test_missing_optional_fields()
    test_source_preservation()
    print("All cleaning tests passed!")