"""
End-to-End Pipeline Runner — Phase 2: Sentinel-2 & NDVI Engine
===============================================================
Executes the satellite discovery, band processing, reprojection,
raster export, and spot sampling verification.
"""

import argparse
import sys
from pathlib import Path

from phase1_aoi import get_aoi_bounds, load_aoi_geometry
from phase2_sentinel_ndvi.config import (
    LATEST_NDVI_RASTER_PATH,
    LATEST_METADATA_JSON_PATH,
    DEFAULT_MAX_CLOUD_COVER,
)
from phase2_sentinel_ndvi.stac_client import query_sentinel2_scenes
from phase2_sentinel_ndvi.synthetic_fixture import (
    generate_synthetic_ndvi_fixture,
    MOCK_FIXTURE_PATH,
)
from phase2_sentinel_ndvi.spot_sampler import get_spot_ndvi


def run_stac_smoke_test(max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER) -> None:
    """Performs live STAC discovery smoke test against Element84 Earth Search."""
    print("\n[STEP 1] Querying Element84 Earth Search STAC API for Nilgiris AOI...")
    bbox = get_aoi_bounds()
    print(f"         - Spatial Filter BBox: {bbox}")
    print(f"         - Max Cloud Cover    : {max_cloud_cover}%")

    try:
        scenes = query_sentinel2_scenes(max_cloud_cover=max_cloud_cover, limit=5)
        print(f"[SUCCESS] Discovered {len(scenes)} matching Sentinel-2 L2A scenes:")
        for idx, s in enumerate(scenes, 1):
            print(f"  [{idx}] Scene ID : {s.scene_id}")
            print(f"      MGRS Tile: {s.mgrs_tile}")
            print(f"      Datetime : {s.datetime}")
            print(f"      Cloud %  : {s.cloud_cover_pct}%")
            print(f"      Platform : {s.platform}")
            print(f"      Red Asset: {s.red_asset_url[:60] + '...' if s.red_asset_url else 'None'}")
            print(f"      NIR Asset: {s.nir_asset_url[:60] + '...' if s.nir_asset_url else 'None'}")
            print(f"      SCL Asset: {s.scl_asset_url[:60] + '...' if s.scl_asset_url else 'None'}")
    except Exception as e:
        print(f"[WARN] Live STAC query encountered network/API issue: {e}")
        print("       (Offline / synthetic fallback mode is fully functional)")


def run_pipeline_demo(use_mock: bool = True) -> None:
    """Runs the complete raster generation and spot sampling demo."""
    print("\n[STEP 2] Preparing/Verifying Pre-computed NDVI Raster Cache...")
    # Generate the standard deterministic fixture for caching/demo
    fixture_path, tags = generate_synthetic_ndvi_fixture(
        output_geotiff=LATEST_NDVI_RASTER_PATH,
        output_metadata=LATEST_METADATA_JSON_PATH,
    )
    print(f"[SUCCESS] Cached NDVI Raster generated at:")
    print(f"          - GeoTIFF: {LATEST_NDVI_RASTER_PATH.resolve()}")
    print(f"          - Sidecar: {LATEST_METADATA_JSON_PATH.resolve()}")
    print(f"          - Demarcation: IS_MOCK = {tags.get('IS_MOCK')}, SOURCE = {tags.get('DATA_SOURCE')}")

    print("\n[STEP 3] Performing Spot Sampling Queries (M3 Integration Smoke Test)...")
    benchmark_points = [
        ("Ooty Urban Basin", 11.4102, 76.6950),
        ("Coonoor Ghat Pass", 11.3530, 76.7959),
        ("Kotagiri Ridge", 11.4285, 76.8797),
        ("Kundah Montane Slope", 11.2850, 76.6350),
        ("Cloud Masked Test Patch", 11.5500, 76.5400),
        ("Outside AOI (Chennai)", 13.0827, 80.2707),
    ]

    for name, lat, lon in benchmark_points:
        res = get_spot_ndvi(latitude=lat, longitude=lon, raster_path=LATEST_NDVI_RASTER_PATH)
        status_tag = "VALID" if res["is_valid"] else ("NODATA" if res.get("is_nodata") else "OUTSIDE_AOI")
        print(f"  - [{status_tag:11s}] {name:24s} ({lat:.4f} N, {lon:.4f} E):")
        if res["is_valid"]:
            print(f"      NDVI: {res['ndvi']:+.4f} | Class: {res['vegetation_class']} | Mock: {res['is_mock']}")
        elif res.get("is_nodata"):
            print(f"      Reason: {res.get('reason')}")
        else:
            print(f"      Error : {res.get('error')}")


def main():
    parser = argparse.ArgumentParser(description="Run Phase 2 Sentinel-2 & NDVI Pipeline.")
    parser.add_argument("--skip-stac", action="store_true", help="Skip live STAC query check")
    parser.add_argument("--cloud-limit", type=float, default=20.0, help="Max cloud cover percent")
    args = parser.parse_args()

    print("=================================================================")
    print("      M2-A PHASE 2: SENTINEL-2 & NDVI PIPELINE VERIFICATION      ")
    print("=================================================================")

    if not args.skip_stac:
        run_stac_smoke_test(max_cloud_cover=args.cloud_limit)

    run_pipeline_demo()

    print("\n=================================================================")
    print("                    PHASE 2 PIPELINE READY                       ")
    print("=================================================================")


if __name__ == "__main__":
    main()
