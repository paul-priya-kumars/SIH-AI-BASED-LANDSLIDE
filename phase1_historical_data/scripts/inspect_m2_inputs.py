import os
import json
from pathlib import Path
import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np

def inspect_m2_a():
    """Inspect M2-A data (satellite imagery + NDVI)."""
    m2a_dir = Path(__file__).parent.parent / 'data' / 'integrated' / 'm2a'
    print(f"Inspecting M2-A directory: {m2a_dir}")
    if not m2a_dir.exists():
        print("  M2-A directory does not exist.")
        return {}

    files = list(m2a_dir.rglob('*'))
    files = [f for f in files if f.is_file()]
    if not files:
        print("  No files found in M2-A directory.")
        return {}

    results = {}
    for f in files:
        rel_path = f.relative_to(m2a_dir)
        print(f"  File: {rel_path}")
        try:
            if f.suffix.lower() in ['.tif', '.tiff']:
                with rasterio.open(f) as src:
                    info = {
                        'type': 'raster',
                        'crs': str(src.crs),
                        'bbox': src.bounds,
                        'width': src.width,
                        'height': src.height,
                        'count': src.count,
                        'dtypes': [str(dt) for dt in src.dtypes],
                        'nodata': src.nodata
                    }
                    # Try to read a small sample to get basic stats
                    if src.count >= 1:
                        data = src.read(1, out_shape=(1, min(100, src.height), min(100, src.width)))
                        valid = data[~np.isnan(data)] if src.nodata is None else data[data != src.nodata]
                        if valid.size > 0:
                            info['sample_min'] = float(np.min(valid))
                            info['sample_max'] = float(np.max(valid))
                            info['sample_mean'] = float(np.mean(valid))
                    results[str(rel_path)] = info
                    print(f"    CRS: {src.crs}")
                    print(f"    Bounds: {src.bounds}")
                    print(f"    Size: {src.width} x {src.height}, Bands: {src.count}")
            elif f.suffix.lower() == '.csv':
                df = pd.read_csv(f)
                info = {
                    'type': 'csv',
                    'rows': len(df),
                    'columns': list(df.columns),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
                }
                results[str(rel_path)] = info
                print(f"    Rows: {len(df)}, Columns: {list(df.columns)}")
            elif f.suffix.lower() == '.geojson' or f.suffix.lower() == '.json':
                if f.suffix.lower() == '.geojson':
                    gdf = gpd.read_file(f)
                    info = {
                        'type': 'vector',
                        'crs': str(gdf.crs),
                        'rows': len(gdf),
                        'geometry_type': gdf.geometry.type.iloc[0] if len(gdf) > 0 else None,
                        'columns': list(gdf.columns.drop('geometry', errors='ignore'))
                    }
                else:
                    with open(f) as jf:
                        data = json.load(jf)
                    info = {
                        'type': 'json',
                        'keys': list(data.keys()) if isinstance(data, dict) else 'list',
                        'length': len(data) if isinstance(data, list) else None
                    }
                results[str(rel_path)] = info
                print(f"    Type: {info['type']}")
                if 'crs' in info:
                    print(f"    CRS: {info['crs']}")
                if 'rows' in info:
                    print(f"    Rows: {info['rows']}")
            else:
                # Generic file
                results[str(rel_path)] = {'type': 'other', 'size': f.stat().st_size}
                print(f"    Size: {f.stat().st_size} bytes")
        except Exception as e:
            print(f"    Error inspecting {f}: {e}")
            results[str(rel_path)] = {'error': str(e)}
    return results

