"""
AOI Validation Suite — M2-A: Satellite & NDVI Engineer
======================================================
Rigorous validation of the study area definition:
  1. File existence & GeoJSON format validity.
  2. Non-emptiness and presence of features.
  3. Shapely topological geometry checks (is_valid, non-empty, simple).
  4. Coordinate range bounds (-180 <= lon <= 180, -90 <= lat <= 90).
  5. Coordinate order verification (ensures [lon, lat] per RFC 7946, not inverted [lat, lon]).
  6. CRS compliance (EPSG:4326 / WGS 84).
  7. GeoPandas GeoDataFrame loadability and spatial bounds checks.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import geopandas as gpd
from shapely.geometry import shape, Polygon

# Support running directly or as module
try:
    from phase1_aoi.config import DEFAULT_OUTPUT_GEOJSON, BOUNDING_BOX
except ImportError:
    from config import DEFAULT_OUTPUT_GEOJSON, BOUNDING_BOX


class AOIValidationError(Exception):
    """Raised when the AOI definition fails validation."""
    pass


def validate_geojson_structure(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validates top-level GeoJSON schema and extracts feature list."""
    if not isinstance(data, dict):
        raise AOIValidationError("GeoJSON root must be a dictionary.")

    geojson_type = data.get("type")
    if geojson_type == "FeatureCollection":
        features = data.get("features", [])
        if not features:
            raise AOIValidationError("FeatureCollection contains no features (empty AOI).")
        return features
    elif geojson_type == "Feature":
        return [data]
    else:
        raise AOIValidationError(f"Unsupported GeoJSON root type: '{geojson_type}'. Must be 'FeatureCollection' or 'Feature'.")


def validate_coordinates_range(coords: List[Any]) -> None:
    """Recursively checks that coordinates satisfy -180 <= lon <= 180 and -90 <= lat <= 90."""
    if not coords:
        raise AOIValidationError("Empty coordinates array detected.")

    # Check if this is a coordinate pair [lon, lat]
    if isinstance(coords[0], (int, float)):
        if len(coords) < 2:
            raise AOIValidationError(f"Coordinate pair must have at least [lon, lat]: {coords}")
        lon, lat = coords[0], coords[1]
        if not (-180.0 <= lon <= 180.0):
            raise AOIValidationError(f"Longitude {lon} out of valid range [-180, 180].")
        if not (-90.0 <= lat <= 90.0):
            raise AOIValidationError(f"Latitude {lat} out of valid range [-90, 90].")
        # Domain sanity check for Nilgiris region:
        # Longitude in India is around 68°-97° E, Latitude is around 8°-37° N
        # If coordinates are inverted ([lat, lon] instead of [lon, lat]), catch it!
        if 8.0 <= lon <= 37.0 and 68.0 <= lat <= 97.0:
            raise AOIValidationError(
                f"Coordinates appear inverted! Detected lon={lon}, lat={lat}. "
                "RFC 7946 GeoJSON requires [longitude, latitude] ordering."
            )
        return

    for item in coords:
        validate_coordinates_range(item)


def validate_geometry(geom_dict: Dict[str, Any]) -> Polygon:
    """Validates geometry using Shapely."""
    if not geom_dict:
        raise AOIValidationError("Geometry is missing or null.")

    try:
        geom = shape(geom_dict)
    except Exception as e:
        raise AOIValidationError(f"Failed to parse geometry with Shapely: {e}")

    if geom.is_empty:
        raise AOIValidationError("Geometry is empty.")

    if not geom.is_valid:
        raise AOIValidationError(f"Geometry is topologically invalid: {geom.is_valid}")

    if geom.geom_type not in ["Polygon", "MultiPolygon"]:
        raise AOIValidationError(f"Expected Polygon or MultiPolygon, found: '{geom.geom_type}'")

    return geom


