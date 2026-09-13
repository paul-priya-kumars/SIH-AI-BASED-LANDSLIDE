"""
JARVIS Phase 4 - Notification

Formats Phase 4 alerts into a notification-ready
message for the UI or future notification service.
"""


def create_notification(alert):
    """
    Convert an alert result into a notification payload.
    """

    if not isinstance(alert, dict):
        raise TypeError("Alert must be a dictionary.")

    required_fields = [
        "alert_required",
        "alert_level",
        "message",
        "overall_risk",
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in alert
    ]

    if missing_fields:
        raise ValueError(
            "Missing alert fields: "
            + ", ".join(missing_fields)
        )

    return {
        "type": "SAFETY_ALERT",
        "level": alert["alert_level"],
        "risk": alert["overall_risk"],
        "message": alert["message"],
        "display": alert["alert_required"],
    }


if __name__ == "__main__":

    test_alert = {
        "alert_required": True,
        "alert_level": "CRITICAL",
        "message": (
            "HIGH RISK detected. "
            "Immediate safety attention is recommended."
        ),
        "overall_risk": "HIGH",
    }

    notification = create_notification(test_alert)

    print("\n============================================")
    print("         PHASE 4 - NOTIFICATION")
    print("============================================")

    print("\nNotification:")
    print("Type    :", notification["type"])
    print("Level   :", notification["level"])
    print("Risk    :", notification["risk"])
    print("Display :", notification["display"])
    print("Message :", notification["message"])

    print("\nNotification: PASSED")

    print("\n============================================")