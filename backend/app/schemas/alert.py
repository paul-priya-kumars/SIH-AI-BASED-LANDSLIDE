from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class AlertResponse(BaseModel):
    id: int
    alert_id: str
    title: str
    message: str
    severity: str
    location: str
    latitude: float
    longitude: float
    issued_at: datetime
    recommended_action: str
    is_active: bool

    class Config:
        from_attributes = True

class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str
    location: str
    latitude: float
    longitude: float
    recommended_action: str
    is_active: bool = True
