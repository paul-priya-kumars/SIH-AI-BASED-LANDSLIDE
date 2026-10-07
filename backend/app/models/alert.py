from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from ..database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False)  # LOW, MODERATE, HIGH, CRITICAL
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    recommended_action = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)