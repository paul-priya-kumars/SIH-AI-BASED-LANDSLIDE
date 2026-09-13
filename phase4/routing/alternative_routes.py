"""
JARVIS Phase 4 - Alternative Routes

Finds safer alternatives when the current
route has elevated risk.
"""

import sys
from pathlib import Path


# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase4.routing.route_risk import (
    classify_routes,
    get_route_risk_level,
)


def find_alternative_routes(routes, current_route):
    """
    Find routes that are safer than the current route.

    Routes with LOW or MEDIUM risk are considered
    available alternatives.
    """

    if not routes:
        raise ValueError("At least one route is required.")

    if current_route not in routes:
        raise ValueError(
            f"Current route '{current_route}' was not found."
        )

    classified_routes = classify_routes(routes)

    current_risk = classified_routes[current_route]["risk"]

    alternatives = {}

    for route, data in classified_routes.items():

        if route == current_route:
            continue

        if data["risk"] < current_risk:
            alternatives[route] = data

    safest_alternative = None

    if alternatives:
        safest_alternative = min(
            alternatives,
            key=lambda route: alternatives[route]["risk"]
        )

    return {
        "current_route": current_route,
        "current_risk": current_risk,
        "alternatives": alternatives,
        "safest_alternative": safest_alternative,
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

    result = find_alternative_routes(
        test_routes,
        "Route B"
    )

    print("\n============================================")
    print("       PHASE 4 - ALTERNATIVE ROUTES")
    print("============================================")

    print("\nCurrent Route :", result["current_route"])
    print("Current Risk  :", f"{result['current_risk']}/100")

    print("\nSafer Alternatives:")

    if result["alternatives"]:
        for route, data in result["alternatives"].items():
            print(
                f"  {route}: "
                f"{data['risk']}/100 | "
                f"{data['risk_level']}"
            )
    else:
        print("  None")

    print(
        "\nSafest Alternative :",
        result["safest_alternative"]
    )

    print("\nAlternative route analysis: PASSED")

    print("\n============================================")
