"""
GeoTIFF Raster Exporter
========================
Writes standardized float32 single-band GeoTIFF rasters with EPSG:4326 CRS,
embedded metadata tags, Affine transform, and explicit NoData (-9999.0) definitions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.crs import CRS

from phase2_sentinel_ndvi.config import (
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    RASTER_DTYPE,
    LATEST_NDVI_RASTER_PATH,
    LATEST_METADATA_JSON_PATH,
)


def export_ndvi_geotiff(
    ndvi_array: np.ndarray,
    transform: rasterio.Affine,
    output_geotiff_path: Path = LATEST_NDVI_RASTER_PATH,
    output_metadata_path: Optional[Path] = LATEST_METADATA_JSON_PATH,
    crs: CRS = CRS.from_string(TARGET_CRS),
    nodata_value: float = RASTER_NODATA_VALUE,
    metadata_tags: Optional[Dict[str, Any]] = None,
    statistics: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Exports a 2D float32 NDVI array as an EPSG:4326 GeoTIFF with embedded metadata.

    Args:
        ndvi_array: 2D numpy array.
        transform: Affine geotransform.
        output_geotiff_path: Destination .tif file path.
        output_metadata_path: Optional destination .json sidecar metadata path.
        crs: Coordinate Reference System (default EPSG:4326).
        nodata_value: Explicit NoData constant (-9999.0).
        metadata_tags: Key-value metadata dictionary to embed in TIFF tags.
        statistics: Summary statistics dict.

    Returns:
        Resolved Path to created GeoTIFF.
    """
    output_geotiff_path = Path(output_geotiff_path)
    output_geotiff_path.parent.mkdir(parents=True, exist_ok=True)

    height, width = ndvi_array.shape

    # Ensure NaN values are replaced with nodata_value
    export_data = np.where(np.isnan(ndvi_array), nodata_value, ndvi_array).astype(np.float32)

    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": RASTER_DTYPE,
        "crs": crs,
        "transform": transform,
        "nodata": nodata_value,
        "compress": "deflate",
    }

    with rasterio.open(output_geotiff_path, "w", **meta) as dst:
        dst.write(export_data, 1)

        # Embed TIFF metadata tags
        tags = {
            "DESCRIPTION": "Sentinel-2 NDVI Landslide Vegetation Layer",
            "UNITS": "NDVI Index (-1.0 to 1.0)",
            "CRS": str(crs),
            "NODATA": str(nodata_value),
        }
        if metadata_tags:
            for k, v in metadata_tags.items():
                tags[str(k).upper()] = str(v)
        dst.update_tags(**tags)

    # Save JSON sidecar if requested
    if output_metadata_path:
        output_metadata_path = Path(output_metadata_path)
        sidecar_data = {
            "geotiff_path": str(output_geotiff_path.resolve()),
            "crs": str(crs),
            "width": width,
            "height": height,
            "nodata_value": nodata_value,
            "bounds": [
                transform.c,
                transform.f + transform.e * height,
                transform.c + transform.a * width,
                transform.f,
            ],
            "metadata_tags": metadata_tags or {},
            "statistics": statistics or {},
        }
        with open(output_metadata_path, "w", encoding="utf-8") as f:
            json.dump(sidecar_data, f, indent=2, ensure_ascii=False)

    return output_geotiff_path
