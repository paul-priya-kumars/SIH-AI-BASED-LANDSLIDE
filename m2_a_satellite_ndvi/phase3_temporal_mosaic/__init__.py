"""
Phase 3: Temporal NDVI Mosaic & Change Detection Engine
=======================================================

Public API for the Phase 3 temporal mosaicking and change detection system.
"""

from .config import (
    LATEST_MOSAIC_RASTER_PATH,
    LATEST_MOSAIC_METADATA_PATH,
    FEATURE_TABLE_PARQUET_PATH,
    FEATURE_TABLE_CSV_PATH,
    TEMPORAL_COMPOSITE_METHODS,
    DEFAULT_COMPOSITE_METHOD,
    QA_BIT_MEANINGS,
    BAND_ORDER_CURRENT_NDVI,
    BAND_ORDER_BASELINE_NDVI,
    BAND_ORDER_DELTA_NDVI,
    BAND_ORDER_QA,
    classify_ndvi_value,
    get_baseline_date_range,
    get_current_date_range,
)

# Import main functions when they're implemented
# from .mosaic_engine import discover_sentinel2_scenes_temporal
# from .temporal_composite import create_temporal_composite
# from .anomaly_detector := calculate_delta_ndvi
# from .qa_generator import generate_qa_band
# from .export_multiband import export_multiband_geotiff
# from .feature_table_exporter import export_feature_table
# from .spot_composite_sampler import get_spot_ndvi_composite

__all__ = [
    # Config exports
    "LATEST_MOSAIC_RASTER_PATH",
    "LATEST_MOSAIC_METADATA_PATH",
    "FEATURE_TABLE_PARQUET_PATH",
    "FEATURE_TABLE_CSV_PATH",
    "TEMPORAL_COMPOSITE_METHODS",
    "DEFAULT_COMPOSITE_METHOD",
    "QA_BIT_MEANINGS",
    "BAND_ORDER_CURRENT_NDVI",
    "BAND_ORDER_BASELINE_NDVI",
    "BAND_ORDER_DELTA_NDVI",
    "BAND_ORDER_QA",
    "classify_ndvi_value",
    "get_baseline_date_range",
    "get_current_date_range",

    # Main API functions (to be uncommented as implementations are added)
    # "discover_sentinel2_scenes_temporal",
    # "create_temporal_composite",
    # "calculate_delta_ndvi",
    # "generate_qa_band",
    # "export_multiband_geotiff",
    # "export_feature_table",
    # "get_spot_ndvi_composite",
]