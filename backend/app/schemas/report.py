from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from ..models.report import HazardType, SeverityLevel, ReportStatus

class ReportBase(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude of the hazard location")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude of the hazard location")
    location_name: Optional[str] = Field(None, max_length=255, description="Readable landmark/location name")
    hazard_type: str = Field(..., description="Category of hazard observed")
    description: str = Field(..., min_length=5, max_length=2000, description="Detailed description of the hazard")
    severity: str = Field(default=SeverityLevel.MEDIUM.value, description="Assessed severity level")
    contact_name: Optional[str] = Field(None, max_length=128)
    contact_phone: Optional[str] = Field(None, max_length=64)

class ReportCreate(ReportBase):
    pass

class ReportStatusUpdate(BaseModel):
    status: str = Field(..., description="Updated status: PENDING, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED")

class ReportResponse(ReportBase):
    id: int
    report_id: str
    user_id: Optional[str] = None
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True