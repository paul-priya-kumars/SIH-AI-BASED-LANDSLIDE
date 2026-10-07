from fastapi import APIRouter, Query
from ..schemas.route import RouteRiskResponse
from ..services.route_service import evaluate_route_risk

router = APIRouter(tags=["Route Safety"])

@router.get("/route-risk", response_model=RouteRiskResponse, summary="Analyze safety of travel routes between locations")
def get_route_safety_assessment(
    start: str = Query("Coonoor", description="Start origin town or coordinates"),
    destination: str = Query("Ooty", description="Destination town or coordinates")
):
    """
    Evaluates alternative travel paths between two locations, comparing hazard zones,
    travel duration, distance, and safety recommendations.
    Phase 1: Returns mock route safety profiles for Nilgiris mountain passes.
    Phase 2: Will integrate dynamic routing engines and real-time M2 hazard layers.
    """
    return evaluate_route_risk(start_location=start, destination=destination)