"""
JARVIS Phase 5 - Final Risk Engine
"""

RISK_VALUES = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def normalize_risk(risk):
    if isinstance(risk, str):
        risk = risk.upper()

        if risk in RISK_VALUES:
            return risk

    if isinstance(risk, (int, float)):
        if risk >= 70:
            return "HIGH"

        if risk >= 40:
            return "MEDIUM"

        return "LOW"

    raise ValueError(f"Invalid risk value: {risk}")


def calculate_final_risk(
    ml_risk,
    image_risk,
    route_risk
):
    ml = normalize_risk(ml_risk)
    image = normalize_risk(image_risk)
    route = normalize_risk(route_risk)

    final_risk = max(
        [ml, image, route],
        key=lambda value: RISK_VALUES[value]
    )

    return {
        "ml_risk": ml,
        "image_risk": image,
        "route_risk": route,
        "final_risk": final_risk
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - FINAL RISK ENGINE")
    print("============================================")

    result = calculate_final_risk(
        ml_risk="HIGH",
        image_risk="HIGH",
        route_risk="LOW"
    )

    print()
    print("Risk Inputs:")
    print("ML Risk    :", result["ml_risk"])
    print("Image Risk :", result["image_risk"])
    print("Route Risk :", result["route_risk"])

    print()
    print("Final Risk :", result["final_risk"])

    assert result["final_risk"] == "HIGH"

    print()
    print("Final risk engine: PASSED")

    print()
    print("============================================")