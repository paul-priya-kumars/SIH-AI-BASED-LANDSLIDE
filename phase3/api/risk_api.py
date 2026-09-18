from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from phase3.risk_engine.predict_risk import predict_risk


app = FastAPI(
    title="JARVIS Phase 3 Risk API",
    description="AI Risk and Prediction Engine API",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# Allows the React/Vite frontend to call this API
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# RISK INPUT MODEL
# ============================================================

class RiskInput(BaseModel):
    rainfall_mm: float
    soil_moisture_pct: float
    slope_deg: float
    elevation_m: float
    temperature_c: float
    river_level_m: float
    vegetation_index: float
    landslide_history: int


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "service": "JARVIS Phase 3 Risk API",
        "status": "online",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "phase": "3",
        "component": "risk_prediction_api",
    }


# ============================================================
# REAL M1 RISK PREDICTION
# ============================================================

@app.post("/predict-risk")
def predict_risk_api(data: RiskInput):
    try:
        result = predict_risk(
            rainfall_mm=data.rainfall_mm,
            soil_moisture_pct=data.soil_moisture_pct,
            slope_deg=data.slope_deg,
            elevation_m=data.elevation_m,
            temperature_c=data.temperature_c,
            river_level_m=data.river_level_m,
            vegetation_index=data.vegetation_index,
            landslide_history=data.landslide_history,
        )

        return {
            "success": True,
            "risk": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "phase3.api.risk_api:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )