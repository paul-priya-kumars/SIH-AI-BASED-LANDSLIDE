"""
Automated Test Suite — Phase 2: Sentinel-2 Ingestion & NDVI Pipeline
=====================================================================
Covers STAC queries, SCL cloud masking, NDVI numerical precision,
zero-denominator safety, UTM-to-EPSG:4326 reprojection, AOI clipping,
GeoTIFF export, spot sampling, outside-AOI handling, and mock demarcation.
"""

import json
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from shapely.geometry import shape

from phase1_aoi import load_aoi_geometry, get_aoi_bounds
from phase2_sentinel_ndvi.config import (
    MASKED_SCL_CLASSES,
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    classify_ndvi_value,
)
from phase2_sentinel_ndvi.stac_client import (
    build_stac_query_payload,
    query_sentinel2_scenes,
    SentinelSceneMetadata,
)
from phase2_sentinel_ndvi.ndvi_processor import (
    compute_ndvi_array,
    compute_ndvi_statistics,
)
from phase2_sentinel_ndvi.reprojection import (
    reproject_raster_array,
    clip_raster_to_aoi_polygon,
)
from phase2_sentinel_ndvi.export_geotiff import export_ndvi_geotiff
from phase2_sentinel_ndvi.synthetic_fixture import (
    generate_synthetic_ndvi_fixture,
    MOCK_FIXTURE_PATH,
)
from phase2_sentinel_ndvi.spot_sampler import get_spot_ndvi


# -------------------------------------------------------------------------
# 1. STAC Query Construction & Filtering Tests
# -------------------------------------------------------------------------
def test_stac_query_construction():
    """Verify STAC query payload uses Phase 1 AOI geometry and cloud criteria."""
    geom = load_aoi_geometry()
    payload = build_stac_query_payload(max_cloud_cover=15.0)

    assert "collections" in payload
    assert payload["collections"] == ["sentinel-2-l2a"]
    assert "intersects" in payload
    assert payload["intersects"]["type"] == "Polygon"
    assert "query" in payload
    assert payload["query"]["eo:cloud_cover"]["lt"] == 15.0
    assert "datetime" in payload
    assert "/" in payload["datetime"]


def test_stac_scene_metadata_dataclass():
    """Verify SentinelSceneMetadata serialization and structure."""
    scene = SentinelSceneMetadata(
        scene_id="S2A_TEST_SCENE",
        datetime="2026-05-19T05:26:04Z",
        cloud_cover_pct=12.5,
        platform="sentinel-2a",
        mgrs_tile="43PGN",
        red_asset_url="https://example.com/red.tif",
        nir_asset_url="https://example.com/nir.tif",
        scl_asset_url="https://example.com/scl.tif",
        bbox=[76.45, 11.20, 77.05, 11.60],
        stac_properties={"eo:cloud_cover": 12.5},
    )
    d = scene.to_dict()
    assert d["scene_id"] == "S2A_TEST_SCENE"
    assert d["mgrs_tile"] == "43PGN"
    assert d["cloud_cover_pct"] == 12.5


# -------------------------------------------------------------------------
# 2. NDVI Numerical Precision & Zero-Denominator Safety
# -------------------------------------------------------------------------
def test_ndvi_numerical_calculation():
    """Test NDVI calculation against known physical surface types."""
    # Pixel 1: Dense vegetation (NIR high, Red low)
    # Pixel 2: Water (NIR very low, Red low)
    # Pixel 3: Soil/Bare rock (NIR ~ Red)
    red = np.array([[0.10, 0.10], [0.20, 0.05]], dtype=np.float32)
    nir = np.array([[0.80, 0.05], [0.30, 0.50]], dtype=np.float32)

    ndvi = compute_ndvi_array(red, nir)

    # Pixel (0,0): (0.8 - 0.1) / (0.8 + 0.1) = 0.7 / 0.9 = 0.7778
    assert ndvi[0, 0] == pytest.approx(0.7778, abs=1e-3)
    # Pixel (0,1): (0.05 - 0.10) / (0.05 + 0.10) = -0.05 / 0.15 = -0.3333
    assert ndvi[0, 1] == pytest.approx(-0.3333, abs=1e-3)
    # Pixel (1,0): (0.3 - 0.2) / (0.3 + 0.2) = 0.1 / 0.5 = 0.2000
    assert ndvi[1, 0] == pytest.approx(0.2000, abs=1e-3)
    # Pixel (1,1): (0.5 - 0.05) / (0.5 + 0.05) = 0.45 / 0.55 = 0.8182
    assert ndvi[1, 1] == pytest.approx(0.8182, abs=1e-3)


