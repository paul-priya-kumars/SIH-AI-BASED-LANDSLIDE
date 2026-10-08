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
    river_level_m: Optional[float] = Field(None, description="River/stream gauge level in metres (M1 feature; demo provider)")
    landslide_history: Optional[int] = Field(None, description="1 if the location has recorded landslide history, else 0 (M1 feature; demo provider)")
    data_source: str = Field(default="MOCK_ENVIRONMENT_PROVIDER", description="Provenance of the environmental values")
    is_mock: bool = Field(default=True, description="True for Phase 1 mock data; False once M2 GIS pipelines are linked")
