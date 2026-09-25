"""
Automated Test Suite — Phase 3: Temporal NDVI Mosaic & Change Detection
=======================================================================

Tests temporal compositing, change detection, QA generation, multiband export,
feature table creation, spot sampling, and synthetic fixture generation.
"""

import json
import tempfile
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from phase3_temporal_mosaic.config import (
    TEMPORAL_COMPOSITE_METHODS,
    DEFAULT_COMPOSITE_METHOD,
    QA_BIT_MEANINGS,
    QA_VALID_PIXEL_BIT,
    QA_CLOUD_BIT,
    QA_SHADOW_BIT,
    QA_WATER_BIT,
    QA_SNOW_ICE_BIT,
    QA_SENTINEL_2A_BIT,
    QA_SENTINEL_2B_BIT,
    QA_MULTI_TILE_BIT,
    RASTER_NODATA_VALUE,
    LATEST_MOSAIC_RASTER_PATH,
    LATEST_MOSAIC_METADATA_PATH,
    FEATURE_TABLE_PARQUET_PATH,
    FEATURE_TABLE_CSV_PATH,
    MOCK_MOSAIC_PATH,
    MOCK_METADATA_PATH,
    classify_ndvi_value,
)
from phase2_sentinel_ndvi.stac_client import SentinelSceneMetadata
from phase3_temporal_mosaic.mosaic_engine import (
    discover_sentinel2_scenes_temporal,
    discover_baseline_and_current_scenes,
    group_scenes_by_mgrs_tile,
)
from phase3_temporal_mosaic.temporal_composite import create_temporal_composite
from phase3_temporal_mosaic.anomaly_detector import calculate_delta_ndvi
from phase3_temporal_mosaic.qa_generator import generate_qa_band
from phase3_temporal_mosaic.export_multiband import export_multiband_geotiff
from phase3_temporal_mosaic.feature_table_exporter import export_feature_table
from phase3_temporal_mosaic.spot_composite_sampler import get_spot_ndvi_composite
from phase3_temporal_mosaic.synthetic_mosaic_fixture import (
    generate_synthetic_mosaic_fixture,
)
from phase1_aoi import load_aoi_geometry, get_aoi_bounds


# -------------------------------------------------------------------------
# 1. Configuration and Constants Tests
# -------------------------------------------------------------------------
def test_config_constants():
    """Verify Phase 3 configuration constants are properly structured."""
    assert DEFAULT_COMPOSITE_METHOD in TEMPORAL_COMPOSITE_METHODS
    assert "MVC" in TEMPORAL_COMPOSITE_METHODS
    assert "MEDIAN" in TEMPORAL_COMPOSITE_METHODS

    # Check QA bit meanings are defined
    assert QA_VALID_PIXEL_BIT in QA_BIT_MEANINGS
    assert QA_CLOUD_BIT in QA_BIT_MEANINGS
    assert QA_SHADOW_BIT in QA_BIT_MEANINGS
    assert QA_WATER_BIT in QA_BIT_MEANINGS
    assert QA_SNOW_ICE_BIT in QA_BIT_MEANINGS
    assert QA_SENTINEL_2A_BIT in QA_BIT_MEANINGS
    assert QA_SENTINEL_2B_BIT in QA_BIT_MEANINGS
    assert QA_MULTI_TILE_BIT in QA_BIT_MEANINGS


