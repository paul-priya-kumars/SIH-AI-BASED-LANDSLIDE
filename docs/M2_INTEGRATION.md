# M2 Integration Contract — GIS, Terrain & Spatial Data

This document defines the formal integration boundary between **M3 (Full-Stack Platform)** and **M2 (GIS & Spatial Data Team)** for the **AI Landslide Monitoring and Early Warning System**.

---

## 1. Responsibilities Breakdown

- **M3 (Full-Stack Platform)**:
  - Renders the interactive Leaflet map, layer controls, hazard polygons, markers, and popups.
  - Exposes `GET /api/environment` and `GET /api/risk-zones`.
  - Consumes GeoJSON polygon boundaries and coordinates to display on client screens.

- **M2 (GIS / Spatial Data Team)**:
  - Prepares spatial rasters: Digital Elevation Model (DEM), Slope gradients, Aspect, Curvature.
  - Integrates meteorological data pipelines (radar precipitation, IMD / automatic weather stations).
  - Supplies vegetation index (Sentinel-2 NDVI rasters).
  - Generates GeoJSON hazard polygons and susceptibility zonation boundaries.
  - Implements the real data retrieval in `backend/app/services/environment_service.py` and feeds the database `risk_zones` table.

---

## 2. API Contract Specification

### Endpoint 1: `GET /api/environment?latitude={lat}&longitude={lon}`

Retrieves spot environmental variables for a given coordinate.

#### Response Schema: `EnvironmentDataResponse`
```json
{
  "latitude": 11.4102,
  "longitude": 76.6950,
  "location_name": "Ooty Catchment",
  "rainfall": 145.0,
  "temperature": 16.5,
  "humidity": 89.0,
  "slope": 37.0,
  "elevation": 2240.0,
  "ndvi": 0.43,
  "soil_saturation_pct": 86.0,
  "is_mock": false
}
```

| Field | Unit | Description | Source Pipeline (M2) |
|---|---|---|---|
| `rainfall` | mm (24h) | Cumulative 24-hour rainfall | Weather Radar / AWS network |
| `temperature` | °C | Ambient surface temperature | Automated Weather Stations |
| `humidity` | % | Relative humidity | Surface hygrometers |
| `slope` | Degrees (°) | Terrain steepness gradient | SRTM / ALOS PALSAR DEM |
| `elevation` | Meters (m) | Altitude above mean sea level | DEM elevation raster |
| `ndvi` | Index (-1 to 1) | Vegetation density index | Sentinel-2 / Landsat 8-9 |
| `soil_saturation_pct` | % | Volumetric soil water content | Soil moisture sensors / SMAP |

---

### Endpoint 2: `GET /api/risk-zones`

Returns spatial hazard zones for Leaflet map display.

#### Response Schema: `List[RiskZoneResponse]`
```json
[
  {
    "id": 1,
    "zone_id": "ZONE-OOTY-CENTRAL",
    "name": "Ooty Urban Valley Slope",
    "risk_level": "VERY_HIGH",
    "risk_probability": 0.82,
    "latitude": 11.4102,
    "longitude": 76.6950,
    "radius_meters": 1800.0,
    "polygon_geojson": "{\"type\":\"Polygon\",\"coordinates\":[[[76.685,11.400],[76.705,11.400],[76.705,11.420],[76.685,11.420],[76.685,11.400]]]}",
    "rainfall_mm": 145.0,
    "slope_deg": 37.0,
    "elevation_m": 2240.0,
    "soil_type": "Colluvial clay with weathered gneiss",
    "updated_at": "2026-09-10T10:30:00"
  }
]
```

---

## 3. How M2 Connects Code in Phase 2

1. **Raster Point Sampling**:
   - Open `backend/app/services/environment_service.py`.
   - Use rasterio / GDAL to sample DEM slopes and precipitation GeoTIFFs at given `(latitude, longitude)`.
   
2. **Dynamic Hazard Boundaries**:
   - Store generated polygon shapes in the `risk_zones` table using standard GeoJSON text format.
   - When migrating to PostgreSQL in Phase 2, `polygon_geojson` can transition to a PostGIS `GEOMETRY(Polygon, 4326)` column with zero changes to frontend Leaflet components.