def test_zero_denominator_handling():
    """Verify that zero and negative denominators produce NaN safely without warnings."""
    red = np.array([[0.0, 0.0], [0.5, np.nan]], dtype=np.float32)
    nir = np.array([[0.0, -0.1], [0.5, 0.5]], dtype=np.float32)

    ndvi = compute_ndvi_array(red, nir)

    # (0, 0) -> denom 0 -> NaN
    assert np.isnan(ndvi[0, 0])
    # (0, -0.1) -> denom <= 0 -> NaN
    assert np.isnan(ndvi[0, 1])
    # (0.5, 0.5) -> (0.5 - 0.5)/(1.0) = 0.0
    assert ndvi[1, 0] == pytest.approx(0.0, abs=1e-4)
    # (nan, 0.5) -> NaN
    assert np.isnan(ndvi[1, 1])


# -------------------------------------------------------------------------
# 3. SCL Cloud & Shadow Masking Tests
# -------------------------------------------------------------------------
def test_scl_cloud_and_shadow_masking():
    """Verify that all documented SCL classes are masked and never converted to 0.0."""
    # Create 3x4 grid covering all 12 SCL classes
    scl = np.arange(12, dtype=np.int32).reshape(3, 4)

    # Healthy vegetation reflectance across all pixels
    red = np.full((3, 4), 0.10, dtype=np.float32)
    nir = np.full((3, 4), 0.70, dtype=np.float32)

    ndvi = compute_ndvi_array(red, nir, scl=scl)

    for val in range(12):
        r, c = divmod(val, 4)
        if val in MASKED_SCL_CLASSES:
            # Classes 0, 1, 3, 8, 9, 10, 11 MUST be NaN
            assert np.isnan(ndvi[r, c]), f"SCL class {val} was not masked to NaN!"
            assert ndvi[r, c] != 0.0, f"SCL class {val} must NOT be 0.0!"
        else:
            # Unmasked classes (e.g. 4=vegetation, 5=bare soil, 6=water) must have valid NDVI
            assert np.isfinite(ndvi[r, c]), f"SCL class {val} was unexpectedly masked!"
            assert ndvi[r, c] == pytest.approx(0.75, abs=1e-2)


def test_sentinel2_resolution_mismatch():
    """Test SCL resolution mismatch handling (20m SCL → 10m nearest-neighbor resampling → SCL masking → NDVI)."""
    # Simulate Sentinel-2 resolution difference:
    # RED/NIR bands at 10m resolution (e.g., 100x100 pixels)
    # SCL band at 20m resolution (e.g., 50x50 pixels for same geographic area)

    # Create high-resolution RED/NIR arrays (10m equivalent)
    height_10m, width_10m = 100, 100
    red = np.full((height_10m, width_10m), 0.10, dtype=np.float32)  # Low reflectance
    nir = np.full((height_10m, width_10m), 0.70, dtype=np.float32)  # High reflectance

    # Create low-resolution SCL array (20m equivalent) - half the dimensions
    height_20m, width_20m = height_10m // 2, width_10m // 2  # 50x50
    scl = np.zeros((height_20m, width_20m), dtype=np.int32)

    # Set some SCL pixels to masked classes (e.g., class 3 = cloud shadow)
    # Top-left quadrant: cloud shadow (should be masked)
    scl[:height_20m//2, :width_20m//2] = 3
    # Bottom-right quadrant: vegetation (class 4, should be unmasked)
    scl[height_20m//2:, width_20m//2:] = 4
    # Other areas: class 0 (no data, should be masked)
    scl[(scl != 3) & (scl != 4)] = 0

    # Compute NDVI with SCL masking - should automatically resample SCL
    ndvi = compute_ndvi_array(red, nir, scl=scl)

    # Verify output shape matches RED/NIR (not SCL)
    assert ndvi.shape == (height_10m, width_10m), f"Output shape {ndvi.shape} does not match RED/NIR shape {(height_10m, width_10m)}"

    # Check that SCL classes were properly resampled and applied
    # Each 20m SCL pixel should map to a 2x2 block in 10m space

    # Top-left 20m pixel (class 3 - cloud shadow) should mask 4 10m pixels
    for i in range(0, 2):
        for j in range(0, 2):
            assert np.isnan(ndvi[i, j]), f"Expected NaN at [{i},{j}] due to SCL class 3 (cloud shadow)"

    # Bottom-right 20m pixel (class 4 - vegetation) should yield valid NDVI for 4 10m pixels
    for i in range(50, 52):  # Last two rows in 100x100 grid corresponding to bottom 20m pixel
        for j in range(50, 52):  # Last two cols in 100x100 grid corresponding to right 20m pixel
            assert np.isfinite(ndvi[i, j]), f"Expected valid NDVI at [{i},{j}] due to SCL class 4 (vegetation)"
            assert ndvi[i, j] == pytest.approx(0.75, abs=1e-2), f"Expected NDVI 0.75 at [{i},{j}] for vegetation"

    # Top-right and bottom-left 20m pixels (class 0 - no data) should mask their 10m pixels
    # Top-right: rows 0-25, cols 50-75 in 20m space -> rows 0-50, cols 100-150 in 10m space (but we only have 0-100)
    # Actually, let's check a few samples from areas that should be masked due to class 0
    for i in range(0, 10):  # Top rows
        for j in range(50, 60):  # Middle-right columns
            # This area corresponds to SCL class 0 (no data) in our test setup
            assert np.isnan(ndvi[i, j]), f"Expected NaN at [{i},{j}] due to SCL class 0 (no data)"

    # Verify that resampling used nearest-neighbor (no intermediate values)
    # All values should be either NaN (masked) or 0.75 (vegetation)
    valid_pixels = ndvi[np.isfinite(ndvi)]
    assert len(valid_pixels) > 0, "Expected some valid pixels"
    assert np.allclose(valid_pixels, 0.75, atol=1e-2), "All valid pixels should have NDVI ~0.75 (vegetation)"


# -------------------------------------------------------------------------
# 4. Reprojection & AOI Polygon Clipping Tests
# -------------------------------------------------------------------------
def test_reprojection_utm_to_epsg4326():
    """Verify reprojection from UTM Zone 43N to EPSG:4326."""
    # Synthetic UTM raster around Nilgiris (approx UTM 43N: Easting 680000, Northing 1260000)
    src_crs = CRS.from_epsg(32643)
    src_transform = from_bounds(660000, 1240000, 720000, 1280000, 60, 40)
    src_data = np.full((40, 60), 0.65, dtype=np.float32)

    dst_data, dst_transform, bounds = reproject_raster_array(
        src_data=src_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_crs=CRS.from_epsg(4326),
    )

    assert dst_data.shape[0] > 0
    assert dst_data.shape[1] > 0
    # Geographic bounds should be in WGS 84 (Lon ~76-77, Lat ~11-12)
    minx, miny, maxx, maxy = bounds
    assert 76.0 <= minx <= 77.5
    assert 11.0 <= miny <= 12.0


def test_polygon_clipping():
    """Verify that pixels outside the Phase 1 polygon are set to nodata."""
    min_lon, min_lat, max_lon, max_lat = get_aoi_bounds()
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, 50, 50)
    data = np.full((50, 50), 0.50, dtype=np.float32)

    clipped = clip_raster_to_aoi_polygon(data, transform, nodata_value=RASTER_NODATA_VALUE)

    # Some pixels outside the irregular polygon must be nodata
    assert np.any(clipped == RASTER_NODATA_VALUE)
    # Pixels inside the polygon must retain valid values
    assert np.any(clipped == 0.50)


# -------------------------------------------------------------------------
# 5. GeoTIFF Export & Metadata Tests
# -------------------------------------------------------------------------
def test_export_geotiff_metadata(tmp_path):
    """Verify exported GeoTIFF contains valid transform, CRS, NoData, and tags."""
    output_tif = tmp_path / "test_ndvi.tif"
    output_json = tmp_path / "test_ndvi.json"

    data = np.array([[0.5, 0.6], [np.nan, 0.4]], dtype=np.float32)
    transform = from_bounds(76.45, 11.20, 77.05, 11.60, 2, 2)

    export_ndvi_geotiff(
        ndvi_array=data,
        transform=transform,
        output_geotiff_path=output_tif,
        output_metadata_path=output_json,
        metadata_tags={"SCENE_ID": "TEST-SCENE-01", "IS_MOCK": "FALSE"},
    )

    assert output_tif.exists()
    assert output_json.exists()

    with rasterio.open(output_tif) as src:
        assert src.crs == CRS.from_string(TARGET_CRS)
        assert src.nodata == RASTER_NODATA_VALUE
        assert src.dtypes[0] == "float32"
        tags = src.tags()
        assert tags.get("SCENE_ID") == "TEST-SCENE-01"
        assert tags.get("IS_MOCK") == "FALSE"

        # Check that NaN was converted to nodata value (-9999.0)
        arr = src.read(1)
        assert arr[1, 0] == RASTER_NODATA_VALUE
        assert arr[0, 0] == pytest.approx(0.5, abs=1e-3)


# -------------------------------------------------------------------------
# 6. Spot Sampler (`get_spot_ndvi`) Tests
# -------------------------------------------------------------------------
def test_spot_sampler_inside_aoi(tmp_path):
    """Verify spot sampler returns valid NDVI and metadata for point inside AOI."""
    # Ensure synthetic fixture exists
    fixture_path, _ = generate_synthetic_ndvi_fixture()

    # Ooty central coordinate: 11.4102 N, 76.6950 E
    res = get_spot_ndvi(latitude=11.4102, longitude=76.6950, raster_path=fixture_path)

    assert res["is_valid"] is True
    assert res["is_nodata"] is False
    assert 0.0 <= res["ndvi"] <= 1.0
    assert res["vegetation_class"] in ["MODERATE_VEGETATION", "DENSE_CANOPY", "SPARSE_OR_DEGRADED"]
    assert res["is_mock"] is True
    assert res["scene_id"] == "MOCK-SYNTHETIC-FIXTURE-S2"


def test_spot_sampler_outside_aoi(tmp_path):
    """Verify coordinates outside the Nilgiris AOI return is_valid=False with error."""
    fixture_path, _ = generate_synthetic_ndvi_fixture()

    # Coordinates in Chennai (far east outside Nilgiris)
    res = get_spot_ndvi(latitude=13.0827, longitude=80.2707, raster_path=fixture_path)

    assert res["is_valid"] is False
    assert res["ndvi"] is None
    assert "outside the Nilgiris study area" in res["error"]


def test_spot_sampler_nodata_pixel(tmp_path):
    """Verify sampling a masked cloud patch returns is_nodata=True and is_valid=False."""
    fixture_path, _ = generate_synthetic_ndvi_fixture()

    # In synthetic_fixture.py, we inserted a cloud patch at Lon 76.54, Lat 11.55
    res = get_spot_ndvi(latitude=11.5500, longitude=76.5400, raster_path=fixture_path)

    assert res["is_valid"] is False
    assert res["is_nodata"] is True
    assert res["ndvi"] is None
    assert "masked" in res["reason"].lower()


def test_mock_fallback_enforcement(tmp_path):
    """Verify that require_real=True strictly rejects synthetic mock data."""
    fixture_path, _ = generate_synthetic_ndvi_fixture()

    with pytest.raises(ValueError) as excinfo:
        get_spot_ndvi(
            latitude=11.4102,
            longitude=76.6950,
            raster_path=fixture_path,
            require_real=True,
        )
    assert "synthetic mock fixture" in str(excinfo.value)