# -------------------------------------------------------------------------
# 2. Synthetic Fixture Tests
# -------------------------------------------------------------------------
def test_synthetic_mosaic_fixture_generation():
    """Test that synthetic mosaic fixture is generated and properly marked."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        geotiff_path = tmp_path / "test_mosaic.tif"
        metadata_path = tmp_path / "test_mosaic.json"

        # Generate synthetic fixture
        created_path, metadata = generate_synthetic_mosaic_fixture(
            output_geotiff=geotiff_path,
            output_metadata=metadata_path,
            width=50,
            height=40,
        )

        assert created_path == geotiff_path
        assert metadata_path.exists()
        assert geotiff_path.exists()

        # Check that it's explicitly marked as mock
        with rasterio.open(geotiff_path) as src:
            tags = src.tags()
            assert tags.get("IS_MOCK") == "TRUE"
            assert tags.get("DATA_SOURCE") == "SYNTHETIC_OFFLINE_TEST_FIXTURE"
            assert "SYNTHETIC" in tags.get("DESCRIPTION", "")


# -------------------------------------------------------------------------
# 3. Mosaic Engine Tests
# -------------------------------------------------------------------------
def test_mosaic_engine_imports():
    """Test that mosaic engine functions can be imported."""
    # This test mainly verifies imports work
    assert callable(discover_sentinel2_scenes_temporal)
    assert callable(discover_baseline_and_current_scenes)
    assert callable(group_scenes_by_mgrs_tile)


def test_group_scenes_by_mgrs_tile():
    """Test grouping scenes by MGRS tile."""
    # Create mock scene metadata
    scene1 = SentinelSceneMetadata(
        scene_id="S2A_TEST_1",
        datetime="2026-05-01T10:00:00Z",
        cloud_cover_pct=10.0,
        platform="sentinel-2a",
        mgrs_tile="43PFN",
        red_asset_url=None,
        nir_asset_url=None,
        scl_asset_url=None,
        bbox=[76.0, 11.0, 77.0, 12.0],
        stac_properties={},
    )

    scene2 = SentinelSceneMetadata(
        scene_id="S2B_TEST_2",
        datetime="2026-05-02T10:00:00Z",
        cloud_cover_pct=15.0,
        platform="sentinel-2b",
        mgrs_tile="43PFN",
        red_asset_url=None,
        nir_asset_url=None,
        scl_asset_url=None,
        bbox=[76.0, 11.0, 77.0, 12.0],
        stac_properties={},
    )

    scene3 = SentinelSceneMetadata(
        scene_id="S2A_TEST_3",
        datetime="2026-05-03T10:00:00Z",
        cloud_cover_pct=5.0,
        platform="sentinel-2a",
        mgrs_tile="43PGN",
        red_asset_url=None,
        nir_asset_url=None,
        scl_asset_url=None,
        bbox=[77.0, 11.0, 78.0, 12.0],
        stac_properties={},
    )

    scenes = [scene1, scene2, scene3]
    grouped = group_scenes_by_mgrs_tile(scenes)

    assert "43PFN" in grouped
    assert "43PGN" in grouped
    assert len(grouped["43PFN"]) == 2
    assert len(grouped["43PGN"]) == 1

    # Check sorting within tiles (most recent first)
    assert grouped["43PFN"][0].datetime == "2026-05-02T10:00:00Z"  # Most recent


# -------------------------------------------------------------------------
# 4. Temporal Composite Tests
# -------------------------------------------------------------------------
def test_create_temporal_composite_mvc():
    """Test MVC composite creation with mock data."""
    # Create mock NDVI arrays with known values
    ndvi1 = np.array([[0.2, 0.4], [0.1, 0.3]], dtype=np.float32)
    ndvi2 = np.array([[0.3, 0.1], [0.2, 0.5]], dtype=np.float32)
    ndvi3 = np.array([[0.1, 0.5], [0.3, 0.2]], dtype=np.float32)

    # Create mock scenes with the NDVI data
    class MockScene:
        def __init__(self, scene_id, ndvi_data):
            self.scene_id = scene_id
            self.datetime = "2026-05-01T10:00:00Z"
            self.platform = "sentinel-2a"
            self.cloud_cover_pct = 10.0
            self.ndvi_data = ndvi_data

    # Since we can't easily test the full function without downloading,
    # we'll test the core MVC logic
    from phase3_temporal_mosaic.temporal_composite import _create_mvc_composite

    processed_scenes = [
        {'scene_id': f'SCENE_{i}', 'datetime': '2026-05-01T10:00:00Z',
         'platform': 'sentinel-2a', 'ndvi': ndvi_data,
         'red': ndvi_data, 'nir': ndvi_data, 'scl': ndvi_data, 'cloud_cover': 10.0}
        for i, ndvi_data in enumerate([ndvi1, ndvi2, ndvi3])
    ]

    # Test MVC composite
    mvc_result = _create_mvc_composite(processed_scenes)

    # Expected MVC: pixel-wise maximum
    expected = np.array([[0.3, 0.5], [0.3, 0.5]], dtype=np.float32)

    np.testing.assert_array_equal(mvc_result, expected)


def test_create_temporal_composite_median():
    """Test Median composite creation with mock data."""
    from phase3_temporal_mosaic.temporal_composite import _create_median_composite

    # Create mock NDVI arrays
    ndvi1 = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
    ndvi2 = np.array([[0.3, 0.4], [0.1, 0.2]], dtype=np.float32)
    ndvi3 = np.array([[0.2, 0.3], [0.2, 0.3]], dtype=np.float32)

    processed_scenes = [
        {'scene_id': f'SCENE_{i}', 'datetime': '2026-05-01T10:00:00Z',
         'platform': 'sentinel-2a', 'ndvi': ndvi_data,
         'red': ndvi_data, 'nir': ndvi_data, 'scl': ndvi_data, 'cloud_cover': 10.0}
        for i, ndvi_data in enumerate([ndvi1, ndvi2, ndvi3])
    ]

    # Test median composite
    median_result = _create_median_composite(processed_scenes)

    # Expected median: [0.2, 0.3], [0.2, 0.3] (median of [0.1,0.3,0.2] and [0.2,0.4,0.3])
    expected = np.array([[0.2, 0.3], [0.2, 0.3]], dtype=np.float32)

    np.testing.assert_array_equal(median_result, expected)


# -------------------------------------------------------------------------
# 5. Anomaly Detector Tests
# -------------------------------------------------------------------------
def test_calculate_delta_ndvi():
    """Test ΔNDVI calculation."""
    current_ndvi = np.array([[0.6, 0.2], [0.1, 0.8]], dtype=np.float32)
    baseline_ndvi = np.array([[0.4, 0.3], [0.2, 0.5]], dtype=np.float32)

    delta_ndvi, metadata = calculate_delta_ndvi(
        current_ndvi=current_ndvi,
        baseline_ndvi=baseline_ndvi,
    )

    # Expected: current - baseline
    expected = np.array([[0.2, -0.1], [-0.1, 0.3]], dtype=np.float32)

    np.testing.assert_allclose(delta_ndvi, expected, rtol=1e-6)

    # Check metadata
    assert metadata['validity_stats']['valid_pixel_count'] == 4
    assert metadata['validity_stats']['mean_delta_ndvi'] == pytest.approx(0.075, abs=1e-3)
    assert metadata['validity_stats']['positive_change_pixels'] == 2  # 0.2 and 0.3
    assert metadata['validity_stats']['negative_change_pixels'] == 2  # -0.1 and -0.1


def test_calculate_delta_ndvi_with_nodata():
    """Test ΔNDVI calculation with NoData values."""
    current_ndvi = np.array([[0.6, RASTER_NODATA_VALUE], [0.1, 0.8]], dtype=np.float32)
    baseline_ndvi = np.array([[0.4, 0.3], [RASTER_NODATA_VALUE, 0.5]], dtype=np.float32)

    delta_ndvi, metadata = calculate_delta_ndvi(
        current_ndvi=current_ndvi,
        baseline_ndvi=baseline_ndvi,
    )

    # Only pixel [0,0] and [1,1] should be valid (both have data in both periods)
    # [0,1]: current has data, baseline is nodata -> result nodata
    # [1,0]: current is nodata, baseline has data -> result nodata
    expected = np.array([[0.2, RASTER_NODATA_VALUE],
                        [RASTER_NODATA_VALUE, 0.3]], dtype=np.float32)

    # Compare valid pixels
    mask = ~np.isnan(expected) & (expected != RASTER_NODATA_VALUE)
    np.testing.assert_allclose(delta_ndvi[mask], expected[mask], rtol=1e-6)

    # Check that nodata pixels are preserved
    assert np.isnan(delta_ndvi[0, 1]) or delta_ndvi[0, 1] == RASTER_NODATA_VALUE
    assert np.isnan(delta_ndvi[1, 0]) or delta_ndvi[1, 0] == RASTER_NODATA_VALUE

    # Check metadata
    assert metadata['validity_stats']['valid_pixel_count'] == 2
    assert metadata['validity_stats']['current_only_count'] == 1  # [0,1]
    assert metadata['validity_stats']['baseline_only_count'] == 1   # [1,0]


# -------------------------------------------------------------------------
# 6. QA Generator Tests
# -------------------------------------------------------------------------
def test_generate_qa_band():
    """Test QA band generation."""
    height, width = 20, 20
    current_ndvi = np.random.uniform(-0.2, 0.8, (height, width)).astype(np.float32)
    baseline_ndvi = np.random.uniform(-0.2, 0.8, (height, width)).astype(np.float32)
    delta_ndvi = current_ndvi - baseline_ndvi

    qa_band, qa_metadata = generate_qa_band(
        current_ndvi=current_ndvi,
        baseline_ndvi=baseline_ndvi,
        delta_ndvi=delta_ndvi,
        multi_tile_processed=True,
    )

    # Check output shape and type
    assert qa_band.shape == (height, width)
    assert qa_band.dtype == np.uint8

    # Check that validity bit is set for reasonable NDVI values
    valid_pixels = (
        np.isfinite(current_ndvi) & (current_ndvi >= -1.0) & (current_ndvi <= 1.0) &
        np.isfinite(baseline_ndvi) & (baseline_ndvi >= -1.0) & (baseline_ndvi <= 1.0) &
        np.isfinite(delta_ndvi) & (delta_ndvi >= -2.0) & (delta_ndvi <= 2.0)
    )

    # At least some pixels should have validity bit set
    validity_set = np.sum(qa_band & (1 << QA_VALID_PIXEL_BIT))
    assert validity_set > 0

    # Check metadata structure
    assert 'bit_meanings' in qa_metadata
    assert 'statistics' in qa_metadata
    assert qa_metadata['bit_depth'] == 8
    assert qa_metadata['multi_tile_processed'] == True


# -------------------------------------------------------------------------
# 7. Multiband Export Tests
# -------------------------------------------------------------------------
def test_export_multiband_geotiff():
    """Test 4-band GeoTIFF export with correct band order."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        geotiff_path = tmp_path / "test_multiband.tif"
        metadata_path = tmp_path / "test_multiband.json"

        # Create test data
        height, width = 10, 10
        current_ndvi = np.full((height, width), 0.5, dtype=np.float32)
        baseline_ndvi = np.full((height, width), 0.3, dtype=np.float32)
        delta_ndvi = current_ndvi - baseline_ndvi  # Should be 0.2
        qa_band = np.full((height, width), 1, dtype=np.uint8)  # Set validity bit

        transform = from_bounds(76.0, 11.0, 77.0, 12.0, width, height)

        # Export the multiband GeoTIFF
        created_path = export_multiband_geotiff(
            current_ndvi=current_ndvi,
            baseline_ndvi=baseline_ndvi,
            delta_ndvi=delta_ndvi,
            qa_band=qa_band,
            transform=transform,
            output_geotiff_path=geotiff_path,
            output_metadata_path=metadata_path,
            metadata_tags={"TEST_TAG": "TEST_VALUE"},
        )

        assert created_path == geotiff_path
        assert geotiff_path.exists()
        assert metadata_path.exists()

        # Verify the GeoTIFF content
        with rasterio.open(geotiff_path) as src:
            assert src.count == 4  # 4 bands
            assert src.width == width
            assert src.height == height
            assert src.crs == CRS.from_string("EPSG:4326")

            # Read each band
            band1 = src.read(1)  # Current NDVI
            band2 = src.read(2)  # Baseline NDVI
            band3 = src.read(3)  # ΔNDVI
            band4 = src.read(4)  # QA band

            # Check band values (with tolerance for nodata conversion)
            np.testing.assert_allclose(band1, np.full((height, width), 0.5), rtol=1e-6)
            np.testing.assert_allclose(band2, np.full((height, width), 0.3), rtol=1e-6)
            np.testing.assert_allclose(band3, np.full((height, width), 0.2), rtol=1e-6)
            np.testing.assert_array_equal(band4, np.full((height, width), 1))

            # Check tags
            tags = src.tags()
            assert tags.get("TEST_TAG") == "TEST_VALUE"
            assert "GeoShield AI Phase 3" in tags.get("DESCRIPTION", "")

            # Check band descriptions
            assert src.descriptions[0] == "Current NDVI Composite"
            assert src.descriptions[1] == "Baseline NDVI Composite"
            assert src.descriptions[2] == "ΔNDVI Change Detection"
            assert src.descriptions[3] == "8-bit QA Band"


