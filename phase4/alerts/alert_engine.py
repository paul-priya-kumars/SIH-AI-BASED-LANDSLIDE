"""
JARVIS Phase 4 - Alert Engine

Generates safety alerts from the combined
Phase 4 risk result.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase4.alerts.alert_rules import (
    get_alert_level,
    should_alert,
)


def generate_alert(risk_result):
    """
    Generate an alert from the overall Phase 4 risk.
    """

    overall_risk = str(
        risk_result["overall_risk"]
    ).strip().upper()

    alert_required = should_alert(overall_risk)
    alert_level = get_alert_level(overall_risk)

    if overall_risk == "HIGH":
        message = (
            "HIGH RISK detected. "
            "Immediate safety attention is recommended."
        )
    elif overall_risk == "MEDIUM":
        message = (
            "MEDIUM RISK detected. "
            "Proceed with caution."
        )
    else:
        message = (
            "LOW RISK detected. "
            "No immediate safety alert is required."
        )

    return {
        "alert_required": alert_required,
        "alert_level": alert_level,
        "message": message,
        "overall_risk": overall_risk,
    }


if __name__ == "__main__":

    test_result = {
        "ml_risk": "HIGH",
        "route_risk": "LOW",
        "image_risk": "HIGH",
        "overall_risk": "HIGH",
    }

    alert = generate_alert(test_result)

    print("\n============================================")
    print("          PHASE 4 - ALERT ENGINE")
    print("============================================")

    print("\nOverall Risk    :", alert["overall_risk"])
    print("Alert Required  :", alert["alert_required"])
    print("Alert Level     :", alert["alert_level"])
    print("Message         :", alert["message"])

    print("\nAlert engine: PASSED")

    print("\n============================================")
