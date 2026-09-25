"""
Phase 3 Configuration — Temporal NDVI Mosaic & Change Detection Engine
=======================================================================

Configuration for multi-tile Sentinel-2 discovery, temporal compositing,
baseline/current NDVI calculation, ΔNDVI computation, QA generation,
multiband export, and feature table creation.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Directory Paths
MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "ndvi"
PHASE3_DATA_DIR = DATA_DIR / "phase3"
PHASE3_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default raster and metadata paths for Phase 3 outputs
LATEST_MOSAIC_RASTER_PATH = PHASE3_DATA_DIR / "latest_mosaic_epsg4326.tif"
LATEST_MOSAIC_METADATA_PATH = PHASE3_DATA_DIR / "latest_mosaic_metadata.json"

# Synthetic fixture paths
MOCK_MOSAIC_PATH = PHASE3_DATA_DIR / "mock_mosaic_epsg4326.tif"
MOCK_METADATA_PATH = PHASE3_DATA_DIR / "mock_mosaic_metadata.json"

# Feature table output paths
FEATURE_TABLE_PARQUET_PATH = PHASE3_DATA_DIR / "feature_table.parquet"
FEATURE_TABLE_CSV_PATH = PHASE3_DATA_DIR / "feature_table.csv"

# Feature table output paths
FEATURE_TABLE_PARQUET_PATH = PHASE3_DATA_DIR / "feature_table.parquet"
FEATURE_TABLE_CSV_PATH = PHASE3_DATA_DIR / "feature_table.csv"

# STAC API Configuration (reuse from Phase 2)
STAC_API_ENDPOINT = "https://earth-search.aws.element84.com/v1"
STAC_SEARCH_URL = f"{STAC_API_ENDPOINT}/search"
STAC_COLLECTION = "sentinel-2-l2a"

# Query Defaults
DEFAULT_MAX_CLOUD_COVER = 20.0  # Percent
DEFAULT_DATE_RANGE_DAYS = 180   # Days to look back for cloud-free observations

# Temporal Compositing Configuration
# MVC = Maximum Value Composite, MEDIAN = Median composite
TEMPORAL_COMPOSITE_METHODS = ["MVC", "MEDIAN"]
DEFAULT_COMPOSITE_METHOD = "MVC"

# Baseline and Current Period Definitions
# These can be overridden via function parameters
DEFAULT_BASELINE_YEARS_BACK = 3  # Use 3-year baseline period
DEFAULT_BASELINE_START_MONTH = 6 # June (start of monsoon season in Nilgiris)
DEFAULT_BASELINE_END_MONTH = 10  # October (end of monsoon season)
DEFAULT_CURRENT_YEAR_OFFSET = 0  # Current year (0 = same year as processing date)

# Minimum Valid Scenes Required for Compositing
MIN_VALID_SCENES_MVC = 3   # Minimum scenes for MVC composite
MIN_VALID_SCENES_MEDIAN = 5 # Minimum scenes for median composite (more robust)

# Insufficient Data Behavior
RETURN_PARTIAL_RESULTS = False  # If True, return results with fewer scenes; if False, return NoData
INSUFFICIENT_DATA_NODATA_VALUE = -9999.0

# Target Coordinate Reference System for Clipped Rasters (reuse from Phase 2)
TARGET_CRS = "EPSG:4326"
TARGET_EPSG = 4326

# Raster Properties (reuse from Phase 2)
RASTER_NODATA_VALUE = -9999.0
RASTER_DTYPE = "float32"

# QA Band Configuration
QA_BIT_DEPTH = 8  # 8-bit QA band
QA_VALID_PIXEL_BIT = 0      # Bit 0: Valid pixel (1 = valid, 0 = invalid/masked)
QA_CLOUD_BIT = 1            # Bit 1: Cloud detected
QA_SHADOW_BIT = 2           # Bit 2: Shadow detected
QA_WATER_BIT = 3            # Bit 3: Water body
QA_SNOW_ICE_BIT = 4         # Bit 4: Snow/Ice
QA_SENTINEL_2A_BIT = 5      # Bit 5: Sentinel-2A platform
QA_SENTINEL_2B_BIT = 6      # Bit 6: Sentinel-2B platform
QA_MULTI_TILE_BIT = 7       # Bit 7: Multi-tile composite (1 = multiple tiles stitched)

# QA Bit Meanings Documentation
QA_BIT_MEANINGS = {
    QA_VALID_PIXEL_BIT: "Valid pixel (0 = invalid/masked, 1 = valid)",
    QA_CLOUD_BIT: "Cloud detected (0 = no cloud, 1 = cloud present)",
    QA_SHADOW_BIT: "Shadow detected (0 = no shadow, 1 = shadow present)",
    QA_WATER_BIT: "Water body (0 = not water, 1 = water)",
    QA_SNOW_ICE_BIT: "Snow/Ice (0 = no snow/ice, 1 = snow/ice present)",
    QA_SENTINEL_2A_BIT: "Sentinel-2A platform (0 = Sentinel-2B or unknown, 1 = Sentinel-2A)",
    QA_SENTINEL_2B_BIT: "Sentinel-2B platform (0 = Sentinel-2A or unknown, 1 = Sentinel-2B)",
    QA_MULTI_TILE_BIT: "Multi-tile composite (0 = single tile, 1 = multi-tile stitched)",
}

# Band Order for 4-band GeoTIFF (exact specification from requirements)
# Band 1 → Current NDVI
# Band 2 → Baseline NDVI
# Band 3 → ΔNDVI (Current - Baseline)
# Band 4 → QA
BAND_ORDER_CURRENT_NDVI = 1
BAND_ORDER_BASELINE_NDVI = 2
BAND_ORDER_DELTA_NDVI = 3
BAND_ORDER_QA = 4

# Vegetation Classification Bins (reuse from Phase 2 for consistency)
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


def get_baseline_date_range(
    reference_date: Optional[datetime] = None,
    years_back: int = DEFAULT_BASELINE_YEARS_BACK,
    start_month: int = DEFAULT_BASELINE_START_MONTH,
    end_month: int = DEFAULT_BASELINE_END_MONTH,
) -> tuple[str, str]:
    """
    Calculate baseline date range for temporal compositing.

    Args:
        reference_date: Reference date (defaults to now)
        years_back: Number of years back for baseline
        start_month: Start month of baseline season (1-12)
        end_month: End month of baseline season (1-12)

    Returns:
        Tuple of (start_date_str, end_date_str) in YYYY-MM-DD format
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Calculate baseline year
    baseline_year = reference_date.year - years_back

    # Handle case where end_month < start_month (season crosses year boundary)
    if end_month < start_month:
        # Season spans two years (e.g., Nov to Feb)
        baseline_start = datetime(baseline_year, start_month, 1)
        baseline_end = datetime(baseline_year + 1, end_month, 28)  # Approximate end
    else:
        # Season within single year
        baseline_start = datetime(baseline_year, start_month, 1)
        baseline_end = datetime(baseline_year, end_month, 28)  # Approximate end

    return (
        baseline_start.strftime("%Y-%m-%d"),
        baseline_end.strftime("%Y-%m-%d")
    )


