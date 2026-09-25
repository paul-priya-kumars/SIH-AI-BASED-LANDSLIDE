"""
Temporal Composite Engine — MVC and Median Compositing
=====================================================

Implements Maximum Value Composite (MVC) and Median composite algorithms
for creating temporal NDVI composites from multi-temporal Sentinel-2 scenes.
"""

from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.mask import mask
from shapely.geometry import mapping
import logging

from phase2_sentinel_ndvi.stac_client import SentinelSceneMetadata
from phase2_sentinel_ndvi.ndvi_processor import compute_ndvi_array
from phase2_sentinel_ndvi.reprojection import reproject_raster_array, clip_raster_to_aoi_polygon
from phase2_sentinel_ndvi.export_geotiff import export_ndvi_geotiff
from phase2_sentinel_ndvi.config import (
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    MASKED_SCL_CLASSES,
)
from phase1_aoi import load_aoi_geometry
from phase3_temporal_mosaic.config import (
    MIN_VALID_SCENES_MVC,
    MIN_VALID_SCENES_MEDIAN,
    RETURN_PARTIAL_RESULTS,
    INSUFFICIENT_DATA_NODATA_VALUE,
    logger,
)


def create_temporal_composite(
    scenes: List[SentinelSceneMetadata],
    method: str = "MVC",
    min_valid_scenes: Optional[int] = None,
) -> Tuple[np.ndarray, rasterio.Affine, Dict[str, Any]]:
    """
    Create a temporal NDVI composite from a list of Sentinel-2 scenes.

    Args:
        scenes: List of SentinelSceneMetadata objects (must have red/nir/scl URLs)
        method: Compositing method - "MVC" (Maximum Value Composite) or "MEDIAN"
        min_valid_scenes: Minimum valid scenes required (overrides method-specific defaults)

    Returns:
        Tuple of (composite_array, transform, metadata_dict)

    Raises:
        ValueError: If method is not supported or insufficient valid scenes
    """
    if method not in ["MVC", "MEDIAN"]:
        raise ValueError(f"Unsupported compositing method: {method}. Use 'MVC' or 'MEDIAN'")

    # Determine minimum valid scenes required
    if min_valid_scenes is None:
        min_valid_scenes = MIN_VALID_SCENES_MVC if method == "MVC" else MIN_VALID_SCENES_MEDIAN

    logger.info(f"Creating {method} composite from {len(scenes)} scenes "
                f"(minimum required: {min_valid_scenes})")

    if len(scenes) < min_valid_scenes:
        if RETURN_PARTIAL_RESULTS:
            logger.warning(f"Insufficient scenes ({len(scenes)} < {min_valid_scenes}), "
                          f"proceeding with partial results")
        else:
            raise ValueError(f"Insufficient scenes for {method} composite: "
                           f"{len(scenes)} < {min_valid_scenes}")

    # Process each scene to extract NDVI, red, nir, and scl arrays
    processed_scenes = []
    reference_transform = None
    reference_crs = None
    reference_shape = None

    for i, scene in enumerate(scenes):
        logger.debug(f"Processing scene {i+1}/{len(scenes)}: {scene.scene_id}")

        try:
            # Download and process red band (B04)
            red_data, red_transform, red_crs = _download_and_process_band(
                scene.red_asset_url, "RED"
            )

            # Download and process nir band (B08)
            nir_data, nir_transform, nir_crs = _download_and_process_band(
                scene.nir_asset_url, "NIR"
            )

            # Download and process scl band
            scl_data, scl_transform, scl_crs = _download_and_process_band(
                scene.scl_asset_url, "SCL"
            )

            # Validate that all bands have consistent geometry
            if reference_transform is None:
                reference_transform = red_transform
                reference_crs = red_crs
                reference_shape = red_data.shape
            else:
                if not (_transforms_equal(reference_transform, red_transform) and
                        reference_crs == red_crs and
                        reference_shape == red_data.shape):
                    logger.warning(f"Scene {scene.scene_id} has different geometry, "
                                 f"reprojecting to reference")
                    # Reproject to reference geometry
                    red_data, _ = _reproject_to_reference(
                        red_data, red_transform, red_crs,
                        reference_transform, reference_crs, reference_shape
                    )
                    nir_data, _ = _reproject_to_reference(
                        nir_data, nir_transform, nir_crs,
                        reference_transform, reference_crs, reference_shape
                    )
                    scl_data, _ = _reproject_to_reference(
                        scl_data, scl_transform, scl_crs,
                        reference_transform, reference_crs, reference_shape
                    )

            # Compute NDVI with SCL masking
            ndvi_data = compute_ndvi_array(red_data, nir_data, scl=scl_data)

            # Clip to AOI polygon
            ndvi_clipped = clip_raster_to_aoi_polygon(
                ndvi_data, reference_transform, nodata_value=RASTER_NODATA_VALUE
            )

            processed_scenes.append({
                'scene_id': scene.scene_id,
                'datetime': scene.datetime,
                'platform': scene.platform,
                'ndvi': ndvi_clipped,
                'red': red_data,
                'nir': nir_data,
                'scl': scl_data,
                'cloud_cover': scene.cloud_cover_pct,
            })

        except Exception as e:
            logger.error(f"Failed to process scene {scene.scene_id}: {e}")
            continue

    if len(processed_scenes) == 0:
        raise RuntimeError("No scenes could be processed successfully")

    logger.info(f"Successfully processed {len(processed_scenes)} scenes for compositing")

    # Create the composite based on method
    if method == "MVC":
        composite_array = _create_mvc_composite(processed_scenes)
    else:  # MEDIAN
        composite_array = _create_median_composite(processed_scenes)

    # Create metadata
    metadata = {
        'method': method,
        'input_scenes_count': len(scenes),
        'processed_scenes_count': len(processed_scenes),
        'scene_ids': [s['scene_id'] for s in processed_scenes],
        'datetimes': [s['datetime'] for s in processed_scenes],
        'platforms': list(set(s['platform'] for s in processed_scenes)),
        'cloud_cover_stats': {
            'mean': np.mean([s['cloud_cover'] for s in processed_scenes]),
            'min': np.min([s['cloud_cover'] for s in processed_scenes]),
            'max': np.max([s['cloud_cover'] for s in processed_scenes]),
        },
        'creation_timestamp': datetime.now().isoformat(),
    }

    return composite_array, reference_transform, metadata


def _download_and_process_band(asset_url: Optional[str], band_name: str) -> Tuple[np.ndarray, rasterio.Affine, str]:
    """
    Download and process a single band asset URL.

    Args:
        asset_url: URL to the band asset (can be None for missing bands)
        band_name: Name of the band for logging ("RED", "NIR", "SCL")

    Returns:
        Tuple of (data_array, transform, crs_string)

    Raises:
        ValueError: If asset_url is None or download fails
    """
    if asset_url is None:
        raise ValueError(f"{band_name} band asset URL is None")

    logger.debug(f"Downloading {band_name} band from {asset_url}")

    # In a real implementation, we would download the asset here
    # For now, we'll simulate by checking if we have local copies or using synthetic data
    # This is a placeholder - in production this would use requests or similar to download

    # For the purposes of this implementation, we'll assume the asset_url points to
    # a local file or we have a mechanism to access the data
    # Since we're building on Phase 2 which already processes real scenes,
    # we'll adapt the approach to work with locally available data

    try:
        with rasterio.open(asset_url) as src:
            data = src.read(1)  # Read first band
            transform = src.transform
            crs = str(src.crs)
            logger.debug(f"Successfully downloaded {band_name} band: {data.shape}")
            return data, transform, crs
    except Exception as e:
        logger.error(f"Failed to download {band_name} band from {asset_url}: {e}")
        raise


