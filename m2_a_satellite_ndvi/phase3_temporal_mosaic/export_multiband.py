"""
Multiband GeoTIFF Exporter — 4-band Output
==========================================

Exports 4-band GeoTIFF with exact band order as specified:
Band 1 → Current NDVI
Band 2 → Baseline NDVI
Band 3 → ΔNDVI
Band 4 → QA

Includes proper metadata documentation and GeoTIFF tags.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.crs import CRS
import json
import logging

from phase3_temporal_mosaic.config import (
    LATEST_MOSAIC_RASTER_PATH,
    LATEST_MOSAIC_METADATA_PATH,
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    RASTER_DTYPE,
    BAND_ORDER_CURRENT_NDVI,
    BAND_ORDER_BASELINE_NDVI,
    BAND_ORDER_DELTA_NDVI,
    BAND_ORDER_QA,
    logger,
)


def export_multiband_geotiff(
    current_ndvi: np.ndarray,
    baseline_ndvi: np.ndarray,
    delta_ndvi: np.ndarray,
    qa_band: np.ndarray,
    transform: rasterio.Affine,
    output_geotiff_path: Path = LATEST_MOSAIC_RASTER_PATH,
    output_metadata_path: Optional[Path] = LATEST_MOSAIC_METADATA_PATH,
    crs: CRS = CRS.from_string(TARGET_CRS),
    nodata_value: float = RASTER_NODATA_VALUE,
    metadata_tags: Optional[Dict[str, Any]] = None,
    processing_metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Export 4-band GeoTIFF with exact band order specification.

    Band Order (as strictly required):
        Band 1 → Current NDVI
        Band 2 → Baseline NDVI
        Band 3 → ΔNDVI (Current - Baseline)
        Band 4 → QA (8-bit quality assessment)

    Args:
        current_ndvi: Current period NDVI composite array
        baseline_ndvi: Baseline period NDVI composite array
        delta_ndvi: ΔNDVI change detection array
        qa_band: 8-bit QA band array
        transform: Affine geotransform
        output_geotiff_path: Destination .tif file path
        output_metadata_path: Optional destination .json sidecar metadata path
        crs: Coordinate Reference System (default EPSG:4326)
        nodata_value: Explicit NoData constant (-9999.0)
        metadata_tags: Key-value metadata dictionary to embed in TIFF tags
        processing_metadata: Additional processing metadata for JSON sidecar

    Returns:
        Resolved Path to created GeoTIFF
    """
    logger.info("Exporting 4-band GeoTIFF with specified band order")

    # Validate all input arrays have same shape
    arrays = [current_ndvi, baseline_ndvi, delta_ndvi, qa_band]
    array_names = ['current_ndvi', 'baseline_ndvi', 'delta_ndvi', 'qa_band']

    for i, (array, name) in enumerate(zip(arrays, array_names)):
        if array.shape != arrays[0].shape:
            raise ValueError(f"Array shape mismatch: {name} {array.shape} != {array_names[0]} {arrays[0].shape}")

    height, width = current_ndvi.shape
    logger.info(f"Exporting {width} x {height} pixel 4-band GeoTIFF")

    # Prepare metadata tags
    tags = {
        "DESCRIPTION": "GeoShield AI Phase 3 Temporal NDVI Change Detection Product",
        "BAND_1": "Current NDVI (Maximum Value or Median Composite)",
        "BAND_2": "Baseline NDVI (Maximum Value or Median Composite)",
        "BAND_3": "ΔNDVI = Current NDVI - Baseline NDVI",
        "BAND_4": "8-bit QA Band (see metadata for bit meanings)",
        "UNITS_BAND_1-3": "NDVI Index (-1.0 to 1.0)",
        "UNITS_BAND_4": "8-bit Integer (0-255)",
        "DATA_TYPE_BAND_1-3": "FP32",
        "DATA_TYPE_BAND_4": "UINT8",
        "CRS": str(crs),
        "NODATA_BAND_1-3": str(nodata_value),
        "NOTE": "Band order strictly follows specification: 1=Current, 2=Baseline, 3=ΔNDVI, 4=QA",
    }

    if metadata_tags:
        for k, v in metadata_tags.items():
            tags[str(k).upper()] = str(v)

    # Prepare JSON sidecar metadata
    sidecar_data = {
        'geotiff_path': str(output_geotiff_path.resolve()),
        'crs': str(crs),
        'width': width,
        'height': height,
        'band_count': 4,
        'band_definitions': {
            1: {
                'name': 'Current NDVI',
                'description': 'Maximum Value or Median Composite of current period',
                'units': 'NDVI Index',
                'data_type': 'FP32',
                'nodata': nodata_value,
                'valid_range': [-1.0, 1.0],
            },
            2: {
                'name': 'Baseline NDVI',
                'description': 'Maximum Value or Median Composite of baseline period',
                'units': 'NDVI Index',
                'data_type': 'FP32',
                'nodata': nodata_value,
                'valid_range': [-1.0, 1.0],
            },
            3: {
                'name': 'ΔNDVI (Change Detection)',
                'description': 'Current NDVI - Baseline NDVI',
                'units': 'NDVI Index Difference',
                'data_type': 'FP32',
                'nodata': nodata_value,
                'valid_range': [-2.0, 2.0],
            },
            4: {
                'name': 'QA Band',
                'description': '8-bit Quality Assessment Band',
                'units': '8-bit Integer',
                'data_type': 'UINT8',
                'valid_range': [0, 255],
                'bit_meanings': {
                    'bit_0': 'Valid pixel (0=invalid, 1=valid)',
                    'bit_1': 'Cloud detected',
                    'bit_2': 'Shadow detected',
                    'bit_3': 'Water body',
                    'bit_4': 'Snow/Ice',
                    'bit_5': 'Sentinel-2A platform',
                    'bit_6': 'Sentinel-2B platform',
                    'bit_7': 'Multi-tile composite',
                }
            }
        },
        'nodata_value': nodata_value,
        'metadata_tags': metadata_tags or {},
        'processing_metadata': processing_metadata or {},
        'creation_timestamp': str(np.datetime64('now')),
        'phase': 'Phase 3 - Temporal NDVI Mosaic & Change Detection',
    }

    # Ensure output directory exists
    output_geotiff_path = Path(output_geotiff_path)
    output_geotiff_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure GeoTIFF metadata for 4-band output
    geo_tiff_meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 4,  # Four bands
        "dtype": RASTER_DTYPE,  # Use float32 for all bands (uint8 values will fit in float32)
        "crs": crs,
        "transform": transform,
        "nodata": nodata_value,  # This applies to all bands by default, but we'll handle per-band
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }

    # Write the 4-band GeoTIFF
    with rasterio.open(output_geotiff_path, "w", **geo_tiff_meta) as dst:
        # Write each band with appropriate data type and handling
        # Band 1: Current NDVI (float32)
        current_data = np.where(np.isnan(current_ndvi), nodata_value, current_ndvi).astype(np.float32)
        dst.write(current_data, BAND_ORDER_CURRENT_NDVI)

        # Band 2: Baseline NDVI (float32)
        baseline_data = np.where(np.isnan(baseline_ndvi), nodata_value, baseline_ndvi).astype(np.float32)
        dst.write(baseline_data, BAND_ORDER_BASELINE_NDVI)

        # Band 3: ΔNDVI (float32)
        delta_data = np.where(np.isnan(delta_ndvi), nodata_value, delta_ndvi).astype(np.float32)
        dst.write(delta_data, BAND_ORDER_DELTA_NDVI)

        # Band 4: QA (uint8)
        qa_data = qa_band.astype(np.uint8)
        dst.write(qa_data, BAND_ORDER_QA)

        # Set band descriptions
        dst.set_band_description(BAND_ORDER_CURRENT_NDVI, "Current NDVI Composite")
        dst.set_band_description(BAND_ORDER_BASELINE_NDVI, "Baseline NDVI Composite")
        dst.set_band_description(BAND_ORDER_DELTA_NDVI, "ΔNDVI Change Detection")
        dst.set_band_description(BAND_ORDER_QA, "8-bit QA Band")

        # Update tags
        dst.update_tags(**tags)

    # Save JSON sidecar if requested
    if output_metadata_path:
        output_metadata_path = Path(output_metadata_path)
        output_metadata_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_metadata_path, "w", encoding="utf-8") as f:
            json.dump(sidecar_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully exported 4-band GeoTIFF to {output_geotiff_path}")
    return output_geotiff_path