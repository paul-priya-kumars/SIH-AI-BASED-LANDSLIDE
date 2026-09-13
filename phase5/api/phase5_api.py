"""
JARVIS Phase 5 - API
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase5.integration.risk_engine import calculate_final_risk
from phase5.integration.decision_engine import make_decision
from phase5.routing.route_risk import calculate_route_risk
from phase5.routing.rerouting import dynamic_reroute
from phase5.alerts.alert_engine import create_alert
from phase5.image.image_risk import calculate_image_risk


def health_check():
    return {
        "service": "JARVIS Phase 5 API",
        "status": "online",
        "version": "1.0.0"
    }


def extract_risk_level(result):
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

    raise ValueError("Unable to extract risk level")


def predict_phase5(
    ml_risk,
    image_data,
    routes,
    current_route
):
    ml_risk = extract_risk_level(ml_risk)

    image_result = calculate_image_risk(image_data)
    image_risk = extract_risk_level(image_result)

    route_results = {}

    for route_name, route_data in routes.items():
        route_results[route_name] = calculate_route_risk(
            route_data["distance"],
            route_data["environmental_risk"]
        )

    current_route_data = route_results[current_route]

    route_risk = extract_risk_level(current_route_data)

    final_result = calculate_final_risk(
        ml_risk,
        image_risk,
        route_risk
    )

    final_risk = extract_risk_level(final_result)

    reroute_result = dynamic_reroute(
        current_route,
        route_results
    )

    safer_route_available = (
        reroute_result["recommended_route"] is not None
    )

    decision = make_decision(
        final_risk,
        route_risk,
        safer_route_available
    )

    alert = create_alert(
        final_risk,
        decision["reroute_required"]
    )

    return {
        "success": True,
        "risk": {
            "ml_risk": ml_risk,
            "image_risk": image_risk,
            "route_risk": route_risk,
            "final_risk": final_risk
        },
        "route": reroute_result,
        "decision": decision,
        "alert": alert
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - API TEST")
    print("============================================")

    health = health_check()

    print()
    print("Health Check:")
    print(health)

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

    print()
    print("Phase 5 Prediction:")
    print("ML Risk       :", result["risk"]["ml_risk"])
    print("Image Risk    :", result["risk"]["image_risk"])
    print("Route Risk    :", result["risk"]["route_risk"])
    print("Final Risk    :", result["risk"]["final_risk"])

    print()
    print("Route Decision:")
    print("Current Route :", result["route"]["current_route"])
    print("Recommended   :", result["route"]["recommended_route"])
    print("Reroute       :", result["route"]["reroute_required"])

    print()
    print("Alert:")
    print("Required      :", result["alert"]["alert_required"])
    print("Level         :", result["alert"]["alert_level"])

    assert health["status"] == "online"
    assert result["success"] is True
    assert result["risk"]["final_risk"] == "HIGH"
    assert result["route"]["recommended_route"] == "Route A"
    assert result["route"]["reroute_required"] is True
    assert result["alert"]["alert_level"] == "CRITICAL"

    print()
    print("Phase 5 API: PASSED")

    print()
    print("============================================")