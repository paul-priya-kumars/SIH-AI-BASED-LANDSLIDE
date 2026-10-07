from typing import Optional
from pydantic import BaseModel, Field

class EnvironmentDataResponse(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = "Nilgiris Region"
    rainfall: float = Field(..., description="Precipitation accumulation in millimeters (mm) over past 24 hours")
    temperature: float = Field(..., description="Surface ambient temperature in Celsius (°C)")
    humidity: float = Field(..., description="Relative humidity percentage (%)")
    slope: float = Field(..., description="Terrain slope gradient in degrees (°)")
    elevation: float = Field(..., description="Altitude above sea level in meters (m)")
    ndvi: float = Field(..., description="Normalized Difference Vegetation Index (-1 to +1)")
    soil_saturation_pct: Optional[float] = Field(82.0, description="Volumetric soil moisture saturation percentage")
    is_mock: bool = Field(default=True, description="True for Phase 1 mock data; False once M2 GIS pipelines are linked")
