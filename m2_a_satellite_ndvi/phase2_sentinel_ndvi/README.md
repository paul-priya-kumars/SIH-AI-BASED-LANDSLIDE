# Phase 2 — Sentinel-2 Satellite Ingestion & NDVI Calculation Engine
**Module**: M2-A: Satellite & NDVI Engineer  
**System**: GeoShield AI — Landslide Risk Prediction System  
**CRS**: `EPSG:4326 (WGS 84)` (Reprojected from native Sentinel-2 UTM Zone 43N)  
**Sensors**: Copernicus Sentinel-2A / Sentinel-2B MSI (Level-2A Bottom-Of-Atmosphere)  

---

## 1. Overview & Data Flow

```
   [Phase 1 AOI: Nilgiris GeoJSON]
                 │
                 ▼
 ┌──────────────────────────────────┐
 │  Dynamic STAC Query              │ ◄── Element84 Earth Search STAC API
 │  (Spatial Intersect + Cloud <20%)│     (Dynamic Scene & Tile Discovery)
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  Band Ingestion (Native UTM)     │ ◄── Band 4 (Red 665nm, 10m)
 │  & SCL Atmospheric Filtering     │ ◄── Band 8 (NIR 842nm, 10m)
 └─────────────────┬────────────────┘ ◄── SCL (Scene Classification Layer)
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  NDVI Math Engine                │
 │  (NIR - Red) / (NIR + Red)       │ ◄── Safe zero-denominator mask
 │  Cloud/Shadow -> NaN (NOT 0.0)   │
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  Reprojection & AOI Clipping     │
 │  rasterio.warp (UTM -> EPSG:4326)│ ◄── Bilinear resampling
 │  rasterio.mask (Exact AOI Poly)  │
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  GeoTIFF Exporter & Sidecar JSON │ ──► data/ndvi/latest_ndvi_epsg4326.tif
 │  (Float32, NoData: -9999.0, Tags)│ ──► data/ndvi/latest_ndvi_metadata.json
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  Pre-computed Spot Sampler       │
 │  get_spot_ndvi(lat, lon)         │ ──► M3 FastAPI /api/environment
 └──────────────────────────────────┘
```

---

## 2. Dynamic STAC Querying (No Hard-Coded Tiles)

Scenes are queried dynamically via the Element84 Earth Search STAC catalog using the Phase 1 Nilgiris AOI boundary geometry:

```python
from phase2_sentinel_ndvi import query_sentinel2_scenes

# Dynamically discovers matching scenes intersecting the Nilgiris AOI
scenes = query_sentinel2_scenes(max_cloud_cover=20.0, limit=5)
for s in scenes:
    print(f"Scene: {s.scene_id}, Date: {s.datetime}, Cloud: {s.cloud_cover_pct}%, MGRS: {s.mgrs_tile}")
```

---

## 3. SCL Cloud & Shadow Masking Specification

The Copernicus Scene Classification Layer (SCL) classifies pixels into 12 discrete categories. In this pipeline, cloud, cloud-shadow, and defective pixels are strictly masked:

| SCL Value | Classification | Action | Rationale |
|---|---|---|---|
| `0` | `NO_DATA` | **MASKED** | Missing sensor observations |
| `1` | `SATURATED_OR_DEFECTIVE` | **MASKED** | Sensor saturation artifact |
| `2` | `DARK_AREA_PIXELS` | Kept | Topographic cast shadow (valid ground) |
| `3` | `CLOUD_SHADOWS` | **MASKED** | Suppressed reflectance distorts vegetation indices |
| `4` | `VEGETATION` | Kept | Target vegetation |
| `5` | `NOT_VEGETATED` | Kept | Bare ground, rock, soil |
| `6` | `WATER` | Kept | Valid hydrological detection (negative NDVI) |
| `7` | `UNCLASSIFIED` | Kept | Evaluated with valid reflectance |
| `8` | `CLOUD_MEDIUM_PROBABILITY`| **MASKED** | Atmospheric interference |
| `9` | `CLOUD_HIGH_PROBABILITY`  | **MASKED** | Full cloud cover |
| `10` | `THIN_CIRRUS`            | **MASKED** | Atmospheric diffuse scattering |
| `11` | `SNOW_ICE`               | **MASKED** | High reflectance artifact |

