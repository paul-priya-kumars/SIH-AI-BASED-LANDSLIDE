from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from ..database import Base

class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    zone_id = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    risk_level = Column(String(32), nullable=False)  # LOW, MODERATE, HIGH, VERY_HIGH
    risk_probability = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=1000.0)
    polygon_geojson = Column(Text, nullable=True)  # GeoJSON string polygon boundaries
    rainfall_mm = Column(Float, nullable=False, default=0.0)
    slope_deg = Column(Float, nullable=False, default=0.0)
    elevation_m = Column(Float, nullable=False, default=0.0)
    soil_type = Column(String(128), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)