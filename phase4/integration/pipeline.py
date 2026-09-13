"""
JARVIS Phase 4 - Complete Integration Pipeline

Connects:
    M1 -> Phase 3 ML prediction
    M2 -> Environmental data
    Image analysis -> Warning detection
    Risk engine -> Overall risk
    Routing -> Safest route / rerouting
    Alerts -> Safety notification
"""

import sys
from pathlib import Path


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# IMPORT PHASE 4 MODULES
# ---------------------------------------------------------

from phase4.integration.m1_adapter import get_ml_risk
from phase4.integration.m2_adapter import get_environment_data

from phase4.risk.risk_engine import calculate_overall_risk
from phase4.risk.risk_explanation import explain_risk

from phase4.routing.route_analyzer import analyze_routes
from phase4.routing.rerouting import determine_reroute

from phase4.alerts.alert_engine import generate_alert
from phase4.alerts.notification import create_notification


# ---------------------------------------------------------
# COMPLETE PIPELINE
# ---------------------------------------------------------

def run_phase4(environment_data, image_data, routes, current_route):
    """
    Execute the complete Phase 4 pipeline.
    """

    # -----------------------------------------------------
    # M2 - ENVIRONMENT DATA
    # -----------------------------------------------------

    validated_environment = get_environment_data(
        environment_data
    )

    # -----------------------------------------------------
    # M1 - ML RISK PREDICTION
    # -----------------------------------------------------

    ml_result = get_ml_risk(
        validated_environment
    )

    ml_risk = ml_result["risk_level"]

    # -----------------------------------------------------
    # IMAGE ANALYSIS
    # -----------------------------------------------------

    image_risk = "LOW"

    if image_data.get("landslide", False):
        image_risk = "HIGH"

    elif image_data.get("flooding", False):
        image_risk = "HIGH"

    elif image_data.get("road_damage", False):
        image_risk = "MEDIUM"

    # -----------------------------------------------------
    # ROUTE ANALYSIS
    # -----------------------------------------------------

    route_result = analyze_routes(routes)

    current_route_risk = routes[current_route]["risk"]

    if current_route_risk < 40:
        route_risk = "LOW"

    elif current_route_risk < 70:
        route_risk = "MEDIUM"

    else:
        route_risk = "HIGH"

    # -----------------------------------------------------
    # RISK COMBINATION
    # -----------------------------------------------------

    risk_result = calculate_overall_risk(
        ml_risk=ml_risk,
        route_risk=route_risk,
        image_risk=image_risk,
    )

    # -----------------------------------------------------
    # RISK EXPLANATION
    # -----------------------------------------------------

    explanation = explain_risk(
        risk_result
    )

    # -----------------------------------------------------
    # DYNAMIC REROUTING
    # -----------------------------------------------------

    reroute_result = determine_reroute(
        routes,
        current_route,
    )

    # -----------------------------------------------------
    # ALERT ENGINE
    # -----------------------------------------------------

    alert_result = generate_alert(
        risk_result
    )

    # -----------------------------------------------------
    # NOTIFICATION
    # -----------------------------------------------------

    notification = create_notification(
        alert_result
    )

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "environment": validated_environment,
        "ml_prediction": ml_result,
        "image_risk": image_risk,
        "route_analysis": route_result,
        "risk": risk_result,
        "explanation": explanation,
        "rerouting": reroute_result,
        "alert": alert_result,
        "notification": notification,
    }


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    environment_data = {
        "rainfall_mm": 180,
        "soil_moisture_pct": 85,
        "slope_deg": 32,
        "elevation_m": 650,
        "temperature_c": 23,
        "river_level_m": 5.2,
        "vegetation_index": 0.35,
        "landslide_history": 1,
    }

    image_data = {
        "landslide": False,
        "flooding": True,
        "road_damage": False,
    }

    routes = {
        "Route A": {
            "distance": 5,
            "risk": 30,
        },
        "Route B": {
            "distance": 8,
            "risk": 85,
        },
        "Route C": {
            "distance": 6,
            "risk": 55,
        },
    }

    current_route = "Route B"

    result = run_phase4(
        environment_data,
        image_data,
        routes,
        current_route,
    )

    print("\n============================================")
    print("       JARVIS PHASE 4 - FULL PIPELINE")
    print("============================================")

    print("\nM2 ENVIRONMENT")
    print("----------------")
    print("Environmental data : PASSED")

    print("\nM1 ML PREDICTION")
    print("----------------")
    print(
        "Risk Level :",
        result["ml_prediction"]["risk_level"]
    )
    print(
        "Confidence :",
        f"{result['ml_prediction']['confidence']:.2%}"
    )

    print("\nIMAGE ANALYSIS")
    print("----------------")
    print(
        "Image Risk :",
        result["image_risk"]
    )

    print("\nROUTE ANALYSIS")
    print("----------------")
    print(
        "Current Route :",
        current_route
    )
    print(
        "Safest Route  :",
        result["route_analysis"]["safest_route"]
    )
    print(
        "Safest Risk   :",
        f"{result['route_analysis']['safest_risk']}/100"
    )

    print("\nRISK COMBINATION")
    print("----------------")
    print(
        "Overall Risk :",
        result["risk"]["overall_risk"]
    )

    print("\nRISK EXPLANATION")
    print("----------------")
    print(
        result["explanation"]["summary"]
    )

    print("\nREROUTING")
    print("----------------")
    print(
        "Required    :",
        result["rerouting"]["should_reroute"]
    )
    print(
        "Recommended :",
        result["rerouting"]["recommended_route"]
    )

    print("\nALERT")
    print("----------------")
    print(
        "Alert Required :",
        result["alert"]["alert_required"]
    )
    print(
        "Alert Level    :",
        result["alert"]["alert_level"]
    )

    print("\nNOTIFICATION")
    print("----------------")
    print(
        "Display :",
        result["notification"]["display"]
    )
    print(
        "Message :",
        result["notification"]["message"]
    )

    print("\n============================================")
    print("       PHASE 4 FULL PIPELINE PASSED")
    print("============================================")
