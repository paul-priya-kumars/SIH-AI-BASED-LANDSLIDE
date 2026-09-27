from fastapi import APIRouter, Query
from ..schemas.environment import EnvironmentDataResponse
from ..services.environment_service import get_environment_data

router = APIRouter(tags=["Environmental Telemetry"])

@router.get("/environment", response_model=EnvironmentDataResponse, summary="Get environmental indicators for location")
def get_location_environment(
    latitude: float = Query(11.4102, ge=-90.0, le=90.0, description="Latitude coordinate"),
    longitude: float = Query(76.6950, ge=-180.0, le=180.0, description="Longitude coordinate")
):
    """
    Returns environmental, meteorological, and topographic variables (rainfall, slope, elevation, NDVI, humidity).
    Phase 1: Calls `environment_service.get_environment_data` with mock values.
    Phase 2: M2 will hook into spatial GIS raster queries.
    """
    return get_environment_data(latitude, longitude)