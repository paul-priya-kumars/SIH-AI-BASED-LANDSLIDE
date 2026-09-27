# Landslide Monitoring & Early Warning System — REST API Reference

Interactive Swagger UI is available when the backend server is running at:
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Base URL
```
http://localhost:8000/api
```

---

## Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check & service status |
| `GET` | `/risk` | Predicts landslide risk for a given (lat, lon) |
| `GET` | `/risk-zones` | Retrieves all geographical hazard zones for map |
| `GET` | `/environment` | Environmental metrics (rainfall, slope, NDVI, etc.) |
| `GET` | `/alerts` | Active emergency bulletins & warnings |
| `GET` | `/alerts/{alert_id}` | Detailed advisory for a specific alert |
| `POST` | `/reports` | Citizen hazard report submission with photo |
| `GET` | `/reports` | List all submitted citizen reports |
| `GET` | `/reports/{report_id}` | Get report by ID |
| `PATCH`| `/reports/{report_id}/status` | Update processing status (Authority review) |
| `GET` | `/route-risk` | Safety comparison between travel corridors |
| `POST` | `/ml/predict` | M1 Model prediction contract endpoint |

---

## Endpoint Details

### 1. Risk Assessment
`GET /api/risk?latitude={lat}&longitude={lon}`

**Sample Response**:
```json
{
  "latitude": 11.4102,
  "longitude": 76.6950,
  "location_name": "Ooty Valley Escarpment",
  "risk_probability": 0.82,
  "risk_level": "VERY_HIGH",
  "confidence": 0.91,
  "factors": [
    "Saturated colluvial regolith on steep slope",
    "24h cumulative rainfall exceeding 120mm threshold",
    "Historical landslide inventory hotspot"
  ],
  "updated_at": "2026-09-10T10:30:00.000Z",
  "is_mock": true
}
```

---

### 2. Hazard Zones Map Layer
`GET /api/risk-zones`

**Sample Response**:
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

### 3. Citizen Hazard Reporting
`POST /api/reports`

**Request Type**: `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `latitude` | `float` | Yes | Coordinates of hazard |
| `longitude` | `float` | Yes | Coordinates of hazard |
| `hazard_type` | `string` | Yes | Road crack, Rockfall, Landslide, Soil movement, etc. |
| `description` | `string` | Yes | Minimum 5 characters |
| `severity` | `string` | Yes | LOW, MEDIUM, HIGH, CRITICAL |
| `location_name` | `string` | No | Human readable landmark |
| `contact_name` | `string` | No | Optional citizen name |
| `contact_phone` | `string` | No | Optional citizen phone |
| `image` | `file` | No | Image file (JPG, PNG, WEBP, <= 10MB) |

**Sample Response (200 OK)**:
```json
{
  "id": 4,
  "report_id": "LSR-2026-0004",
  "user_id": "citizen-anon",
  "latitude": 11.4125,
  "longitude": 76.6980,
  "location_name": "Ooty - Fern Hill Road",
  "hazard_type": "Road crack",
  "description": "Deep longitudinal fissure observed after rainfall.",
  "severity": "HIGH",
  "image_path": "uploads/a3f2b8...jpg",
  "image_url": "http://localhost:8000/uploads/a3f2b8...jpg",
  "contact_name": "Arun Kumar",
  "contact_phone": "+91 98401 23456",
  "status": "PENDING",
  "created_at": "2026-09-10T11:45:00.000Z",
  "updated_at": "2026-09-10T11:45:00.000Z"
}
```

---

### 4. Route Risk Assessment
`GET /api/route-risk?start=Coonoor&destination=Ooty`

**Sample Response**:
```json
{
  "start_location": "Coonoor",
  "destination": "Ooty",
  "recommended_route": {
    "name": "Route A (Via Valley Ridge Arterial)",
    "risk_level": "LOW",
    "distance_km": 32.4,
    "travel_time_mins": 55,
    "hazard_zones_crossed": ["None - Slopes stabilized with retaining netting"],
    "is_recommended": true,
    "summary_advisory": "Recommended for all vehicle categories.",
    "waypoints": [[11.353, 76.7959], [11.4102, 76.695]]
  },
  "alternative_route": {
    "name": "Route B (Via Old Ghat Cut Pass)",
    "risk_level": "HIGH",
    "distance_km": 28.1,
    "travel_time_mins": 48,
    "hazard_zones_crossed": ["Coonoor Hairpin Hazard Zone"],
    "is_recommended": false,
    "summary_advisory": "Passes through active rockfall warning zones.",
    "waypoints": [[11.353, 76.7959], [11.399, 76.764], [11.4102, 76.695]]
  },
  "overall_advisory": "Route A offers a 75% reduction in hazard exposure.",
  "timestamp": "2026-09-10T11:45:00.000Z",
  "is_mock": true
}
```
