"""
Study Area Configuration — M2-A: Satellite & NDVI Engineer
===========================================================
Single source of truth for the geographic study area (AOI) definition,
bounding coordinates, coordinate reference system (CRS), and metadata.

Target: Nilgiris Landslide Risk Corridor (Western Ghats, Tamil Nadu, India).
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple

# Base directory for Phase 1 AOI module
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_GEOJSON = BASE_DIR / "study_area.geojson"

# Study Area Metadata
STUDY_AREA_METADATA: Dict[str, Any] = {
    "name": "Nilgiris Landslide Risk Study Area",
    "short_code": "AOI-NILGIRIS-01",
    "region": "Nilgiris District, Western Ghats",
    "state": "Tamil Nadu",
    "country": "India",
    "crs": "EPSG:4326",
    "epsg": 4326,
    "datum": "WGS 84",
    "purpose": (
        "Geographical Area of Interest (AOI) for Sentinel-2 Level-2A satellite "
        "data ingestion, cloud masking, NDVI computation, spatial clipping, "
        "and integration with M2-B (DEM/Terrain) and M2-C (Rainfall/Hydrology)."
    ),
    "data_source": "Survey of India / Western Ghats Geomorphic Basin Definition",
    "target_satellite_sensor": "Sentinel-2 MSI (Multispectral Instrument)",
    "sentinel_bands_required": ["B04 (Red - 665nm)", "B08 (NIR - 842nm)"],
    "native_resolution_meters": 10.0,
    "key_catchments": [
        "Ooty Central Urban Valley",
        "Coonoor Ghat Corridor",
        "Kotagiri Ridge & Slopes",
        "Kundah Hydel Basin",
        "Gudalur Western Escarpment",
    ],
}

# Coordinate Extents (EPSG:4326 - WGS 84)
# Coordinate ordering in GeoJSON is [longitude, latitude] per RFC 7946
BOUNDING_BOX: Dict[str, float] = {
    "min_lon": 76.4500,  # Western boundary (Gudalur / Wayanad transition)
    "min_lat": 11.2000,  # Southern boundary (Mettupalayam foothills / Bhavani basin)
    "max_lon": 77.0500,  # Eastern boundary (Kotagiri / Sirumugai descent)
    "max_lat": 11.6000,  # Northern boundary (Mudumalai / Moyar gorge)
}

# Key Representative Reference Center (Ooty catchment center)
CENTER_COORDINATES: Tuple[float, float] = (76.6950, 11.4102)  # (Longitude, Latitude)

# Nilgiris Highland Plateau Boundary Polygon (EPSG:4326, Lon/Lat pairs)
# Encloses the high-risk mountain terrain including Ooty, Coonoor, Kotagiri, and Kundah
POLYGON_COORDINATES: List[Tuple[float, float]] = [
    (76.4500, 11.5000),  # Gudalur NW ridge
    (76.5500, 11.6000),  # Mudumalai northern plateau rim
    (76.7500, 11.6000),  # Moyar gorge northeast overlook
    (77.0500, 11.4500),  # Kotagiri eastern escarpment
    (76.9500, 11.3000),  # Coonoor southeast ghat pass
    (76.7000, 11.2000),  # Kundah southern montane flank
    (76.5000, 11.2500),  # Silent Valley border southwest
    (76.4500, 11.3800),  # Western Ghats western divide
    (76.4500, 11.5000),  # Closing vertex back to start
]


def get_bounding_box_tuple() -> Tuple[float, float, float, float]:
    """
    Returns the bounding box as a tuple: (min_lon, min_lat, max_lon, max_lat).
    Compatible with GeoPandas and Shapely bounds format (minx, miny, maxx, maxy).
    """
    return (
        BOUNDING_BOX["min_lon"],
        BOUNDING_BOX["min_lat"],
        BOUNDING_BOX["max_lon"],
        BOUNDING_BOX["max_lat"],
    )


def get_bbox_polygon_coordinates() -> List[Tuple[float, float]]:
    """
    Returns the rectangular bounding box polygon coordinates closed loop [Lon, Lat].
    """
    min_x, min_y, max_x, max_y = get_bounding_box_tuple()
    return [
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
        (min_x, min_y),
    ]
