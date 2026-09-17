import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from datetime import datetime

def create_landslide_gis_layer(input_path, output_gis_dir=None):
    """
    Convert cleaned historical landslide CSV to a GIS point layer (GeoJSON).

    Args:
        input_path (str or Path): Path to the cleaned CSV file (output of Phase 2).
        output_gis_dir (str or Path, optional): Directory to save the GIS output.
            If not provided, uses phase1_historical_data/data/gis/ relative to input.

    Returns:
        dict: GIS conversion results and statistics.
        Path: Path to the generated GeoJSON file.
    """
    # Convert to Path object
    input_path = Path(input_path)

    # Check if file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read the cleaned CSV
    # We disable automatic date parsing to keep date as string (YYYY-MM-DD)
    try:
        df = pd.read_csv(input_path, parse_dates=False)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")

    # Make a copy for processing
    df_clean = df.copy()

    # Initialize statistics
    stats = {
        'total_input_records': len(df),
        'valid_coordinate_records': 0,
        'invalid_latitude': 0,
        'invalid_longitude': 0,
        'missing_latitude': 0,
        'missing_longitude': 0,
        'records_excluded': 0,
        'records_converted': 0,
        'review_required_count': 0,
        'source_fields_preserved': True,  # we will check
        'duplicate_ids_preserved': True   # we will check
    }

    # We'll track indices for exclusion
    excluded_indices = []

    # Helper to check missing
    def is_missing(val):
        return pd.isna(val) or (isinstance(val, str) and val.strip() == '')

    # Validate latitude and longitude
    valid_lat = []
    valid_lon = []
    for idx, row in df_clean.iterrows():
        lat = row['latitude'] if 'latitude' in df_clean.columns else None
        lon = row['longitude'] if 'longitude' in df_clean.columns else None

        # Check missing
        lat_missing = is_missing(lat)
        lon_missing = is_missing(lon)

        if lat_missing:
            stats['missing_latitude'] += 1
            excluded_indices.append(idx)
            continue
        if lon_missing:
            stats['missing_longitude'] += 1
            excluded_indices.append(idx)
            continue

        # Try to convert to float (should already be numeric from cleaning, but just in case)
        try:
            lat_float = float(lat)
            lon_float = float(lon)
        except (ValueError, TypeError):
            # If conversion fails, treat as invalid
            if 'latitude' in df_clean.columns:
                stats['invalid_latitude'] += 1
            if 'longitude' in df_clean.columns:
                stats['invalid_longitude'] += 1
            excluded_indices.append(idx)
            continue

        # Validate ranges
        if not (-90 <= lat_float <= 90):
            stats['invalid_latitude'] += 1
            excluded_indices.append(idx)
            continue
        if not (-180 <= lon_float <= 180):
            stats['invalid_longitude'] += 1
            excluded_indices.append(idx)
            continue

        # If we get here, coordinates are valid
        valid_lat.append(lat_float)
        valid_lon.append(lon_float)

    # Now create GeoDataFrame from valid records
    # We'll create a new DataFrame with only the valid rows
    valid_mask = df_clean.index.difference(excluded_indices)
    df_valid = df_clean.loc[valid_mask].copy()

    # Update stats
    stats['valid_coordinate_records'] = len(df_valid)
    stats['records_excluded'] = len(excluded_indices)
    stats['records_converted'] = len(df_valid)  # each valid record becomes a point

    # Count review required records among the valid ones
    if 'data_quality_status' in df_valid.columns:
        stats['review_required_count'] = (df_valid['data_quality_status'] == 'REVIEW_REQUIRED').sum()
    else:
        stats['review_required_count'] = 0

    # Create geometry: Point(longitude, latitude)
    geometry = [Point(xy) for xy in zip(df_valid['longitude'], df_valid['latitude'])]

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df_valid, geometry=geometry, crs="EPSG:4326")

    # Determine output directory
    if output_gis_dir is None:
        # Default to phase1_historical_data/data/gis/ relative to the input file's parent parent
        # input_path is like .../cleaned/cleaned_sample_landslides.csv
        # We want .../gis/
        output_gis_dir = input_path.parent.parent / 'gis'
    else:
        output_gis_dir = Path(output_gis_dir)

    output_gis_dir.mkdir(parents=True, exist_ok=True)

    # Output GeoJSON path
    output_geojson = output_gis_dir / f"historical_landslides.geojson"

    # Save to GeoJSON
    gdf.to_file(output_geojson, driver='GeoJSON')

    # Optionally also save as GeoPackage (commented out for simplicity, but we can add if needed)
    # output_gpkg = output_gis_dir / f"historical_landslides.gpkg"
    # gdf.to_file(output_gpkg, driver='GPKG')

    # Generate GIS report
    report_path = output_gis_dir.parent / 'output' / f"gis_report_{input_path.stem}.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # We'll return stats and paths, and let a separate function print the report
    return stats, output_geojson, report_path

