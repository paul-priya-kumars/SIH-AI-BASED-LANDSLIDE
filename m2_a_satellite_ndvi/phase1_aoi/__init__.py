"""
Phase 1 AOI Package — M2-A: Satellite & NDVI Engineer
======================================================
Provides clean, reusable interfaces for downstream satellite processing scripts
(Phase 2: Sentinel-2 data acquisition, NDVI calculation, raster clipping, ML prep).

Usage in Phase 2:
    from phase1_aoi import load_aoi_gdf, load_aoi_geometry, get_aoi_bounds

    gdf = load_aoi_gdf()
    geometry = load_aoi_geometry()
    bbox = get_aoi_bounds()
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import geopandas as gpd
from shapely.geometry import shape, Polygon

from phase1_aoi.config import (
    DEFAULT_OUTPUT_GEOJSON,
    STUDY_AREA_METADATA,
    BOUNDING_BOX,
    get_bounding_box_tuple,
)
from phase1_aoi.validate_aoi import validate_aoi, AOIValidationError


def load_aoi_geojson(file_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads and returns the raw study area GeoJSON dictionary.
    Automatically generates the file if it does not exist yet.
    """
    path = Path(file_path or DEFAULT_OUTPUT_GEOJSON)
    if not path.exists():
        from phase1_aoi.create_aoi import generate_aoi_geojson
        generate_aoi_geojson(output_path=path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_aoi_gdf(file_path: Optional[Path] = None) -> gpd.GeoDataFrame:
    """
    Loads the study area as a GeoPandas GeoDataFrame with CRS EPSG:4326.
    """
    path = Path(file_path or DEFAULT_OUTPUT_GEOJSON)
    if not path.exists():
        from phase1_aoi.create_aoi import generate_aoi_geojson
        generate_aoi_geojson(output_path=path)
    return gpd.read_file(path)


def load_aoi_geometry(file_path: Optional[Path] = None) -> Polygon:
    """
    Extracts and returns the primary Shapely Polygon of the study area.
    Ideal for STAC API searches, rasterio masking, and Shapely spatial operations.
    """
    data = load_aoi_geojson(file_path)
    features = data.get("features", [])
    if not features:
        raise ValueError("AOI GeoJSON contains no features.")
    geom_dict = features[0]["geometry"]
    return shape(geom_dict)


def get_aoi_bounds(file_path: Optional[Path] = None) -> Tuple[float, float, float, float]:
    """
    Returns the bounding box coordinates tuple (min_lon, min_lat, max_lon, max_lat)
    in EPSG:4326 (WGS 84).
    """
    polygon = load_aoi_geometry(file_path)
    bounds = polygon.bounds  # (minx, miny, maxx, maxy)
    return (float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3]))


def get_aoi_metadata() -> Dict[str, Any]:
    """
    Returns a copy of the canonical study area metadata.
    """
    return dict(STUDY_AREA_METADATA)


__all__ = [
    "load_aoi_geojson",
    "load_aoi_gdf",
    "load_aoi_geometry",
    "get_aoi_bounds",
    "get_aoi_metadata",
    "validate_aoi",
    "AOIValidationError",
    "STUDY_AREA_METADATA",
    "BOUNDING_BOX",
    "DEFAULT_OUTPUT_GEOJSON",
]
