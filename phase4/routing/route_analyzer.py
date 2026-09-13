"""
JARVIS Phase 4 - Route Analyzer

Analyzes available routes and identifies
the safest available route.
"""

import sys
from pathlib import Path


# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase4.routing.route_risk import classify_routes


def analyze_routes(routes):
    """
    Analyze routes and return classified routes
    plus the safest route.
    """

    if not routes:
        raise ValueError("At least one route is required.")

    classified_routes = classify_routes(routes)

    safest_route = min(
        classified_routes,
        key=lambda route: classified_routes[route]["risk"]
    )

    safest_data = classified_routes[safest_route]

    return {
        "routes": classified_routes,
        "safest_route": safest_route,
        "safest_risk": safest_data["risk"],
        "safest_level": safest_data["risk_level"],
        "safest_distance": safest_data["distance"],
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

    result = analyze_routes(test_routes)

    print("\n============================================")
    print("       PHASE 4 - ROUTE ANALYZER")
    print("============================================")

    print("\nAnalyzed Routes:")

    for route, data in result["routes"].items():
        print(
            f"{route}: "
            f"Distance = {data['distance']} km | "
            f"Risk = {data['risk']}/100 | "
            f"Level = {data['risk_level']}"
        )

    print("\nSafest Route :", result["safest_route"])
    print("Risk Score   :", f"{result['safest_risk']}/100")
    print("Risk Level   :", result["safest_level"])
    print("Distance     :", f"{result['safest_distance']} km")

    print("\nRoute analyzer: PASSED")

    print("\n============================================")
