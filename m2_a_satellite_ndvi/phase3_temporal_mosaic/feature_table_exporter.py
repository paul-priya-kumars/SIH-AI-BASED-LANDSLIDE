"""
Feature Table Exporter — M1 Integration Point
=============================================

Exports feature table (Parquet/CSV) containing appropriate fields for M1 consumption:
- latitude, longitude
- current_ndvi, baseline_ndvi, delta_ndvi
- quality indicators
- composite metadata
- vegetation classifications
"""

from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple
import numpy as np
import pandas as pd
import logging
import rasterio
from rasterio.transform import from_bounds

from phase3_temporal_mosaic.config import (
    FEATURE_TABLE_PARQUET_PATH,
    FEATURE_TABLE_CSV_PATH,
    RASTER_NODATA_VALUE,
    classify_ndvi_value,
    logger,
)
from phase1_aoi import load_aoi_geometry, get_aoi_bounds


def export_feature_table(
    current_ndvi: np.ndarray,
    baseline_ndvi: np.ndarray,
    delta_ndvi: np.ndarray,
    qa_band: np.ndarray,
    transform: rasterio.Affine,
    output_parquet_path: Path = FEATURE_TABLE_PARQUET_PATH,
    output_csv_path: Path = FEATURE_TABLE_CSV_PATH,
    sample_interval: int = 1,  # Sample every Nth pixel (1 = every pixel)
    nodata_value: float = RASTER_NODATA_VALUE,
    include_qa_details: bool = True,
) -> Tuple[Path, Optional[Path]]:
    """
    Export feature table for M1 consumption.

    Args:
        current_ndvi: Current period NDVI composite array
        baseline_ndvi: Baseline period NDVI composite array
        delta_ndvi: ΔNDVI change detection array
        qa_band: 8-bit QA band array
        transform: Affine geotransform for pixel-to-coordinate conversion
        output_parquet_path: Destination Parquet file path
        output_csv_path: Destination CSV file path
        sample_interval: Sampling interval (1 = every pixel, 10 = every 10th pixel)
        nodata_value: Value representing NoData in input arrays
        include_qa_details: Whether to include individual QA bit columns

    Returns:
        Tuple of (parquet_path, csv_path) - csv_path may be None if not requested
    """
    logger.info("Exporting feature table for M1 integration")

    # Validate input arrays have same shape
    arrays = [current_ndvi, baseline_ndvi, delta_ndvi, qa_band]
    array_names = ['current_ndvi', 'baseline_ndvi', 'delta_ndvi', 'qa_band']

    for i, (array, name) in enumerate(zip(arrays, array_names)):
        if array.shape != arrays[0].shape:
            raise ValueError(f"Array shape mismatch: {name} {array.shape} != {array_names[0]} {arrays[0].shape}")

    height, width = current_ndvi.shape
    logger.info(f"Processing {width} x {height} pixel array with sample interval {sample_interval}")

    # Create coordinate grids
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))

    # Apply sampling interval
    if sample_interval > 1:
        rows = rows[::sample_interval, ::sample_interval]
        cols = cols[::sample_interval, ::sample_interval]
        current_ndvi_sampled = current_ndvi[::sample_interval, ::sample_interval]
        baseline_ndvi_sampled = baseline_ndvi[::sample_interval, ::sample_interval]
        delta_ndvi_sampled = delta_ndvi[::sample_interval, ::sample_interval]
        qa_band_sampled = qa_band[::sample_interval, ::sample_interval]
    else:
        current_ndvi_sampled = current_ndvi
        baseline_ndvi_sampled = baseline_ndvi
        delta_ndvi_sampled = delta_ndvi
        qa_band_sampled = qa_band
        rows = rows
        cols = cols

    # Convert pixel coordinates to geographic coordinates
    # Using rasterio.transform * (col, row) -> (x, y) / (longitude, latitude)
    xs, ys = rasterio.transform.xy(transform, cols, rows)
    longitudes = np.array(xs)
    latitudes = np.array(ys)

    # Flatten arrays for DataFrame creation
    latitudes_flat = latitudes.flatten()
    longitudes_flat = longitudes.flatten()
    current_ndvi_flat = current_ndvi_sampled.flatten()
    baseline_ndvi_flat = baseline_ndvi_sampled.flatten()
    delta_ndvi_flat = delta_ndvi_sampled.flatten()
    qa_band_flat = qa_band_sampled.flatten()

    # Create validity mask
    valid_mask = (
        np.isfinite(current_ndvi_flat) & (current_ndvi_flat != nodata_value) &
        np.isfinite(baseline_ndvi_flat) & (baseline_ndvi_flat != nodata_value) &
        np.isfinite(delta_ndvi_flat) & (delta_ndvi_flat != nodata_value)
    )

    # Filter to valid pixels only
    latitudes_valid = latitudes_flat[valid_mask]
    longitudes_valid = longitudes_flat[valid_mask]
    current_ndvi_valid = current_ndvi_flat[valid_mask]
    baseline_ndvi_valid = baseline_ndvi_flat[valid_mask]
    delta_ndvi_valid = delta_ndvi_flat[valid_mask]
    qa_band_valid = qa_band_flat[valid_mask]

    logger.info(f"Total pixels: {len(latitudes_flat)}, Valid pixels: {len(latitudes_valid)}")

    # Create base DataFrame
    feature_data = {
        'latitude': latitudes_valid,
        'longitude': longitudes_valid,
        'current_ndvi': current_ndvi_valid,
        'baseline_ndvi': baseline_ndvi_valid,
        'delta_ndvi': delta_ndvi_valid,
    }

    # Add vegetation classifications
    feature_data['current_vegetation_class'] = [
        classify_ndvi_value(val) for val in current_ndvi_valid
    ]
    feature_data['baseline_vegetation_class'] = [
        classify_ndvi_value(val) for val in baseline_ndvi_valid
    ]

    # Add change detection categories
    feature_data['change_magnitude'] = np.abs(delta_ndvi_valid)
    feature_data['change_direction'] = np.where(
        delta_ndvi_valid > 0.01, 'increasing',
        np.where(delta_ndvi_valid < -0.01, 'decreasing', 'stable')
    )

    # Add QA information
    if include_qa_details:
        # Overall QA validity (bit 0)
        feature_data['qa_valid_pixel'] = ((qa_band_valid >> 0) & 1).astype(bool)

        # Individual QA bits
        feature_data['qa_cloud_detected'] = ((qa_band_valid >> 1) & 1).astype(bool)
        feature_data['qa_shadow_detected'] = ((qa_band_valid >> 2) & 1).astype(bool)
        feature_data['qa_water_detected'] = ((qa_band_valid >> 3) & 1).astype(bool)
        feature_data['qa_snow_ice_detected'] = ((qa_band_valid >> 4) & 1).astype(bool)
        feature_data['qa_sentinel_2a'] = ((qa_band_valid >> 5) & 1).astype(bool)
        feature_data['qa_sentinel_2b'] = ((qa_band_valid >> 6) & 1).astype(bool)
        feature_data['qa_multi_tile'] = ((qa_band_valid >> 7) & 1).astype(bool)

        # QA band raw value
        feature_data['qa_band_value'] = qa_band_valid

    # Add processing metadata
    feature_data['processing_timestamp'] = str(np.datetime64('now'))

    # Create DataFrame
    df = pd.DataFrame(feature_data)

    # Sort by latitude, longitude for consistent ordering
    df = df.sort_values(['latitude', 'longitude']).reset_index(drop=True)

    logger.info(f"Feature table created with {len(df)} rows and {len(df.columns)} columns")

    # Export to Parquet
    output_parquet_path = Path(output_parquet_path)
    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet_path, index=False)
    logger.info(f"Exported feature table to Parquet: {output_parquet_path}")

    # Export to CSV if requested
    csv_path_exported = None
    if output_csv_path is not None:
        output_csv_path = Path(output_csv_path)
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv_path, index=False)
        logger.info(f"Exported feature table to CSV: {output_csv_path}")
        csv_path_exported = output_csv_path

    return output_parquet_path, csv_path_exported