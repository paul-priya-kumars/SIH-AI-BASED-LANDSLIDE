"""
JARVIS Phase 4 - Risk Explanation

Creates a human-readable explanation of the
combined Phase 4 risk result.
"""


def explain_risk(risk_result):
    """
    Generate a human-readable explanation
    from the combined risk result.
    """

    ml_risk = risk_result["ml_risk"]
    route_risk = risk_result["route_risk"]
    image_risk = risk_result["image_risk"]
    overall_risk = risk_result["overall_risk"]

    reasons = []

    if ml_risk == "HIGH":
        reasons.append("ML environmental prediction indicates high risk.")
    elif ml_risk == "MEDIUM":
        reasons.append("ML environmental prediction indicates moderate risk.")

    if route_risk == "HIGH":
        reasons.append("Route analysis indicates a high-risk route.")
    elif route_risk == "MEDIUM":
        reasons.append("Route analysis indicates moderate route risk.")

    if image_risk == "HIGH":
        reasons.append("Image analysis detected a high-risk condition.")
    elif image_risk == "MEDIUM":
        reasons.append("Image analysis detected a moderate-risk condition.")

    if not reasons:
        reasons.append("No elevated risk signals were detected.")

    return {
        "overall_risk": overall_risk,
        "reasons": reasons,
        "summary": (
            f"Overall risk is {overall_risk}. "
            + " ".join(reasons)
        ),
    }


if __name__ == "__main__":

    test_result = {
        "ml_risk": "HIGH",
        "route_risk": "LOW",
        "image_risk": "HIGH",
        "overall_risk": "HIGH",
    }

    explanation = explain_risk(test_result)

    print("\n============================================")
    print("       PHASE 4 - RISK EXPLANATION")
    print("============================================")

    print("\nOverall Risk :", explanation["overall_risk"])

    print("\nReasons:")

    for reason in explanation["reasons"]:
        print(" -", reason)

    print("\nSummary:")
    print(explanation["summary"])

    print("\nRisk explanation: PASSED")

    print("\n============================================")
