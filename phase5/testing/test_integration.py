"""
JARVIS Phase 5 - Integration Test
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase5.integration.risk_engine import calculate_final_risk
from phase5.integration.prediction_pipeline import run_prediction
from phase5.integration.decision_engine import make_decision
from phase5.routing.route_risk import calculate_route_risk
from phase5.routing.rerouting import dynamic_reroute
from phase5.alerts.alert_engine import create_alert
from phase5.image.image_risk import calculate_image_risk


def get_risk_level(result):
    if isinstance(result, str):
        return result.upper()

    if isinstance(result, dict):

        if "risk_level" in result:
            return str(result["risk_level"]).upper()

        if "final_risk" in result:
            return str(result["final_risk"]).upper()

        if "risk" in result:
            risk = result["risk"]

            if isinstance(risk, str):
                return risk.upper()

            if isinstance(risk, dict):

                if "risk_level" in risk:
                    return str(risk["risk_level"]).upper()

                if "final_risk" in risk:
                    return str(risk["final_risk"]).upper()

    raise ValueError("Risk level not found")


def main():

    print()
    print("============================================")
    print("       PHASE 5 - INTEGRATION TEST")
    print("============================================")

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

    print()
    print("1. M2 -> M1 Prediction")

    prediction = run_prediction(environment_data)

    ml_risk = get_risk_level(prediction)

    print("ML Risk :", ml_risk)

    assert ml_risk == "HIGH"

    print("Prediction integration : PASSED")

    print()
    print("2. Image Risk")

    image_data = {
        "landslide": False,
        "flooding": True,
        "road_damage": False
    }

    image_result = calculate_image_risk(image_data)

    image_risk = get_risk_level(image_result)

    print("Image Risk :", image_risk)

    assert image_risk == "MEDIUM"

    print("Image integration : PASSED")

    print()
    print("3. Route Risk")

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

    route_results = {}

    for route_name, route_data in routes.items():

        route_results[route_name] = calculate_route_risk(
            route_data["distance"],
            route_data["environmental_risk"]
        )

    current_route = "Route B"

    current_route_risk = get_risk_level(
        route_results[current_route]
    )

    print("Current Route :", current_route)
    print("Route Risk    :", current_route_risk)

    assert current_route_risk == "HIGH"

    print("Route integration : PASSED")

    print()
    print("4. Final Risk Engine")

    final_result = calculate_final_risk(
        ml_risk,
        image_risk,
        current_route_risk
    )

    final_risk = get_risk_level(final_result)

    print("Final Risk :", final_risk)

    assert final_risk == "HIGH"

    print("Final risk integration : PASSED")

    print()
    print("5. Dynamic Rerouting")

    reroute_result = dynamic_reroute(
        current_route,
        route_results
    )

    print(
        "Recommended Route :",
        reroute_result["recommended_route"]
    )

    print(
        "Reroute Required   :",
        reroute_result["reroute_required"]
    )

    assert reroute_result["reroute_required"] is True
    assert reroute_result["recommended_route"] == "Route A"

    print("Rerouting integration : PASSED")

    print()
    print("6. Decision Engine")

    decision = make_decision(
        final_risk,
        current_route_risk,
        True
    )

    print("Action   :", decision["route_action"])
    print("Priority :", decision["priority"])

    assert decision["route_action"] == "REROUTE"
    assert decision["priority"] == "IMMEDIATE"

    print("Decision integration : PASSED")

    print()
    print("7. Alert Engine")

    alert = create_alert(
        final_risk,
        decision["reroute_required"]
    )

    print("Alert Level :", alert["alert_level"])
    print("Required    :", alert["alert_required"])

    assert alert["alert_required"] is True
    assert alert["alert_level"] == "CRITICAL"

    print("Alert integration : PASSED")

    print()
    print("============================================")
    print("       PHASE 5 INTEGRATION PASSED")
    print("============================================")


if __name__ == "__main__":
    main()