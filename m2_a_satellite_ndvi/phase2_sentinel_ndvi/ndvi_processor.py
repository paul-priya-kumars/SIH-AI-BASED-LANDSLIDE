"""
NDVI Processor & SCL Masking Engine
====================================
Vectorized float32 calculation of Normalized Difference Vegetation Index (NDVI)
with safe zero-denominator protection and explicit Scene Classification Layer (SCL)
cloud/shadow masking.
"""

from typing import Dict, Any, Optional, Set, Tuple
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

from phase2_sentinel_ndvi.config import (
    MASKED_SCL_CLASSES,
    SCL_CLASS_NAMES,
    RASTER_NODATA_VALUE,
    NDVI_CLASSIFICATIONS,
    classify_ndvi_value,
)


def compute_ndvi_array(
    red: np.ndarray,
    nir: np.ndarray,
    scl: Optional[np.ndarray] = None,
    masked_scl_classes: Optional[Set[int]] = None,
) -> np.ndarray:
    """
    Computes NDVI from Red (B04) and NIR (B08) 2D arrays with safe zero-denominator
    handling and SCL cloud/shadow masking.

    Formula:
        NDVI = (NIR - Red) / (NIR + Red)

    Returns:
        2D float32 numpy array with valid values in [-1.0, 1.0] and np.nan for masked/nodata pixels.
    """
    if red.shape != nir.shape:
        raise ValueError(f"Shape mismatch: Red {red.shape} vs NIR {nir.shape}")

    # Ensure float32 representation
    red_f = red.astype(np.float32)
    nir_f = nir.astype(np.float32)

    # Calculate denominator
    denom = nir_f + red_f

    # Create safe valid mask: denominator must be positive and non-zero
    # (Prevents DivisionByZero and invalid reflectance math)
    valid_mask = (denom > 1e-6) & np.isfinite(red_f) & np.isfinite(nir_f)

    # Initialize output array filled with NaN
    ndvi = np.full(red_f.shape, np.nan, dtype=np.float32)

    # Calculate NDVI only where denominator is safely positive
    numer = nir_f - red_f
    ndvi[valid_mask] = numer[valid_mask] / denom[valid_mask]

    # Clip mathematically valid values to theoretical bounds [-1.0, 1.0]
    np.clip(ndvi, -1.0, 1.0, out=ndvi)

    # Apply SCL Cloud / Shadow Masking if SCL layer is provided
    if scl is not None:
        if scl.shape != ndvi.shape:
            # Resample SCL to match RED/NIR resolution using nearest-neighbor resampling
            # to preserve discrete classification values
            scl = _resample_scl_to_match(scl, ndvi.shape)

        mask_classes = masked_scl_classes if masked_scl_classes is not None else MASKED_SCL_CLASSES
        scl_int = scl.astype(np.int32)
        scl_mask = np.isin(scl_int, list(mask_classes))

        # Explicitly set cloud/shadow/nodata pixels to NaN (NEVER 0.0)
        ndvi[scl_mask] = np.nan

    return ndvi


