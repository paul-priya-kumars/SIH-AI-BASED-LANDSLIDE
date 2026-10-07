from typing import List, Optional
from pydantic import BaseModel, Field

class RouteSegment(BaseModel):
    name: str
    risk_level: str
    distance_km: float
    travel_time_mins: int
    hazard_zones_crossed: List[str]
    is_recommended: bool
    summary_advisory: str
    waypoints: List[List[float]] = []  # List of [lat, lon] coordinates

class RouteRiskResponse(BaseModel):
    start_location: str
    destination: str
    recommended_route: RouteSegment
    alternative_route: RouteSegment
    overall_advisory: str
    timestamp: str
    is_mock: bool = True
