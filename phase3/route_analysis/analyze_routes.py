def get_risk_level(risk_score):
    """Convert a 0-100 risk score into a risk level."""

    if risk_score < 40:
        return "LOW"

    elif risk_score < 70:
        return "MEDIUM"

    else:
        return "HIGH"


def analyze_routes(routes):
    """Analyze all available routes."""

    analyzed_routes = {}

    for route_name, route_data in routes.items():

        distance = route_data["distance"]
        risk_score = route_data["risk"]

        risk_level = get_risk_level(risk_score)

        analyzed_routes[route_name] = {
            "distance": distance,
            "risk": risk_score,
            "risk_level": risk_level,
        }

    return analyzed_routes


def find_safest_route(analyzed_routes):
    """Find the route with the lowest risk score."""

    return min(
        analyzed_routes,
        key=lambda route: analyzed_routes[route]["risk"],
    )


def main():
    print("\n============================================")
    print("      PHASE 3.9.1 - ROUTE RISK ANALYSIS")
    print("============================================\n")

    # Simulated route data for development.
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

    analyzed_routes = analyze_routes(routes)

    print("Route Analysis:")

    for route, data in analyzed_routes.items():

        print(
            f"  {route}: "
            f"Distance = {data['distance']} km | "
            f"Risk = {data['risk']}/100 | "
            f"Level = {data['risk_level']}"
        )

    safest_route = find_safest_route(
        analyzed_routes
    )

    safest_data = analyzed_routes[safest_route]

    print("\n============================================")
    print("          ROUTE RECOMMENDATION")
    print("============================================")

    print(
        f"\nSafest Route : "
        f"{safest_route}"
    )

    print(
        f"Distance     : "
        f"{safest_data['distance']} km"
    )

    print(
        f"Risk Score   : "
        f"{safest_data['risk']}/100"
    )

    print(
        f"Risk Level   : "
        f"{safest_data['risk_level']}"
    )

    print("\n============================================")
    print("      PHASE 3.9.1 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
