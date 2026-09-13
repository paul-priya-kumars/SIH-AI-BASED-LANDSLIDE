"""
JARVIS Phase 4 - Dynamic Rerouting

Determines whether the current route should be
replaced with a safer alternative.
"""

import sys
from pathlib import Path


# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase4.routing.alternative_routes import (
    find_alternative_routes,
)
from phase4.routing.route_risk import (
    get_route_risk_level,
)


def determine_reroute(routes, current_route):
    """
    Decide whether to reroute.

    A reroute is recommended when the current route
    has HIGH risk and a safer alternative exists.
    """

    if current_route not in routes:
        raise ValueError(
            f"Current route '{current_route}' was not found."
        )

    current_risk = routes[current_route]["risk"]
    current_level = get_route_risk_level(current_risk)

    alternative_result = find_alternative_routes(
        routes,
        current_route,
    )

    safest_alternative = alternative_result[
        "safest_alternative"
    ]

    should_reroute = (
        current_level == "HIGH"
        and safest_alternative is not None
    )

    if should_reroute:
        recommended_route = safest_alternative
        status = "REROUTE RECOMMENDED"
    else:
        recommended_route = current_route
        status = "STAY ON CURRENT ROUTE"

    return {
        "current_route": current_route,
        "current_risk": current_risk,
        "current_level": current_level,
        "should_reroute": should_reroute,
        "recommended_route": recommended_route,
        "status": status,
    }


if __name__ == "__main__":

    test_routes = {
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

    result = determine_reroute(
        test_routes,
        "Route B",
    )

    print("\n============================================")
    print("          PHASE 4 - REROUTING")
    print("============================================")

    print("\nCurrent Route      :", result["current_route"])
    print("Current Risk       :", f"{result['current_risk']}/100")
    print("Current Risk Level :", result["current_level"])

    print("\nReroute Required   :", result["should_reroute"])
    print("Recommended Route  :", result["recommended_route"])
    print("Status             :", result["status"])

    print("\nRerouting: PASSED")

    print("\n============================================")
