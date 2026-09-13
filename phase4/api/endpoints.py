"""
JARVIS Phase 4 - API Endpoints

Provides API-style endpoints for the complete
Phase 4 safety pipeline.
"""

import sys
from pathlib import Path


# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------

from phase4.integration.phase4_pipeline import run_phase4

from phase4.api.schemas import (
    EnvironmentInput,
    ImageInput,
    RouteInput,
    environment_to_dict,
    image_to_dict,
    routes_to_dict,
)


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

def health_check():
    """
    Check whether the Phase 4 API is online.
    """

    return {
        "service": "JARVIS Phase 4 API",
        "status": "online",
        "version": "1.0.0",
    }


# ---------------------------------------------------------
# RISK ENDPOINT
# ---------------------------------------------------------

def predict_risk_endpoint(
    environment: EnvironmentInput,
    image: ImageInput,
    routes: dict,
    current_route: str,
):
    """
    Run the complete Phase 4 risk pipeline.
    """

    environment_data = environment_to_dict(
        environment
    )

    image_data = image_to_dict(
        image
    )

    route_data = routes_to_dict(
        routes
    )

    result = run_phase4(
        environment_data=environment_data,
        image_data=image_data,
        routes=route_data,
        current_route=current_route,
    )

    return {
        "success": True,
        "result": result,
    }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    environment = EnvironmentInput(
        rainfall_mm=180,
        soil_moisture_pct=85,
        slope_deg=32,
        elevation_m=650,
        temperature_c=23,
        river_level_m=5.2,
        vegetation_index=0.35,
        landslide_history=1,
    )

    image = ImageInput(
        landslide=False,
        flooding=True,
        road_damage=False,
    )

    routes = {
        "Route A": RouteInput(
            distance=5,
            risk=30,
        ),
        "Route B": RouteInput(
            distance=8,
            risk=85,
        ),
        "Route C": RouteInput(
            distance=6,
            risk=55,
        ),
    }

    print("\n============================================")
    print("       PHASE 4 - API ENDPOINTS")
    print("============================================")

    health = health_check()

    print("\nHealth Check:")
    print(health)

    result = predict_risk_endpoint(
        environment=environment,
        image=image,
        routes=routes,
        current_route="Route B",
    )

    print("\nAPI Prediction:")
    print(
        "Overall Risk :",
        result["result"]["risk"]["overall_risk"]
    )

    print(
        "Safest Route :",
        result["result"]["route_analysis"]["safest_route"]
    )

    print(
        "Rerouting    :",
        result["result"]["rerouting"]["should_reroute"]
    )

    print(
        "Alert Level  :",
        result["result"]["alert"]["alert_level"]
    )

    print("\nAPI endpoints: PASSED")

    print("\n============================================")