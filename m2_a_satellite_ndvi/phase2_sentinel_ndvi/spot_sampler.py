"""
Spot Telemetry Sampler — M2-A Integration Point
================================================
Extracts point NDVI values from a pre-computed/cached raster for a given
geographic coordinate (latitude, longitude).

Does NOT download or process satellite scenes on every request.
Designed for high-throughput, low-latency queries from M3 / environment_service.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.transform import rowcol
from shapely.geometry import Point

from phase1_aoi import load_aoi_geometry, get_aoi_bounds
from phase2_sentinel_ndvi.config import (
    LATEST_NDVI_RASTER_PATH,
    RASTER_NODATA_VALUE,
    classify_ndvi_value,
)
from phase2_sentinel_ndvi.synthetic_fixture import (
    MOCK_FIXTURE_PATH,
    generate_synthetic_ndvi_fixture,
)


def get_spot_ndvi(
    latitude: float,
    longitude: float,
    raster_path: Optional[Path] = None,
    require_real: bool = False,
) -> Dict[str, Any]:
    """
    Samples NDVI at a spot coordinate from the cached GeoTIFF raster.

    Args:
        latitude: Target latitude (degrees North).
        longitude: Target longitude (degrees East).
        raster_path: Optional path to specific raster. Defaults to latest production raster,
                     or synthetic mock fixture if no production raster is found.
        require_real: If True, strictly rejects mock/synthetic data.

    Returns:
        Structured response dictionary with validity, ndvi, classification, and metadata.
    """
    # 1. Coordinate range validation
    if not (-90.0 <= latitude <= 90.0):
        return {
            "is_valid": False,
            "is_nodata": False,
            "error": f"Invalid latitude {latitude}: must be between -90 and 90.",
            "latitude": latitude,
            "longitude": longitude,
            "ndvi": None,
            "vegetation_class": None,
        }
    if not (-180.0 <= longitude <= 180.0):
        return {
            "is_valid": False,
            "is_nodata": False,
            "error": f"Invalid longitude {longitude}: must be between -180 and 180.",
            "latitude": latitude,
            "longitude": longitude,
            "ndvi": None,
            "vegetation_class": None,
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
            "ndvi": None,
            "vegetation_class": None,
        }

    # 3. Locate raster file
    target_path = raster_path or LATEST_NDVI_RASTER_PATH
    if not target_path.exists():
        # If production raster does not exist and real data is required, raise error
        if require_real:
            raise FileNotFoundError(
                f"Production NDVI raster not found at {target_path}. Run satellite ingestion first."
            )
        # Otherwise fallback to synthetic mock fixture
        if not MOCK_FIXTURE_PATH.exists():
            generate_synthetic_ndvi_fixture()
        target_path = MOCK_FIXTURE_PATH

    # 4. Open raster and read metadata tags
    with rasterio.open(target_path) as src:
        tags = src.tags()
        is_mock = tags.get("IS_MOCK", "FALSE").upper() == "TRUE"

        if require_real and is_mock:
            raise ValueError(
                "Real satellite observation required, but the cached raster is marked as a synthetic mock fixture."
            )

        data_source = tags.get("DATA_SOURCE", "SENTINEL_2_L2A")
        scene_id = tags.get("SCENE_ID", "UNKNOWN_SCENE")
        acquisition_date = tags.get("ACQUISITION_DATE", None)
        cloud_pct = tags.get("CLOUD_COVER_PCT", None)

        # 5. Coordinate to pixel transformation
        try:
            row, col = rowcol(src.transform, longitude, latitude)
        except Exception as e:
            return {
                "is_valid": False,
                "is_nodata": False,
                "error": f"Failed to compute row/column from coordinates: {e}",
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "ndvi": None,
                "vegetation_class": None,
            }

        # Verify pixel row/col is within raster bounds
        if row < 0 or row >= src.height or col < 0 or col >= src.width:
            return {
                "is_valid": False,
                "is_nodata": False,
                "error": "Pixel index falls outside raster matrix.",
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "ndvi": None,
                "vegetation_class": None,
            }

        # Read single pixel value
        # Window format: ((row_start, row_stop), (col_start, col_stop))
        window = rasterio.windows.Window(col, row, 1, 1)
        pixel_val = float(src.read(1, window=window)[0, 0])

    # 6. Check for NoData / Masked Pixel
    if (
        np.isnan(pixel_val)
        or pixel_val == RASTER_NODATA_VALUE
        or pixel_val < -1.0
        or pixel_val > 1.0
    ):
        return {
            "is_valid": False,
            "is_nodata": True,
            "reason": "Pixel masked by SCL cloud/shadow filter, water body, or outside perimeter.",
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "ndvi": None,
            "vegetation_class": "NO_DATA_OR_MASKED",
            "is_mock": is_mock,
            "data_source": data_source,
            "scene_id": scene_id,
            "acquisition_date": acquisition_date,
        }

    # 7. Return Valid Spot Result
    ndvi_clean = round(pixel_val, 4)
    return {
        "is_valid": True,
        "is_nodata": False,
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "ndvi": ndvi_clean,
        "vegetation_class": classify_ndvi_value(ndvi_clean),
        "is_mock": is_mock,
        "data_source": data_source,
        "scene_id": scene_id,
        "acquisition_date": acquisition_date,
        "cloud_cover_pct": float(cloud_pct) if cloud_pct else None,
    }
