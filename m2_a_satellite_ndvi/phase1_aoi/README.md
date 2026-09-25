# Phase 1 — Study Area / Area of Interest (AOI) Setup
**Module**: M2-A (Satellite & NDVI Engineer)  
**System**: GeoShield AI — Landslide Early Warning & Hazard Zonation  
**Coordinate Reference System**: EPSG:4326 (WGS 84)  
**Standard**: RFC 7946 GeoJSON  

---

## 1. Study Area Overview

| Attribute | Specification |
|---|---|
| **Study Area Name** | Nilgiris Landslide Risk Study Area |
| **Short Identifier** | `AOI-NILGIRIS-01` |
| **Geographic Region** | Nilgiris District, Western Ghats |
| **Administrative Unit** | Tamil Nadu, India |
| **Datum / CRS** | WGS 84 (`EPSG:4326` / `urn:ogc:def:crs:OGC:1.3:CRS84`) |
| **Coordinate Ordering** | `[Longitude, Latitude]` (RFC 7946 compliant) |
| **Surface Area** | ~2,073.45 km² |
| **Center Benchmark** | `76.6950° E, 11.4102° N` (Ooty Urban Catchment) |
| **Target Satellite Sensor**| Copernicus Sentinel-2 MSI (Level-2A Surface Reflectance) |
| **Primary Spectral Bands**| Band 4 (Red — 665 nm, 10m), Band 8 (NIR — 842 nm, 10m) |
| **Data Source** | Survey of India / Western Ghats Geomorphic Basin Inventory |

---

## 2. Spatial Extent & Bounding Coordinates

The study area encompasses the high-altitude Nilgiris plateau and its steep, landslide-prone escarpments and ghat corridors:

```
                  11.6000° N (Mudumalai / Moyar Rim)
                           ▲
                           │
       76.4500° E ◄────────┼────────► 77.0500° E
   (Gudalur Escarpment)    │      (Kotagiri Eastern Ridge)
                           ▼
                  11.2000° N (Kundah / Bhavani Flank)
```

### Detailed Coordinate Bounds

| Cardinal Boundary | Latitude / Longitude | Landmark Description |
|---|---|---|
| **West (`min_lon`)** | `76.4500° E` | Gudalur western ghats escarpment / Wayanad pass |
| **South (`min_lat`)** | `11.2000° N` | Kundah southern hydel basin & Bhavani river transition |
| **East (`max_lon`)** | `77.0500° E` | Kotagiri eastern ridge & Sirumugai valley descent |
| **North (`max_lat`)** | `11.6000° N` | Mudumalai plateau edge & Moyar gorge overlook |

### Key Risk Sub-Catchments Included
1. **Ooty Central Urban Valley** (`11.4102° N, 76.6950° E`): High population density, steep modified cut-slopes.
2. **Coonoor Ghat Corridor** (`11.3530° N, 76.7959° E`): NH-181 mountain pass, frequent debris flow corridors.
3. **Kotagiri Ridge & Slopes** (`11.4285° N, 76.8797° E`): High rainfall intensity tea plantation slopes.
4. **Kundah Hydel Basin** (`11.2850° N, 76.6350° E`): High elevation steep regolith prone to translational slides.
5. **Gudalur Western Escarpment** (`11.5050° N, 76.4950° E`): High monsoon precipitation zone.

---

## 3. Purpose of the AOI

This AOI serves as the canonical geographic boundary for the entire data pipeline:
1. **Sentinel-2 Data Acquisition (Phase 2)**: Direct spatial filtering via STAC API (Earth Search, Microsoft Planetary Computer, or Copernicus Data Space) to query scenes covering tile `T43PGN` / `T43PGP`.
2. **NDVI (Normalized Difference Vegetation Index)**: Precise bounding mask for extracting surface reflectance `(NIR - Red) / (NIR + Red)` at 10-meter spatial resolution.
3. **Multi-Module Spatial Alignment**:
   - **M2-B (DEM & Terrain)**: Clipping SRTM/Copernicus 30m DEM rasters for slope gradient, aspect, and curvature.
   - **M2-C (Rainfall & Hydrology)**: Bounding GPM / IMD automatic weather station interpolation.
   - **M3 (Platform Integration)**: GeoJSON hazard boundaries feeding FastAPI `/api/risk-zones` and Leaflet map rendering.
   - **M1 (AI/ML Modeling)**: Spatial feature grid alignment for landslide probability prediction.

---

## 4. File Structure

```
phase1_aoi/
├── __init__.py           # Reusable Python API (load_aoi_gdf, load_aoi_geometry, get_aoi_bounds)
├── config.py             # Single source of truth for coordinates, CRS, and metadata
├── create_aoi.py         # AOI generator script (computes geodesic area, outputs GeoJSON)
├── validate_aoi.py       # Multi-check validation suite (Shapely, GeoPandas, CRS, bounds)
├── study_area.geojson    # Standard RFC 7946 GeoJSON file
└── README.md             # This documentation
```

---

## 5. Usage & Commands

### Generate the AOI
```powershell
python -m phase1_aoi.create_aoi
```
Or with custom output path:
```powershell
python -m phase1_aoi.create_aoi --output path/to/study_area.geojson
```

### Validate the AOI
```powershell
python -m phase1_aoi.validate_aoi
```

### Programmatic Usage in Python (for Phase 2)
```python
from phase1_aoi import load_aoi_gdf, load_aoi_geometry, get_aoi_bounds, get_aoi_metadata

# 1. Load as GeoPandas GeoDataFrame (CRS: EPSG:4326)
gdf = load_aoi_gdf()
print(gdf.crs)          # EPSG:4326
print(gdf.total_bounds) # [76.45, 11.20, 77.05, 11.60]

# 2. Load as Shapely Polygon (for rasterio masking or STAC spatial queries)
polygon = load_aoi_geometry()
print(f"Area: {polygon.area:.4f} degrees², Centroid: {polygon.centroid}")

# 3. Retrieve bounding box tuple (min_lon, min_lat, max_lon, max_lat)
min_lon, min_lat, max_lon, max_lat = get_aoi_bounds()

# 4. Access canonical metadata dictionary
metadata = get_aoi_metadata()
print(f"Target Sensor: {metadata['target_satellite_sensor']}")
```

---

## 6. Validation Checks Enforced

The validation script `validate_aoi.py` runs 7 critical verification stages:
- [x] **File Integrity**: File exists, non-empty, and parses as valid JSON.
- [x] **GeoJSON Specification**: Matches RFC 7946 `FeatureCollection` schema.
- [x] **Topological Validity**: Shapely `is_valid` is `True`, non-empty, and polygon is closed.
- [x] **Coordinate Range**: All vertices conform to `-180 <= lon <= 180` and `-90 <= lat <= 90`.
- [x] **Coordinate Ordering**: Strictly verifies `[longitude, latitude]` format to prevent inverted lat/lon bugs.
- [x] **Coordinate Reference System**: Explicitly verifies `EPSG:4326`.
- [x] **GIS Library Interoperability**: Successfully loads and computes spatial extents with `geopandas` and `shapely`.
