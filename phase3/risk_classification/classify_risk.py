from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RISK_ENGINE_DIR = PROJECT_ROOT / "phase3" / "risk_engine"

sys.path.insert(0, str(RISK_ENGINE_DIR))

from predict_risk import predict_risk


def classify_risk(result):
    """
    Convert ML prediction and confidence into
    a standardized JARVIS risk classification.
    """

    risk_level = result["risk_level"]
    confidence = result["confidence"]

    # Confidence-aware classification
    if risk_level == "HIGH":
        status = "HIGH RISK"
        action = "WARNING"

    elif risk_level == "MEDIUM":
        status = "MEDIUM RISK"
        action = "CAUTION"

    else:
        status = "LOW RISK"
        action = "SAFE"

    # Confidence category
    if confidence >= 0.80:
        confidence_level = "HIGH CONFIDENCE"

    elif confidence >= 0.60:
        confidence_level = "MODERATE CONFIDENCE"

    else:
        confidence_level = "LOW CONFIDENCE"

    return {
        "risk_level": risk_level,
        "status": status,
        "action": action,
        "confidence": confidence,
        "confidence_level": confidence_level,
    }


def main():
    print("\n============================================")
    print("   PHASE 3.6.2 - CONFIDENCE CLASSIFICATION")
    print("============================================\n")

    test_input = {
        "rainfall_mm": 180,
        "soil_moisture_pct": 85,
        "slope_deg": 32,
        "elevation_m": 650,
        "temperature_c": 23,
        "river_level_m": 5.2,
        "vegetation_index": 0.35,
        "landslide_history": 1,
    }

    print("Running risk prediction...")

    prediction = predict_risk(**test_input)

    classification = classify_risk(prediction)

    print("\n============================================")
    print("        CLASSIFICATION RESULT")
    print("============================================")

    print(
        f"\nRisk Level       : "
        f"{classification['risk_level']}"
    )

    print(
        f"Status           : "
        f"{classification['status']}"
    )

    print(
        f"Action           : "
        f"{classification['action']}"
    )

    print(
        f"Confidence       : "
        f"{classification['confidence'] * 100:.2f}%"
    )

    print(
        f"Confidence Level : "
        f"{classification['confidence_level']}"
    )

    print("\n============================================")
    print("   PHASE 3.6.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
