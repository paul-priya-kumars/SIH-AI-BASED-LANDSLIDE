"""
JARVIS Phase 5 - Routing Test
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase5.routing.route_risk import (
    get_risk_level,
    calculate_route_risk
)

from phase5.routing.rerouting import (
    should_reroute,
    select_safest_route,
    dynamic_reroute
)


def main():

    print()
    print("============================================")
    print("       PHASE 5 - ROUTING TEST")
    print("============================================")

    print()
    print("1. Risk Level Classification")

    assert get_risk_level(20) == "LOW"
    assert get_risk_level(50) == "MEDIUM"
    assert get_risk_level(80) == "HIGH"

    print("LOW    : PASSED")
    print("MEDIUM : PASSED")
    print("HIGH   : PASSED")

    print()
    print("2. Route Risk Calculation")

    route_a = calculate_route_risk(
        distance_km=5,
        environmental_risk=30
    )

    route_b = calculate_route_risk(
        distance_km=8,
        environmental_risk=85
    )

    route_c = calculate_route_risk(
        distance_km=6,
        environmental_risk=55
    )

    print(
        "Route A:",
        route_a["risk_score"],
        "/100",
        "|",
        route_a["risk_level"]
    )

    print(
        "Route B:",
        route_b["risk_score"],
        "/100",
        "|",
        route_b["risk_level"]
    )

    print(
        "Route C:",
        route_c["risk_score"],
        "/100",
        "|",
        route_c["risk_level"]
    )

    assert route_a["risk_level"] == "LOW"
    assert route_b["risk_level"] == "HIGH"
    assert route_c["risk_level"] == "MEDIUM"

    print("Route risk calculation : PASSED")

    print()
    print("3. Safest Route Selection")

    routes = {
        "Route A": {
            "risk_score": route_a["risk_score"],
            "risk_level": route_a["risk_level"]
        },
        "Route B": {
            "risk_score": route_b["risk_score"],
            "risk_level": route_b["risk_level"]
        },
        "Route C": {
            "risk_score": route_c["risk_score"],
            "risk_level": route_c["risk_level"]
        }
    }

    safest = select_safest_route(routes)

    print("Safest Route :", safest["route"])
    print("Risk Score   :", safest["risk_score"])
    print("Risk Level   :", safest["risk_level"])

    assert safest["route"] == "Route A"

    print("Safest route selection : PASSED")

    print()
    print("4. Reroute Decision")

    assert should_reroute("HIGH", True) is True
    assert should_reroute("HIGH", False) is False
    assert should_reroute("MEDIUM", True) is False
    assert should_reroute("LOW", True) is False

    print("Reroute decision : PASSED")

    print()
    print("5. Dynamic Rerouting")

    result = dynamic_reroute(
        "Route B",
        routes
    )

    print("Current Route     :", result["current_route"])
    print("Current Risk      :", result["current_risk"])
    print("Recommended Route :", result["recommended_route"])
    print("Reroute Required  :", result["reroute_required"])
    print("Status            :", result["status"])

    assert result["current_route"] == "Route B"
    assert result["current_risk_level"] == "HIGH"
    assert result["recommended_route"] == "Route A"
    assert result["reroute_required"] is True
    assert result["status"] == "REROUTE RECOMMENDED"

    print("Dynamic rerouting : PASSED")

    print()
    print("============================================")
    print("       ALL ROUTING TESTS PASSED")
    print("============================================")


if __name__ == "__main__":
    main()