"""
Dynamic STAC Client — Sentinel-2 L2A Ingestion
===============================================
Queries STAC catalogs (Element84 Earth Search / AWS Open Data) dynamically
using the Phase 1 Nilgiris study area geometry and cloud-cover filters.

Does NOT hardcode tiles: spatial intersections dynamically determine matching scenes.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

import requests
from shapely.geometry import mapping, shape

from phase1_aoi import load_aoi_geometry, get_aoi_bounds
from phase2_sentinel_ndvi.config import (
    STAC_SEARCH_URL,
    STAC_COLLECTION,
    DEFAULT_MAX_CLOUD_COVER,
    DEFAULT_DATE_RANGE_DAYS,
)


@dataclass
class SentinelSceneMetadata:
    """Standardized metadata for a discovered Sentinel-2 L2A scene."""
    scene_id: str
    datetime: str
    cloud_cover_pct: float
    platform: str
    mgrs_tile: str
    red_asset_url: Optional[str]
    nir_asset_url: Optional[str]
    scl_asset_url: Optional[str]
    bbox: List[float]
    stac_properties: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_stac_query_payload(
    geometry_dict: Optional[Dict[str, Any]] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Constructs an RFC-compliant STAC search POST payload using the study area geometry.
    """
    if geometry_dict is None and bbox is None:
        geom = load_aoi_geometry()
        geometry_dict = mapping(geom)

    # Format datetime interval (start/end)
    def _to_iso_datetime(date_str: Optional[str], is_start: bool = True) -> str:
        """Convert date string to ISO datetime string."""
        if not date_str:
            # Return appropriate default
            now = datetime.now(timezone.utc)
            if is_start:
                # Default start: N days ago
                default_dt = now - timedelta(days=DEFAULT_DATE_RANGE_DAYS)
                return default_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # Default end: now
                return now.strftime("%Y-%m-%dT%H:%M:%SZ")
        # If already in ISO format with time, use as-is
        if "T" in date_str and ("Z" in date_str or "+" in date_str):
            return date_str
        # Assume YYYY-MM-DD format, convert to ISO datetime
        try:
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate format
            if is_start:
                return f"{date_str}T00:00:00Z"  # Start of day
            else:
                return f"{date_str}T23:59:59Z"  # End of day
        except ValueError:
            # If parsing fails, fall back to appropriate default
            now = datetime.now(timezone.utc)
            if is_start:
                default_dt = now - timedelta(days=DEFAULT_DATE_RANGE_DAYS)
                return default_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                return now.strftime("%Y-%m-%dT%H:%M:%SZ")

    formatted_start_date = _to_iso_datetime(start_date, is_start=True)
    formatted_end_date = _to_iso_datetime(end_date, is_start=False)

    datetime_param = f"{formatted_start_date}/{formatted_end_date}"

    payload: Dict[str, Any] = {
        "collections": [STAC_COLLECTION],
        "limit": limit,
        "datetime": datetime_param,
        "query": {
            "eo:cloud_cover": {"lt": max_cloud_cover}
        },
    }

    if geometry_dict:
        payload["intersects"] = geometry_dict
    elif bbox:
        payload["bbox"] = list(bbox)

    return payload


def query_sentinel2_scenes(
    max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    search_url: str = STAC_SEARCH_URL,
    timeout: int = 15,
) -> List[SentinelSceneMetadata]:
    """
    Queries STAC API dynamically using the Phase 1 Nilgiris AOI geometry.

    Returns:
        List of SentinelSceneMetadata sorted by lowest cloud cover and recency.
    """
    geom = load_aoi_geometry()
    payload = build_stac_query_payload(
        geometry_dict=mapping(geom),
        max_cloud_cover=max_cloud_cover,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    try:
        response = requests.post(
            search_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"STAC API query failed at {search_url}: {e}")

    features = data.get("features", [])
    scenes: List[SentinelSceneMetadata] = []

    for item in features:
        props = item.get("properties", {})
        assets = item.get("assets", {})

        # Extract band asset URLs (Earth Search uses 'red', 'nir', 'scl' or 'red-jp2')
        red_url = None
        nir_url = None
        scl_url = None

        for k in ["red", "B04", "red-jp2"]:
            if k in assets and "href" in assets[k]:
                red_url = assets[k]["href"]
                break

        for k in ["nir", "B08", "nir-jp2", "nir08"]:
            if k in assets and "href" in assets[k]:
                nir_url = assets[k]["href"]
                break

        for k in ["scl", "SCL", "scl-jp2"]:
            if k in assets and "href" in assets[k]:
                scl_url = assets[k]["href"]
                break

        # Discover MGRS tile information dynamically
        mgrs = props.get("mgrs:utm_zone", "")
        tile_str = props.get("s2:mgrs_tile", "")
        if not tile_str and "id" in item:
            parts = item["id"].split("_")
            if len(parts) >= 2:
                tile_str = parts[1]

        cloud_val = float(props.get("eo:cloud_cover", 0.0))

        scene = SentinelSceneMetadata(
            scene_id=item.get("id", "UNKNOWN"),
            datetime=props.get("datetime", ""),
            cloud_cover_pct=round(cloud_val, 2),
            platform=props.get("platform", "sentinel-2"),
            mgrs_tile=tile_str or str(mgrs),
            red_asset_url=red_url,
            nir_asset_url=nir_url,
            scl_asset_url=scl_url,
            bbox=item.get("bbox", []),
            stac_properties=props,
        )
        scenes.append(scene)

    # Sort primarily by cloud cover ascending, then by date descending
    scenes.sort(key=lambda s: (s.cloud_cover_pct, s.datetime), reverse=False)
    return scenes
