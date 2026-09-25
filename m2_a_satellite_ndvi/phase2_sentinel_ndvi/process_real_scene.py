"""
Production Real-Data Pipeline — Sentinel-2 L2A Ingestion
=========================================================
Executes end-to-end real satellite data processing:
  1. STAC scene discovery (Element84 Earth Search).
  2. Direct Cloud-Optimized GeoTIFF (COG) streaming for B04, B08, and SCL.
  3. SCL cloud/shadow masking & float32 safe NDVI calculation.
  4. Native UTM (EPSG:32643) to WGS 84 (EPSG:4326) reprojection.
  5. Exact Phase 1 Nilgiris AOI polygon boundary clipping.
  6. Real-data GeoTIFF export (is_mock=False).
  7. Spot telemetry verification via get_spot_ndvi().
"""

import time
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from pyproj import Transformer

from phase1_aoi import get_aoi_bounds, load_aoi_geometry
from phase2_sentinel_ndvi.config import (
    DATA_DIR,
    TARGET_CRS,
    RASTER_NODATA_VALUE,
    DEFAULT_MAX_CLOUD_COVER,
)
from phase2_sentinel_ndvi.stac_client import query_sentinel2_scenes, SentinelSceneMetadata
from phase2_sentinel_ndvi.ndvi_processor import compute_ndvi_array, compute_ndvi_statistics
from phase2_sentinel_ndvi.reprojection import reproject_raster_array, clip_raster_to_aoi_polygon
from phase2_sentinel_ndvi.export_geotiff import export_ndvi_geotiff
from phase2_sentinel_ndvi.spot_sampler import get_spot_ndvi

REAL_NDVI_GEOTIFF = DATA_DIR / "real_s2_ndvi_epsg4326.tif"
REAL_NDVI_METADATA = DATA_DIR / "real_s2_ndvi_metadata.json"


