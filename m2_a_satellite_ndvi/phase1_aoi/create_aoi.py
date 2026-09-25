"""
AOI Generator Script — M2-A: Satellite & NDVI Engineer
======================================================
Builds the standardized GeoJSON study area definition for Sentinel-2
satellite ingestion and landslide hazard zonation.

Conforms to RFC 7946 GeoJSON specification using WGS 84 (EPSG:4326).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from pyproj import Geod
from shapely.geometry import Polygon, mapping

# Support running directly as a script or as a module
try:
    from phase1_aoi.config import (
        STUDY_AREA_METADATA,
        BOUNDING_BOX,
        POLYGON_COORDINATES,
        DEFAULT_OUTPUT_GEOJSON,
        get_bounding_box_tuple,
    )
except ImportError:
    from config import (
        STUDY_AREA_METADATA,
        BOUNDING_BOX,
        POLYGON_COORDINATES,
        DEFAULT_OUTPUT_GEOJSON,
        get_bounding_box_tuple,
    )


def compute_geodesic_area_sq_km(polygon: Polygon) -> float:
    """
    Calculates accurate ellipsoidal surface area in square kilometers
    using the WGS 84 reference ellipsoid via PyProj Geod.
    """
    geod = Geod(ellps="WGS84")
    area_meters, _ = geod.geometry_area_perimeter(polygon)
    return round(abs(area_meters) / 1_000_000.0, 2)


def generate_aoi_geojson(
    output_path: Path = DEFAULT_OUTPUT_GEOJSON,
    indent: int = 2
) -> Dict[str, Any]:
    """
    Generates and saves the RFC 7946 compliant GeoJSON FeatureCollection.

    Args:
        output_path: Destination path for study_area.geojson.
        indent: JSON indentation formatting.

    Returns:
        Dict representing the GeoJSON structure.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Build Shapely Polygon and verify validity
    polygon = Polygon(POLYGON_COORDINATES)
    if not polygon.is_valid:
        raise ValueError("Invalid polygon topology constructed from coordinate vertices.")

    # 2. Geodesic area calculation
    area_sq_km = compute_geodesic_area_sq_km(polygon)
    centroid = polygon.centroid
    bounds = get_bounding_box_tuple()  # (min_lon, min_lat, max_lon, max_lat)

    # 3. Construct Feature Properties
    now_iso = datetime.now(timezone.utc).isoformat()
    properties = {
        **STUDY_AREA_METADATA,
        "created_at_utc": now_iso,
        "area_sq_km": area_sq_km,
        "centroid": {
            "longitude": round(centroid.x, 4),
            "latitude": round(centroid.y, 4),
        },
        "bbox": [bounds[0], bounds[1], bounds[2], bounds[3]],
    }

    # 4. Construct RFC 7946 FeatureCollection
    geojson_data = {
        "type": "FeatureCollection",
        "name": STUDY_AREA_METADATA["name"],
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"  # RFC 7946 standard WGS84 CRS URN
            }
        },
        "bbox": [bounds[0], bounds[1], bounds[2], bounds[3]],
        "features": [
            {
                "type": "Feature",
                "id": STUDY_AREA_METADATA["short_code"],
                "properties": properties,
                "geometry": mapping(polygon),
                "bbox": [bounds[0], bounds[1], bounds[2], bounds[3]],
            }
        ],
    }

    # 5. Save to disk
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=indent, ensure_ascii=False)

    print(f"[SUCCESS] AOI GeoJSON successfully created: {output_path.resolve()}")
    print(f"          - Study Area : {STUDY_AREA_METADATA['name']}")
    print(f"          - CRS        : {STUDY_AREA_METADATA['crs']}")
    print(f"          - BoundingBox: {bounds}")
    print(f"          - Surface Area: ~{area_sq_km} sq km")

    return geojson_data


def main():
    parser = argparse.ArgumentParser(
        description="Generate standard study area GeoJSON for Sentinel-2 satellite ingestion."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT_GEOJSON,
        help=f"Target path for study_area.geojson (default: {DEFAULT_OUTPUT_GEOJSON})",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON without indent",
    )
    args = parser.parse_args()

    indent = None if args.compact else 2
    try:
        generate_aoi_geojson(output_path=args.output, indent=indent)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Failed to generate AOI GeoJSON: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
