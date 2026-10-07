import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum
from ..database import Base

class HazardType(str, enum.Enum):
    ROAD_CRACK = "Road crack"
    GROUND_CRACK = "Ground crack"
    ROCKFALL = "Rockfall"
    SOIL_MOVEMENT = "Soil movement"
    LANDSLIDE = "Landslide"
    WATER_SEEPAGE = "Water seepage"
    FALLEN_DEBRIS = "Fallen debris"
    OTHER = "OTHER"

class SeverityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"

class HazardReport(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(String(64), nullable=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location_name = Column(String(255), nullable=True)
    hazard_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False, default=SeverityLevel.MEDIUM.value)
    image_path = Column(String(512), nullable=True)
    contact_name = Column(String(128), nullable=True)
    contact_phone = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default=ReportStatus.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)