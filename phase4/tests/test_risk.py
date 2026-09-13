"""
JARVIS Phase 4 - Risk Tests
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase4.risk.risk_levels import get_highest_risk
from phase4.risk.risk_engine import calculate_overall_risk
from phase4.risk.risk_explanation import explain_risk


def test_risk_levels():

    assert get_highest_risk(
        "LOW",
        "MEDIUM",
        "HIGH"
    ) == "HIGH"


def test_risk_engine():

    result = calculate_overall_risk(
        ml_risk="HIGH",
        route_risk="LOW",
        image_risk="HIGH",
    )

    assert result["overall_risk"] == "HIGH"


def test_risk_explanation():

    result = {
        "ml_risk": "HIGH",
        "route_risk": "LOW",
        "image_risk": "HIGH",
        "overall_risk": "HIGH",
    }

    explanation = explain_risk(result)

    assert explanation["overall_risk"] == "HIGH"
    assert len(explanation["reasons"]) > 0


if __name__ == "__main__":

    print("\n============================================")
    print("       PHASE 4 - RISK TESTS")
    print("============================================")

    test_risk_levels()
    print("Risk levels       : PASSED")

    test_risk_engine()
    print("Risk engine       : PASSED")

    test_risk_explanation()
    print("Risk explanation  : PASSED")

    print("\n============================================")
    print("       ALL RISK TESTS PASSED")
    print("============================================")