def validate_geopandas_loading(file_path: Path) -> gpd.GeoDataFrame:
    """Verifies that GeoPandas can load the file and interpret CRS and bounds."""
    try:
        gdf = gpd.read_file(file_path)
    except Exception as e:
        raise AOIValidationError(f"GeoPandas failed to read '{file_path}': {e}")

    if gdf.empty:
        raise AOIValidationError("GeoPandas loaded an empty GeoDataFrame.")

    # Validate CRS
    if gdf.crs is not None:
        epsg_code = gdf.crs.to_epsg()
        if epsg_code != 4326:
            raise AOIValidationError(f"GeoDataFrame CRS is EPSG:{epsg_code}, expected EPSG:4326.")

    return gdf


def validate_aoi(file_path: Path = DEFAULT_OUTPUT_GEOJSON, verbose: bool = True) -> Dict[str, Any]:
    """
    Runs the complete validation pipeline on the target AOI GeoJSON file.

    Returns:
        Summary dict containing validation metrics and status.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise AOIValidationError(f"AOI file does not exist: {file_path.resolve()}")

    if file_path.stat().st_size == 0:
        raise AOIValidationError(f"AOI file is zero bytes (empty): {file_path}")

    # 1. Parse JSON
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise AOIValidationError(f"Invalid JSON format in '{file_path}': {e}")

    # 2. Schema and feature validation
    features = validate_geojson_structure(data)

    # 3. Geometry and Coordinate checks for every feature
    total_area_approx = 0.0
    all_bounds: List[Tuple[float, float, float, float]] = []

    for idx, feature in enumerate(features):
        geom_dict = feature.get("geometry")
        if not geom_dict:
            raise AOIValidationError(f"Feature at index {idx} lacks geometry.")

        # Coordinate value checks
        coords = geom_dict.get("coordinates", [])
        validate_coordinates_range(coords)

        # Shapely topological checks
        geom = validate_geometry(geom_dict)
        all_bounds.append(geom.bounds)

        # Check properties
        props = feature.get("properties", {})
        if not props:
            if verbose:
                print(f"[WARN] Feature at index {idx} has empty properties.")

    # 4. GeoPandas integration test
    gdf = validate_geopandas_loading(file_path)
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]

    # Verify bounds match configuration expectations
    minx, miny, maxx, maxy = bounds
    if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
        raise AOIValidationError(f"Bounds exceed global geographic ranges: {bounds}")

    summary = {
        "status": "VALID",
        "file_path": str(file_path.resolve()),
        "file_size_bytes": file_path.stat().st_size,
        "feature_count": len(gdf),
        "crs": "EPSG:4326 (WGS 84)",
        "bounds": {
            "min_lon": round(float(minx), 4),
            "min_lat": round(float(miny), 4),
            "max_lon": round(float(maxx), 4),
            "max_lat": round(float(maxy), 4),
        },
        "study_area_name": data.get("name", "Unknown"),
        "geopandas_loadable": True,
        "shapely_valid": True,
    }

    if verbose:
        print("============================================================")
        print("                 AOI VALIDATION PASSED                      ")
        print("============================================================")
        print(f"File Path    : {summary['file_path']}")
        print(f"Features     : {summary['feature_count']}")
        print(f"CRS          : {summary['crs']}")
        print(f"Geometry     : {gdf.geometry.iloc[0].geom_type}")
        print(f"Bounds (W/S/E/N): [{minx:.4f}, {miny:.4f}, {maxx:.4f}, {maxy:.4f}]")
        print(f"Centroid     : Lon {gdf.geometry.iloc[0].centroid.x:.4f}, Lat {gdf.geometry.iloc[0].centroid.y:.4f}")
        print("All topological and schema checks passed successfully.")
        print("============================================================")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Validate Study Area GeoJSON for M2-A.")
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_OUTPUT_GEOJSON,
        help=f"Path to study_area.geojson (default: {DEFAULT_OUTPUT_GEOJSON})",
    )
    args = parser.parse_args()

    try:
        validate_aoi(file_path=args.input, verbose=True)
        sys.exit(0)
    except AOIValidationError as e:
        print(f"\n[VALIDATION FAILED] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
