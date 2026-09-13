"""
JARVIS Phase 5 - Route Risk Intelligence
"""


def get_risk_level(risk_score):
    if risk_score >= 70:
        return "HIGH"

    if risk_score >= 40:
        return "MEDIUM"

    return "LOW"


def calculate_route_risk(distance_km, environmental_risk):
    if distance_km < 0:
        raise ValueError("Distance cannot be negative")

    if not 0 <= environmental_risk <= 100:
        raise ValueError(
            "Environmental risk must be between 0 and 100"
        )

    distance_factor = min(distance_km * 2, 20)

    risk_score = min(
        100,
        round(
            environmental_risk * 0.8
            + distance_factor
        )
    )

    return {
        "distance_km": distance_km,
        "risk_score": risk_score,
        "risk_level": get_risk_level(risk_score)
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - ROUTE RISK")
    print("============================================")

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

    print()

    results = {}

    for route_name, route_data in routes.items():

        result = calculate_route_risk(
            route_data["distance"],
            route_data["environmental_risk"]
        )

        results[route_name] = result

        print(
            f"{route_name}: "
            f"Distance = {result['distance_km']} km | "
            f"Risk Score = {result['risk_score']}/100 | "
            f"Level = {result['risk_level']}"
        )

    assert results["Route A"]["risk_level"] == "LOW"
    assert results["Route B"]["risk_level"] == "HIGH"
    assert results["Route C"]["risk_level"] == "MEDIUM"

    print()
    print("Route risk intelligence: PASSED")

    print()
    print("============================================")