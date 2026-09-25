"""
Synthetic Offline Test Fixture Generator
=========================================
Generates a deterministic synthetic test raster for offline testing and CI/CD.

CRITICAL POLICY:
This data is EXPLICITLY marked as test/mock fixture (is_mock=True).
It will NEVER be presented as real satellite observations.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from phase1_aoi import get_aoi_bounds
from phase2_sentinel_ndvi.config import (
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    DATA_DIR,
)
from phase2_sentinel_ndvi.reprojection import clip_raster_to_aoi_polygon
from phase2_sentinel_ndvi.export_geotiff import export_ndvi_geotiff
from phase2_sentinel_ndvi.ndvi_processor import compute_ndvi_statistics

MOCK_FIXTURE_PATH = DATA_DIR / "mock_ndvi_fixture.tif"
MOCK_METADATA_PATH = DATA_DIR / "mock_ndvi_fixture.json"


def generate_synthetic_ndvi_fixture(
    output_geotiff: Path = MOCK_FIXTURE_PATH,
    output_metadata: Path = MOCK_METADATA_PATH,
    width: int = 120,
    height: int = 80,
) -> Tuple[Path, Dict[str, Any]]:
    """
    Builds a deterministic, explicitly labeled synthetic NDVI raster
    conforming strictly to the Phase 1 Nilgiris AOI bounds and polygon.

    Returns:
        Tuple of (Path to created GeoTIFF, metadata dict)
    """
    min_lon, min_lat, max_lon, max_lat = get_aoi_bounds()
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

    # Deterministic spatial grid: higher NDVI in forests, lower in urban center
    lon_grid = np.linspace(min_lon, max_lon, width)
    lat_grid = np.linspace(max_lat, min_lat, height)
    xx, yy = np.meshgrid(lon_grid, lat_grid)

    # Base NDVI ~ 0.55 (dense Western Ghats vegetation)
    base_ndvi = 0.55 + 0.20 * np.sin((xx - 76.45) * 6.0) * np.cos((yy - 11.20) * 8.0)

    # Ooty central basin urban depression (~ 11.41 N, 76.69 E)
    dist_ooty = np.sqrt((xx - 76.695)**2 + (yy - 11.410)**2)
    urban_depression = np.exp(-dist_ooty / 0.05) * 0.25
    synthetic_ndvi = base_ndvi - urban_depression

    # Clamp to valid range [0.05, 0.85]
    synthetic_ndvi = np.clip(synthetic_ndvi, 0.05, 0.85).astype(np.float32)

    # Insert a synthetic cloud/shadow patch in the northern quadrant (simulating SCL mask)
    cloud_patch = (xx >= 76.50) & (xx <= 76.58) & (yy >= 11.52) & (yy <= 11.58)
    synthetic_ndvi[cloud_patch] = np.nan

    # Clip to exact Phase 1 AOI boundary polygon
    clipped_ndvi = clip_raster_to_aoi_polygon(
        synthetic_ndvi,
        transform=transform,
        nodata_value=RASTER_NODATA_VALUE,
    )

    stats = compute_ndvi_statistics(clipped_ndvi, nodata_value=RASTER_NODATA_VALUE)

    metadata_tags = {
        "IS_MOCK": "TRUE",
        "DATA_SOURCE": "SYNTHETIC_OFFLINE_TEST_FIXTURE",
        "SCENE_ID": "MOCK-SYNTHETIC-FIXTURE-S2",
        "ACQUISITION_DATE": "2026-09-01T00:00:00Z",
        "CLOUD_COVER_PCT": "5.0",
        "DESCRIPTION": "SYNTHETIC TEST FIXTURE (DO NOT USE AS REAL SATELLITE DATA)",
    }

    created_path = export_ndvi_geotiff(
        ndvi_array=clipped_ndvi,
        transform=transform,
        output_geotiff_path=output_geotiff,
        output_metadata_path=output_metadata,
        crs=CRS.from_string(TARGET_CRS),
        nodata_value=RASTER_NODATA_VALUE,
        metadata_tags=metadata_tags,
        statistics=stats,
    )

    return created_path, metadata_tags