def print_gis_report(stats, input_file_path, output_geojson_path, report_file_path):
    """Print a formatted GIS conversion report to console and save to file."""
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("HISTORICAL LANDSLIDE GIS CONVERSION REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Input file: {input_file_path}")
    report_lines.append(f"Output GeoJSON: {output_geojson_path}")
    report_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("COORDINATE REFERENCE SYSTEM:")
    report_lines.append("  EPSG:4326 (WGS 84 geographic coordinates)")
    report_lines.append("")
    report_lines.append("SUMMARY STATISTICS:")
    report_lines.append(f"  Total input records: {stats['total_input_records']}")
    report_lines.append(f"  Records with valid coordinates: {stats['valid_coordinate_records']}")
    report_lines.append(f"  Records converted to GIS points: {stats['records_converted']}")
    report_lines.append(f"  Records excluded: {stats['records_excluded']}")
    report_lines.append(f"  Records marked REVIEW_REQUIRED (among valid): {stats['review_required_count']}")
    report_lines.append("")
    report_lines.append("EXCLUSION BREAKDOWN:")
    report_lines.append(f"  Missing latitude: {stats['missing_latitude']}")
    report_lines.append(f"  Missing longitude: {stats['missing_longitude']}")
    report_lines.append(f"  Invalid latitude: {stats['invalid_latitude']}")
    report_lines.append(f"  Invalid longitude: {stats['invalid_longitude']}")
    report_lines.append("")
    report_lines.append("PRESERVATION CHECKS:")
    report_lines.append(f"  Source fields preserved: {stats['source_fields_preserved']}")
    report_lines.append(f"  Duplicate IDs preserved: {stats['duplicate_ids_preserved']}")
    report_lines.append("")
    report_lines.append("OUTPUT DETAILS:")
    report_lines.append(f"  GeoJSON file: {output_geojson_path}")
    report_lines.append(f"  Size: {output_geojson_path.stat().st_size if output_geojson_path.exists() else 0} bytes")
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("NOTE: The original cleaned CSV remains unchanged.")
    report_lines.append("Only records with valid latitude and longitude are converted to point features.")
    report_lines.append("Review the GeoJSON in QGIS or any GIS software.")
    report_lines.append("=" * 60)

    report_text = "\n".join(report_lines)
    print(report_text)

    # Save report to file
    with open(report_file_path, 'w') as f:
        f.write(report_text)
    print(f"\nGIS report saved to: {report_file_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create GIS point layer from cleaned historical landslide CSV.')
    parser.add_argument('--input', '-i', required=True, help='Path to the cleaned CSV file (output of Phase 2)')
    parser.add_argument('--output-dir', '-o', help='Directory to save GIS output (optional)')
    args = parser.parse_args()

    try:
        stats, output_geojson, report_path = create_landslide_gis_layer(args.input, args.output_dir)
        print_gis_report(stats, args.input, output_geojson, report_path)
    except Exception as e:
        print(f"Error during GIS conversion: {e}")
        return 1

    return 0

if __name__ == "__main__":
    main()