"""
JARVIS Phase 4 - Alert Rules

Defines the conditions that determine when
a safety alert should be generated.
"""


def get_alert_level(overall_risk):
    """
    Convert overall risk into an alert level.
    """

    level = str(overall_risk).strip().upper()

    if level == "HIGH":
        return "CRITICAL"
    elif level == "MEDIUM":
        return "WARNING"
    elif level == "LOW":
        return "INFO"
    else:
        raise ValueError(
            f"Invalid overall risk level: {overall_risk}"
        )


def should_alert(overall_risk):
    """
    Determine whether an alert should be generated.

    HIGH and MEDIUM risks generate alerts.
    LOW risk does not require a safety alert.
    """

    level = str(overall_risk).strip().upper()

    if level not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError(
            f"Invalid overall risk level: {overall_risk}"
        )

    return level in {"MEDIUM", "HIGH"}


if __name__ == "__main__":

    print("\n============================================")
    print("          PHASE 4 - ALERT RULES")
    print("============================================")

    for risk in ["LOW", "MEDIUM", "HIGH"]:
        print(
            f"{risk:7} -> "
            f"Alert Level: {get_alert_level(risk):8} | "
            f"Alert Required: {should_alert(risk)}"
        )

    print("\nAlert rules: PASSED")

    print("\n============================================")
