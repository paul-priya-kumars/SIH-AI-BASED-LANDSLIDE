"""
Phase 2 — Sentinel-2 Satellite Ingestion & NDVI Pipeline
=========================================================
Exports public functions for STAC querying, safe NDVI computation,
SCL cloud masking, UTM-to-EPSG:4326 reprojection, GeoTIFF export, and spot sampling.
"""

from phase2_sentinel_ndvi.config import (
    STAC_SEARCH_URL,
    STAC_COLLECTION,
    MASKED_SCL_CLASSES,
    SCL_CLASS_NAMES,
    NDVI_CLASSIFICATIONS,
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    LATEST_NDVI_RASTER_PATH,
    LATEST_METADATA_JSON_PATH,
    classify_ndvi_value,
)
from phase2_sentinel_ndvi.stac_client import (
    query_sentinel2_scenes,
    build_stac_query_payload,
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
from phase2_sentinel_ndvi.synthetic_fixture import generate_synthetic_ndvi_fixture
from phase2_sentinel_ndvi.spot_sampler import get_spot_ndvi

__all__ = [
    "query_sentinel2_scenes",
    "build_stac_query_payload",
    "SentinelSceneMetadata",
    "compute_ndvi_array",
    "compute_ndvi_statistics",
    "reproject_raster_array",
    "clip_raster_to_aoi_polygon",
    "export_ndvi_geotiff",
    "generate_synthetic_ndvi_fixture",
    "get_spot_ndvi",
    "classify_ndvi_value",
    "MASKED_SCL_CLASSES",
    "SCL_CLASS_NAMES",
    "NDVI_CLASSIFICATIONS",
    "TARGET_CRS",
    "RASTER_NODATA_VALUE",
    "LATEST_NDVI_RASTER_PATH",
    "LATEST_METADATA_JSON_PATH",
]
