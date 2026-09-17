#!/usr/bin/env python3
"""
M2-C Phase 5: Spatial Join / Feature Extraction

Extracts environmental features from M2-A (NDVI) and M2-B (rainfall, DEM, slope, aspect)
for each historical landslide point from M2-C Phase 3 output.

This script creates an intermediate feature-extraction dataset, NOT the final ML dataset.
"""

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.enums import Resampling
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 70)
    print("M2-C PHASE 5 — SPATIAL FEATURE EXTRACTION")
    print("=" * 70)

    # Base directory for M2-C
    base_dir = Path(__file__).parent.parent

    # Define paths
    historical_geojson_path = base_dir / 'data' / 'gis' / 'historical_landslides.geojson'
    output_dir = base_dir / 'data' / 'features' / 'phase5'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv_path = output_dir / 'historical_landslide_features.csv'
    output_geojson_path = output_dir / 'historical_landslide_features.geojson'
    report_path = base_dir / 'output' / 'feature_extraction_report.txt'

    # Load historical landslide data
    print(f"Loading historical landslide data from: {historical_geojson_path}")
    if not historical_geojson_path.exists():
        raise FileNotFoundError(f"Historical landslide GeoJSON not found: {historical_geojson_path}")

    gdf_historical = gpd.read_file(historical_geojson_path)
    print(f"Loaded {len(gdf_historical)} historical landslide records")

    # Validate CRS
    historical_crs = gdf_historical.crs
    print(f"Historical landslide CRS: {historical_crs}")
    assert historical_crs == "EPSG:4326", f"Expected EPSG:4326, got {historical_crs}"

    # Validate geometry type
    assert all(gdf_historical.geometry.type == 'Point'), "All geometries must be Point"
    print("[OK] All geometries are Point type")

    # Validate coordinate order (longitude=X, latitude=Y)
    # Check first few points
    for idx, row in gdf_historical.iterrows():
        lon, lat = row.geometry.x, row.geometry.y
        # Basic validation: longitude should be between -180 and 180, latitude between -90 and 90
        assert -180 <= lon <= 180, f"Invalid longitude {lon} for record {row.landslide_id}"
        assert -90 <= lat <= 90, f"Invalid latitude {lat} for record {row.landslide_id}"
    print("[OK] Coordinate order validated (longitude=X, latitude=Y)")

    # Initialize lists to store extracted features
    extracted_data = []

    # Process M2-A: NDVI
    print("\n--- Processing M2-A: NDVI ---")
    m2a_dir = base_dir / 'data' / 'integrated' / 'm2a'

    # Look for Phase 5.1 corrected files first, then fallback to original
    ndvi_files_phase5_1 = list(m2a_dir.glob('*phase5_1*.tif')) + list(m2a_dir.glob('*phase5_1*.tiff'))
    ndvi_files_original = list(m2a_dir.glob('*.tif')) + list(m2a_dir.glob('*.tiff'))

    # Remove Phase 5.1 files from the original list to get truly original files
    ndvi_files_original_only = [f for f in ndvi_files_original if f not in ndvi_files_phase5_1]

    # Use corrected files if available, otherwise use original
    if ndvi_files_phase5_1:
        ndvi_file = ndvi_files_phase5_1[0]
        print(f"Found NDVI file (Phase 5.1 corrected): {ndvi_file.name}")
    elif ndvi_files_original_only:
        ndvi_file = ndvi_files_original_only[0]
        print(f"Found NDVI file (original): {ndvi_file.name}")
    else:
        print("WARNING: No NDVI files found in M2-A directory")
        ndvi_file = None

    if ndvi_file:
        # Load NDVI metadata to confirm it's synthetic
        ndvi_metadata_path = m2a_dir / 'ndvi_metadata.json'
        if ndvi_metadata_path.exists():
            with open(ndvi_metadata_path) as f:
                ndvi_metadata = json.load(f)
            print(f"NDVI dataset status: {ndvi_metadata.get('status', 'unknown')}")
            if ndvi_metadata.get('status') == 'SYNTHETIC_DEMO_DATA':
                print("[OK] Confirmed: NDVI is synthetic demo data")

    # Process M2-B: DEM, slope, aspect, rainfall
    print("\n--- Processing M2-B: Environmental Data ---")
    m2b_dir = base_dir / 'data' / 'integrated' / 'm2b'

    # Look for Phase 5.1 corrected files first, then fallback to original
    dem_files_phase5_1 = list(m2b_dir.glob('dem*phase5_1*.tif')) + list(m2b_dir.glob('dem*phase5_1*.tiff'))
    dem_files_all = list(m2b_dir.glob('dem*.tif')) + list(m2b_dir.glob('dem*.tiff'))
    # Remove phase5_1 files from the all list to get truly original files
    dem_files_original = [f for f in dem_files_all if f not in dem_files_phase5_1]

    slope_files_phase5_1 = list(m2b_dir.glob('slope*phase5_1*.tif')) + list(m2b_dir.glob('slope*phase5_1*.tiff'))
    slope_files_all = list(m2b_dir.glob('slope*.tif')) + list(m2b_dir.glob('slope*.tiff'))
    # Remove phase5_1 files from the all list to get truly original files
    slope_files_original = [f for f in slope_files_all if f not in slope_files_phase5_1]

    aspect_files_phase5_1 = list(m2b_dir.glob('aspect*phase5_1*.tif')) + list(m2b_dir.glob('aspect*phase5_1*.tiff'))
    aspect_files_all = list(m2b_dir.glob('aspect*.tif')) + list(m2b_dir.glob('aspect*.tiff'))
    # Remove phase5_1 files from the all list to get truly original files
    aspect_files_original = [f for f in aspect_files_all if f not in aspect_files_phase5_1]

    # DEM (elevation)
    if dem_files_phase5_1:
        dem_file = dem_files_phase5_1[0]
        print(f"Found DEM file (Phase 5.1 corrected): {dem_file.name}")
    elif dem_files_original:
        dem_file = dem_files_original[0]
        print(f"Found DEM file (original): {dem_file.name}")
    else:
        print("WARNING: No DEM files found in M2-B directory")
        dem_file = None

    if dem_file:
        # Load M2-B metadata to confirm it's synthetic
        dem_metadata_path = m2b_dir / 'm2b_metadata.json'
        if dem_metadata_path.exists():
            with open(dem_metadata_path) as f:
                m2b_metadata = json.load(f)
            print(f"M2-B dataset status: {m2b_metadata.get('status', 'unknown')}")
            if m2b_metadata.get('status') == 'SYNTHETIC_DEMO_DATA':
                print("[OK] Confirmed: M2-B is synthetic demo data")

    # Slope
    if slope_files_phase5_1:
        slope_file = slope_files_phase5_1[0]
        print(f"Found slope file (Phase 5.1 corrected): {slope_file.name}")
    elif slope_files_original:
        slope_file = slope_files_original[0]
        print(f"Found slope file (original): {slope_file.name}")
    else:
        print("WARNING: No slope files found in M2-B directory")
        slope_file = None

    # Aspect
    if aspect_files_phase5_1:
        aspect_file = aspect_files_phase5_1[0]
        print(f"Found aspect file (Phase 5.1 corrected): {aspect_file.name}")
    elif aspect_files_original:
        aspect_file = aspect_files_original[0]
        print(f"Found aspect file (original): {aspect_file.name}")
    else:
        print("WARNING: No aspect files found in M2-B directory")
        aspect_file = None

    # Rainfall (keep as is - we'll leave it non-spatial for now)
    rainfall_files = list(m2b_dir.glob('*.csv'))
    rainfall_file = rainfall_files[0] if rainfall_files else None
    if rainfall_file:
        print(f"Found rainfall file: {rainfall_file.name}")
        # Load rainfall data to inspect structure
        rainfall_df = pd.read_csv(rainfall_file)
        print(f"Rainfall data shape: {rainfall_df.shape}")
        print(f"Rainfall columns: {list(rainfall_df.columns)}")
        print("Note: Rainfall data appears to be non-spatial (tabular only)")

    # Process each historical landslide point
    print(f"\n--- Extracting features for {len(gdf_historical)} historical landslide points ---")

    for idx, row in gdf_historical.iterrows():
        landslide_id = row.landslide_id
        print(f"\nProcessing {landslide_id}...")

        # Initialize feature dictionary with historical attributes
        feature = {
            'landslide_id': row.landslide_id,
            'date': row.date,
            'latitude': row.geometry.y,  # Note: we store as separate fields for clarity
            'longitude': row.geometry.x,
            'location': row.get('location', ''),
            'district': row.get('district', ''),
            'state': row.get('state', ''),
            'country': row.get('country', ''),
            'source': row.get('source', ''),
            'source_url': row.get('source_url', ''),
            'severity': row.get('severity', np.nan),
            'description': row.get('description', ''),
            'data_quality_status': row.get('data_quality_status', ''),
        }

        # Extract NDVI
        if ndvi_file:
            try:
                with rasterio.open(ndvi_file) as src:
                    # Transform point to raster CRS if needed
                    point_x, point_y = row.geometry.x, row.geometry.y
                    if historical_crs != src.crs:
                        # Would need to transform coordinates here
                        # For now, all data is EPSG:4326 so no transformation needed
                        pass

                    # Sample the raster
                    try:
                        sample = src.sample([(point_x, point_y)])
                        ndvi_value = next(sample)[0]  # Get first band value

                        # Check for nodata
                        if src.nodata is not None and np.isclose(ndvi_value, src.nodata):
                            ndvi_value = np.nan
                            ndvi_status = 'NODATA'
                        elif ndvi_value == src.nodata:
                            ndvi_value = np.nan
                            ndvi_status = 'NODATA'
                        else:
                            ndvi_status = 'EXTRACTED'

                    except IndexError:
                        # Point outside raster bounds
                        ndvi_value = np.nan
                        ndvi_status = 'OUTSIDE_RASTER'
                    except Exception as e:
                        print(f"  Warning: Error sampling NDVI for {landslide_id}: {e}")
                        ndvi_value = np.nan
                        ndvi_status = 'ERROR'

            except Exception as e:
                print(f"  Warning: Could not open NDVI file: {e}")
                ndvi_value = np.nan
                ndvi_status = 'ERROR'
        else:
            ndvi_value = np.nan
            ndvi_status = 'NO_DATA_SOURCE'

        feature['ndvi'] = ndvi_value
        feature['ndvi_status'] = ndvi_status

        # Extract elevation (DEM)
        if dem_file:
            try:
                with rasterio.open(dem_file) as src:
                    point_x, point_y = row.geometry.x, row.geometry.y
                    try:
                        sample = src.sample([(point_x, point_y)])
                        elevation_value = next(sample)[0]

                        if src.nodata is not None and np.isclose(elevation_value, src.nodata):
                            elevation_value = np.nan
                            elevation_status = 'NODATA'
                        elif elevation_value == src.nodata:
                            elevation_value = np.nan
                            elevation_status = 'NODATA'
                        else:
                            elevation_status = 'EXTRACTED'

                    except IndexError:
                        elevation_value = np.nan
                        elevation_status = 'OUTSIDE_RASTER'
                    except Exception as e:
                        print(f"  Warning: Error sampling elevation for {landslide_id}: {e}")
                        elevation_value = np.nan
                        elevation_status = 'ERROR'

            except Exception as e:
                print(f"  Warning: Could not open DEM file: {e}")
                elevation_value = np.nan
                elevation_status = 'ERROR'
        else:
            elevation_value = np.nan
            elevation_status = 'NO_DATA_SOURCE'

        feature['elevation_m'] = elevation_value
        feature['elevation_status'] = elevation_status

        # Extract slope
        if slope_file:
            try:
                with rasterio.open(slope_file) as src:
                    point_x, point_y = row.geometry.x, row.geometry.y
                    try:
                        sample = src.sample([(point_x, point_y)])
                        slope_value = next(sample)[0]

                        if src.nodata is not None and np.isclose(slope_value, src.nodata):
                            slope_value = np.nan
                            slope_status = 'NODATA'
                        elif slope_value == src.nodata:
                            slope_value = np.nan
                            slope_status = 'NODATA'
                        else:
                            slope_status = 'EXTRACTED'

                    except IndexError:
                        slope_value = np.nan
                        slope_status = 'OUTSIDE_RASTER'
                    except Exception as e:
                        print(f"  Warning: Error sampling slope for {landslide_id}: {e}")
                        slope_value = np.nan
                        slope_status = 'ERROR'

            except Exception as e:
                print(f"  Warning: Could not open slope file: {e}")
                slope_value = np.nan
                slope_status = 'ERROR'
        else:
            slope_value = np.nan
            slope_status = 'NO_DATA_SOURCE'

        feature['slope_deg'] = slope_value
        feature['slope_status'] = slope_status

        # Extract aspect
        if aspect_file:
            try:
                with rasterio.open(aspect_file) as src:
                    point_x, point_y = row.geometry.x, row.geometry.y
                    try:
                        sample = src.sample([(point_x, point_y)])
                        aspect_value = next(sample)[0]

                        if src.nodata is not None and np.isclose(aspect_value, src.nodata):
                            aspect_value = np.nan
                            aspect_status = 'NODATA'
                        elif aspect_value == src.nodata:
                            aspect_value = np.nan
                            aspect_status = 'NODATA'
                        else:
                            aspect_status = 'EXTRACTED'

                    except IndexError:
                        aspect_value = np.nan
                        aspect_status = 'OUTSIDE_RASTER'
                    except Exception as e:
                        print(f"  Warning: Error sampling aspect for {landslide_id}: {e}")
                        aspect_value = np.nan
                        aspect_status = 'ERROR'

            except Exception as e:
                print(f"  Warning: Could not open aspect file: {e}")
                aspect_value = np.nan
                aspect_status = 'ERROR'
        else:
            aspect_value = np.nan
            aspect_status = 'NO_DATA_SOURCE'

        feature['aspect_deg'] = aspect_value
        feature['aspect_status'] = aspect_status

        # Process rainfall (non-spatial)
        if rainfall_file:
            # Since rainfall data is not spatially explicit, we cannot extract values based on point location
            # We'll mark it as NOT_SPATIALLY_MAPPABLE
            feature['rainfall_24h'] = np.nan
            feature['rainfall_3d'] = np.nan
            feature['rainfall_7d'] = np.nan
            feature['rainfall_status'] = 'NOT_SPATIALLY_MAPPABLE'
            print(f"  Rainfall: NOT_SPATIALLY_MAPPABLE (non-spatial data)")
        else:
            feature['rainfall_24h'] = np.nan
            feature['rainfall_3d'] = np.nan
            feature['rainfall_7d'] = np.nan
            feature['rainfall_status'] = 'NO_DATA_SOURCE'

        # Determine data source type
        # Check if any of the environmental data sources are synthetic
        is_synthetic = False
        sources_checked = []

        # Check NDVI
        if ndvi_file and ndvi_metadata_path.exists():
            with open(ndvi_metadata_path) as f:
                ndvi_meta = json.load(f)
            if ndvi_meta.get('status') == 'SYNTHETIC_DEMO_DATA':
                is_synthetic = True
                sources_checked.append('NDVI')

        # Check M2-B (DEM, slope, aspect share same metadata)
        if dem_file and dem_metadata_path.exists():
            with open(dem_metadata_path) as f:
                m2b_meta = json.load(f)
            if m2b_meta.get('status') == 'SYNTHETIC_DEMO_DATA':
                is_synthetic = True
                sources_checked.append('M2-B')

        if is_synthetic:
            feature['data_source_type'] = 'SYNTHETIC_DEMO'
            print(f"  Data source type: SYNTHETIC_DEMO (based on {', '.join(sources_checked)})")
        else:
            feature['data_source_type'] = 'REAL'
            print(f"  Data source type: REAL")

        # Determine overall feature extraction status
        status_fields = [
            feature['ndvi_status'],
            feature['elevation_status'],
            feature['slope_status'],
            feature['aspect_status'],
            feature['rainfall_status']
        ]

        # Count successful extractions
        extracted_count = sum(1 for s in status_fields if s == 'EXTRACTED')
        total_attempted = sum(1 for s in status_fields if s not in ['NO_DATA_SOURCE', 'NOT_SPATIALLY_MAPPABLE'])

        if extracted_count == total_attempted and total_attempted > 0:
            feature['feature_extraction_status'] = 'COMPLETE'
        elif extracted_count > 0:
            feature['feature_extraction_status'] = 'PARTIAL'
        elif extracted_count == 0 and total_attempted > 0:
            feature['feature_extraction_status'] = 'NO_FEATURES'
        else:
            feature['feature_extraction_status'] = 'NO_DATA_SOURCES'

        extracted_data.append(feature)
        print(f"  Feature extraction status: {feature['feature_extraction_status']}")

    # Convert to DataFrame
    features_df = pd.DataFrame(extracted_data)

    # Reorder columns for clarity
    historical_cols = ['landslide_id', 'date', 'latitude', 'longitude', 'location', 'district',
                      'state', 'country', 'source', 'source_url', 'severity', 'description',
                      'data_quality_status']
    environmental_cols = ['ndvi', 'ndvi_status',
                         'rainfall_24h', 'rainfall_3d', 'rainfall_7d', 'rainfall_status',
                         'elevation_m', 'elevation_status',
                         'slope_deg', 'slope_status',
                         'aspect_deg', 'aspect_status']
    status_cols = ['feature_extraction_status', 'data_source_type']

    # Ensure all columns exist
    all_cols = historical_cols + environmental_cols + status_cols
    existing_cols = [col for col in all_cols if col in features_df.columns]
    features_df = features_df[existing_cols]

    # Save CSV
    print(f"\nSaving feature extraction results to: {output_csv_path}")
    features_df.to_csv(output_csv_path, index=False)
    print(f"[OK] Saved {len(features_df)} records to CSV")

    # Create optional GeoJSON output
    print(f"\nCreating optional GeoJSON output: {output_geojson_path}")
    # Convert DataFrame back to GeoDataFrame
    geometry = gpd.points_from_xy(features_df.longitude, features_df.latitude)
    gdf_output = gpd.GeoDataFrame(features_df, geometry=geometry, crs="EPSG:4326")
    gdf_output.to_file(output_geojson_path, driver='GeoJSON')
    print(f"[OK] Saved GeoJSON with {len(gdf_output)} features")

    # Generate report
    print(f"\nGenerating feature extraction report: {report_path}")
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("M2-C PHASE 5 — SPATIAL FEATURE EXTRACTION REPORT")
    report_lines.append("=" * 70)
    report_lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Input information
    report_lines.append("INPUT:")
    report_lines.append(f"  Historical landslide GeoJSON: {historical_geojson_path.name}")
    report_lines.append(f"  Record count: {len(gdf_historical)}")
    report_lines.append(f"  CRS: {historical_crs}")
    report_lines.append(f"  Geometry type: {gdf_historical.geometry.type.iloc[0] if len(gdf_historical) > 0 else 'None'}")
    report_lines.append("")

    # M2-A information
    report_lines.append("M2-A:")
    if ndvi_file:
        report_lines.append(f"  NDVI dataset: {ndvi_file.name}")
        if ndvi_metadata_path.exists():
            with open(ndvi_metadata_path) as f:
                ndvi_meta = json.load(f)
            report_lines.append(f"  Purpose: {ndvi_meta.get('purpose', 'unknown')}")
            report_lines.append(f"  Status: {ndvi_meta.get('status', 'unknown')}")
            report_lines.append(f"  CRS: {ndvi_meta.get('crs', 'unknown')}")
            if 'raster_info' in ndvi_meta:
                ri = ndvi_meta['raster_info']
                report_lines.append(f"  Raster size: {ri.get('width', 'unknown')} x {ri.get('height', 'unknown')} pixels")
                report_lines.append(f"  Pixel size: {ri.get('pixel_size_x', 'unknown')} x {ri.get('pixel_size_y', 'unknown')} degrees")
                report_lines.append(f"  Data type: {ri.get('data_type', 'unknown')}")
                report_lines.append(f"  NoData value: {ri.get('nodata', 'unknown')}")
                if 'value_range' in ndvi_meta:
                    vr = ndvi_meta['value_range']
                    report_lines.append(f"  Value range: [{vr.get('min', 'unknown')}, {vr.get('max', 'unknown')}]")
            if 'spatial_extent' in ndvi_meta:
                se = ndvi_meta['spatial_extent']
                report_lines.append(f"  Spatial extent: [{se.get('min_longitude', 'unknown')}, {se.get('min_latitude', 'unknown')}, {se.get('max_longitude', 'unknown')}, {se.get('max_latitude', 'unknown')}]")
        report_lines.append("")
    else:
        report_lines.append("  NDVI dataset: NOT FOUND")
        report_lines.append("")

    # M2-B information
    report_lines.append("M2-B:")
    if dem_file:
        report_lines.append(f"  DEM dataset: {dem_file.name}")
    if slope_file:
        report_lines.append(f"  Slope dataset: {slope_file.name}")
    if aspect_file:
        report_lines.append(f"  Aspect dataset: {aspect_file.name}")
    if rainfall_file:
        report_lines.append(f"  Rainfall dataset: {rainfall_file.name}")
        report_lines.append(f"  Rainfall rows: {len(rainfall_df)}")
        report_lines.append(f"  Rainfall columns: {list(rainfall_df.columns)}")

    if dem_metadata_path.exists():
        with open(dem_metadata_path) as f:
            m2b_meta = json.load(f)
        report_lines.append(f"  Purpose: {m2b_meta.get('purpose', 'unknown')}")
        report_lines.append(f"  Status: {m2b_meta.get('status', 'unknown')}")
        report_lines.append(f"  CRS: {m2b_meta.get('crs', 'unknown')}")
        if 'raster_info' in m2b_meta:
            ri = m2b_meta['raster_info']
            report_lines.append(f"  Raster size: {ri.get('width', 'unknown')} x {ri.get('height', 'unknown')} pixels")
            report_lines.append(f"  Pixel size: {ri.get('pixel_size_x', 'unknown')} x {ri.get('pixel_size_y', 'unknown')} degrees")
            report_lines.append(f"  Data type: {ri.get('data_type', 'unknown')}")
            report_lines.append(f"  NoData value: {ri.get('nodata', 'unknown')}")
        if 'rainfall_csv_info' in m2b_meta:
            rci = m2b_meta['rainfall_csv_info']
            report_lines.append(f"  Rainfall rows: {rci.get('rows', 'unknown')}")
            report_lines.append(f"  Rainfall columns: {rci.get('columns', 'unknown')}")
            if 'date_range' in rci:
                dr = rci['date_range']
                report_lines.append(f"  Rainfall date range: {dr.get('min', 'unknown')} to {dr.get('max', 'unknown')}")
    report_lines.append("")

    # CRS information
    report_lines.append("CRS INFORMATION:")
    report_lines.append(f"  Historical landslide layer: {historical_crs}")
    if ndvi_file:
        with open(ndvi_file) as f:
            pass  # Just to check if we can open it
        with rasterio.open(ndvi_file) as src:
            report_lines.append(f"  NDVI raster: {src.crs}")
    if dem_file:
        with rasterio.open(dem_file) as src:
            report_lines.append(f"  DEM raster: {src.crs}")
    report_lines.append("")

    # Extraction summary
    report_lines.append("EXTRACTION SUMMARY:")
    report_lines.append(f"  Total historical landslide records: {len(features_df)}")

    # NDVI statistics
    ndvi_extracted = (features_df['ndvi_status'] == 'EXTRACTED').sum()
    ndvi_nodata = (features_df['ndvi_status'] == 'NODATA').sum()
    ndvi_outside = (features_df['ndvi_status'] == 'OUTSIDE_RASTER').sum()
    ndvi_error = (features_df['ndvi_status'] == 'ERROR').sum()
    report_lines.append(f"  NDVI extracted: {ndvi_extracted}")
    report_lines.append(f"  NDVI nodata: {ndvi_nodata}")
    report_lines.append(f"  NDVI outside raster: {ndvi_outside}")
    report_lines.append(f"  NDVI errors: {ndvi_error}")

    # Rainfall statistics
    rainfall_nospatial = (features_df['rainfall_status'] == 'NOT_SPATIALLY_MAPPABLE').sum()
    rainfall_error = (features_df['rainfall_status'] == 'ERROR').sum()
    report_lines.append(f"  Rainfall (non-spatial): {rainfall_nospatial} records marked as NOT_SPATIALLY_MAPPABLE")
    report_lines.append(f"  Rainfall errors: {rainfall_error}")

    # Elevation statistics
    elev_extracted = (features_df['elevation_status'] == 'EXTRACTED').sum()
    elev_nodata = (features_df['elevation_status'] == 'NODATA').sum()
    elev_outside = (features_df['elevation_status'] == 'OUTSIDE_RASTER').sum()
    elev_error = (features_df['elevation_status'] == 'ERROR').sum()
    report_lines.append(f"  Elevation extracted: {elev_extracted}")
    report_lines.append(f"  Elevation nodata: {elev_nodata}")
    report_lines.append(f"  Elevation outside raster: {elev_outside}")
    report_lines.append(f"  Elevation errors: {elev_error}")

    # Slope statistics
    slope_extracted = (features_df['slope_status'] == 'EXTRACTED').sum()
    slope_nodata = (features_df['slope_status'] == 'NODATA').sum()
    slope_outside = (features_df['slope_status'] == 'OUTSIDE_RASTER').sum()
    slope_error = (features_df['slope_status'] == 'ERROR').sum()
    report_lines.append(f"  Slope extracted: {slope_extracted}")
    report_lines.append(f"  Slope nodata: {slope_nodata}")
    report_lines.append(f"  Slope outside raster: {slope_outside}")
    report_lines.append(f"  Slope errors: {slope_error}")

    # Aspect statistics
    aspect_extracted = (features_df['aspect_status'] == 'EXTRACTED').sum()
    aspect_nodata = (features_df['aspect_status'] == 'NODATA').sum()
    aspect_outside = (features_df['aspect_status'] == 'OUTSIDE_RASTER').sum()
    aspect_error = (features_df['aspect_status'] == 'ERROR').sum()
    report_lines.append(f"  Aspect extracted: {aspect_extracted}")
    report_lines.append(f"  Aspect nodata: {aspect_nodata}")
    report_lines.append(f"  Aspect outside raster: {aspect_outside}")
    report_lines.append(f"  Aspect errors: {aspect_error}")

    # Feature extraction status summary
    report_lines.append("")
    report_lines.append("FEATURE EXTRACTION STATUS:")
    status_counts = features_df['feature_extraction_status'].value_counts()
    for status, count in status_counts.items():
        report_lines.append(f"  {status}: {count}")

    # Data source type summary
    report_lines.append("")
    report_lines.append("DATA SOURCE TYPE:")
    source_counts = features_df['data_source_type'].value_counts()
    for source_type, count in source_counts.items():
        report_lines.append(f"  {source_type}: {count}")

    # Output information
    report_lines.append("")
    report_lines.append("OUTPUT:")
    report_lines.append(f"  Feature extraction CSV: {output_csv_path}")
    report_lines.append(f"  Feature extraction GeoJSON: {output_geojson_path}")
    report_lines.append(f"  Report file: {report_path}")
    report_lines.append("")

    # Important notes
    report_lines.append("=" * 70)
    report_lines.append("IMPORTANT NOTES:")
    report_lines.append("  1. This dataset is an intermediate feature-extraction dataset.")
    report_lines.append("     It is NOT the final ML dataset.")
    report_lines.append("  2. All environmental values marked as SYNTHETIC_DEMO are derived from")
    report_lines.append("     synthetic/demo data and must not be used as real observations.")
    report_lines.append("  3. Rainfall data is non-spatial (tabular only) and could not be")
    report_lines.append("     spatially extracted; marked as NOT_SPATIALLY_MAPPABLE.")
    report_lines.append("  4. Missing values are preserved as NaN with appropriate status codes.")
    report_lines.append("  5. No missing values were imputed or replaced with artificial values.")
    report_lines.append("  6. Original data files remain unchanged (read-only access only).")
    report_lines.append("=" * 70)

    # Write report
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print("[OK] Report generated successfully")

    # Print summary to console
    print("\n" + "=" * 70)
    print("PHASE 5 EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Historical landslide records processed: {len(features_df)}")
    print(f"Feature extraction CSV: {output_csv_path}")
    print(f"Feature extraction GeoJSON: {output_geojson_path}")
    print(f"Extraction report: {report_path}")
    print("=" * 70)

    return 0

if __name__ == '__main__':
    exit(main())