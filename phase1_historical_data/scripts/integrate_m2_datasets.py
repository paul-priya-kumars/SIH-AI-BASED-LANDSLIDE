import os
import json
from pathlib import Path
import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
from datetime import datetime

def load_inspection_results():
    """Load the inspection results from the JSON file if available."""
    inspection_file = Path(__file__).parent.parent.parent / 'data' / 'integrated' / 'integration_metadata' / 'inspection_results.json'
    if inspection_file.exists():
        with open(inspection_file) as f:
            return json.load(f)
    else:
        return None

def inspect_dataset(filepath):
    """Inspect a dataset and return metadata."""
    if not filepath.exists():
        return {'error': 'File not found'}
    try:
        if filepath.suffix.lower() in ['.tif', '.tiff']:
            with rasterio.open(filepath) as src:
                info = {
                    'type': 'raster',
                    'crs': str(src.crs),
                    'bbox': list(src.bounds),  # [minx, miny, maxx, maxy]
                    'width': src.width,
                    'height': src.height,
                    'count': src.count,
                    'dtypes': [str(dt) for dt in src.dtypes],
                    'nodata': src.nodata
                }
                # Try to read a small sample to get basic stats
                if src.count >= 1:
                    # Read a small window (e.g., 100x100 or full if smaller)
                    win_width = min(100, src.width)
                    win_height = min(100, src.height)
                    data = src.read(1, window=rasterio.windows.Window(0, 0, win_width, win_height))
                    valid = data[~np.isnan(data)] if src.nodata is None else data[data != src.nodata]
                    if valid.size > 0:
                        info['sample_min'] = float(np.min(valid))
                        info['sample_max'] = float(np.max(valid))
                        info['sample_mean'] = float(np.mean(valid))
                return info
        elif filepath.suffix.lower() == '.csv':
            df = pd.read_csv(filepath)
            info = {
                'type': 'csv',
                'rows': len(df),
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            # If there are latitude/longitude columns, compute extent
            lat_cols = [c for c in df.columns if 'lat' in c.lower()]
            lon_cols = [c for c in df.columns if 'lon' in c.lower()]
            if lat_cols and lon_cols:
                lat_col = lat_cols[0]
                lon_col = lon_cols[0]
                # Ensure numeric
                df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
                df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
                valid = df.dropna(subset=[lat_col, lon_col])
                if len(valid) > 0:
                    info['bbox'] = [
                        valid[lon_col].min(),  # minx
                        valid[lat_col].min(),  # miny
                        valid[lon_col].max(),  # maxx
                        valid[lat_col].max()   # maxy
                    ]
            return info
        elif filepath.suffix.lower() == '.geojson' or filepath.suffix.lower() == '.json':
            if filepath.suffix.lower() == '.geojson':
                gdf = gpd.read_file(filepath)
                info = {
                    'type': 'vector',
                    'crs': str(gdf.crs),
                    'rows': len(gdf),
                    'geometry_type': gdf.geometry.type.iloc[0] if len(gdf) > 0 else None,
                    'columns': list(gdf.columns.drop('geometry', errors='ignore')),
                }
                if len(gdf) > 0:
                    info['bbox'] = list(gdf.total_bounds)  # [minx, miny, maxx, maxy]
                return info
            else:
                with open(filepath) as jf:
                    data = json.load(jf)
                info = {
                    'type': 'json',
                    'keys': list(data.keys()) if isinstance(data, dict) else 'list',
                    'length': len(data) if isinstance(data, list) else None
                }
                return info
        else:
            # Generic file
            return {'type': 'other', 'size': filepath.stat().st_size}
    except Exception as e:
        return {'error': str(e)}

def check_crs_compatibility(datasets, target_crs='EPSG:4326'):
    """Check CRS compatibility and suggest integration CRS."""
    crs_info = {}
    for ds_id, ds_info in datasets.items():
        if 'crs' in ds_info and 'error' not in ds_info:
            crs_info[ds_id] = {
                'original_crs': ds_info['crs'],
                'integration_crs': target_crs if ds_info['crs'] != target_crs else target_crs,
                'needs_reprojection': ds_info['crs'] != target_crs
            }
        else:
            crs_info[ds_id] = {
                'original_crs': None,
                'integration_crs': None,
                'needs_reprojection': False
            }
    return crs_info

def check_spatial_overlap(datasets):
    """Check spatial overlap of datasets that have bounding boxes."""
    # We'll compute the intersection of all bboxes
    bboxes = {}
    for ds_id, ds_info in datasets.items():
        if 'bbox' in ds_info and 'error' not in ds_info:
            bboxes[ds_id] = ds_info['bbox']  # [minx, miny, maxx, maxy]
    if len(bboxes) < 2:
        return {'overlap': 'insufficient_data', 'message': 'Need at least two datasets with bounding boxes'}
    # Compute intersection
    minx = max(bbox[0] for bbox in bboxes.values())
    miny = max(bbox[1] for bbox in bboxes.values())
    maxx = min(bbox[2] for bbox in bboxes.values())
    maxy = min(bbox[3] for bbox in bboxes.values())
    if minx < maxx and miny < maxy:
        overlap_area = (maxx - minx) * (maxy - miny)
        return {
            'overlap': 'YES',
            'intersection_bbox': [minx, miny, maxx, maxy],
            'intersection_area': overlap_area
        }
    else:
        return {
            'overlap': 'NO',
            'message': 'No spatial overlap'
        }

def generate_dataset_registry(datasets, crs_info, output_path):
    """Generate a JSON dataset registry."""
    registry = {
        'generated_at': datetime.now().isoformat(),
        'datasets': []
    }
    for ds_id, ds_info in datasets.items():
        if 'error' in ds_info:
            continue  # skip datasets with errors
        entry = {
            'dataset_id': ds_id,
            'module': ds_info.get('module', 'unknown'),
            'purpose': ds_info.get('purpose', 'unknown'),
            'path': ds_info.get('path', 'unknown'),
            'format': ds_info.get('type', 'unknown'),
            'original_crs': ds_info.get('crs', 'unknown'),
            'integration_crs': crs_info.get(ds_id, {}).get('integration_crs', 'unknown'),
            'status': ds_info.get('status', 'unknown')
        }
        registry['datasets'].append(entry)
    with open(output_path, 'w') as f:
        json.dump(registry, f, indent=2)

def generate_integration_manifest(datasets, crs_info, overlap_info, output_path):
    """Generate a CSV integration manifest."""
    rows = []
    for ds_id, ds_info in datasets.items():
        if 'error' in ds_info:
            continue
        row = {
            'dataset_id': ds_id,
            'module': ds_info.get('module', 'unknown'),
            'dataset_name': ds_info.get('purpose', 'unknown'),
            'file_path': ds_info.get('path', 'unknown'),
            'file_format': ds_info.get('type', 'unknown'),
            'crs': ds_info.get('crs', 'unknown'),
            'integration_crs': crs_info.get(ds_id, {}).get('integration_crs', 'unknown'),
            'spatial': 'yes' if ds_info.get('type') in ['raster', 'vector'] else 'no',
            'record_count': ds_info.get('rows', ds_info.get('count', 'N/A')),
            'min_x': ds_info.get('bbox', [None, None, None, None])[0] if 'bbox' in ds_info else None,
            'max_x': ds_info.get('bbox', [None, None, None, None])[2] if 'bbox' in ds_info else None,
            'min_y': ds_info.get('bbox', [None, None, None, None])[1] if 'bbox' in ds_info else None,
            'max_y': ds_info.get('bbox', [None, None, None, None])[3] if 'bbox' in ds_info else None,
            'status': ds_info.get('status', 'unknown'),
            'notes': ds_info.get('warning', '')
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

def generate_integration_report(m2a_info, m2b_info, m2c_info, crs_info, overlap_info, registry_path, manifest_path, output_path):
    """Generate a human-readable integration report."""
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("M2 PHASE 4 — DATA INTEGRATION REPORT")
    report_lines.append("=" * 70)
    report_lines.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # M2-A status
    report_lines.append("M2-A STATUS:")
    if m2a_info:
        # Flatten the m2a_info to show datasets
        for ds_name, ds_info in m2a_info.items():
            if 'error' in ds_info:
                report_lines.append(f"  {ds_name}: ERROR - {ds_info['error']}")
            else:
                report_lines.append(f"  {ds_name}:")
                report_lines.append(f"    Type: {ds_info.get('type', 'unknown')}")
                report_lines.append(f"    CRS: {ds_info.get('crs', 'unknown')}")
                if 'bbox' in ds_info:
                    report_lines.append(f"    Bounding box: {ds_info['bbox']}")
                report_lines.append(f"    Status: {ds_info.get('status', 'unknown')}")
    else:
        report_lines.append("  No M2-A data found.")
    report_lines.append("")

    # M2-B status
    report_lines.append("M2-B STATUS:")
    if m2b_info:
        for ds_name, ds_info in m2b_info.items():
            if 'error' in ds_info:
                report_lines.append(f"  {ds_name}: ERROR - {ds_info['error']}")
            else:
                report_lines.append(f"  {ds_name}:")
                report_lines.append(f"    Type: {ds_info.get('type', 'unknown')}")
                report_lines.append(f"    CRS: {ds_info.get('crs', 'unknown')}")
                if 'bbox' in ds_info:
                    report_lines.append(f"    Bounding box: {ds_info['bbox']}")
                report_lines.append(f"    Status: {ds_info.get('status', 'unknown')}")
    else:
        report_lines.append("  No M2-B data found.")
    report_lines.append("")

    # M2-C status
    report_lines.append("M2-C STATUS:")
    if m2c_info:
        for ds_name, ds_info in m2c_info.items():
            if 'error' in ds_info:
                report_lines.append(f"  {ds_name}: ERROR - {ds_info['error']}")
            else:
                report_lines.append(f"  {ds_name}:")
                report_lines.append(f"    Type: {ds_info.get('type', 'unknown')}")
                report_lines.append(f"    CRS: {ds_info.get('crs', 'unknown')}")
                report_lines.append(f"    Rows: {ds_info.get('rows', 'unknown')}")
                if 'bbox' in ds_info:
                    report_lines.append(f"    Bounding box: {ds_info['bbox']}")
                report_lines.append(f"    Status: {ds_info.get('status', 'unknown')}")
    else:
        report_lines.append("  No M2-C data found.")
    report_lines.append("")

    # Dataset inventory (from registry)
    report_lines.append("DATASET INVENTORY:")
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
        for ds in registry.get('datasets', []):
            report_lines.append(f"  {ds['dataset_id']} ({ds['module']}): {ds['purpose']}")
            report_lines.append(f"    Path: {ds['path']}")
            report_lines.append(f"    Format: {ds['format']}")
            report_lines.append(f"    Original CRS: {ds['original_crs']}")
            report_lines.append(f"    Integration CRS: {ds['integration_crs']}")
            report_lines.append(f"    Status: {ds['status']}")
    report_lines.append("")

    # CRS check
    report_lines.append("CRS CHECK:")
    for ds_id, info in crs_info.items():
        report_lines.append(f"  {ds_id}:")
        report_lines.append(f"    Original CRS: {info['original_crs']}")
        report_lines.append(f"    Integration CRS: {info['integration_crs']}")
        report_lines.append(f"    Needs reprojection: {info['needs_reprojection']}")
    report_lines.append("")

    # Spatial extent check
    report_lines.append("SPATIAL EXTENT CHECK:")
    if overlap_info.get('overlap') == 'YES':
        report_lines.append(f"  Spatial overlap: YES")
        report_lines.append(f"  Intersection bounding box: {overlap_info['intersection_bbox']}")
        report_lines.append(f"  Intersection area: {overlap_info['intersection_area']:.2f} square units")
    elif overlap_info.get('overlap') == 'NO':
        report_lines.append(f"  Spatial overlap: NO")
        report_lines.append(f"  Reason: {overlap_info.get('message', 'Unknown')}")
    else:
        report_lines.append(f"  Spatial overlap: {overlap_info.get('overlap', 'unknown')}")
        report_lines.append(f"  Reason: {overlap_info.get('message', 'Unknown')}")
    report_lines.append("")

    # Integration status
    # Determine overall status
    has_error = False
    for ds_dict in [m2a_info, m2b_info, m2c_info]:
        if ds_dict:
            for ds_info in ds_dict.values():
                if 'error' in ds_info:
                    has_error = True
    if has_error:
        integration_status = "BLOCKED"
    elif overlap_info.get('overlap') == 'NO':
        integration_status = "REVIEW_REQUIRED"
    else:
        integration_status = "READY"

    report_lines.append("INTEGRATION STATUS:")
    report_lines.append(f"  Status: {integration_status}")
    report_lines.append("")

    report_lines.append("=" * 70)
    report_lines.append("NOTE: This report summarizes the inspection of M2-A, M2-B, and M2-C datasets.")
    report_lines.append("It does not perform any data modification or spatial joins.")
    report_lines.append("The original data remains unchanged.")
    report_lines.append("=" * 70)

    report_text = "\n".join(report_lines)
    print(report_text)

    # Save report to file
    with open(output_path, 'w') as f:
        f.write(report_text)
    print(f"\nIntegration report saved to: {output_path}")

def main():
    print("Starting M2-C Phase 4: Data Integration")

    # Base directory for M2-C
    base_dir = Path(__file__).parent.parent.parent

    # Define paths to the integrated data directories
    m2a_dir = base_dir / 'phase1_historical_data' / 'data' / 'integrated' / 'm2a'
    m2b_dir = base_dir / 'phase1_historical_data' / 'data' / 'integrated' / 'm2b'
    m2c_dir = base_dir / 'phase1_historical_data' / 'data' / 'gis'  # M2-C GeoJSON is here

    # Collect all candidate files
    datasets = {}

    # Inspect M2-A directory
    if m2a_dir.exists():
        for f in m2a_dir.rglob('*'):
            if f.is_file():
                rel_path = f.relative_to(m2a_dir)
                ds_id = f"M2A_{rel_path.as_posix().replace('/', '_').replace('.', '_')}"
                # Try to get metadata from accompanying JSON if exists
                meta_path = f.with_suffix('.json')
                module = 'M2-A'
                purpose = 'unknown'
                status = 'unknown'
                if meta_path.exists():
                    try:
                        with open(meta_path) as mf:
                            meta = json.load(mf)
                            module = meta.get('module', 'M2-A')
                            purpose = meta.get('purpose', 'unknown')
                            status = meta.get('status', 'unknown')
                    except:
                        pass
                info = inspect_dataset(f)
                info.update({
                    'module': module,
                    'purpose': purpose,
                    'path': str(f),
                    'status': status
                })
                datasets[ds_id] = info

    # Inspect M2-B directory
    if m2b_dir.exists():
        for f in m2b_dir.rglob('*'):
            if f.is_file():
                rel_path = f.relative_to(m2b_dir)
                ds_id = f"M2B_{rel_path.as_posix().replace('/', '_').replace('.', '_')}"
                meta_path = f.with_suffix('.json')
                module = 'M2-B'
                purpose = 'unknown'
                status = 'unknown'
                if meta_path.exists():
                    try:
                        with open(meta_path) as mf:
                            meta = json.load(mf)
                            module = meta.get('module', 'M2-B')
                            purpose = meta.get('purpose', 'unknown')
                            status = meta.get('status', 'unknown')
                    except:
                        pass
                info = inspect_dataset(f)
                info.update({
                    'module': module,
                    'purpose': purpose,
                    'path': str(f),
                    'status': status
                })
                datasets[ds_id] = info

    # Inspect M2-C GeoJSON (historical landslides)
    m2c_geojson = m2c_dir / 'historical_landslides.geojson'
    if m2c_geojson.exists():
        ds_id = "M2C_HISTORICAL_LANDSLIDES_GEOJSON"
        # Try to get metadata from any accompanying files? We'll just use defaults.
        info = inspect_dataset(m2c_geojson)
        info.update({
            'module': 'M2-C',
            'purpose': 'Historical landslide locations',
            'path': str(m2c_geojson),
            'status': 'unknown'
        })
        datasets[ds_id] = info

    # Also include the cleaned CSV? Might be useful but not required for integration.
    # We'll skip it for now to keep focus on the GIS layer.

    # If no datasets found, create some placeholder? But we already created demo data.

    # Check CRS compatibility (assuming target EPSG:4326)
    crs_info = check_crs_compatibility(datasets, target_crs='EPSG:4326')

    # Check spatial overlap
    overlap_info = check_spatial_overlap(datasets)

    # Output directories
    integrated_dir = base_dir / 'phase1_historical_data' / 'data' / 'integrated'
    metadata_dir = integrated_dir / 'integration_metadata'
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Generate dataset registry (JSON)
    registry_path = metadata_dir / 'dataset_registry.json'
    generate_dataset_registry(datasets, crs_info, registry_path)

    # Generate integration manifest (CSV)
    manifest_path = metadata_dir / 'integration_manifest.csv'
    generate_integration_manifest(datasets, crs_info, overlap_info, manifest_path)

    # Generate integration report
    report_path = base_dir / 'phase1_historical_data' / 'output' / 'integration_report.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_integration_report(
        {k: v for k, v in datasets.items() if k.startswith('M2A_')},
        {k: v for k, v in datasets.items() if k.startswith('M2B_')},
        {k: v for k, v in datasets.items() if k.startswith('M2C_')},
        crs_info,
        overlap_info,
        registry_path,
        manifest_path,
        report_path
    )

    print("\nIntegration process completed.")

if __name__ == '__main__':
    main()