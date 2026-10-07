from pydantic import BaseModel, Field, validator
from typing import List
from ..schemas.risk import RiskPredictionResponse


class BatchCoordinate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")


class BatchRiskPredictRequest(BaseModel):
    coordinates: List[BatchCoordinate] = Field(
        ...,
        description="List of latitude/longitude coordinates for batch risk prediction",
        min_items=1
    )

    @validator('coordinates')
    def validate_batch_size(cls, v):
        # Maximum batch size will be checked in the service/route using settings
        # This validator just ensures we have at least one item
        if len(v) == 0:
            raise ValueError("Batch must contain at least one coordinate")
        return v


class BatchRiskPredictResponse(BaseModel):
    predictions: List[RiskPredictionResponse] = Field(
        ...,
        description="List of risk predictions corresponding to input coordinates"
    )

    @validator('predictions')
    def validate_predictions_length(cls, v, values):
        # Ensure predictions length matches input coordinates length
        if 'coordinates' in values and len(v) != len(values['coordinates']):
            raise ValueError("Number of predictions must match number of input coordinates")
        return v