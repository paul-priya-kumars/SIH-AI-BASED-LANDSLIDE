"""
Phase 2 Configuration — Sentinel-2 Ingestion & NDVI Calculation Engine
=======================================================================
Single source of truth for STAC query endpoints, SCL cloud/shadow masks,
NDVI classification categories, raster formatting, and cache locations.
"""

from pathlib import Path
from typing import Dict, Set, Any, List

# Directory Paths
MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "ndvi"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default raster and metadata paths
LATEST_NDVI_RASTER_PATH = DATA_DIR / "latest_ndvi_epsg4326.tif"
LATEST_METADATA_JSON_PATH = DATA_DIR / "latest_ndvi_metadata.json"

# STAC API Configuration (Element84 Earth Search AWS Open Data)
STAC_API_ENDPOINT = "https://earth-search.aws.element84.com/v1"
STAC_SEARCH_URL = f"{STAC_API_ENDPOINT}/search"
STAC_COLLECTION = "sentinel-2-l2a"

# Query Defaults
DEFAULT_MAX_CLOUD_COVER = 20.0  # Percent
DEFAULT_DATE_RANGE_DAYS = 180   # Days to look back for cloud-free observations

# Target Coordinate Reference System for Clipped Rasters
TARGET_CRS = "EPSG:4326"
TARGET_EPSG = 4326

# Raster Properties
RASTER_NODATA_VALUE = -9999.0
RASTER_DTYPE = "float32"

# -------------------------------------------------------------------------
# Sentinel-2 Scene Classification Layer (SCL) Specification
# -------------------------------------------------------------------------
# The SCL band provides categorical land and atmospheric classification:
# 0: NO_DATA
# 1: SATURATED_OR_DEFECTIVE
# 2: DARK_AREA_PIXELS
# 3: CLOUD_SHADOWS
# 4: VEGETATION
# 5: NOT_VEGETATED
# 6: WATER
# 7: UNCLASSIFIED
# 8: CLOUD_MEDIUM_PROBABILITY
# 9: CLOUD_HIGH_PROBABILITY
# 10: THIN_CIRRUS
# 11: SNOW_ICE

SCL_CLASS_NAMES: Dict[int, str] = {
    0: "NO_DATA",
    1: "SATURATED_OR_DEFECTIVE",
    2: "DARK_AREA_PIXELS",
    3: "CLOUD_SHADOWS",
    4: "VEGETATION",
    5: "NOT_VEGETATED",
    6: "WATER",
    7: "UNCLASSIFIED",
    8: "CLOUD_MEDIUM_PROBABILITY",
    9: "CLOUD_HIGH_PROBABILITY",
    10: "THIN_CIRRUS",
    11: "SNOW_ICE",
}

# Explicitly masked SCL classes (converted to NaN / NoData, NEVER 0.0)
MASKED_SCL_CLASSES: Set[int] = {
    0,   # NO_DATA
    1,   # SATURATED_OR_DEFECTIVE
    3,   # CLOUD_SHADOWS
    8,   # CLOUD_MEDIUM_PROBABILITY
    9,   # CLOUD_HIGH_PROBABILITY
    10,  # THIN_CIRRUS
    11,  # SNOW_ICE
}

# -------------------------------------------------------------------------
# Landslide Hazard Vegetation Classification Bins
# -------------------------------------------------------------------------
NDVI_CLASSIFICATIONS: List[Dict[str, Any]] = [
    {
        "class": "WATER_OR_BARREN",
        "min_ndvi": -1.0,
        "max_ndvi": 0.10,
        "description": "Water bodies, bare rock, or active scarp surfaces.",
        "slope_stability_factor": "Variable / Scarp prone if steep rock",
    },
    {
        "class": "SPARSE_OR_DEGRADED",
        "min_ndvi": 0.10,
        "max_ndvi": 0.30,
        "description": "Sparse grass, degraded tea cut-slopes, or exposed soil.",
        "slope_stability_factor": "HIGH VULNERABILITY (lack of deep root anchoring)",
    },
    {
        "class": "MODERATE_VEGETATION",
        "min_ndvi": 0.30,
        "max_ndvi": 0.50,
        "description": "Thick shrubland, healthy tea estates, cultivated terraces.",
        "slope_stability_factor": "Moderate stability with surface protection",
    },
    {
        "class": "DENSE_CANOPY",
        "min_ndvi": 0.50,
        "max_ndvi": 1.00,
        "description": "Dense evergreen forest, montane Shola canopy.",
        "slope_stability_factor": "HIGH STABILITY (deep mechanical root tensile strength)",
    },
]


def classify_ndvi_value(ndvi: float) -> str:
    """Classifies a single valid NDVI value into a susceptibility vegetation category."""
    if ndvi is None or (isinstance(ndvi, float) and (ndvi != ndvi or ndvi == RASTER_NODATA_VALUE)):
        return "NO_DATA_OR_MASKED"
    for cat in NDVI_CLASSIFICATIONS:
        if cat["min_ndvi"] <= ndvi < cat["max_ndvi"]:
            return cat["class"]
    if ndvi >= 1.0:
        return "DENSE_CANOPY"
    return "UNKNOWN"