def inspect_m2_b():
    """Inspect M2-B data (rainfall + DEM + Terrain)."""
    m2b_dir = Path(__file__).parent.parent / 'data' / 'integrated' / 'm2b'
    print(f"Inspecting M2-B directory: {m2b_dir}")
    if not m2b_dir.exists():
        print("  M2-B directory does not exist.")
        return {}

    files = list(m2b_dir.rglob('*'))
    files = [f for f in files if f.is_file()]
    if not files:
        print("  No files found in M2-B directory.")
        return {}

    results = {}
    for f in files:
        rel_path = f.relative_to(m2b_dir)
        print(f"  File: {rel_path}")
        try:
            if f.suffix.lower() in ['.tif', '.tiff']:
                with rasterio.open(f) as src:
                    info = {
                        'type': 'raster',
                        'crs': str(src.crs),
                        'bbox': src.bounds,
                        'width': src.width,
                        'height': src.height,
                        'count': src.count,
                        'dtypes': [str(dt) for dt in src.dtypes],
                        'nodata': src.nodata
                    }
                    if src.count >= 1:
                        data = src.read(1, out_shape=(1, min(100, src.height), min(100, src.width)))
                        valid = data[~np.isnan(data)] if src.nodata is None else data[data != src.nodata]
                        if valid.size > 0:
                            info['sample_min'] = float(np.min(valid))
                            info['sample_max'] = float(np.max(valid))
                            info['sample_mean'] = float(np.mean(valid))
                    results[str(rel_path)] = info
                    print(f"    CRS: {src.crs}")
                    print(f"    Bounds: {src.bounds}")
                    print(f"    Size: {src.width} x {src.height}, Bands: {src.count}")
            elif f.suffix.lower() == '.csv':
                df = pd.read_csv(f)
                info = {
                    'type': 'csv',
                    'rows': len(df),
                    'columns': list(df.columns),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
                }
                results[str(rel_path)] = info
                print(f"    Rows: {len(df)}, Columns: {list(df.columns)}")
            elif f.suffix.lower() == '.geojson' or f.suffix.lower() == '.json':
                if f.suffix.lower() == '.geojson':
                    gdf = gpd.read_file(f)
                    info = {
                        'type': 'vector',
                        'crs': str(gdf.crs),
                        'rows': len(gdf),
                        'geometry_type': gdf.geometry.type.iloc[0] if len(gdf) > 0 else None,
                        'columns': list(gdf.columns.drop('geometry', errors='ignore'))
                    }
                else:
                    with open(f) as jf:
                        data = json.load(jf)
                    info = {
                        'type': 'json',
                        'keys': list(data.keys()) if isinstance(data, dict) else 'list',
                        'length': len(data) if isinstance(data, list) else None
                    }
                results[str(rel_path)] = info
                print(f"    Type: {info['type']}")
                if 'crs' in info:
                    print(f"    CRS: {info['crs']}")
                if 'rows' in info:
                    print(f"    Rows: {info['rows']}")
            else:
                results[str(rel_path)] = {'type': 'other', 'size': f.stat().st_size}
                print(f"    Size: {f.stat().st_size} bytes")
        except Exception as e:
            print(f"    Error inspecting {f}: {e}")
            results[str(rel_path)] = {'error': str(e)}
    return results

def inspect_m2_c():
    """Inspect M2-C Phase 3 output (historical landslide GeoJSON)."""
    m2c_geojson = Path(__file__).parent.parent / 'data' / 'gis' / 'historical_landslides.geojson'
    print(f"Inspecting M2-C GeoJSON: {m2c_geojson}")
    if not m2c_geojson.exists():
        print("  M2-C GeoJSON does not exist.")
        return {}

    try:
        gdf = gpd.read_file(m2c_geojson)
        info = {
            'type': 'vector',
            'crs': str(gdf.crs),
            'rows': len(gdf),
            'geometry_type': gdf.geometry.type.iloc[0] if len(gdf) > 0 else None,
            'columns': list(gdf.columns.drop('geometry', errors='ignore')),
            'bbox': gdf.total_bounds.tolist() if len(gdf) > 0 else None
        }
        print(f"  CRS: {gdf.crs}")
        print(f"  Rows: {len(gdf)}")
        print(f"  Geometry type: {gdf.geometry.type.iloc[0] if len(gdf) > 0 else 'None'}")
        print(f"  Columns: {list(gdf.columns.drop('geometry', errors='ignore'))}")
        if len(gdf) > 0:
            print(f"  Bounding box: {gdf.total_bounds}")
        return {'historical_landslides_geojson': info}
    except Exception as e:
        print(f"  Error reading GeoJSON: {e}")
        return {'error': str(e)}

def main():
    print("=" * 60)
    print("M2-A + M2-B + M2-C INPUTS INSPECTION")
    print("=" * 60)

    m2a_info = inspect_m2_a()
    print()
    m2b_info = inspect_m2_b()
    print()
    m2c_info = inspect_m2_c()

    # Save inspection results to a JSON file for record
    output_dir = Path(__file__).parent.parent.parent / 'data' / 'integrated' / 'integration_metadata'
    output_dir.mkdir(parents=True, exist_ok=True)
    inspection_file = output_dir / 'inspection_results.json'
    with open(inspection_file, 'w') as f:
        json.dump({
            'M2-A': m2a_info,
            'M2-B': m2b_info,
            'M2-C': m2c_info
        }, f, indent=2)
    print(f"\nInspection results saved to: {inspection_file}")

if __name__ == '__main__':
    main()