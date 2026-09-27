"""
Route Risk Assessment Service
=============================
Evaluates safe transit corridors by comparing route geometries against active landslide hazard zones.
Phase 1: Returns mock route comparisons between standard Nilgiris corridors.
Phase 2: Can incorporate routing engines (e.g., OSRM / OpenRouteService) with M2 hazard polygon overlays.
"""

from datetime import datetime
from ..schemas.route import RouteSegment, RouteRiskResponse
from ..cache import get_prediction_cache
from ..metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL, CACHE_ERRORS_TOTAL
from ..config import settings
import logging

logger = logging.getLogger(__name__)

def evaluate_route_risk(start_location: str, destination: str) -> RouteRiskResponse:
    """
    Compares two alternative travel paths between start and destination,
    assessing risk level based on mock hazard zones.
    Includes caching layer for performance optimization.
    """
    # Check if caching is enabled
    if not settings.CACHE_ENABLED:
        return _evaluate_route_risk_uncached(start_location, destination)

    # Generate cache key based on normalized locations
    # Normalize: strip whitespace, convert to lowercase
    start_norm = start_location.strip().lower() if start_location else ""
    dest_norm = destination.strip().lower() if destination else ""
    cache_key = f"route:{start_norm}:{dest_norm}"

    try:
        cache = get_prediction_cache()
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            CACHE_HITS_TOTAL.labels(cache_type="route").inc()
            logger.debug(f"Route cache hit for key: {cache_key}")
            return cached_result

        # Cache miss
        CACHE_MISSES_TOTAL.labels(cache_type="route").inc()
        logger.debug(f"Route cache miss for key: {cache_key}")

        # Compute result
        result = _evaluate_route_risk_uncached(start_location, destination)

        # Store in cache
        cache.set(cache_key, result)
        logger.debug(f"Stored route result in cache for key: {cache_key}")

        return result
    except Exception as e:
        # If cache fails, log error and fall back to uncached computation
        CACHE_ERRORS_TOTAL.labels(cache_type="route").inc()
        logger.error(f"Route cache error: {e}. Falling back to uncached computation.")
        return _evaluate_route_risk_uncached(start_location, destination)


def _evaluate_route_risk_uncached(start_location: str, destination: str) -> RouteRiskResponse:
    """
    Internal function that evaluates route risk without caching.
    This contains the original logic from evaluate_route_risk.
    """
    """
    Compares two alternative travel paths between start and destination,
    assessing risk level based on mock hazard zones.
    """
    # Sample realistic waypoints for Nilgiris mountain passes
    safe_waypoints = [
        [11.3530, 76.7959], # Coonoor
        [11.3850, 76.7510],
        [11.4010, 76.7220],
        [11.4102, 76.6950]  # Ooty
    ]

    hazardous_waypoints = [
        [11.3530, 76.7820],
        [11.3710, 76.7820],
        [11.3990, 76.7640], # Passing directly through unstable gorge
        [11.4102, 76.6950]
    ]

    route_a = RouteSegment(
        name="Route A (Via Valley Ridge Arterial)",
        risk_level="LOW",
        distance_km=32.4,
        travel_time_mins=55,
        hazard_zones_crossed=["None - Slopes stabilized with retaining netting"],
        is_recommended=True,
        summary_advisory="Engineered drainage and reinforced gabion walls along this sector provide stable passage. Recommended for all vehicle categories.",
        waypoints=safe_waypoints
    )

    route_b = RouteSegment(
        name="Route B (Via Old Ghat Cut Pass)",
        risk_level="HIGH",
        distance_km=28.1,
        travel_time_mins=48,
        hazard_zones_crossed=["Coonoor Hairpin Hazard Zone", "Lovedale Runoff Corridor"],
        is_recommended=False,
        summary_advisory="Passes through active rockfall warning zones and saturated slope cuts. Non-essential travel strictly discouraged during rain.",
        waypoints=hazardous_waypoints
    )

    return RouteRiskResponse(
        start_location=start_location or "Coonoor Foothills",
        destination=destination or "Ooty Town Center",
        recommended_route=route_a,
        alternative_route=route_b,
        overall_advisory="Significant slope instability detected on eastern bypass. Route A offers a 12% longer transit with a 75% reduction in landslide exposure.",
        timestamp=datetime.utcnow().isoformat(),
        is_mock=True
    )