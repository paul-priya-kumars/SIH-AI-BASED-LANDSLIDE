"""
QA Generator — 8-bit Quality Assessment Band
============================================

Generates an 8-bit QA band with clearly documented bit meanings for
quality assessment of temporal NDVI composites and change detection products.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import logging

from phase3_temporal_mosaic.config import (
    QA_BIT_DEPTH,
    QA_VALID_PIXEL_BIT,
    QA_CLOUD_BIT,
    QA_SHADOW_BIT,
    QA_WATER_BIT,
    QA_SNOW_ICE_BIT,
    QA_SENTINEL_2A_BIT,
    QA_SENTINEL_2B_BIT,
    QA_MULTI_TILE_BIT,
    QA_BIT_MEANINGS,
    RASTER_NODATA_VALUE,
    logger,
)


def generate_qa_band(
    current_ndvi: np.ndarray,
    baseline_ndvi: np.ndarray,
    delta_ndvi: np.ndarray,
    current_scenes_info: Optional[Dict[str, Any]] = None,
    baseline_scenes_info: Optional[Dict[str, Any]] = None,
    multi_tile_processed: bool = False,
    nodata_value: float = RASTER_NODATA_VALUE,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate an 8-bit QA band with documented bit meanings.

    Args:
        current_ndvi: Current period NDVI composite array
        baseline_ndvi: Baseline period NDVI composite array
        delta_ndvi: ΔNDVI change detection array
        current_scenes_info: Metadata about current period scenes
        baseline_scenes_info: Metadata about baseline period scenes
        multi_tile_processed: True if multiple tiles were stitched together
        nodata_value: Value representing NoData in input arrays

    Returns:
        Tuple of (qa_band_array, qa_metadata_dict)

    Bit Meanings:
        Bit 0 (LSB): Valid pixel (0 = invalid/masked, 1 = valid)
        Bit 1: Cloud detected (0 = no cloud, 1 = cloud present in either period)
        Bit 2: Shadow detected (0 = no shadow, 1 = shadow present in either period)
        Bit 3: Water body (0 = not water, 1 = water detected)
        Bit 4: Snow/Ice (0 = no snow/ice, 1 = snow/ice present)
        Bit 5: Sentinel-2A platform (0 = Sentinel-2B or unknown, 1 = Sentinel-2A present)
        Bit 6: Sentinel-2B platform (0 = Sentinel-2A or unknown, 1 = Sentinel-2B present)
        Bit 7 (MSB): Multi-tile composite (0 = single tile, 1 = multi-tile stitched)
    """
    logger.info("Generating 8-bit QA band")

    # Validate input arrays have same shape
    if not (current_ndvi.shape == baseline_ndvi.shape == delta_ndvi.shape):
        raise ValueError("All input arrays must have the same shape")

    height, width = current_ndvi.shape
    qa_band = np.zeros((height, width), dtype=np.uint8)

    # Create validity masks for both periods
    current_valid = np.isfinite(current_ndvi) & (current_ndvi != nodata_value)
    baseline_valid = np.isfinite(baseline_ndvi) & (baseline_ndvi != nodata_value)
    delta_valid = np.isfinite(delta_ndvi) & (delta_ndvi != nodata_value)

    # Overall valid pixel: valid in all three bands (current, baseline, delta)
    valid_pixel = current_valid & baseline_valid & delta_valid

    # Set validity bit (Bit 0)
    qa_band[valid_pixel] = np.where(
        ((qa_band[valid_pixel] // (2 ** QA_VALID_PIXEL_BIT)) % 2) == 0,
        qa_band[valid_pixel] + (2 ** QA_VALID_PIXEL_BIT),
        qa_band[valid_pixel]
    )

    # TODO: In a full implementation, we would extract cloud/shadow/water/snow information
    # from the SCL bands of the input scenes. For now, we'll set these based on
    # NDVI value thresholds as proxies, noting this is a simplification.

    # Water detection (Bit 3): Very low NDVI values (< 0.1) often indicate water
    water_mask = (current_ndvi < 0.1) & (baseline_ndvi < 0.1) & valid_pixel
    qa_band[water_mask] = np.where(
        ((qa_band[water_mask] // (2 ** QA_WATER_BIT)) % 2) == 0,
        qa_band[water_mask] + (2 ** QA_WATER_BIT),
        qa_band[water_mask]
    )

    # Snow/Ice detection (Bit 4): Very high NDVI values (> 0.8) in cold regions might indicate snow/ice
    # This is a simplified proxy - real implementation would use SCL or thermal bands
    snow_ice_mask = (current_ndvi > 0.8) & (baseline_ndvi > 0.8) & valid_pixel
    qa_band[snow_ice_mask] = np.where(
        ((qa_band[snow_ice_mask] // (2 ** QA_SNOW_ICE_BIT)) % 2) == 0,
        qa_band[snow_ice_mask] + (2 ** QA_SNOW_ICE_BIT),
        qa_band[snow_ice_mask]
    )

    # Platform bits (Bits 5-6): Extract from scene metadata if available
    if current_scenes_info and 'platforms' in current_scenes_info:
        platforms_current = set(current_scenes_info['platforms'])
        if 'sentinel-2a' in [p.lower() for p in platforms_current]:
            qa_band[valid_pixel] = np.where(
                ((qa_band[valid_pixel] // (2 ** QA_SENTINEL_2A_BIT)) % 2) == 0,
                qa_band[valid_pixel] + (2 ** QA_SENTINEL_2A_BIT),
                qa_band[valid_pixel]
            )
        if 'sentinel-2b' in [p.lower() for p in platforms_current]:
            qa_band[valid_pixel] = np.where(
                ((qa_band[valid_pixel] // (2 ** QA_SENTINEL_2B_BIT)) % 2) == 0,
                qa_band[valid_pixel] + (2 ** QA_SENTINEL_2B_BIT),
                qa_band[valid_pixel]
            )

    if baseline_scenes_info and 'platforms' in baseline_scenes_info:
        platforms_baseline = set(baseline_scenes_info['platforms'])
        if 'sentinel-2a' in [p.lower() for p in platforms_baseline]:
            qa_band[valid_pixel] = np.where(
                ((qa_band[valid_pixel] // (2 ** QA_SENTINEL_2A_BIT)) % 2) == 0,
                qa_band[valid_pixel] + (2 ** QA_SENTINEL_2A_BIT),
                qa_band[valid_pixel]
            )
        if 'sentinel-2b' in [p.lower() for p in platforms_baseline]:
            qa_band[valid_pixel] = np.where(
                ((qa_band[valid_pixel] // (2 ** QA_SENTINEL_2B_BIT)) % 2) == 0,
                qa_band[valid_pixel] + (2 ** QA_SENTINEL_2B_BIT),
                qa_band[valid_pixel]
            )

    # Multi-tile bit (Bit 7)
    if multi_tile_processed:
        qa_band[valid_pixel] = np.where(
            ((qa_band[valid_pixel] // (2 ** QA_MULTI_TILE_BIT)) % 2) == 0,
            qa_band[valid_pixel] + (2 ** QA_MULTI_TILE_BIT),
            qa_band[valid_pixel]
        )

    # Calculate QA statistics
    qa_stats = _calculate_qa_statistics(qa_band, valid_pixel)

    # Prepare metadata
    qa_metadata = {
        'bit_depth': QA_BIT_DEPTH,
        'bit_meanings': QA_BIT_MEANINGS,
        'statistics': qa_stats,
        'valid_pixel_count': int(np.sum(valid_pixel)),
        'total_pixel_count': int(current_ndvi.size),
        'generation_timestamp': str(np.datetime64('now')),
        'multi_tile_processed': multi_tile_processed,
    }

    logger.info(f"QA band generated: {qa_stats}")

    return qa_band, qa_metadata


def _calculate_qa_statistics(qa_band: np.ndarray, valid_pixel_mask: np.ndarray) -> Dict[str, Any]:
    """
    Calculate statistics for each QA bit.

    Args:
        qa_band: 8-bit QA band array
        valid_pixel_mask: Mask indicating valid pixels

    Returns:
        Dictionary with statistics for each QA bit
    """
    stats = {}
    total_pixels = qa_band.size
    valid_pixels = np.sum(valid_pixel_mask)

    for bit_num, bit_name in QA_BIT_MEANINGS.items():
        # Extract bit values using integer division to avoid bitwise operation issues
        bit_values = (qa_band // (2 ** bit_num)) % 2
        bit_set_count = np.sum(bit_values)

        stats[f'{bit_name}_set_count'] = int(bit_set_count)
        stats[f'{bit_name}_set_percentage'] = round(
            (bit_set_count / max(total_pixels, 1)) * 100.0, 2
        )
        stats[f'{bit_name}_valid_set_count'] = int(np.sum(bit_values[valid_pixel_mask]))
        stats[f'{bit_name}_valid_set_percentage'] = round(
            (np.sum(bit_values[valid_pixel_mask]) / max(valid_pixels, 1)) * 100.0, 2
        )

    return stats