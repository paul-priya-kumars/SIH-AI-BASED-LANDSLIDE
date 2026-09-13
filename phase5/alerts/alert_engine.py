"""
JARVIS Phase 5 - Alert Engine
"""


def create_alert(final_risk, reroute_required):
    final_risk = final_risk.upper()

    if final_risk not in ("LOW", "MEDIUM", "HIGH"):
        raise ValueError("Invalid risk level")

    if final_risk == "HIGH":
        alert_required = True
        alert_level = "CRITICAL"
        message = (
            "HIGH RISK detected. "
            "Immediate safety attention is recommended."
        )

    elif final_risk == "MEDIUM":
        alert_required = True
        alert_level = "WARNING"
        message = (
            "MEDIUM RISK detected. "
            "Caution is recommended."
        )

    else:
        alert_required = False
        alert_level = "INFO"
        message = "LOW RISK detected. Conditions are currently safe."

    if reroute_required:
        route_message = " Rerouting is recommended."
    else:
        route_message = ""

    return {
        "alert_required": alert_required,
        "alert_level": alert_level,
        "risk_level": final_risk,
        "message": message + route_message
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - ALERT ENGINE")
    print("============================================")

    result = create_alert(
        final_risk="HIGH",
        reroute_required=True
    )

    print()
    print("Risk Level     :", result["risk_level"])
    print("Alert Required :", result["alert_required"])
    print("Alert Level    :", result["alert_level"])
    print("Message        :", result["message"])

    assert result["risk_level"] == "HIGH"
    assert result["alert_required"] is True
    assert result["alert_level"] == "CRITICAL"
    assert "Rerouting is recommended." in result["message"]

    print()
    print("Alert engine: PASSED")

    print()
    print("============================================")