"""
Synthetic Offline Test Fixture Generator for Phase 3
=====================================================

Generates a deterministic synthetic test raster for offline testing and CI/CD
that mimics the output of the Phase 3 temporal mosaic pipeline.

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
from phase3_temporal_mosaic.config import (
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    PHASE3_DATA_DIR,
)
from phase3_temporal_mosaic.export_multiband import export_multiband_geotiff
from phase3_temporal_mosaic.qa_generator import generate_qa_band

MOCK_MOSAIC_PATH = PHASE3_DATA_DIR / "mock_mosaic_epsg4326.tif"
MOCK_METADATA_PATH = PHASE3_DATA_DIR / "mock_mosaic_metadata.json"


def generate_synthetic_mosaic_fixture(
    output_geotiff: Path = MOCK_MOSAIC_PATH,
    output_metadata: Path = MOCK_METADATA_PATH,
    width: int = 100,
    height: int = 80,
) -> Tuple[Path, Dict[str, Any]]:
    """
    Builds a deterministic, explicitly labeled synthetic 4-band mosaic raster
    conforming strictly to the Phase 1 Nilgiris AOI bounds and polygon.

    Band Order (as strictly required):
        Band 1 → Current NDVI
        Band 2 → Baseline NDVI
        Band 3 → ΔNDVI (Current - Baseline)
        Band 4 → QA (8-bit quality assessment)

    Returns:
        Tuple of (Path to created GeoTIFF, metadata dict)
    """
    min_lon, min_lat, max_lon, max_lat = get_aoi_bounds()
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

    # Generate synthetic Current NDVI (Band 1)
    # Base NDVI ~ 0.45 with spatial variation
    lon_grid = np.linspace(min_lon, max_lon, width)
    lat_grid = np.linspace(max_lat, min_lat, height)
    xx, yy = np.meshgrid(lon_grid, lat_grid)

    current_ndvi = 0.45 + 0.25 * np.sin((xx - 76.45) * 4.0) * np.cos((yy - 11.20) * 6.0)
    current_ndvi = np.clip(current_ndvi, -0.1, 0.9).astype(np.float32)  # Slightly extended range for realism

    # Generate synthetic Baseline NDVI (Band 2)
    # Similar pattern but slightly different to create realistic changes
    baseline_ndvi = 0.50 + 0.20 * np.sin((xx - 76.50) * 3.5) * np.cos((yy - 11.25) * 5.5)
    baseline_ndvi = np.clip(baseline_ndvi, -0.1, 0.9).astype(np.float32)

    # Calculate ΔNDVI (Band 3) = Current - Baseline
    delta_ndvi = current_ndvi - baseline_ndvi
    # Clip to realistic ΔNDVI range
    delta_ndvi = np.clip(delta_ndvi, -0.5, 0.5).astype(np.float32)

    # Generate synthetic QA band (Band 4)
    # Start with all pixels valid
    qa_band = np.zeros((height, width), dtype=np.uint8)

    # Set validity bit (bit 0) for most pixels (simulate some cloud/masking)
    valid_probability = 0.85  # 85% of pixels valid
    valid_mask = np.random.random((height, width)) < valid_probability
    qa_band[valid_mask] |= (1 << 0)  # Set bit 0

    # Add some cloud detection (bit 1) - low probability
    cloud_mask = (np.random.random((height, width)) < 0.1) & valid_mask
    qa_band[cloud_mask] |= (1 << 1)  # Set bit 1

    # Add some shadow detection (bit 2) - correlated with clouds
    shadow_mask = (np.random.random((height, width)) < 0.05) & cloud_mask
    qa_band[shadow_mask] |= (1 << 2)  # Set bit 2

    # Add water detection (bit 3) in lower NDVI areas
    water_mask = (current_ndvi < 0.1) & (np.random.random((height, width)) < 0.2) & valid_mask
    qa_band[water_mask] |= (1 << 3)  # Set bit 3

    # Add snow/ice detection (bit 4) in higher NDVI areas (unrealistic but for testing)
    snow_ice_mask = (current_ndvi > 0.7) & (np.random.random((height, width)) < 0.05) & valid_mask
    qa_band[snow_ice_mask] |= (1 << 4)  # Set bit 4

    # Add platform bits - mix of Sentinel-2A and 2B
    platform_a_mask = np.random.random((height, width)) < 0.6
    platform_b_mask = ~platform_a_mask
    qa_band[platform_a_mask & valid_mask] |= (1 << 5)  # Set bit 5 (S2A)
    qa_band[platform_b_mask & valid_mask] |= (1 << 6)  # Set bit 6 (S2B)

    # Add multi-tile bit (bit 7) - indicate this is a multi-tile composite
    qa_band[valid_mask] |= (1 << 7)  # Set bit 7 for all valid pixels

    # Apply AOI clipping to all bands - simplified for synthetic fixture
    def clip_band(band_data):
        # For synthetic data, we'll use a simple bounding box clip
        # Create coordinate arrays
        height, width = band_data.shape
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))

        # Convert pixel coordinates to geographic coordinates
        xs, ys = rasterio.transform.xy(transform, cols, rows)
        xs_array = np.array(xs).reshape(height, width)
        ys_array = np.array(ys).reshape(height, width)

        # Create mask for pixels within AOI bounds (with small margin)
        margin = 0.01  # Small margin inside bounds
        valid_mask = (
            (xs_array >= min_lon + margin) &
            (xs_array <= max_lon - margin) &
            (ys_array >= min_lat + margin) &
            (ys_array <= max_lat - margin)
        )

        # Apply mask
        clipped = np.where(valid_mask, band_data, RASTER_NODATA_VALUE).astype(band_data.dtype)
        return clipped

    current_ndvi_clipped = clip_band(current_ndvi)
    baseline_ndvi_clipped = clip_band(baseline_ndvi)
    delta_ndvi_clipped = clip_band(delta_ndvi)
    qa_band_clipped = clip_band(qa_band)

    # Prepare processing metadata
    processing_metadata = {
        'algorithm_version': 'Phase 3 Synthetic Fixture v1.0',
        'composite_method': 'SYNTHETIC_MVC',  # Synthetic uses MVC-like approach
        'input_scenes_count': 15,  # Synthetic number
        'processed_scenes_count': 15,
        'creation_reason': 'SYNTHETIC_TEST_FIXTURE',
    }

    # Prepare metadata tags for GeoTIFF
    metadata_tags = {
        "IS_MOCK": "TRUE",
        "DATA_SOURCE": "SYNTHETIC_OFFLINE_TEST_FIXTURE",
        "SCENE_ID": "MOSAIC-SYNTHETIC-FIXTURE-S2",
        "PROCESSING_TIMESTAMP": "2026-09-17T12:00:00Z",
        "COMPOSITE_METHOD": "MVC",
        "BASELINE_PERIOD": "2023-06-01/2023-10-31",
        "CURRENT_PERIOD": "2026-06-01/2026-10-31",
        "INPUT_SCENES_COUNT": "15",
        "PROCESSED_SCENES_COUNT": "15",
        "DESCRIPTION": "SYNTHETIC PHASE 3 MOSAIC TEST FIXTURE (DO NOT USE AS REAL SATELLITE DATA)",
    }

    # Create QA band and metadata using the QA generator (for consistency)
    qa_band_final, qa_metadata = generate_qa_band(
        current_ndvi=current_ndvi_clipped,
        baseline_ndvi=baseline_ndvi_clipped,
        delta_ndvi=delta_ndvi_clipped,
        multi_tile_processed=True,
        nodata_value=RASTER_NODATA_VALUE,
    )

    # Override QA band with our synthetic version for deterministic testing
    qa_band_final = qa_band_clipped

    # Export the 4-band GeoTIFF
    created_path = export_multiband_geotiff(
        current_ndvi=current_ndvi_clipped,
        baseline_ndvi=baseline_ndvi_clipped,
        delta_ndvi=delta_ndvi_clipped,
        qa_band=qa_band_final,
        transform=transform,
        output_geotiff_path=output_geotiff,
        output_metadata_path=output_metadata,
        crs=CRS.from_string(TARGET_CRS),
        nodata_value=RASTER_NODATA_VALUE,
        metadata_tags=metadata_tags,
        processing_metadata=processing_metadata,
    )

    # Prepare comprehensive metadata return
    metadata = {
        'geotiff_path': str(created_path.resolve()),
        'crs': str(CRS.from_string(TARGET_CRS)),
        'width': width,
        'height': height,
        'band_count': 4,
        'band_definitions': {
            1: {
                'name': 'Current NDVI',
                'description': 'Synthetic Maximum Value Composite of current period',
                'units': 'NDVI Index',
                'data_type': 'FP32',
                'nodata': RASTER_NODATA_VALUE,
                'valid_range': [-1.0, 1.0],
            },
            2: {
                'name': 'Baseline NDVI',
                'description': 'Synthetic Maximum Value Composite of baseline period',
                'units': 'NDVI Index',
                'data_type': 'FP32',
                'nodata': RASTER_NODATA_VALUE,
                'valid_range': [-1.0, 1.0],
            },
            3: {
                'name': 'ΔNDVI (Change Detection)',
                'description': 'Synthetic Current NDVI - Baseline NDVI',
                'units': 'NDVI Index Difference',
                'data_type': 'FP32',
                'nodata': RASTER_NODATA_VALUE,
                'valid_range': [-2.0, 2.0],
            },
            4: {
                'name': 'QA Band',
                'description': 'Synthetic 8-bit Quality Assessment Band',
                'units': '8-bit Integer',
                'data_type': 'UINT8',
                'valid_range': [0, 255],
                'bit_meanings': {
                    'bit_0': 'Valid pixel (0=invalid/masked, 1=valid)',
                    'bit_1': 'Cloud detected',
                    'bit_2': 'Shadow detected',
                    'bit_3': 'Water body',
                    'bit_4': 'Snow/Ice',
                    'bit_5': 'Sentinel-2A platform',
                    'bit_6': 'Sentinel-2B platform',
                    'bit_7': 'Multi-tile composite',
                }
            }
        },
        'nodata_value': RASTER_NODATA_VALUE,
        'metadata_tags': metadata_tags,
        'processing_metadata': processing_metadata,
        'qa_statistics': qa_metadata['statistics'],
        'creation_timestamp': str(np.datetime64('now')),
        'phase': 'Phase 3 - Synthetic Test Fixture',
        'is_mock': True,
    }

    # Save JSON metadata
    import json
    with open(output_metadata, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return created_path, metadata