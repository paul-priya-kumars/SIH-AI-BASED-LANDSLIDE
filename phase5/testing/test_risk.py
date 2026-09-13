"""
JARVIS Phase 5 - Risk Test
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase5.integration.risk_engine import calculate_final_risk
from phase5.integration.decision_engine import make_decision
from phase5.image.image_risk import calculate_image_risk


def get_risk_level(result):
    if isinstance(result, str):
        return result.upper()

    if isinstance(result, dict):

        if "risk_level" in result:
            return str(result["risk_level"]).upper()

        if "final_risk" in result:
            return str(result["final_risk"]).upper()

        if "risk" in result:
            risk = result["risk"]

            if isinstance(risk, str):
                return risk.upper()

            if isinstance(risk, dict):

                if "risk_level" in risk:
                    return str(risk["risk_level"]).upper()

                if "final_risk" in risk:
                    return str(risk["final_risk"]).upper()

    raise ValueError("Risk level not found")


def main():

    print()
    print("============================================")
    print("       PHASE 5 - RISK TEST")
    print("============================================")

    print()
    print("1. Final Risk Engine")

    test_cases = [
        ("LOW", "LOW", "LOW", "LOW"),
        ("MEDIUM", "LOW", "LOW", "MEDIUM"),
        ("HIGH", "LOW", "LOW", "HIGH"),
        ("LOW", "HIGH", "LOW", "HIGH"),
        ("LOW", "LOW", "HIGH", "HIGH"),
        ("HIGH", "HIGH", "LOW", "HIGH"),
        ("HIGH", "MEDIUM", "HIGH", "HIGH")
    ]

    for ml_risk, image_risk, route_risk, expected in test_cases:

        result = calculate_final_risk(
            ml_risk,
            image_risk,
            route_risk
        )

        final_risk = get_risk_level(result)

        print(
            f"ML={ml_risk} | "
            f"Image={image_risk} | "
            f"Route={route_risk} "
            f"-> Final={final_risk}"
        )

        assert final_risk == expected

    print("Final risk engine : PASSED")

    print()
    print("2. Image Risk Analysis")

    safe_image = {
        "landslide": False,
        "flooding": False,
        "road_damage": False
    }

    medium_image = {
        "landslide": False,
        "flooding": True,
        "road_damage": False
    }

    high_image = {
        "landslide": True,
        "flooding": False,
        "road_damage": False
    }

    safe_result = calculate_image_risk(safe_image)
    medium_result = calculate_image_risk(medium_image)
    high_result = calculate_image_risk(high_image)

    assert get_risk_level(safe_result) == "LOW"
    assert get_risk_level(medium_result) == "MEDIUM"
    assert get_risk_level(high_result) == "HIGH"

    print("LOW image risk    : PASSED")
    print("MEDIUM image risk : PASSED")
    print("HIGH image risk   : PASSED")

    print()
    print("3. Decision Engine")

    low_decision = make_decision(
        "LOW",
        "LOW",
        False
    )

    medium_decision = make_decision(
        "MEDIUM",
        "MEDIUM",
        False
    )

    high_decision = make_decision(
        "HIGH",
        "HIGH",
        True
    )

    print(
        "LOW    ->",
        low_decision["priority"]
    )

    print(
        "MEDIUM ->",
        medium_decision["priority"]
    )

    print(
        "HIGH   ->",
        high_decision["priority"]
    )

    assert low_decision["priority"] != "IMMEDIATE"
    assert medium_decision["priority"] == "HIGH"
    assert high_decision["priority"] == "IMMEDIATE"
    assert high_decision["reroute_required"] is True

    print("Decision engine : PASSED")

    print()
    print("4. Risk Escalation")

    result = calculate_final_risk(
        "HIGH",
        "LOW",
        "LOW"
    )

    assert get_risk_level(result) == "HIGH"

    result = calculate_final_risk(
        "LOW",
        "HIGH",
        "LOW"
    )

    assert get_risk_level(result) == "HIGH"

    result = calculate_final_risk(
        "LOW",
        "LOW",
        "HIGH"
    )

    assert get_risk_level(result) == "HIGH"

    print("Risk escalation : PASSED")

    print()
    print("============================================")
    print("       ALL RISK TESTS PASSED")
    print("============================================")


if __name__ == "__main__":
    main()