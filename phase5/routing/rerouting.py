"""
JARVIS Phase 5 - Dynamic Rerouting
"""


def should_reroute(current_risk, safer_route_available):
    current_risk = current_risk.upper()

    if current_risk not in ("LOW", "MEDIUM", "HIGH"):
        raise ValueError("Invalid route risk level")

    if current_risk == "HIGH" and safer_route_available:
        return True

    return False


def select_safest_route(routes):
    if not routes:
        return None

    safest_route = min(
        routes.items(),
        key=lambda item: item[1]["risk_score"]
    )

    return {
        "route": safest_route[0],
        "risk_score": safest_route[1]["risk_score"],
        "risk_level": safest_route[1]["risk_level"]
    }


def dynamic_reroute(current_route, routes):
    if current_route not in routes:
        raise ValueError("Current route not found")

    current_data = routes[current_route]

    alternative_routes = {
        name: data
        for name, data in routes.items()
        if name != current_route
        and data["risk_score"] < current_data["risk_score"]
    }

    safest = select_safest_route(alternative_routes)

    reroute_required = should_reroute(
        current_data["risk_level"],
        safest is not None
    )

    if reroute_required:
        recommended_route = safest["route"]
        status = "REROUTE RECOMMENDED"
    else:
        recommended_route = None
        status = "NO REROUTE REQUIRED"

    return {
        "current_route": current_route,
        "current_risk": current_data["risk_score"],
        "current_risk_level": current_data["risk_level"],
        "reroute_required": reroute_required,
        "recommended_route": recommended_route,
        "status": status
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - DYNAMIC REROUTING")
    print("============================================")

    routes = {
        "Route A": {
            "risk_score": 34,
            "risk_level": "LOW"
        },
        "Route B": {
            "risk_score": 84,
            "risk_level": "HIGH"
        },
        "Route C": {
            "risk_score": 56,
            "risk_level": "MEDIUM"
        }
    }

    result = dynamic_reroute(
        "Route B",
        routes
    )

    print()
    print("Current Route      :", result["current_route"])
    print("Current Risk       :", result["current_risk"], "/100")
    print("Current Risk Level :", result["current_risk_level"])

    print()
    print("Reroute Required   :", result["reroute_required"])
    print("Recommended Route  :", result["recommended_route"])
    print("Status             :", result["status"])

    assert result["reroute_required"] is True
    assert result["recommended_route"] == "Route A"
    assert result["status"] == "REROUTE RECOMMENDED"

    print()
    print("Dynamic rerouting: PASSED")

    print()
    print("============================================")