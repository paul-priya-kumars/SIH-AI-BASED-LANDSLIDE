# M2-A: Satellite & NDVI Engineer
**Component**: GeoShield AI Early Warning & Landslide Risk Prediction System  
**Role**: Satellite Data Ingestion, Atmospheric/Cloud Correction, and NDVI Vegetation Dynamics  

---

## Architecture Context

GeoShield AI integrates spatial and environmental hazard telemetry across three specialized GIS pipelines:
- **M2-A (This Module)**: Satellite data acquisition (Sentinel-2 MSI Level-2A) & NDVI surface reflectance calculation.
- **M2-B (Terrain & Elevation)**: DEM processing, slope steepness, aspect, and curvature matrices.
- **M2-C (Hydrometeorology)**: Precipitation radar, AWS weather stations, and soil moisture assimilation.

---

## Phase Status

### Completed: Phase 1 — Study Area / Area of Interest (AOI) Setup
- [x] Defined standardized Area of Interest for the **Nilgiris Landslide Risk Corridor (Western Ghats)**.
- [x] Standard geographic CRS: **EPSG:4326 (WGS 84)**.
- [x] Canonical GeoJSON specification conforming to RFC 7946 stored at `phase1_aoi/study_area.geojson`.
- [x] Single source of truth configuration in `phase1_aoi/config.py`.
- [x] Multi-layer validation suite (`phase1_aoi/validate_aoi.py`) verifying geometry, CRS, coordinate ranges, and GeoPandas loadability.
- [x] Programmatic Python API for downstream consumers (`phase1_aoi/__init__.py`).
- [x] Automated test suite (`tests/test_aoi.py`).

### Completed: Phase 2 — Sentinel-2 Ingestion & NDVI Calculation Engine
- [x] **Dynamic STAC Client** (`phase2_sentinel_ndvi/stac_client.py`): Queries Element84 Earth Search using the Phase 1 AOI polygon geometry and cloud cover criteria (<20%). Does not hardcode tile IDs; discovers `43PGN`, `43PFN`, etc. dynamically.
- [x] **Safe NDVI Processor** (`phase2_sentinel_ndvi/ndvi_processor.py`): Vectorized `(B08 - B04)/(B08 + B04)` float32 math with zero-denominator protection.
- [x] **Strict SCL Cloud/Shadow Masking**: Classes `[0, 1, 3, 8, 9, 10, 11]` are converted to `np.nan` and written as `NoData (-9999.0)`. Never converted to 0.0.
- [x] **Reprojection Engine** (`phase2_sentinel_ndvi/reprojection.py`): Formal `rasterio.warp.reproject` from native Sentinel-2 UTM Zone 43N to `EPSG:4326` with bilinear resampling, followed by exact Phase 1 AOI polygon boundary masking.
- [x] **GeoTIFF Exporter** (`phase2_sentinel_ndvi/export_geotiff.py`): Outputs float32 single-band GeoTIFF with affine transform, CRS metadata, and JSON sidecar.
- [x] **Pre-computed Spot Sampler** (`phase2_sentinel_ndvi/spot_sampler.py`): `get_spot_ndvi(lat, lon)` queries the cached raster with AOI validation and NoData handling for M3 integration.
- [x] **Mock Demarcation** (`phase2_sentinel_ndvi/synthetic_fixture.py`): Synthetic test data is unambiguously tagged with `is_mock=True` and `DATA_SOURCE="SYNTHETIC_OFFLINE_TEST_FIXTURE"`.
- [x] **Automated Test Suite** (`tests/test_phase2_ndvi.py`): 12 automated unit and integration tests (22 tests total in repo).

---

## Quickstart

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Phase 1: Generate and Validate AOI
```powershell
python -m phase1_aoi.create_aoi
python -m phase1_aoi.validate_aoi
```

### 3. Phase 2: Run Satellite Pipeline & Spot Sampler Demo
```powershell
python -m phase2_sentinel_ndvi.run_pipeline
```

### 4. Run Full Test Suite (Phase 1 & Phase 2)
```powershell
pytest -v tests/
```

### 5. Python API Examples

#### Spot NDVI Coordinate Sampling (for M3 / FastAPI)
```python
from phase2_sentinel_ndvi import get_spot_ndvi

# Query point inside study area (e.g. Ooty central catchment)
spot = get_spot_ndvi(latitude=11.4102, longitude=76.6950)
print(spot)
# {
#   "is_valid": True,
#   "is_nodata": False,
#   "latitude": 11.4102,
#   "longitude": 76.695,
#   "ndvi": 0.2934,
#   "vegetation_class": "SPARSE_OR_DEGRADED",
#   "is_mock": True,
#   "scene_id": "MOCK-SYNTHETIC-FIXTURE-S2"
# }
```

#### Dynamic STAC Satellite Query
```python
from phase2_sentinel_ndvi import query_sentinel2_scenes

# Query scenes intersecting Nilgiris AOI with cloud cover < 20%
scenes = query_sentinel2_scenes(max_cloud_cover=20.0, limit=5)
for s in scenes:
    print(f"Scene: {s.scene_id} | Tile: {s.mgrs_tile} | Date: {s.datetime} | Cloud: {s.cloud_cover_pct}%")
```
