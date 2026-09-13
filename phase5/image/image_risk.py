"""
JARVIS Phase 5 - Image Risk Analysis
"""


def calculate_image_risk(image_result):
    if not isinstance(image_result, dict):
        raise ValueError("Image result must be a dictionary")

    landslide = bool(image_result.get("landslide", False))
    flooding = bool(image_result.get("flooding", False))
    road_damage = bool(image_result.get("road_damage", False))

    detected_conditions = []

    if landslide:
        detected_conditions.append("LANDSLIDE")

    if flooding:
        detected_conditions.append("FLOODING")

    if road_damage:
        detected_conditions.append("ROAD_DAMAGE")

    condition_count = len(detected_conditions)

    if landslide:
        risk_level = "HIGH"
        risk_score = 90

    elif flooding and road_damage:
        risk_level = "HIGH"
        risk_score = 80

    elif flooding or road_damage:
        risk_level = "MEDIUM"
        risk_score = 60

    else:
        risk_level = "LOW"
        risk_score = 10

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "detected_conditions": detected_conditions,
        "condition_count": condition_count
    }


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - IMAGE RISK ANALYSIS")
    print("============================================")

    image_result = {
        "landslide": False,
        "flooding": True,
        "road_damage": False
    }

    result = calculate_image_risk(image_result)

    print()
    print("Image Conditions:")

    if result["detected_conditions"]:
        for condition in result["detected_conditions"]:
            print(" -", condition)
    else:
        print(" - NONE")

    print()
    print("Image Risk Score :", result["risk_score"], "/100")
    print("Image Risk Level :", result["risk_level"])

    assert result["risk_level"] == "MEDIUM"
    assert result["risk_score"] == 60
    assert "FLOODING" in result["detected_conditions"]

    print()
    print("Image risk analysis: PASSED")

    print()
    print("============================================")