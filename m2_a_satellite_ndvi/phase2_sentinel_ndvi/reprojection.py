"""
Reprojection & Spatial Masking Engine
=====================================
Performs rigorous coordinate transformation from native UTM projections
(e.g., EPSG:32643 UTM Zone 43N) to standard EPSG:4326 (WGS 84), followed by
spatial masking to the Phase 1 Nilgiris AOI polygon.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import calculate_default_transform, reproject
from shapely.geometry import mapping

from phase1_aoi import load_aoi_geometry, get_aoi_bounds
from phase2_sentinel_ndvi.config import (
    TARGET_CRS,
    RASTER_NODATA_VALUE,
)


def reproject_raster_array(
    src_data: np.ndarray,
    src_transform: rasterio.Affine,
    src_crs: CRS,
    dst_crs: CRS = CRS.from_string(TARGET_CRS),
    src_nodata: float = RASTER_NODATA_VALUE,
    dst_nodata: float = RASTER_NODATA_VALUE,
    resampling: Resampling = Resampling.bilinear,
    resolution: Optional[float] = None,
) -> Tuple[np.ndarray, rasterio.Affine, Tuple[float, float, float, float]]:
    """
    Reprojects a 2D raster array from native source CRS (e.g., UTM Zone 43N)
    to target CRS (EPSG:4326) with proper affine transform and dimension calculation.

    Returns:
        Tuple of (dst_data, dst_transform, (minx, miny, maxx, maxy))
    """
    src_height, src_width = src_data.shape

    # If src_data has NaNs, fill them with src_nodata for reproject
    filled_src = np.where(np.isnan(src_data), src_nodata, src_data).astype(np.float32)

    # Compute bounding coordinates in source CRS from transform and shape
    x0 = src_transform.c
    y0 = src_transform.f
    x1 = x0 + src_transform.a * src_width
    y1 = y0 + src_transform.e * src_height
    left, right = min(x0, x1), max(x0, x1)
    bottom, top = min(y0, y1), max(y0, y1)

    # Calculate default transform and dimensions in destination CRS
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs,
        dst_crs,
        src_width,
        src_height,
        left=left,
        bottom=bottom,
        right=right,
        top=top,
        resolution=resolution,
    )

    # Allocate destination array with dst_nodata
    dst_data = np.full((dst_height, dst_width), dst_nodata, dtype=np.float32)

    # Execute warping
    reproject(
        source=filled_src,
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=resampling,
        src_nodata=src_nodata,
        dst_nodata=dst_nodata,
    )

    # Calculate geographic bounds in destination CRS
    minx = dst_transform.c
    maxy = dst_transform.f
    maxx = minx + dst_transform.a * dst_width
    miny = maxy + dst_transform.e * dst_height
    bounds = (min(minx, maxx), min(miny, maxy), max(minx, maxx), max(miny, maxy))

    return dst_data, dst_transform, bounds


def clip_raster_to_aoi_polygon(
    data: np.ndarray,
    transform: rasterio.Affine,
    crs: CRS = CRS.from_string(TARGET_CRS),
    nodata_value: float = RASTER_NODATA_VALUE,
) -> np.ndarray:
    """
    Masks out any pixels that fall outside the exact Phase 1 Nilgiris AOI polygon,
    setting them to nodata_value.

    Does NOT simply use a rectangular bounding box: enforces the true polygon perimeter.
    """
    aoi_polygon = load_aoi_geometry()
    geom_dict = mapping(aoi_polygon)

    height, width = data.shape

    # geometry_mask returns True for pixels OUTSIDE the geometries
    outside_mask = geometry_mask(
        [geom_dict],
        out_shape=(height, width),
        transform=transform,
        invert=False,  # False: pixels outside geometry are True
        all_touched=True,
    )

    clipped_data = data.copy()
    clipped_data[outside_mask] = nodata_value

    return clipped_data
