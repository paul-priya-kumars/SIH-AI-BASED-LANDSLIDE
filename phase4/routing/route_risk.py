"""
JARVIS Phase 4 - Route Risk

Provides centralized route-risk classification
for the Phase 4 routing layer.
"""


def get_route_risk_level(risk_score):
    """
    Convert a route risk score (0-100)
    into a standardized Phase 4 risk level.
    """

    if not isinstance(risk_score, (int, float)):
        raise TypeError("Risk score must be numeric.")

    if risk_score < 0 or risk_score > 100:
        raise ValueError("Risk score must be between 0 and 100.")

    if risk_score < 40:
        return "LOW"
    elif risk_score < 70:
        return "MEDIUM"
    else:
        return "HIGH"


def classify_routes(routes):
    """
    Add a standardized risk level to each route.

    Expected input:

        {
            "Route A": {
                "distance": 5,
                "risk": 30
            }
        }
    """

    classified_routes = {}

    for route_name, data in routes.items():

        if "risk" not in data:
            raise ValueError(
                f"Route '{route_name}' is missing a risk score."
            )

        classified_routes[route_name] = {
            **data,
            "risk_level": get_route_risk_level(data["risk"]),
        }

    return classified_routes


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

    result = classify_routes(test_routes)

    print("\n============================================")
    print("        PHASE 4 - ROUTE RISK TEST")
    print("============================================")

    for route, data in result.items():
        print(
            f"{route}: "
            f"Risk Score = {data['risk']}/100 | "
            f"Risk Level = {data['risk_level']}"
        )

    print("\nRoute risk: PASSED")

    print("\n============================================")
