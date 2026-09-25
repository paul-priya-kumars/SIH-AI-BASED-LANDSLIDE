"""
Automated Test Suite — Phase 1 AOI Setup
========================================
Tests study area generation, validation, GeoPandas/Shapely compatibility,
coordinate constraints, and error catching for M2-A.
"""

import json
import pytest
from pathlib import Path
import geopandas as gpd
from shapely.geometry import shape, Polygon

from phase1_aoi import (
    load_aoi_geojson,
    load_aoi_gdf,
    load_aoi_geometry,
    get_aoi_bounds,
    get_aoi_metadata,
    validate_aoi,
    AOIValidationError,
    DEFAULT_OUTPUT_GEOJSON,
    BOUNDING_BOX,
    STUDY_AREA_METADATA,
)
from phase1_aoi.config import get_bounding_box_tuple
from phase1_aoi.validate_aoi import (
    validate_coordinates_range,
    validate_geometry,
    validate_geojson_structure,
)


def test_config_integrity():
    """Verify configuration constants are properly structured."""
    bbox = get_bounding_box_tuple()
    assert len(bbox) == 4
    min_lon, min_lat, max_lon, max_lat = bbox
    assert min_lon < max_lon
    assert min_lat < max_lat
    assert 76.0 <= min_lon <= 77.0
    assert 11.0 <= min_lat <= 12.0

    assert STUDY_AREA_METADATA["crs"] == "EPSG:4326"
    assert STUDY_AREA_METADATA["epsg"] == 4326


def test_study_area_geojson_exists():
    """Verify that study_area.geojson exists and is non-empty."""
    assert DEFAULT_OUTPUT_GEOJSON.exists()
    assert DEFAULT_OUTPUT_GEOJSON.stat().st_size > 0


def test_geojson_schema_and_rfc7946():
    """Verify GeoJSON structure complies with RFC 7946."""
    data = load_aoi_geojson()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) == 1

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"
    assert "properties" in feature
    assert feature["properties"]["name"] == "Nilgiris Landslide Risk Study Area"
    assert feature["properties"]["crs"] == "EPSG:4326"


def test_shapely_topological_validity():
    """Verify the polygon geometry is valid, simple, and has expected bounds."""
    geom = load_aoi_geometry()
    assert isinstance(geom, Polygon)
    assert geom.is_valid
    assert not geom.is_empty
    assert geom.area > 0

    minx, miny, maxx, maxy = geom.bounds
    assert minx >= BOUNDING_BOX["min_lon"]
    assert miny >= BOUNDING_BOX["min_lat"]
    assert maxx <= BOUNDING_BOX["max_lon"]
    assert maxy <= BOUNDING_BOX["max_lat"]

    # Verify centroid is inside the bounding envelope
    centroid = geom.centroid
    assert minx <= centroid.x <= maxx
    assert miny <= centroid.y <= maxy


def test_geopandas_interoperability():
    """Verify GeoPandas can load the GeoJSON and read CRS/attributes correctly."""
    gdf = load_aoi_gdf()
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert not gdf.empty
    assert len(gdf) == 1
    assert gdf.crs is not None
    assert gdf.crs.to_epsg() == 4326

    # Verify total bounds
    bounds = gdf.total_bounds
    assert bounds[0] == pytest.approx(BOUNDING_BOX["min_lon"], abs=1e-3)
    assert bounds[1] == pytest.approx(BOUNDING_BOX["min_lat"], abs=1e-3)
    assert bounds[2] == pytest.approx(BOUNDING_BOX["max_lon"], abs=1e-3)
    assert bounds[3] == pytest.approx(BOUNDING_BOX["max_lat"], abs=1e-3)


def test_coordinate_bounds_and_order():
    """Verify that coordinates are strictly [lon, lat] and not inverted."""
    data = load_aoi_geojson()
    coords = data["features"][0]["geometry"]["coordinates"][0]
    for pt in coords:
        lon, lat = pt[0], pt[1]
        assert -180.0 <= lon <= 180.0
        assert -90.0 <= lat <= 90.0
        # Ensure longitude is ~76-77 and latitude is ~11 (India Nilgiris)
        assert 76.0 <= lon <= 78.0, f"Unexpected longitude: {lon}"
        assert 11.0 <= lat <= 12.0, f"Unexpected latitude: {lat}"


def test_validation_function_success():
    """Verify that validate_aoi() completes without errors and returns status VALID."""
    result = validate_aoi(file_path=DEFAULT_OUTPUT_GEOJSON, verbose=False)
    assert result["status"] == "VALID"
    assert result["crs"] == "EPSG:4326 (WGS 84)"
    assert result["geopandas_loadable"] is True
    assert result["shapely_valid"] is True


def test_validation_catches_invalid_geometry(tmp_path):
    """Verify that validator catches self-intersecting / bowtie polygons."""
    bowtie_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Invalid Bowtie"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]]  # Classic self-intersecting hourglass
                    ],
                },
            }
        ],
    }
    bad_file = tmp_path / "bad.geojson"
    bad_file.write_text(json.dumps(bowtie_geojson))

    with pytest.raises(AOIValidationError) as excinfo:
        validate_aoi(file_path=bad_file, verbose=False)
    assert "topologically invalid" in str(excinfo.value).lower()


def test_validation_catches_inverted_coordinates(tmp_path):
    """Verify that validator detects inverted [lat, lon] coordinates."""
    inverted_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Inverted Coords"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[11.41, 76.69], [11.45, 76.69], [11.45, 76.75], [11.41, 76.75], [11.41, 76.69]]
                    ],
                },
            }
        ],
    }
    inverted_file = tmp_path / "inverted.geojson"
    inverted_file.write_text(json.dumps(inverted_geojson))

    with pytest.raises(AOIValidationError) as excinfo:
        validate_aoi(file_path=inverted_file, verbose=False)
    assert "inverted" in str(excinfo.value).lower()


def test_public_api_helpers():
    """Verify package level API exports."""
    bounds = get_aoi_bounds()
    assert len(bounds) == 4
    metadata = get_aoi_metadata()
    assert "name" in metadata
    assert "target_satellite_sensor" in metadata
