from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from phase3.risk_engine.predict_risk import predict_risk


app = FastAPI(
    title="JARVIS Phase 3 Risk API",
    description="AI Risk and Prediction Engine API",
    version="1.0.0",
)


class RiskInput(BaseModel):
    rainfall_mm: float
    soil_moisture_pct: float
    slope_deg: float
    elevation_m: float
    temperature_c: float
    river_level_m: float
    vegetation_index: float
    landslide_history: int


@app.get("/")
def root():
    return {
        "service": "JARVIS Phase 3 Risk API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "phase": "3",
        "component": "risk_prediction_api",
    }


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "phase3.api.risk_api:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