def _transforms_equal(t1: rasterio.Affine, t2: rasterio.Affine, tolerance: float = 1e-10) -> bool:
    """Check if two affine transforms are equal within tolerance."""
    return all(abs(a - b) < tolerance for a, b in zip(t1, t2))


def _reproject_to_reference(
    data: np.ndarray,
    src_transform: rasterio.Affine,
    src_crs: str,
    dst_transform: rasterio.Affine,
    dst_crs: str,
    dst_shape: Tuple[int, int]
) -> Tuple[np.ndarray, rasterio.Affine]:
    """
    Reproject data to match reference geometry.

    Args:
        data: Source data array
        src_transform: Source affine transform
        src_crs: Source CRS string
        dst_transform: Destination affine transform
        dst_crs: Destination CRS string
        dst_shape: Destination shape (height, width)

    Returns:
        Tuple of (reprojected_data, dst_transform)
    """
    src_crs_obj = rasterio.CRS.from_string(src_crs)
    dst_crs_obj = rasterio.CRS.from_string(dst_crs)

    # Reproject array
    dst_data = np.full(dst_shape, RASTER_NODATA_VALUE, dtype=rasterio.float32)

    reproject(
        source=data,
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs_obj,
        dst_transform=dst_transform,
        dst_crs=dst_crs_obj,
        resampling=Resampling.bilinear,
        src_nodata=RASTER_NODATA_VALUE,
        dst_nodata=RASTER_NODATA_VALUE,
    )

    return dst_data, dst_transform


def _create_mvc_composite(processed_scenes: List[Dict[str, Any]]) -> np.ndarray:
    """
    Create Maximum Value Composite (MVC) from processed scenes.

    Args:
        processed_scenes: List of processed scene dictionaries

    Returns:
        MVC composite NDVI array
    """
    logger.debug("Creating MVC composite")

    # Stack all NDVI arrays
    ndvi_stack = np.dstack([scene['ndvi'] for scene in processed_scenes])

    # For MVC, we take the maximum value along the time axis
    # But we need to handle NoData values properly
    mvc_composite = np.full_like(ndvi_stack[:, :, 0], RASTER_NODATA_VALUE, dtype=np.float32)

    # Find valid pixels (not NoData) in each time step
    valid_mask = np.isfinite(ndvi_stack) & (ndvi_stack != RASTER_NODATA_VALUE)

    # For each pixel, if there's at least one valid observation, take the max
    any_valid = np.any(valid_mask, axis=2)
    mvc_composite[any_valid] = np.nanmax(ndvi_stack[any_valid, :], axis=1)

    # Set pixels with no valid observations to NoData
    mvc_composite[~any_valid] = RASTER_NODATA_VALUE

    return mvc_composite


def _create_median_composite(processed_scenes: List[Dict[str, Any]]) -> np.ndarray:
    """
    Create Median composite from processed scenes.

    Args:
        processed_scenes: List of processed scene dictionaries

    Returns:
        Median composite NDVI array
    """
    logger.debug("Creating Median composite")

    # Stack all NDVI arrays
    ndvi_stack = np.dstack([scene['ndvi'] for scene in processed_scenes])

    # For median composite, we take the median value along the time axis
    median_composite = np.full_like(ndvi_stack[:, :, 0], RASTER_NODATA_VALUE, dtype=np.float32)

    # Find valid pixels (not NoData) in each time step
    valid_mask = np.isfinite(ndvi_stack) & (ndvi_stack != RASTER_NODATA_VALUE)

    # Count valid observations per pixel
    valid_count = np.sum(valid_mask, axis=2)

    # For pixels with sufficient valid observations, take the median
    sufficient_valid = valid_count >= 2  # Need at least 2 observations for meaningful median
    median_composite[sufficient_valid] = np.nanmedian(ndvi_stack[sufficient_valid, :], axis=1)

    # Set pixels with insufficient valid observations to NoData
    median_composite[~sufficient_valid] = RASTER_NODATA_VALUE

    return median_composite