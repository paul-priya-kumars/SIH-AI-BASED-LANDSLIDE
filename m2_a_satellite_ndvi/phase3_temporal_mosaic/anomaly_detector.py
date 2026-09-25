"""
Anomaly Detector — ΔNDVI Change Detection
=========================================

Computes change detection by calculating ΔNDVI = Current NDVI - Baseline NDVI.
Handles edge cases like missing data, NoData values, and uncertainty quantification.
"""

from typing import Tuple, Optional, Dict, Any
import numpy as np
import logging

from phase3_temporal_mosaic.config import (
    RASTER_NODATA_VALUE,
    logger,
)


def calculate_delta_ndvi(
    current_ndvi: np.ndarray,
    baseline_ndvi: np.ndarray,
    nodata_value: float = RASTER_NODATA_VALUE,
    uncertainty_threshold: float = 0.3,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Calculate ΔNDVI = Current NDVI - Baseline NDVI for change detection.

    Args:
        current_ndji: Current period NDVI composite array
        baseline_ndvi: Baseline period NDVI composite array
        nodata_value: Value representing NoData pixels
        uncertainty_threshold: Threshold for high uncertainty flagging

    Returns:
        Tuple of (delta_ndvi_array, metadata_dict)
    """
    logger.info("Calculating ΔNDVI change detection")

    # Validate input arrays have same shape
    if current_ndvi.shape != baseline_ndvi.shape:
        raise ValueError(f"Array shape mismatch: current {current_ndvi.shape} != baseline {baseline_ndvi.shape}")

    # Initialize output array with NoData
    delta_ndvi = np.full_like(current_ndvi, nodata_value, dtype=np.float32)

    # Create validity masks
    current_valid = np.isfinite(current_ndvi) & (current_ndvi != nodata_value)
    baseline_valid = np.isfinite(baseline_ndvi) & (baseline_ndvi != nodata_value)

    # Pixels valid in both periods
    both_valid = current_valid & baseline_valid

    # Pixels valid in only one period (indicates potential data issues)
    current_only = current_valid & ~baseline_valid
    baseline_only = ~current_valid & baseline_valid

    # Calculate ΔNDVI where both periods have valid data
    delta_ndvi[both_valid] = current_ndvi[both_valid] - baseline_ndvi[both_valid]

    # Clip to realistic bounds for ΔNDVI (-2.0 to 2.0 covers extreme vegetation changes)
    # Theoretical NDVI bounds are [-1, 1], so ΔNDVI bounds are [-2, 2]
    # Only clip the valid delta values, preserve NoData values
    valid_delta_mask = both_valid
    delta_ndvi[valid_delta_mask] = np.clip(delta_ndvi[valid_delta_mask], -2.0, 2.0)

    # Calculate statistics
    valid_delta_pixels = delta_ndvi[both_valid]
    stats = {}

    if valid_delta_pixels.size > 0:
        stats = {
            'valid_pixel_count': int(np.sum(both_valid)),
            'current_only_count': int(np.sum(current_only)),
            'baseline_only_count': int(np.sum(baseline_only)),
            'mean_delta_ndvi': float(np.mean(valid_delta_pixels)),
            'median_delta_ndvi': float(np.median(valid_delta_pixels)),
            'std_delta_ndvi': float(np.std(valid_delta_pixels)),
            'min_delta_ndvi': float(np.min(valid_delta_pixels)),
            'max_delta_ndvi': float(np.max(valid_delta_pixels)),
            'positive_change_pixels': int(np.sum(valid_delta_pixels > 0)),
            'negative_change_pixels': int(np.sum(valid_delta_pixels < 0)),
            'no_change_pixels': int(np.sum(np.abs(valid_delta_pixels) < 0.01)),  # Essentially no change
        }

        # Calculate change magnitude categories
        stats['large_positive_change'] = int(np.sum(valid_delta_pixels > 0.3))   # Significant greening
        stats['moderate_positive_change'] = int(np.sum((valid_delta_pixels > 0.1) & (valid_delta_pixels <= 0.3)))
        stats['small_positive_change'] = int(np.sum((valid_delta_pixels > 0.01) & (valid_delta_pixels <= 0.1)))
        stats['large_negative_change'] = int(np.sum(valid_delta_pixels < -0.3))  # Significant browning
        stats['moderate_negative_change'] = int(np.sum((valid_delta_pixels < -0.1) & (valid_delta_pixels >= -0.3)))
        stats['small_negative_change'] = int(np.sum((valid_delta_pixels < -0.01) & (valid_delta_pixels >= -0.3)))
    else:
        stats = {
            'valid_pixel_count': 0,
            'current_only_count': int(np.sum(current_only)),
            'baseline_only_count': int(np.sum(baseline_only)),
            'mean_delta_ndvi': None,
            'median_delta_ndvi': None,
            'std_delta_ndvi': None,
            'min_delta_ndvi': None,
            'max_delta_ndvi': None,
        }

    # Prepare metadata
    metadata = {
        'calculation_method': 'direct_subtraction',
        'nodata_value': nodata_value,
        'input_shapes': {
            'current_ndvi': current_ndvi.shape,
            'baseline_ndvi': baseline_ndvi.shape,
            'delta_ndvi': delta_ndvi.shape,
        },
        'validity_stats': stats,
        'uncertainty_threshold': uncertainty_threshold,
        'high_uncertainty_pixels': int(np.sum(~(both_valid))),  # Pixels missing data in one or both periods
        'calculation_timestamp': str(np.datetime64('now')),
    }

    logger.info(f"ΔNDVI calculation complete: {stats.get('valid_pixel_count', 0)} valid pixels")

    return delta_ndvi, metadata