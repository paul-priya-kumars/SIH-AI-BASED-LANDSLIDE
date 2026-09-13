"""
JARVIS Phase 4 - Risk Engine

Combines multiple risk signals into one overall
Phase 4 risk level.
"""

import sys
from pathlib import Path


# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase4.risk.risk_levels import (
    get_highest_risk,
    normalize_risk_level,
)


def calculate_overall_risk(
    ml_risk,
    route_risk,
    image_risk,
):
    """
    Calculate the overall Phase 4 risk.

    The highest validated risk signal determines
    the overall risk level.
    """

    ml_risk = normalize_risk_level(ml_risk)
    route_risk = normalize_risk_level(route_risk)
    image_risk = normalize_risk_level(image_risk)

    overall_risk = get_highest_risk(
        ml_risk,
        route_risk,
        image_risk,
    )

    return {
        "ml_risk": ml_risk,
        "route_risk": route_risk,
        "image_risk": image_risk,
        "overall_risk": overall_risk,
    }


if __name__ == "__main__":

    test_result = calculate_overall_risk(
        ml_risk="HIGH",
        route_risk="LOW",
        image_risk="HIGH",
    )

    print("\n============================================")
    print("          PHASE 4 - RISK ENGINE")
    print("============================================")

    print("\nRisk Inputs:")
    print("ML Risk    :", test_result["ml_risk"])
    print("Route Risk :", test_result["route_risk"])
    print("Image Risk :", test_result["image_risk"])

    print("\nOverall Risk :", test_result["overall_risk"])

    print("\nRisk engine: PASSED")

    print("\n============================================")
