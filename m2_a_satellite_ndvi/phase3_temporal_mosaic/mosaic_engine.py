"""
Temporal Mosaic Engine — Multi-Temporal Sentinel-2 Discovery
============================================================

Handles dynamic discovery of Sentinel-2 L2A scenes for temporal compositing,
including baseline and current period queries with cloud filtering.
Reuses Phase 2 STAC client infrastructure where possible.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import logging

from phase2_sentinel_ndvi.stac_client import (
    build_stac_query_payload,
    query_sentinel2_scenes,
    SentinelSceneMetadata,
)
from phase1_aoi import load_aoi_geometry
from phase3_temporal_mosaic.config import (
    STAC_SEARCH_URL,
    DEFAULT_MAX_CLOUD_COVER,
    logger,
)

logger = logging.getLogger(__name__)


def discover_sentinel2_scenes_temporal(
    start_date: str,
    end_date: str,
    max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER,
    limit: int = 50,
) -> List[SentinelSceneMetadata]:
    """
    Discover Sentinel-2 L2A scenes for a temporal window using dynamic STAC queries.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_cloud_cover: Maximum cloud cover percentage (0-100)
        limit: Maximum number of scenes to return

    Returns:
        List of SentinelSceneMetadata objects sorted by cloud cover (ascending) and date (descending)
    """
    logger.info(f"Discovering Sentinel-2 scenes for {start_date} to {end_date} "
                f"with max cloud cover {max_cloud_cover}%")

    # Use Phase 1 AOI geometry for spatial filtering
    aoi_geometry = load_aoi_geometry()

    # Build STAC query payload using reused Phase 2 function
    payload = build_stac_query_payload(
        geometry_dict=aoi_geometry.__geo_interface__,  # Convert Shapely to GeoJSON dict
        max_cloud_cover=max_cloud_cover,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    # Execute query using reused Phase 2 function
    scenes = query_sentinel2_scenes(
        max_cloud_cover=max_cloud_cover,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        search_url=STAC_SEARCH_URL,
    )

    logger.info(f"Discovered {len(scenes)} Sentinel-2 scenes for temporal window")
    return scenes


def discover_baseline_and_current_scenes(
    baseline_start: str,
    baseline_end: str,
    current_start: str,
    current_end: str,
    max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER,
) -> Tuple[List[SentinelSceneMetadata], List[SentinelSceneMetadata]]:
    """
    Discover Sentinel-2 scenes for both baseline and current periods.

    Args:
        baseline_start: Baseline period start date (YYYY-MM-DD)
        baseline_end: Baseline period end date (YYYY-MM-DD)
        current_start: Current period start date (YYYY-MM-DD)
        current_end: Current period end date (YYYY-MM-DD)
        max_cloud_cover: Maximum cloud cover percentage

    Returns:
        Tuple of (baseline_scenes, current_scenes) lists
    """
    logger.info("Discovering baseline and current Sentinel-2 scenes")

    baseline_scenes = discover_sentinel2_scenes_temporal(
        start_date=baseline_start,
        end_date=baseline_end,
        max_cloud_cover=max_cloud_cover,
    )

    current_scenes = discover_sentinel2_scenes_temporal(
        start_date=current_start,
        end_date=current_end,
        max_cloud_cover=max_cloud_cover,
    )

    logger.info(f"Baseline: {len(baseline_scenes)} scenes, Current: {len(current_scenes)} scenes")
    return baseline_scenes, current_scenes


def group_scenes_by_mgrs_tile(
    scenes: List[SentinelSceneMetadata]
) -> Dict[str, List[SentinelSceneMetadata]]:
    """
    Group Sentinel-2 scenes by MGRS tile for multi-tile processing.

    Args:
        scenes: List of SentinelSceneMetadata objects

    Returns:
        Dictionary mapping MGRS tile IDs to lists of scenes
    """
    tile_groups: Dict[str, List[SentinelSceneMetadata]] = {}

    for scene in scenes:
        tile_id = scene.mgrs_tile
        if tile_id not in tile_groups:
            tile_groups[tile_id] = []
        tile_groups[tile_id].append(scene)

    # Sort scenes within each tile by date (most recent first)
    for tile_id in tile_groups:
        tile_groups[tile_id].sort(key=lambda s: s.datetime, reverse=True)

    return tile_groups