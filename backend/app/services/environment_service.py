"""
Environmental Data Service (M2 Integration Point)
=================================================
NOTE FOR M2 TEAM:
In Phase 1, this service returns realistic mock values based on geographic coordinates.
In Phase 2, M2 will replace `get_environment_data` and spatial queries with GIS pipelines
(e.g., DEM slope calculations, automated weather station (AWS) rainfall rasters, Sentinel-2 NDVI, and soil layers).
"""

from ..schemas.environment import EnvironmentDataResponse
from ..cache import get_prediction_cache
from ..metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL, CACHE_ERRORS_TOTAL
from ..config import settings
import logging

logger = logging.getLogger(__name__)

def get_environment_data(latitude: float, longitude: float) -> EnvironmentDataResponse:
    """
    Retrieves environmental parameters for a given coordinate.
    Phase 1: Returns mock data representative of Western Ghats / Nilgiris terrain.
    Phase 2: M2 will hook into GIS raster pipelines / IoT weather sensors.
    Includes caching layer for performance optimization.
    """
    # Check if caching is enabled
    if not settings.CACHE_ENABLED:
        return _get_environment_data_uncached(latitude, longitude)

    # Generate cache key based on normalized coordinates
    # Normalize to 4 decimal places (~11 meters precision)
    lat_key = round(latitude, 4)
    lon_key = round(longitude, 4)
    cache_key = f"environment:{lat_key}:{lon_key}"

    try:
        cache = get_prediction_cache()
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            CACHE_HITS_TOTAL.labels(cache_type="environment").inc()
            logger.debug(f"Environment cache hit for key: {cache_key}")
            return cached_result

        # Cache miss
        CACHE_MISSES_TOTAL.labels(cache_type="environment").inc()
        logger.debug(f"Environment cache miss for key: {cache_key}")

        # Compute result
        result = _get_environment_data_uncached(latitude, longitude)

        # Store in cache
        cache.set(cache_key, result)
        logger.debug(f"Stored environment result in cache for key: {cache_key}")

        return result
    except Exception as e:
        # If cache fails, log error and fall back to uncached computation
        CACHE_ERRORS_TOTAL.labels(cache_type="environment").inc()
        logger.error(f"Environment cache error: {e}. Falling back to uncached computation.")
        return _get_environment_data_uncached(latitude, longitude)


def _get_environment_data_uncached(latitude: float, longitude: float) -> EnvironmentDataResponse:
    """
    Internal function that retrieves environmental data without caching.
    This contains the original logic from get_environment_data.
    """
    dist_ooty = abs(latitude - 11.41) + abs(longitude - 76.69)

    if dist_ooty < 0.08:
        # High rainfall highland conditions (e.g. Ooty center)
        rainfall = 145.0
        temperature = 16.5
        humidity = 89.0
        slope = 37.0
        elevation = 2240.0
        ndvi = 0.43
        soil_sat = 86.0
        river_level = 4.2
        landslide_history = 1
        loc_name = "Ooty Catchment"
    elif dist_ooty < 0.2:
        # Coonoor / Kotagiri corridor
        rainfall = 118.0
        temperature = 19.0
        humidity = 82.0
        slope = 31.0
        elevation = 1850.0
        ndvi = 0.52
        soil_sat = 74.0
        river_level = 3.1
        landslide_history = 1
        loc_name = "Nilgiris Slope Basin"
    else:
        # Lower elevation foothills
        rainfall = 55.0
        temperature = 26.0
        humidity = 68.0
        slope = 14.0
        elevation = 620.0
        ndvi = 0.65
        soil_sat = 42.0
        river_level = 1.4
        landslide_history = 0
        loc_name = "Foothills Transition Zone"

    return EnvironmentDataResponse(
        latitude=round(latitude, 4),
        longitude=round(longitude, 4),
        location_name=loc_name,
        rainfall=rainfall,
        temperature=temperature,
        humidity=humidity,
        slope=slope,
        elevation=elevation,
        ndvi=ndvi,
        soil_saturation_pct=soil_sat,
        # M1 features (river_level_m, landslide_history) come from this demo
        # provider, so the environment response stays is_mock=True even though
        # the M1 model that consumes them is real.
        river_level_m=river_level,
        landslide_history=landslide_history,
        data_source="MOCK_ENVIRONMENT_PROVIDER",
        is_mock=True
    )