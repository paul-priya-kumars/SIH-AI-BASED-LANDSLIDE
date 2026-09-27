# M1 Integration Contract — AI & Machine Learning Prediction

This document defines the formal integration boundary between **M3 (Full-Stack Platform)** and **M1 (AI/ML Prediction Team)** for the **AI Landslide Monitoring and Early Warning System**.

---

## 1. Responsibilities Breakdown

- **M3 (Full-Stack Platform)**:
  - Hosts and exposes the `/api/risk` and `/api/ml/predict` endpoints.
  - Passes user coordinates and spatial/environmental features from M2 into the model.
  - Visualizes predicted landslide risk probability, risk level badge, and contributing factors in the UI.
  - Handles fallback gracefully if the ML service is offline or loading.

- **M1 (AI / ML Team)**:
  - Develops and trains the landslide susceptibility & risk prediction models (e.g. Random Forest, XGBoost, CatBoost, or Deep Neural Network).
  - Supplies the model artifact or microservice.
  - Analyzes citizen report photographs to classify landslide/crack severity (Phase 2).
  - Implements the logic inside `backend/app/services/risk_service.py` or wires up the `POST /api/ml/predict` endpoint.

---

## 2. API Contract Specification

### Endpoint: `POST /api/ml/predict`

In Phase 1, M3 provides a working mock implementation at `backend/app/routes/ml_contract.py` and `backend/app/services/risk_service.py`.

In Phase 2, M1 will replace the mock inference with actual model execution.

#### Request Schema: `MLPredictRequest`
```json
{
  "latitude": 11.4102,
  "longitude": 76.6950,
  "features": {
    "rainfall": 145.0,
    "slope": 37.0,
    "elevation": 2240.0,
    "ndvi": 0.43,
    "soil_saturation": 84.0,
    "aspect": 185.0,
    "lithology_code": 3
  }
}
```

| Field | Type | Description |
|---|---|---|
| `latitude` | `float` | Target location latitude |
| `longitude` | `float` | Target location longitude |
| `features.rainfall` | `float` | 24h cumulative precipitation in mm |
| `features.slope` | `float` | Slope inclination in degrees (0 - 90°) |
| `features.elevation` | `float` | Elevation in meters above sea level |
| `features.ndvi` | `float` | Normalized Difference Vegetation Index (-1.0 to 1.0) |
| `features.soil_saturation` | `float` | Volumetric soil moisture percentage |

#### Response Schema: `MLPredictResponse`
```json
{
  "risk_probability": 0.82,
  "risk_level": "VERY_HIGH",
  "confidence": 0.91,
  "factors": [
    "Saturated colluvial regolith on steep slope",
    "24h cumulative rainfall exceeding 120mm threshold",
    "Historical landslide inventory hotspot"
  ],
  "model_version": "M1-CATBOOST-v1.2"
}
```

| Field | Type | Enum / Range | Description |
|---|---|---|---|
| `risk_probability` | `float` | `0.0` – `1.0` | Probability of landslide occurrence |
| `risk_level` | `string` | `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH` | Standardized categorical severity rating |
| `confidence` | `float` | `0.0` – `1.0` | Uncertainty/confidence score from the model |
| `factors` | `array[string]` | Human-readable bullet factors | Primary risk driving features for citizen clarity |
| `model_version` | `string` | e.g. `v1.0.0` | Model release tag for auditability |

---

## 3. How M1 Connects Code in Phase 2

1. Open `backend/app/services/risk_service.py`.
2. Locate function `get_risk_prediction(latitude: float, longitude: float)`.
3. Load the serialized model (`.pkl`, `.onnx`, or PyTorch `.pt`) inside the service or query M1's model server:
   ```python
   # Example Phase 2 Hook in risk_service.py:
   import joblib
   model = joblib.load("models/landslide_model.pkl")
   
   def get_risk_prediction(latitude: float, longitude: float) -> RiskPredictionResponse:
       features = environment_service.get_environment_data(latitude, longitude)
       input_vector = [[features.rainfall, features.slope, features.elevation, features.ndvi]]
       prob = float(model.predict_proba(input_vector)[0][1])
       level = "VERY_HIGH" if prob > 0.75 else "HIGH" if prob > 0.55 else ...
       ...
   ```
4. As long as `RiskPredictionResponse` is returned, **no frontend or API routes need to be modified.**