def get_current_date_range(
    reference_date: Optional[datetime] = None,
    year_offset: int = DEFAULT_CURRENT_YEAR_OFFSET,
    start_month: int = DEFAULT_BASELINE_START_MONTH,
    end_month: int = DEFAULT_BASELINE_END_MONTH,
) -> tuple[str, str]:
    """
    Calculate current date range for temporal compositing.

    Args:
        reference_date: Reference date (defaults to now)
        year_offset: Year offset from reference date (0 = same year)
        start_month: Start month of current season (1-12)
        end_month: End month of current season (1-12)

    Returns:
        Tuple of (start_date_str, end_date_str) in YYYY-MM-DD format
    """
    if reference_date is None:
        reference_date = datetime.now()

    # Calculate current year
    current_year = reference_date.year + year_offset

    # Handle case where end_month < start_month (season crosses year boundary)
    if end_month < start_month:
        # Season spans two years
        current_start = datetime(current_year, start_month, 1)
        current_end = datetime(current_year + 1, end_month, 28)  # Approximate end
    else:
        # Season within single year
        current_start = datetime(current_year, start_month, 1)
        current_end = datetime(current_year, end_month, 28)  # Approximate end

    return (
        current_start.strftime("%Y-%m-%d"),
        current_end.strftime("%Y-%m-%d")
    )