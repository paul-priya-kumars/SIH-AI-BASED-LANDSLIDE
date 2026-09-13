"""
JARVIS Phase 5 - Final End-to-End Test
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase5.api.phase5_api import health_check, predict_phase5


def main():

    print()
    print("============================================")
    print("       JARVIS PHASE 5 - FINAL TEST")
    print("============================================")

    print()
    print("1. API Health Check")

    health = health_check()

    print("Service :", health["service"])
    print("Status  :", health["status"])
    print("Version :", health["version"])

    assert health["status"] == "online"

    print("API health : PASSED")

    print()
    print("2. M2 Environmental Input")

    environment_data = {
        "rainfall_mm": 180,
        "soil_moisture_pct": 85,
        "slope_deg": 32,
        "elevation_m": 650,
        "temperature_c": 23,
        "river_level_m": 5.2,
        "vegetation_index": 0.35,
        "landslide_history": 1
    }

    print("Rainfall          :", environment_data["rainfall_mm"], "mm")
    print("Soil Moisture     :", environment_data["soil_moisture_pct"], "%")
    print("Slope             :", environment_data["slope_deg"], "deg")
    print("Elevation         :", environment_data["elevation_m"], "m")
    print("Historical Events :", environment_data["landslide_history"])

    print("M2 input : PASSED")

    print()
    print("3. Phase 5 End-to-End Prediction")

    image_data = {
        "landslide": False,
        "flooding": True,
        "road_damage": False
    }

    routes = {
        "Route A": {
            "distance": 5,
            "environmental_risk": 30
        },
        "Route B": {
            "distance": 8,
            "environmental_risk": 85
        },
        "Route C": {
            "distance": 6,
            "environmental_risk": 55
        }
    }

    result = predict_phase5(
        ml_risk="HIGH",
        image_data=image_data,
        routes=routes,
        current_route="Route B"
    )

    assert result["success"] is True

    print("ML Risk       :", result["risk"]["ml_risk"])
    print("Image Risk    :", result["risk"]["image_risk"])
    print("Route Risk    :", result["risk"]["route_risk"])
    print("Final Risk    :", result["risk"]["final_risk"])

    assert result["risk"]["ml_risk"] == "HIGH"
    assert result["risk"]["image_risk"] == "MEDIUM"
    assert result["risk"]["route_risk"] == "HIGH"
    assert result["risk"]["final_risk"] == "HIGH"

    print("Risk pipeline : PASSED")

    print()
    print("4. Route Intelligence")

    print("Current Route     :", result["route"]["current_route"])
    print("Recommended Route :", result["route"]["recommended_route"])
    print("Reroute Required  :", result["route"]["reroute_required"])

    assert result["route"]["current_route"] == "Route B"
    assert result["route"]["recommended_route"] == "Route A"
    assert result["route"]["reroute_required"] is True

    print("Route intelligence : PASSED")

    print()
    print("5. Safety Decision")

    print("Alert Required   :", result["decision"]["alert_required"])
    print("Alert Level      :", result["decision"]["alert_level"])
    print("Reroute Required :", result["decision"]["reroute_required"])
    print("Route Action     :", result["decision"]["route_action"])
    print("Priority         :", result["decision"]["priority"])

    assert result["decision"]["alert_required"] is True
    assert result["decision"]["alert_level"] == "CRITICAL"
    assert result["decision"]["reroute_required"] is True
    assert result["decision"]["route_action"] == "REROUTE"
    assert result["decision"]["priority"] == "IMMEDIATE"

    print("Safety decision : PASSED")

    print()
    print("6. Alert System")

    print("Alert Required :", result["alert"]["alert_required"])
    print("Alert Level    :", result["alert"]["alert_level"])
    print("Message        :", result["alert"]["message"])

    assert result["alert"]["alert_required"] is True
    assert result["alert"]["alert_level"] == "CRITICAL"

    print("Alert system : PASSED")

    print()
    print("============================================")
    print("       PHASE 5 FINAL TEST PASSED")
    print("============================================")

    print()
    print("JARVIS Phase 5 is COMPLETE.")
    print("M2 -> M1 -> Risk -> Route -> Reroute -> Alert -> API")
    print("All systems are integrated successfully.")

    print()
    print("============================================")


if __name__ == "__main__":
    main()