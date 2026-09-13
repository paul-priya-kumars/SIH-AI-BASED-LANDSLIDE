def get_risk_level(risk_score):
    if risk_score < 40:
        return "LOW"
    elif risk_score < 70:
        return "MEDIUM"
    else:
        return "HIGH"


def find_safe_route(routes):
    safe_routes = {
        route: data
        for route, data in routes.items()
        if data["risk"] < 70
    }

    if not safe_routes:
        return None

    return min(
        safe_routes,
        key=lambda route: safe_routes[route]["risk"]
    )


def dynamic_reroute(routes, current_route):
    current_risk = routes[current_route]["risk"]
    current_level = get_risk_level(current_risk)

    if current_level != "HIGH":
        return {
            "rerouted": False,
            "recommended_route": current_route,
            "reason": "Current route is not high risk.",
        }

    alternative_route = find_safe_route(routes)

    if alternative_route is None:
        return {
            "rerouted": False,
            "recommended_route": None,
            "reason": "No safe alternative route available.",
        }

    return {
        "rerouted": True,
        "recommended_route": alternative_route,
        "reason": "Current route is high risk.",
    }


def main():
    print("\n============================================")
    print("   PHASE 3.10.2 - NO SAFE ROUTE TEST")
    print("============================================\n")

    routes = {
        "Route A": {
            "distance": 5,
            "risk": 85,
        },
        "Route B": {
            "distance": 8,
            "risk": 90,
        },
        "Route C": {
            "distance": 6,
            "risk": 78,
        },
    }

    current_route = "Route A"

    print("Available Routes:")

    for route, data in routes.items():
        print(
            f"  {route}: "
            f"Risk = {data['risk']}/100 | "
            f"Level = {get_risk_level(data['risk'])}"
        )

    result = dynamic_reroute(
        routes,
        current_route
    )

    print("\n============================================")
    print("           REROUTING RESULT")
    print("============================================")

    print(
        f"\nRerouting Required : "
        f"{result['rerouted']}"
    )

    print(
        f"Recommended Route  : "
        f"{result['recommended_route']}"
    )

    print(
        f"Reason             : "
        f"{result['reason']}"
    )

    print("\n============================================")
    print("      PHASE 3.10.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