> [!IMPORTANT]
> **NoData Representation**: Masked pixels are converted to `np.nan` during float32 computation and written to the raster with explicit `NoData = -9999.0`. **Masked pixels are NEVER converted to 0.0**, because an NDVI of 0.0 corresponds to bare soil/rock transition.

---

## 4. Safe NDVI Numerical Calculation

$$\text{NDVI} = \frac{\text{B08} - \text{B04}}{\text{B08} + \text{B04}}$$

- **Zero-Denominator Protection**: If `(B08 + B04) <= 1e-6` or either band contains non-finite values, the pixel is marked invalid and assigned `np.nan`.
- **Dynamic Clamping**: Mathematically valid values are strictly constrained to $[-1.0, 1.0]$.
- **Data Type**: Single-precision `float32`.

### Susceptibility Classification Bins

| Category | NDVI Range | Landscape Type | Landslide Susceptibility Impact |
|---|---|---|---|
| **`WATER_OR_BARREN`** | `< 0.10` | Water bodies, bare rock outcrops | Variable / High scarp rockfall risk |
| **`SPARSE_OR_DEGRADED`**| `0.10 - 0.30` | Degraded tea slopes, cut-banks | **HIGH VULNERABILITY** (lack of root anchoring) |
| **`MODERATE_VEGETATION`**| `0.30 - 0.50` | Shrubland, tea gardens | Moderate stability |
| **`DENSE_CANOPY`** | `> 0.50` | Primary montane Shola forest | **HIGH STABILITY** (deep root tensile strength) |

---

## 5. UTM to EPSG:4326 Reprojection & Polygon Clipping

1. Native Sentinel-2 tiles are projected in **UTM Zone 43N (EPSG:32643)** in meters.
2. The pipeline computes the target transform and grid in **EPSG:4326 (WGS 84)** using `rasterio.warp.calculate_default_transform`.
3. Warps the array using `rasterio.warp.reproject` with bilinear resampling.
4. Clips the warped raster against the exact Phase 1 Nilgiris AOI polygon (`phase1_aoi/study_area.geojson`) using `rasterio.features.geometry_mask`.
5. Pixels outside the polygon perimeter are set to `NoData (-9999.0)`.

---

## 6. Spot Sampler (`get_spot_ndvi`)

High-performance coordinate sampler designed for the M3 platform:

```python
from phase2_sentinel_ndvi import get_spot_ndvi

# 1. Query point inside study area (e.g. Ooty central basin)
res = get_spot_ndvi(latitude=11.4102, longitude=76.6950)
print(res)
# Output:
# {
#   "is_valid": True,
#   "is_nodata": False,
#   "latitude": 11.4102,
#   "longitude": 76.695,
#   "ndvi": 0.4852,
#   "vegetation_class": "MODERATE_VEGETATION",
#   "is_mock": False,
#   "data_source": "SENTINEL_2_L2A",
#   "scene_id": "S2A_43PGN_20260519_0_L2A",
#   "acquisition_date": "2026-05-19T05:26:04Z"
# }

# 2. Query point outside AOI
res_out = get_spot_ndvi(latitude=13.0827, longitude=80.2707)
print(res_out)
# Output: {"is_valid": False, "error": "Coordinate ... outside study area"}
```

---

## 7. Real Data vs. Mock/Fallback Policy

- Live satellite data queries always set `is_mock = False` and embed real scene IDs.
- For offline tests, CI/CD, and air-gapped demo runs, `phase2_sentinel_ndvi/synthetic_fixture.py` creates a deterministic fixture with `IS_MOCK = "TRUE"`, `DATA_SOURCE = "SYNTHETIC_OFFLINE_TEST_FIXTURE"`, and `SCENE_ID = "MOCK-SYNTHETIC-FIXTURE-S2"`.
- Production workflows can pass `require_real=True` to `get_spot_ndvi()` to strictly forbid mock data.
