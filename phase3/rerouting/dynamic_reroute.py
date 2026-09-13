def get_risk_level(risk_score):
    """Convert risk score to a risk level."""

    if risk_score < 40:
        return "LOW"
    elif risk_score < 70:
        return "MEDIUM"
    else:
        return "HIGH"


def find_safe_route(routes):
    """Find the lowest-risk route."""

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
    """Reroute when the current route is high risk."""

    current_risk = routes[current_route]["risk"]
    current_level = get_risk_level(current_risk)

    if current_level != "HIGH":
        return {
            "rerouted": False,
            "current_route": current_route,
            "recommended_route": current_route,
            "reason": "Current route is not high risk.",
        }

    alternative_route = find_safe_route(routes)

    if alternative_route is None:
        return {
            "rerouted": False,
            "current_route": current_route,
            "recommended_route": None,
            "reason": "No safe alternative route available.",
        }

    return {
        "rerouted": True,
        "current_route": current_route,
        "recommended_route": alternative_route,
        "reason": "Current route is high risk.",
    }


def main():
    print("\n============================================")
    print("       PHASE 3.10.1 - DYNAMIC REROUTING")
    print("============================================\n")

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

    print("Current Route:")
    print(f"  Route       : {current_route}")
    print(f"  Risk Score  : {routes[current_route]['risk']}/100")
    print(
        f"  Risk Level  : "
        f"{get_risk_level(routes[current_route]['risk'])}"
    )

    result = dynamic_reroute(
        routes,
        current_route
    )

    print("\n============================================")
    print("           REROUTING DECISION")
    print("============================================")

    print(
        f"\nRerouting Required : "
        f"{result['rerouted']}"
    )

    print(
        f"Current Route      : "
        f"{result['current_route']}"
    )

    print(
        f"Recommended Route  : "
        f"{result['recommended_route']}"
    )

    print(
        f"Reason             : "
        f"{result['reason']}"
    )

    if result["rerouted"]:
        recommended = result["recommended_route"]

        print("\nNEW ROUTE DETAILS")
        print(
            f"  Distance : "
            f"{routes[recommended]['distance']} km"
        )
        print(
            f"  Risk     : "
            f"{routes[recommended]['risk']}/100"
        )
        print(
            f"  Level    : "
            f"{get_risk_level(routes[recommended]['risk'])}"
        )

    print("\n============================================")
    print("      PHASE 3.10.1 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
