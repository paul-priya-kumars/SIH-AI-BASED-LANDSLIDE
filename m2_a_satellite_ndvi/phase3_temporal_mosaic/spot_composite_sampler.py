"""
Spot Composite Sampler — M2-A Integration Point
================================================

Extracts point NDVI values from pre-computed Phase 3 mosaic outputs for a given
geographic coordinate (latitude, longitude).

Designed for high-throughput, low-latency queries from M1 / environment_service.
Does NOT download or process satellite imagery on every request.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.transform import rowcol
from shapely.geometry import Point

from phase1_aoi import load_aoi_geometry, get_aoi_bounds
from phase3_temporal_mosaic.config import (
    LATEST_MOSAIC_RASTER_PATH,
    RASTER_NODATA_VALUE,
    classify_ndvi_value,
)
from phase3_temporal_mosaic.synthetic_mosaic_fixture import (
    MOCK_MOSAIC_PATH,
    generate_synthetic_mosaic_fixture,
)


def get_spot_ndvi_composite(
    latitude: float,
    longitude: float,
    raster_path: Optional[Path] = None,
    require_real: bool = False,
) -> Dict[str, Any]:
    """
    Samples NDVI values at a spot coordinate from the Phase 3 mosaic GeoTIFF.

    Args:
        latitude: Target latitude (degrees North).
        longitude: Target longitude (degrees East).
        raster_path: Optional path to specific raster. Defaults to latest production raster,
                     or synthetic mock fixture if no production raster is found.
        require_real: If True, strictly rejects mock/synthetic data.

    Returns:
        Structured response dictionary with validity, NDVI values, classification,
        change detection results, and metadata.

    Returns dictionary with keys:
        - is_valid: Boolean indicating if coordinate is valid and within AOI
        - is_nodata: Boolean indicating if pixel is NoData/masked
        - latitude, longitude: Input coordinates (rounded to 4 decimal places)
        - current_ndvi: Current period NDVI value or None if invalid
        - baseline_ndvi: Baseline period NDVI value or None if invalid
        - delta_ndvi: ΔNDVI (current - baseline) value or None if invalid
        - current_vegetation_class: Vegetation class for current period
        - baseline_vegetation_class: Vegetation class for baseline period
        - change_direction: 'increasing', 'decreasing', or 'stable'
        - change_magnitude: Absolute value of delta_ndvi
        - is_mock: Boolean indicating if data is synthetic mock
        - data_source: Source of the data (real satellite or synthetic fixture)
        - scene_id: Identifier of the mosaic/scene
        - processing_timestamp: Timestamp of mosaic generation
        - qa_valid: Boolean indicating QA validity (bit 0)
        - qa_cloud_detected: Boolean indicating cloud detection (bit 1)
        - qa_shadow_detected: Boolean indicating shadow detection (bit 2)
        - qa_water_detected: Boolean indicating water detection (bit 3)
        - qa_snow_ice_detected: Boolean indicating snow/ice detection (bit 4)
        - qa_sentinel_2a: Boolean indicating Sentinel-2A presence (bit 5)
        - qa_sentinel_2b: Boolean indicating Sentinel-2B presence (bit 6)
        - qa_multi_tile: Boolean indicating multi-tile composite (bit 7)
    """
    # 1. Coordinate range validation
    if not (-90.0 <= latitude <= 90.0):
        return {
            "is_valid": False,
            "is_nodata": False,
            "error": f"Invalid latitude {latitude}: must be between -90 and 90.",
            "latitude": latitude,
            "longitude": longitude,
            "current_ndvi": None,
            "baseline_ndvi": None,
            "delta_ndvi": None,
            "current_vegetation_class": None,
            "baseline_vegetation_class": None,
            "change_direction": None,
            "change_magnitude": None,
        }
    if not (-180.0 <= longitude <= 180.0):
        return {
            "is_valid": False,
            "is_nodata": False,
            "error": f"Invalid longitude {longitude}: must be between -180 and 180.",
            "latitude": latitude,
            "longitude": longitude,
            "current_ndvi": None,
            "baseline_ndvi": None,
            "delta_ndvi": None,
            "current_vegetation_class": None,
            "baseline_vegetation_class": None,
            "change_direction": None,
            "change_magnitude": None,
        }

    # 2. Check if coordinate falls inside Phase 1 AOI boundary
    point = Point(longitude, latitude)
    aoi_polygon = load_aoi_geometry()

    if not aoi_polygon.contains(point):
        return {
            "is_valid": False,
            "is_nodata": False,
            "error": f"Coordinate ({latitude:.4f}, {longitude:.4f}) is outside the Nilgiris study area.",
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current_ndvi": None,
            "baseline_ndvi": None,
            "delta_ndvi": None,
            "current_vegetation_class": None,
            "baseline_vegetation_class": None,
            "change_direction": None,
            "change_magnitude": None,
        }

    # 3. Locate raster file
    target_path = raster_path or LATEST_MOSAIC_RASTER_PATH
    if not target_path.exists():
        # If production raster does not exist and real data is required, raise error
        if require_real:
            raise FileNotFoundError(
                f"Production mosaic raster not found at {target_path}. Run Phase 3 pipeline first."
            )
        # Otherwise fallback to synthetic mock fixture
        if not MOCK_MOSAIC_PATH.exists():
            generate_synthetic_mosaic_fixture()
        target_path = MOCK_MOSAIC_PATH

    # 4. Open raster and read metadata tags
    with rasterio.open(target_path) as src:
        tags = src.tags()
        is_mock = tags.get("IS_MOCK", "FALSE").upper() == "TRUE"

        if require_real and is_mock:
            raise ValueError(
                "Real satellite observation required, but the cached raster is marked as a synthetic mock fixture."
            )

        data_source = tags.get("DATA_SOURCE", "UNKNOWN")
        scene_id = tags.get("SCENE_ID", "UNKNOWN_MOSAIC")
        processing_timestamp = tags.get("PROCESSING_TIMESTAMP", None)

        # 5. Coordinate to pixel transformation (4-band raster)
        try:
            row, col = rowcol(src.transform, longitude, latitude)
        except Exception as e:
            return {
                "is_valid": False,
                "is_nodata": False,
                "error": f"Failed to compute row/column from coordinates: {e}",
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "current_ndvi": None,
                "baseline_ndvi": None,
                "delta_ndvi": None,
                "current_vegetation_class": None,
                "baseline_vegetation_class": None,
                "change_direction": None,
                "change_magnitude": None,
            }

        # Verify pixel row/col is within raster bounds
        if row < 0 or row >= src.height or col < 0 or col >= src.width:
            return {
                "is_valid": False,
                "is_nodata": False,
                "error": "Pixel index falls outside raster matrix.",
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "current_ndvi": None,
                "baseline_ndvi": None,
                "delta_ndvi": None,
                "current_vegetation_class": None,
                "baseline_vegetation_class": None,
                "change_direction": None,
                "change_magnitude": None,
            }

        # Read all 4 bands at the pixel location
        # Window format: ((row_start, row_stop), (col_start, col_stop))
        window = rasterio.windows.Window(col, row, 1, 1)
        pixel_bands = src.read(window=window)  # Shape: (4, 1, 1)

        # Extract band values (Band 1=Current, Band 2=Baseline, Band 3=ΔNDVI, Band 4=QA)
        current_ndvi_val = float(pixel_bands[0, 0, 0])
        baseline_ndvi_val = float(pixel_bands[1, 0, 0])
        delta_ndvi_val = float(pixel_bands[2, 0, 0])
        qa_val = int(pixel_bands[3, 0, 0])

    # 6. Check for NoData / Masked Pixels in any of the first 3 bands
    nodata_mask = (
        np.isnan(current_ndvi_val) or current_ndvi_val == RASTER_NODATA_VALUE or
        np.isnan(baseline_ndvi_val) or baseline_ndvi_val == RASTER_NODATA_VALUE or
        np.isnan(delta_ndvi_val) or delta_ndvi_val == RASTER_NODATA_VALUE
    )

    # Also check if values are outside valid NDVI ranges
    valid_range_mask = (
        (current_ndvi_val < -1.0) or (current_ndvi_val > 1.0) or
        (baseline_ndvi_val < -1.0) or (baseline_ndvi_val > 1.0) or
        (delta_ndvi_val < -2.0) or (delta_ndvi_val > 2.0)  # ΔNDVI theoretical range
    )

    is_nodata = nodata_mask or valid_range_mask

    if is_nodata:
        # Determine vegetation class for nodata case
        current_class = "NO_DATA_OR_MASKED"
        baseline_class = "NO_DATA_OR_MASKED"
        change_direction = None
        change_magnitude = None
    else:
        # 7. Return Valid Composite Result
        current_ndvi_clean = round(current_ndvi_val, 4)
        baseline_ndvi_clean = round(baseline_ndvi_val, 4)
        delta_ndvi_clean = round(delta_ndvi_val, 4)

        current_class = classify_ndvi_value(current_ndvi_clean)
        baseline_class = classify_ndvi_value(baseline_ndvi_clean)

        # Determine change direction and magnitude
        if delta_ndvi_clean > 0.01:
            change_direction = "increasing"
        elif delta_ndvi_clean < -0.01:
            change_direction = "decreasing"
        else:
            change_direction = "stable"

        change_magnitude = round(abs(delta_ndvi_clean), 4)

    # 8. Extract QA bit information
    qa_valid = bool(qa_val & (1 << 0))  # Bit 0
    qa_cloud_detected = bool(qa_val & (1 << 1))  # Bit 1
    qa_shadow_detected = bool(qa_val & (1 << 2))  # Bit 2
    qa_water_detected = bool(qa_val & (1 << 3))  # Bit 3
    qa_snow_ice_detected = bool(qa_val & (1 << 4))  # Bit 4
    qa_sentinel_2a = bool(qa_val & (1 << 5))  # Bit 5
    qa_sentinel_2b = bool(qa_val & (1 << 6))  # Bit 6
    qa_multi_tile = bool(qa_val & (1 << 7))  # Bit 7

    return {
        "is_valid": True,
        "is_nodata": False,
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "current_ndvi": current_ndvi_clean if not is_nodata else None,
        "baseline_ndvi": baseline_ndvi_clean if not is_nodata else None,
        "delta_ndvi": delta_ndvi_clean if not is_nodata else None,
        "current_vegetation_class": current_class,
        "baseline_vegetation_class": baseline_class,
        "change_direction": change_direction,
        "change_magnitude": change_magnitude,
        "is_mock": is_mock,
        "data_source": data_source,
        "scene_id": scene_id,
        "processing_timestamp": processing_timestamp,
        "qa_valid": qa_valid,
        "qa_cloud_detected": qa_cloud_detected,
        "qa_shadow_detected": qa_shadow_detected,
        "qa_water_detected": qa_water_detected,
        "qa_snow_ice_detected": qa_snow_ice_detected,
        "qa_sentinel_2a": qa_sentinel_2a,
        "qa_sentinel_2b": qa_sentinel_2b,
        "qa_multi_tile": qa_multi_tile,
    }