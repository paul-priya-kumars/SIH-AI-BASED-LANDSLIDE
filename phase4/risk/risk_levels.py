"""
JARVIS Phase 4 - Risk Levels

Centralized risk-level definitions used by
the Phase 4 risk engine.
"""


RISK_VALUES = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def normalize_risk_level(risk_level):
    """
    Normalize a risk level to LOW, MEDIUM, or HIGH.
    """

    level = str(risk_level).strip().upper()

    if level == "MODERATE":
        level = "MEDIUM"

    if level not in RISK_VALUES:
        raise ValueError(
            f"Invalid risk level: {risk_level}"
        )

    return level


def get_highest_risk(*risk_levels):
    """
    Return the highest risk level supplied.
    """

    normalized_levels = [
        normalize_risk_level(level)
        for level in risk_levels
    ]

    if not normalized_levels:
        raise ValueError("At least one risk level is required.")

    return max(
        normalized_levels,
        key=lambda level: RISK_VALUES[level]
    )


def get_risk_value(risk_level):
    """
    Return the numeric value for a risk level.
    """

    level = normalize_risk_level(risk_level)

    return RISK_VALUES[level]


if __name__ == "__main__":

    print("\n============================================")
    print("       PHASE 4 - RISK LEVEL TEST")
    print("============================================")

    print("\nRisk Values:")
    print("LOW    :", get_risk_value("LOW"))
    print("MEDIUM :", get_risk_value("MEDIUM"))
    print("HIGH   :", get_risk_value("HIGH"))

    highest = get_highest_risk(
        "LOW",
        "MEDIUM",
        "HIGH"
    )

    print("\nHighest Risk :", highest)

    moderate_test = normalize_risk_level("MODERATE")
    print("MODERATE Normalized :", moderate_test)

    print("\nRisk levels: PASSED")

    print("\n============================================")
