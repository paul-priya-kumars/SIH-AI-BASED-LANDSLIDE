"""
JARVIS Phase 5 - Decision Engine

Converts risk information into safety decisions.
"""


RISK_VALUES = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3
}


def make_decision(
    final_risk,
    current_route_risk,
    safer_route_available
):
    final_risk = final_risk.upper()
    current_route_risk = current_route_risk.upper()

    if final_risk not in RISK_VALUES:
        raise ValueError("Invalid final risk level")

    if current_route_risk not in RISK_VALUES:
        raise ValueError("Invalid route risk level")

    alert_required = final_risk in ("MEDIUM", "HIGH")

    if final_risk == "HIGH":
        alert_level = "CRITICAL"
    elif final_risk == "MEDIUM":
        alert_level = "WARNING"
    else:
        alert_level = "INFO"

    reroute_required = (
        current_route_risk == "HIGH"
        and safer_route_available
    )

    if reroute_required:
        route_action = "REROUTE"
    else:
        route_action = "CONTINUE"

    if final_risk == "HIGH":
        priority = "IMMEDIATE"
    elif final_risk == "MEDIUM":
        priority = "HIGH"
    else:
        priority = "NORMAL"

    return {
        "final_risk": final_risk,
        "alert_required": alert_required,
        "alert_level": alert_level,
        "reroute_required": reroute_required,
        "route_action": route_action,
        "priority": priority
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - DECISION ENGINE")
    print("============================================")

    result = make_decision(
        final_risk="HIGH",
        current_route_risk="HIGH",
        safer_route_available=True
    )

    print()
    print("Final Risk       :", result["final_risk"])
    print("Alert Required   :", result["alert_required"])
    print("Alert Level      :", result["alert_level"])
    print("Reroute Required :", result["reroute_required"])
    print("Route Action     :", result["route_action"])
    print("Priority         :", result["priority"])

    assert result["final_risk"] == "HIGH"
    assert result["alert_required"] is True
    assert result["alert_level"] == "CRITICAL"
    assert result["reroute_required"] is True
    assert result["route_action"] == "REROUTE"
    assert result["priority"] == "IMMEDIATE"

    print()
    print("Decision engine: PASSED")

    print()
    print("============================================")