def process_real_sentinel_scene(
    scene: SentinelSceneMetadata,
    output_tif: Path = REAL_NDVI_GEOTIFF,
    output_json: Path = REAL_NDVI_METADATA,
    downsample_factor: int = 2,  # 2x downsample for balanced transfer speed (~20m res)
) -> Tuple[Path, Dict[str, Any]]:
    """
    Downloads/streams actual Sentinel-2 bands, computes real NDVI, reprojects to EPSG:4326,
    clips to Nilgiris AOI polygon, and exports the final GeoTIFF.
    """
    print(f"\n[PIPELINE] Processing Real Scene: {scene.scene_id}")
    print(f"           - Platform    : {scene.platform}")
    print(f"           - Datetime    : {scene.datetime}")
    print(f"           - Cloud Cover : {scene.cloud_cover_pct}%")
    print(f"           - MGRS Tile   : {scene.mgrs_tile}")
    print(f"           - Red URL     : {scene.red_asset_url}")
    print(f"           - NIR URL     : {scene.nir_asset_url}")
    print(f"           - SCL URL     : {scene.scl_asset_url}")

    if not (scene.red_asset_url and scene.nir_asset_url):
        raise ValueError("Selected scene lacks valid Red or NIR asset URLs.")

    # 1. Transform AOI bounds (EPSG:4326) to Scene Native UTM (EPSG:32643)
    minx, miny, maxx, maxy = get_aoi_bounds()
    tf_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    u_minx, u_miny, u_maxx, u_maxy = tf_to_utm.transform_bounds(minx, miny, maxx, maxy)

    t0 = time.time()
    # 2. Open B04 to determine spatial window and native transform
    print("\n[STEP 1] Streaming Red (B04), NIR (B08), and SCL assets via HTTP range requests...")
    with rasterio.open(scene.red_asset_url) as src_red:
        src_crs = src_red.crs
        src_bounds = src_red.bounds

        # Calculate intersection between AOI and scene in UTM
        int_minx = max(u_minx, src_bounds.left)
        int_miny = max(u_miny, src_bounds.bottom)
        int_maxx = min(u_maxx, src_bounds.right)
        int_maxy = min(u_maxy, src_bounds.top)

        if int_minx >= int_maxx or int_miny >= int_maxy:
            raise ValueError("Scene does not spatially intersect the Nilgiris AOI.")

        red_window = from_bounds(int_minx, int_miny, int_maxx, int_maxy, src_red.transform)
        out_h = max(1, int(red_window.height / downsample_factor))
        out_w = max(1, int(red_window.width / downsample_factor))

        # Read B04 (Red)
        red_data = src_red.read(1, window=red_window, out_shape=(out_h, out_w)).astype(np.float32)
        win_transform = rasterio.windows.transform(red_window, src_red.transform)
        sub_transform = win_transform * rasterio.Affine.scale(
            red_window.width / out_w, red_window.height / out_h
        )

    # 3. Read B08 (NIR)
    with rasterio.open(scene.nir_asset_url) as src_nir:
        nir_window = from_bounds(int_minx, int_miny, int_maxx, int_maxy, src_nir.transform)
        nir_data = src_nir.read(1, window=nir_window, out_shape=(out_h, out_w)).astype(np.float32)

    # 4. Read SCL (Scene Classification Layer)
    scl_data = None
    if scene.scl_asset_url:
        try:
            with rasterio.open(scene.scl_asset_url) as src_scl:
                scl_window = from_bounds(int_minx, int_miny, int_maxx, int_maxy, src_scl.transform)
                scl_data = src_scl.read(
                    1,
                    window=scl_window,
                    out_shape=(out_h, out_w),
                    resampling=Resampling.nearest,
                ).astype(np.int32)
                print(f"         - SCL band read successfully: shape {scl_data.shape}")
        except Exception as e:
            print(f"[WARN] Failed to stream SCL band: {e}. Proceeding without SCL mask.")

    read_elapsed = round(time.time() - t0, 2)
    print(f"         - Successfully read arrays in {read_elapsed}s (Shape: {red_data.shape})")

    # 5. Compute NDVI and apply SCL Cloud/Shadow Masking
    print("\n[STEP 2] Computing NDVI and applying SCL cloud/shadow filtering...")
    raw_ndvi = compute_ndvi_array(red=red_data, nir=nir_data, scl=scl_data)

    # 6. Reproject to EPSG:4326 (WGS 84)
    print("\n[STEP 3] Reprojecting native UTM raster to EPSG:4326 (WGS 84)...")
    reprojected_ndvi, dst_transform, bounds_4326 = reproject_raster_array(
        src_data=raw_ndvi,
        src_transform=sub_transform,
        src_crs=src_crs,
        dst_crs=CRS.from_string(TARGET_CRS),
        dst_nodata=RASTER_NODATA_VALUE,
    )
    print(f"         - Reprojected shape: {reprojected_ndvi.shape}")
    print(f"         - Bounds (WGS84)   : {bounds_4326}")

    # 7. Clip to Exact Phase 1 AOI Polygon Boundary
    print("\n[STEP 4] Clipping raster to exact Nilgiris AOI polygon boundary...")
    clipped_ndvi = clip_raster_to_aoi_polygon(
        data=reprojected_ndvi,
        transform=dst_transform,
        nodata_value=RASTER_NODATA_VALUE,
    )

    stats = compute_ndvi_statistics(clipped_ndvi, nodata_value=RASTER_NODATA_VALUE)
    print(f"         - Total Pixels : {stats['total_pixels']}")
    print(f"         - Valid Pixels : {stats['valid_pixels']} ({stats['valid_pct']}%)")
    print(f"         - Mean NDVI    : {stats['mean']}")
    print(f"         - Median NDVI  : {stats['median']}")

    # 8. Export Real GeoTIFF and Metadata Sidecar
    print("\n[STEP 5] Exporting real-data GeoTIFF and sidecar metadata...")
    metadata_tags = {
        "IS_MOCK": "FALSE",
        "DATA_SOURCE": "COPERNICUS_SENTINEL_2_L2A",
        "SCENE_ID": scene.scene_id,
        "ACQUISITION_DATE": scene.datetime,
        "CLOUD_COVER_PCT": str(scene.cloud_cover_pct),
        "MGRS_TILE": scene.mgrs_tile,
        "PLATFORM": scene.platform,
        "RED_ASSET": scene.red_asset_url,
        "NIR_ASSET": scene.nir_asset_url,
        "SCL_ASSET": scene.scl_asset_url or "NONE",
        "DESCRIPTION": "Real Copernicus Sentinel-2 Level-2A NDVI surface reflectance layer.",
    }

    created_path = export_ndvi_geotiff(
        ndvi_array=clipped_ndvi,
        transform=dst_transform,
        output_geotiff_path=output_tif,
        output_metadata_path=output_json,
        crs=CRS.from_string(TARGET_CRS),
        nodata_value=RASTER_NODATA_VALUE,
        metadata_tags=metadata_tags,
        statistics=stats,
    )
    print(f"[SUCCESS] Real-data GeoTIFF generated: {created_path.resolve()}")
    print(f"[SUCCESS] Real-data Metadata JSON:     {output_json.resolve()}")

    return created_path, metadata_tags


