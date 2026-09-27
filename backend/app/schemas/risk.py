from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RiskPredictionResponse(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = "Selected Region"
    risk_probability: float = Field(..., ge=0.0, le=1.0, description="Predicted probability of landslide occurrence (0 to 1)")
    risk_level: str = Field(..., description="LOW, MODERATE, HIGH, VERY_HIGH")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score")
    factors: List[str] = Field(..., description="Primary environmental and topographic risk contributing factors")
    updated_at: datetime
    is_mock: bool = Field(default=True, description="True for Phase 1 mock output; False once M1 model is plugged in")

class RiskZoneResponse(BaseModel):
    id: int
    zone_id: str
    name: str
    risk_level: str
    risk_probability: float
    latitude: float
    longitude: float
    radius_meters: float
    polygon_geojson: Optional[str] = None
    rainfall_mm: float
    slope_deg: float
    elevation_m: float
    soil_type: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class MLPredictRequest(BaseModel):
    """Schema for future M1 machine learning prediction endpoint."""
    latitude: float
    longitude: float
    features: Dict[str, Any] = Field(
        ...,
        example={
            "rainfall": 145.0,
            "slope": 37.0,
            "elevation": 2240.0,
            "ndvi": 0.43
        },
        description="Features extracted from spatial and temporal data layers"
    )

class MLPredictResponse(BaseModel):
    """Schema for future M1 machine learning prediction output."""
    risk_probability: float
    risk_level: str
    confidence: float
    factors: Optional[List[str]] = None
    model_version: Optional[str] = "M1-MOCK-v1.0"