# -------------------------------------------------------------------------
# 8. Feature Table Exporter Tests
# -------------------------------------------------------------------------
def test_export_feature_table():
    """Test feature table export."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        parquet_path = tmp_path / "test_features.parquet"
        csv_path = tmp_path / "test_features.csv"

        # Create test data
        height, width = 5, 5
        current_ndvi = np.full((height, width), 0.6, dtype=np.float32)
        baseline_ndvi = np.full((height, width), 0.4, dtype=np.float32)
        delta_ndvi = current_ndvi - baseline_ndvi  # 0.2
        qa_band = np.full((height, width), 1, dtype=np.uint8)  # Validity bit set

        transform = from_bounds(76.0, 11.0, 77.0, 12.0, width, height)

        # Export feature table
        created_parquet, created_csv = export_feature_table(
            current_ndvi=current_ndvi,
            baseline_ndvi=baseline_ndvi,
            delta_ndvi=delta_ndvi,
            qa_band=qa_band,
            transform=transform,
            output_parquet_path=parquet_path,
            output_csv_path=csv_path,
            sample_interval=1,  # Every pixel
        )

        assert created_parquet == parquet_path
        assert created_csv == csv_path
        assert parquet_path.exists()
        assert csv_path.exists()

        # Try to read the parquet file (if pandas is available)
        try:
            import pandas as pd
            df = pd.read_parquet(parquet_path)
            assert len(df) == height * width  # 25 rows
            assert 'latitude' in df.columns
            assert 'longitude' in df.columns
            assert 'current_ndvi' in df.columns
            assert 'baseline_ndvi' in df.columns
            assert 'delta_ndvi' in df.columns
            assert 'current_vegetation_class' in df.columns
            assert 'baseline_vegetation_class' in df.columns
            assert 'change_direction' in df.columns
            assert 'change_magnitude' in df.columns

            # Check some values
            assert (df['current_ndvi'] == 0.6).all()
            assert (df['baseline_ndvi'] == 0.4).all()
            assert np.allclose(df['delta_ndvi'], 0.2, rtol=1e-6)
        except ImportError:
            # If pandas not available, at least check files exist
            pass


# -------------------------------------------------------------------------
# 9. Spot Composite Sampler Tests
# -------------------------------------------------------------------------
def test_spot_composite_sampler_synthetic():
    """Test spot composite sampler with synthetic data."""
    # Generate synthetic mosaic first
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        geotiff_path = tmp_path / "test_mosaic.tif"
        metadata_path = tmp_path / "test_mosaic.json"

        generate_synthetic_mosaic_fixture(
            output_geotiff=geotiff_path,
            output_metadata=metadata_path,
        )

        # Test sampling inside AOI (using approximate Nilgiris coordinates)
        # Ooty: approximately 11.4102 N, 76.6950 E
        result = get_spot_ndvi_composite(
            latitude=11.4102,
            longitude=76.6950,
            raster_path=geotiff_path,
        )

        # Should return a valid result (coordinates are inside our test bounds)
        # Note: exact values depend on the synthetic fixture generation
        assert 'is_valid' in result
        assert 'latitude' in result
        assert 'longitude' in result
        assert 'current_ndvi' in result
        assert 'baseline_ndvi' in result
        assert 'delta_ndvi' in result
        assert 'is_mock' in result
        assert result['is_mock'] == True

        # Test QA bit extraction
        assert 'qa_valid' in result
        assert 'qa_cloud_detected' in result
        assert 'qa_shadow_detected' in result
        assert 'qa_water_detected' in result
        assert 'qa_snow_ice_detected' in result
        assert 'qa_sentinel_2a' in result
        assert 'qa_sentinel_2b' in result
        assert 'qa_multi_tile' in result


def test_spot_composite_sampler_outside_aoi():
    """Test spot composite sampler with coordinates outside AOI."""
    # Test with clearly outside coordinates (Chennai, far to the east)
    result = get_spot_ndvi_composite(
        latitude=13.0827,
        longitude=80.2707,
    )

    assert result['is_valid'] == False
    assert 'outside the Nilgiris study area' in result['error']
    assert result['current_ndvi'] is None
    assert result['baseline_ndvi'] is None
    assert result['delta_ndvi'] is None


# -------------------------------------------------------------------------
# 10. Integration Tests
# -------------------------------------------------------------------------
def test_phase3_pipeline_synthetic_end_to_end():
    """Test end-to-end Phase 3 pipeline with synthetic data."""
    # This test runs the actual pipeline in synthetic mode
    from phase3_temporal_mosaic.run_phase3_pipeline import run_synthetic_mode

    # Run the synthetic mode pipeline
    success = run_synthetic_mode()
    assert success == True

    # Check that outputs were created
    assert LATEST_MOSAIC_RASTER_PATH.exists()
    assert LATEST_MOSAIC_METADATA_PATH.exists()
    assert FEATURE_TABLE_PARQUET_PATH.exists()
    assert FEATURE_TABLE_CSV_PATH.exists()

    # Verify the GeoTIFF has correct structure
    with rasterio.open(LATEST_MOSAIC_RASTER_PATH) as src:
        assert src.count == 4  # 4 bands as required
        assert src.width > 0
        assert src.height > 0

        # Check band descriptions match specification
        assert src.descriptions[0] == "Current NDVI Composite"
        assert src.descriptions[1] == "Baseline NDVI Composite"
        assert src.descriptions[2] == "ΔNDVI Change Detection"
        assert src.descriptions[3] == "8-bit QA Band"

        # Check that it's marked as mock
        tags = src.tags()
        assert tags.get("IS_MOCK") == "TRUE"


def test_baseline_and_current_date_ranges():
    """Test helper functions for calculating date ranges."""
    from phase3_temporal_mosaic.config import get_baseline_date_range, get_current_date_range
    from datetime import datetime

    # Test with known date
    test_date = datetime(2026, 6, 15)

    baseline_start, baseline_end = get_baseline_date_range(
        reference_date=test_date,
        years_back=3,
        start_month=6,
        end_month=10,
    )

    # Should be 3 years back: 2023-06-01 to 2023-10-28
    assert baseline_start == "2023-06-01"
    assert baseline_end == "2023-10-28"  # Approximate end of month

    current_start, current_end = get_current_date_range(
        reference_date=test_date,
        year_offset=0,  # Same year
        start_month=6,
        end_month=10,
    )

    # Should be same year: 2026-06-01 to 2026-10-28
    assert current_start == "2026-06-01"
    assert current_end == "2026-10-28"


# -------------------------------------------------------------------------
# 11. Edge Case and Error Handling Tests
# -------------------------------------------------------------------------
def test_anomaly_detector_identical_arrays():
    """Test ΔNDVI calculation when current and baseline are identical."""
    test_array = np.array([[0.5, 0.3], [0.1, 0.7]], dtype=np.float32)

    delta_ndvi, metadata = calculate_delta_ndvi(
        current_ndvi=test_array,
        baseline_ndvi=test_array,
    )

    # Should be all zeros (or very close due to floating point)
    expected = np.zeros_like(test_array)
    np.testing.assert_array_almost_equal(delta_ndvi, expected, decimal=6)

    # Check metadata
    assert metadata['validity_stats']['mean_delta_ndvi'] == pytest.approx(0.0, abs=1e-6)
    assert metadata['validity_stats']['positive_change_pixels'] == 0
    assert metadata['validity_stats']['negative_change_pixels'] == 0
    assert metadata['validity_stats']['no_change_pixels'] == 4


def test_anomaly_detector_extreme_values():
    """Test ΔNDVI calculation with extreme values near boundaries."""
    # Test near NDVI boundaries
    current_ndvi = np.array([[1.0, -1.0]], dtype=np.float32)  # Max and min NDVI
    baseline_ndvi = np.array([[0.0, 0.0]], dtype=np.float32)  # Zero

    delta_ndvi, metadata = calculate_delta_ndvi(
        current_ndvi=current_ndvi,
        baseline_ndvi=baseline_ndvi,
    )

    # Expected: [1.0-0.0, -1.0-0.0] = [1.0, -1.0]
    # Should be clipped to [-2.0, 2.0] range, so no clipping needed
    expected = np.array([[1.0, -1.0]], dtype=np.float32)
    np.testing.assert_array_equal(delta_ndvi, expected)

    # Test values that would exceed ΔNDVI boundaries
    current_ndvi = np.array([[1.0, 1.0]], dtype=np.float32)   # Max NDVI
    baseline_ndvi = np.array([[-1.0, -1.0]], dtype=np.float32) # Min NDVI

    delta_ndvi, metadata = calculate_delta_ndvi(
        current_ndvi=current_ndvi,
        baseline_ndvi=baseline_ndvi,
    )

    # Expected: [1.0-(-1.0), 1.0-(-1.0)] = [2.0, 2.0]
    # Should be clipped to [2.0, 2.0] (no change as it's at limit)
    expected = np.array([[2.0, 2.0]], dtype=np.float32)
    np.testing.assert_array_equal(delta_ndvi, expected)

    # Test the other extreme
    current_ndvi = np.array([[-1.0, -1.0]], dtype=np.float32) # Min NDVI
    baseline_ndvi = np.array([[1.0, 1.0]], dtype=np.float32)  # Max NDVI

    delta_ndvi, metadata = calculate_delta_ndvi(
        current_ndvi=current_ndvi,
        baseline_ndvi=baseline_ndvi,
    )

    # Expected: [-1.0-1.0, -1.0-1.0] = [-2.0, -2.0]
    expected = np.array([[-2.0, -2.0]], dtype=np.float32)
    np.testing.assert_array_equal(delta_ndvi, expected)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])