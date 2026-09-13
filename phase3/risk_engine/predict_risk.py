from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "model_training"
    / "risk_model.joblib"
)


FEATURE_COLUMNS = [
    "rainfall_mm",
    "soil_moisture_pct",
    "slope_deg",
    "elevation_m",
    "temperature_c",
    "river_level_m",
    "vegetation_index",
    "landslide_history",
]


def load_model():
    """Load the trained Phase 3 risk model."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Risk model not found: {MODEL_FILE}"
        )

    return joblib.load(MODEL_FILE)


def predict_risk(
    rainfall_mm,
    soil_moisture_pct,
    slope_deg,
    elevation_m,
    temperature_c,
    river_level_m,
    vegetation_index,
    landslide_history,
):
    """
    Predict risk level and class probabilities.

    Returns:
        Dictionary containing risk level,
        probabilities, and confidence.
    """

    model = load_model()

    input_data = pd.DataFrame(
        [[
            rainfall_mm,
            soil_moisture_pct,
            slope_deg,
            elevation_m,
            temperature_c,
            river_level_m,
            vegetation_index,
            landslide_history,
        ]],
        columns=FEATURE_COLUMNS,
    )

    prediction = model.predict(input_data)[0]

    probabilities = model.predict_proba(input_data)[0]

    classes = model.classes_

    probability_map = {
        str(label): float(probability)
        for label, probability in zip(
            classes,
            probabilities,
        )
    }

    confidence = probability_map[str(prediction)]

    return {
        "risk_level": str(prediction),
        "probabilities": probability_map,
        "confidence": float(confidence),
    }


def main():
    print("\n============================================")
    print("   PHASE 3.5.2 - RISK PROBABILITY ENGINE")
    print("============================================\n")

    # Test environmental conditions
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

    print("Input Conditions:")

    for key, value in test_input.items():
        print(f"  {key:<22}: {value}")

    result = predict_risk(**test_input)

    print("\n============================================")
    print("             PREDICTION RESULT")
    print("============================================")

    print(
        f"\nPredicted Risk : "
        f"{result['risk_level']}"
    )

    print("\nRisk Probabilities:")

    for level in ["LOW", "MEDIUM", "HIGH"]:
        probability = result["probabilities"].get(
            level,
            0.0,
        )

        print(
            f"  {level:<7}: "
            f"{probability * 100:.2f}%"
        )

    print(
        f"\nConfidence     : "
        f"{result['confidence'] * 100:.2f}%"
    )

    print("\n============================================")
    print("     PHASE 3.5.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
