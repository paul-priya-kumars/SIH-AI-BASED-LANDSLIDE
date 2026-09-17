import sys
import os
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Add the scripts directory to the path so we can import create_landslide_layer
sys.path.append(str(Path(__file__).parent))
from create_landslide_layer import create_landslide_gis_layer

def test_valid_point_creation():
    """Test that valid latitude/longitude creates a Point with correct order."""
    data = """landslide_id,date,latitude,longitude,location,district,state,country,source,source_url,severity,description,data_quality_status
TEST-001,2020-01-01,10.0,20.0,Test Location,Test District,Test State,Test Country,Test Source,http://example.com,Low,A test record,CLEAN
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_valid_point.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        # Read the GeoJSON
        gdf = gpd.read_file(output_geojson)
        # Check that we have one feature
        assert len(gdf) == 1
        # Check that the geometry is a Point
        assert gdf.geometry.iloc[0].geom_type == 'Point'
        # Check that the coordinates are correct (longitude, latitude)
        point = gdf.geometry.iloc[0]
        assert point.x == 20.0  # longitude
        assert point.y == 10.0  # latitude
        # Check that attributes are preserved
        assert gdf.iloc[0]['landslide_id'] == 'TEST-001'
        date_val = gdf.iloc[0]['date']
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime('%Y-%m-%d')
        else:
            date_str = str(date_val).strip()
        assert date_str == '2020-01-01'
        print("PASS: test_valid_point_creation")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_lat_longitude_order():
    """Test that longitude is used as X and latitude as Y (not reversed)."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_order.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        point = gdf.geometry.iloc[0]
        # If reversed, we would get (10.0, 20.0) as (x,y) meaning x=10, y=20.
        # We expect x=20, y=10.
        assert point.x == 20.0
        assert point.y == 10.0
        print("PASS: test_lat_longitude_order")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_crs_is_epsg4326():
    """Test that the CRS is set to EPSG:4326."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_crs.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        # Check CRS
        assert gdf.crs == "EPSG:4326"
        print("PASS: test_crs_is_epsg4326")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_missing_latitude_excluded():
    """Test that records with missing latitude are excluded from GIS points."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,,20.0
TEST-002,2020-01-02,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_missing_lat.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        # Only the second record should be converted
        assert len(gdf) == 1
        assert gdf.iloc[0]['landslide_id'] == 'TEST-002'
        # Check that stats show one missing latitude
        assert stats['missing_latitude'] == 1
        print("PASS: test_missing_latitude_excluded")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_missing_longitude_excluded():
    """Test that records with missing longitude are excluded."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,
TEST-002,2020-01-02,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_missing_lon.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        assert len(gdf) == 1
        assert gdf.iloc[0]['landslide_id'] == 'TEST-002'
        assert stats['missing_longitude'] == 1
        print("PASS: test_missing_longitude_excluded")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_invalid_latitude_excluded():
    """Test that records with invalid latitude (out of range) are excluded."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,91.0,20.0
TEST-002,2020-01-02,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_lat.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        assert len(gdf) == 1
        assert gdf.iloc[0]['landslide_id'] == 'TEST-002'
        assert stats['invalid_latitude'] == 1
        print("PASS: test_invalid_latitude_excluded")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_invalid_longitude_excluded():
    """Test that records with invalid longitude are excluded."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,181.0
TEST-002,2020-01-02,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_invalid_lon.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        assert len(gdf) == 1
        assert gdf.iloc[0]['landslide_id'] == 'TEST-002'
        assert stats['invalid_longitude'] == 1
        print("PASS: test_invalid_longitude_excluded")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_output_geojson_can_be_read():
    """Test that the output GeoJSON is valid and can be read."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
TEST-002,2020-01-02,-10.5,20.7
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_read.geojson")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        # Try to read it back
        gdf = gpd.read_file(output_geojson)
        assert len(gdf) == 2
        # Check that we can access geometry
        assert gdf.geometry.iloc[0] is not None
        print("PASS: test_output_geojson_can_be_read")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_number_of_valid_points_matches_expected():
    """Test that the number of valid GIS points matches expected count."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
TEST-002,2020-01-02,,-   # missing latitude
TEST-003,2020-01-03,30.0,30.0
TEST-004,2020-01-04,40.0,40.0
TEST-005,2020-01-05,91.0,5.0   # invalid latitude
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_count.csv")
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        gdf = gpd.read_file(output_geojson)
        # Expected valid: TEST-001, TEST-003, TEST-004 -> 3 points
        assert len(gdf) == 3
        assert stats['records_converted'] == 3
        assert stats['valid_coordinate_records'] == 3
        print("PASS: test_number_of_valid_points_matches_expected")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

def test_raw_and_cleaned_unchanged():
    """Test that the input cleaned CSV is not modified."""
    data = """landslide_id,date,latitude,longitude
TEST-001,2020-01-01,10.0,20.0
"""
    df = pd.read_csv(pd.io.common.StringIO(data))
    temp_file = Path("temp_unchanged.csv")
    original_content = df.to_csv(index=False)
    df.to_csv(temp_file, index=False)
    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(temp_file)
        # Read the file again
        df_after = pd.read_csv(temp_file)
        after_content = df_after.to_csv(index=False)
        assert original_content == after_content
        print("PASS: test_raw_and_cleaned_unchanged")
    finally:
        temp_file.unlink()
        if output_geojson.exists():
            output_geojson.unlink()
        if report_path.exists():
            report_path.unlink()

if __name__ == "__main__":
    test_valid_point_creation()
    test_lat_longitude_order()
    test_crs_is_epsg4326()
    test_missing_latitude_excluded()
    test_missing_longitude_excluded()
    test_invalid_latitude_excluded()
    test_invalid_longitude_excluded()
    test_output_geojson_can_be_read()
    test_number_of_valid_points_matches_expected()
    test_raw_and_cleaned_unchanged()
    print("All GIS tests passed!")