def run_real_end_to_end_smoke_test():
    """Runs the end-to-end smoke test using real satellite assets."""
    print("=================================================================")
    print("          M2-A: REAL-DATA SENTINEL-2 END-TO-END SMOKE TEST       ")
    print("=================================================================")

    # 1. Query STAC for scenes intersecting Nilgiris AOI
    scenes = query_sentinel2_scenes(max_cloud_cover=20.0, limit=5)
    if not scenes:
        raise RuntimeError("No Sentinel-2 scenes found intersecting the AOI.")

    # Select the top scene covering the core Ooty/Nilgiris basin (43PFN)
    target_scene = None
    for s in scenes:
        if "43PFN" in s.scene_id:
            target_scene = s
            break
    if not target_scene:
        target_scene = scenes[0]

    # 2. Process real scene through complete production pipeline
    tif_path, tags = process_real_sentinel_scene(target_scene)

    # 3. Test Spot Sampler (require_real=True) on points inside AOI
    print("\n=================================================================")
    print("          SPOT SAMPLER VERIFICATION ON REAL SATELLITE RASTER     ")
    print("=================================================================")

    inside_coords = [
        ("Ooty Central Catchment", 11.4102, 76.6950),
        ("Kundah Hydel Basin", 11.2850, 76.6350),
        ("Gudalur West Ridge", 11.5050, 76.4950),
    ]

    for name, lat, lon in inside_coords:
        res = get_spot_ndvi(
            latitude=lat,
            longitude=lon,
            raster_path=tif_path,
            require_real=True,
        )
        print(f"\n[TEST POINT] {name} ({lat:.4f} N, {lon:.4f} E):")
        print(f"  - is_valid        : {res['is_valid']}")
        print(f"  - is_mock         : {res['is_mock']}")
        print(f"  - data_source     : {res['data_source']}")
        print(f"  - scene_id        : {res['scene_id']}")
        print(f"  - acquisition_date: {res['acquisition_date']}")
        print(f"  - ndvi            : {res['ndvi']}")
        print(f"  - vegetation_class: {res['vegetation_class']}")

        # Strict assertion checks
        assert res["is_mock"] is False, "Expected is_mock == False for real data!"
        assert res["data_source"] == "COPERNICUS_SENTINEL_2_L2A"
        assert res["scene_id"] == target_scene.scene_id

    # 4. Test Coordinate Outside AOI
    outside_lat, outside_lon = 13.0827, 80.2707  # Chennai
    res_outside = get_spot_ndvi(
        latitude=outside_lat,
        longitude=outside_lon,
        raster_path=tif_path,
        require_real=True,
    )
    print(f"\n[TEST POINT OUTSIDE AOI] Chennai ({outside_lat:.4f} N, {outside_lon:.4f} E):")
    print(f"  - is_valid        : {res_outside['is_valid']}")
    print(f"  - error           : {res_outside.get('error')}")
    assert res_outside["is_valid"] is False, "Expected is_valid == False for outside-AOI point!"

    print("\n=================================================================")
    print("      REAL-DATA SENTINEL-2 SMOKE TEST COMPLETED SUCCESSFULLY     ")
    print("=================================================================")


if __name__ == "__main__":
    run_real_end_to_end_smoke_test()