def _resample_scl_to_match(scl_array: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
    """
    Resample SCL array to match target shape using nearest-neighbor resampling.
    Preserves discrete classification values by avoiding interpolation.

    Args:
        scl_array: Input SCL array with shape (H, W)
        target_shape: Target shape (height, width) to resample to

    Returns:
        Resampled SCL array with target_shape
    """
    if scl_array.shape == target_shape:
        return scl_array

    # Calculate zoom factors
    zoom_y = target_shape[0] / scl_array.shape[0]
    zoom_x = target_shape[1] / scl_array.shape[1]

    # For nearest-neighbor resampling, we repeat elements
    # First repeat along rows (axis 0)
    if zoom_y >= 1:
        # Upsampling: repeat rows
        repeat_y = int(np.ceil(zoom_y))
        repeated = np.repeat(scl_array, repeat_y, axis=0)
        # Trim to exact size if we overshot
        if repeated.shape[0] > target_shape[0]:
            repeated = repeated[:target_shape[0], :]
    else:
        # Downsampling: take every nth row
        step_y = max(1, int(np.ceil(1 / zoom_y)))
        repeated = scl_array[::step_y, :]
        # Ensure we don't undershoot
        if repeated.shape[0] < target_shape[0]:
            # Pad with edge values if needed
            padding = target_shape[0] - repeated.shape[0]
            if padding > 0:
                repeated = np.pad(repeated, ((0, padding), (0, 0)), mode='edge')

    # Then repeat along columns (axis 1)
    if zoom_x >= 1:
        # Upsampling: repeat columns
        repeat_x = int(np.ceil(zoom_x))
        resampled = np.repeat(repeated, repeat_x, axis=1)
        # Trim to exact size if we overshot
        if resampled.shape[1] > target_shape[1]:
            resampled = resampled[:, :target_shape[1]]
    else:
        # Downsampling: take every nth column
        step_x = max(1, int(np.ceil(1 / zoom_x)))
        resampled = repeated[:, ::step_x]
        # Ensure we don't undershoot
        if resampled.shape[1] < target_shape[1]:
            # Pad with edge values if needed
            padding = target_shape[1] - resampled.shape[1]
            if padding > 0:
                resampled = np.pad(resampled, ((0, 0), (0, padding)), mode='edge')

    # Final check - ensure exact shape match
    if resampled.shape != target_shape:
        # If still not exact (due to rounding), use slicing/padding
        y_diff = target_shape[0] - resampled.shape[0]
        x_diff = target_shape[1] - resampled.shape[1]

        # Handle height dimension
        if y_diff > 0:
            resampled = np.pad(resampled, ((0, y_diff), (0, 0)), mode='edge')
        elif y_diff < 0:
            resampled = resampled[:target_shape[0], :]

        # Handle width dimension
        if x_diff > 0:
            resampled = np.pad(resampled, ((0, 0), (0, x_diff)), mode='edge')
        elif x_diff < 0:
            resampled = resampled[:, :target_shape[1]]

    return resampled.astype(scl_array.dtype)


def compute_ndvi_statistics(
    ndvi: np.ndarray,
    nodata_value: float = RASTER_NODATA_VALUE,
) -> Dict[str, Any]:
    """
    Calculates detailed summary statistics and vegetation classification distribution
    from an NDVI array.
    """
    # Identify valid non-nan pixels that are not equal to nodata_value
    valid_mask = np.isfinite(ndvi) & (ndvi != nodata_value) & (ndvi >= -1.0) & (ndvi <= 1.0)
    valid_pixels = ndvi[valid_mask]

    total_pixel_count = ndvi.size
    valid_pixel_count = int(valid_pixels.size)
    masked_pixel_count = int(total_pixel_count - valid_pixel_count)

    if valid_pixel_count == 0:
        return {
            "valid_pixels": 0,
            "masked_pixels": total_pixel_count,
            "valid_pct": 0.0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "class_distribution": {},
        }

    # Statistical metrics
    mean_val = float(np.mean(valid_pixels))
    median_val = float(np.median(valid_pixels))
    min_val = float(np.min(valid_pixels))
    max_val = float(np.max(valid_pixels))
    std_val = float(np.std(valid_pixels))

    # Vegetation classification breakdown
    class_counts: Dict[str, Dict[str, Any]] = {}
    for cat in NDVI_CLASSIFICATIONS:
        cat_mask = (valid_pixels >= cat["min_ndvi"]) & (valid_pixels < cat["max_ndvi"])
        count = int(np.sum(cat_mask))
        pct = round((count / valid_pixel_count) * 100.0, 2)
        class_counts[cat["class"]] = {
            "count": count,
            "percentage": pct,
            "description": cat["description"],
            "slope_stability_factor": cat["slope_stability_factor"],
        }

    return {
        "total_pixels": total_pixel_count,
        "valid_pixels": valid_pixel_count,
        "masked_pixels": masked_pixel_count,
        "valid_pct": round((valid_pixel_count / total_pixel_count) * 100.0, 2),
        "mean": round(mean_val, 4),
        "median": round(median_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "std": round(std_val, 4),
        "class_distribution": class_counts,
    }
