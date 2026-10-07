from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.risk_zone import RiskZone
from ..schemas.risk import RiskPredictionResponse, RiskZoneResponse
from ..services.risk_service import get_risk_prediction

router = APIRouter(tags=["Risk Assessment"])

@router.get("/risk", response_model=RiskPredictionResponse, summary="Get landslide risk prediction for location")
def get_location_risk(
    latitude: float = Query(11.4102, ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(76.6950, ge=-180.0, le=180.0, description="Longitude coordinate")
):
    """
    Returns the landslide risk prediction and contributing factors for a given coordinate.
    Phase 1: Calls `risk_service.get_risk_prediction` which returns structured mock data.
    Phase 2: M1 will replace this service with AI/ML inference.
    """
    return get_risk_prediction(latitude, longitude)

@router.get("/risk-zones", response_model=List[RiskZoneResponse], summary="Get all landslide hazard zones for map visualization")
def get_risk_zones(db: Session = Depends(get_db)):
    """
    Returns geographic hazard zones with risk levels, soil info, and boundaries for Leaflet map display.
    Phase 2: M2 will supply real GIS vector layers and dynamic hazard boundaries.
    """
    zones = db.query(RiskZone).all()
    return zones