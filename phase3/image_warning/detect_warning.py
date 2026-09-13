WARNING_TYPES = [
    "landslide",
    "flooding",
    "road_damage",
]


def detect_warning(image_result):
    """
    Convert image-analysis indicators into
    a standardized warning result.
    """

    detected_conditions = []

    for warning_type in WARNING_TYPES:
        if image_result.get(warning_type, False):
            detected_conditions.append(
                warning_type.upper()
            )

    # Determine severity
    if "LANDSLIDE" in detected_conditions:
        warning_level = "HIGH"
        action = "WARNING"

    elif "FLOODING" in detected_conditions:
        warning_level = "HIGH"
        action = "WARNING"

    elif "ROAD_DAMAGE" in detected_conditions:
        warning_level = "MEDIUM"
        action = "CAUTION"

    else:
        warning_level = "LOW"
        action = "SAFE"

    return {
        "detected_conditions": detected_conditions,
        "warning_level": warning_level,
        "action": action,
        "warning_detected": bool(detected_conditions),
    }


def main():
    print("\n============================================")
    print(" PHASE 3.8.2 - IMAGE WARNING SEVERITY")
    print("============================================\n")

    # Simulated image-analysis result.
    image_result = {
        "landslide": False,
        "flooding": True,
        "road_damage": False,
    }

    print("Image Analysis Input:")

    for condition, detected in image_result.items():
        print(
            f"  {condition:<15}: {detected}"
        )

    result = detect_warning(image_result)

    print("\n============================================")
    print("          WARNING RESULT")
    print("============================================")

    print(
        f"\nWarning Detected : "
        f"{result['warning_detected']}"
    )

    print(
        f"Warning Level    : "
        f"{result['warning_level']}"
    )

    print(
        f"Recommended Action: "
        f"{result['action']}"
    )

    print("\nDetected Conditions:")

    if result["detected_conditions"]:
        for condition in result["detected_conditions"]:
            print(f"  - {condition}")
    else:
        print("  None")

    print("\n============================================")
    print(" PHASE 3.8.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
