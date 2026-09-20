from pathlib import Path

import joblib
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "model_training"
    / "xgboost_tuned_risk_model.joblib"
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
    """Load the tuned XGBoost risk model and label encoder."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Tuned XGBoost model not found: {MODEL_FILE}"
        )

    saved_model = joblib.load(MODEL_FILE)

    return (
        saved_model["model"],
        saved_model["label_encoder"],
    )


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
    Predict risk level and class probabilities
    using the tuned XGBoost model.

    Returns:
        Dictionary containing risk level,
        probabilities, and confidence.
    """

    model, label_encoder = load_model()

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

    # XGBoost returns the encoded class number.
    prediction_encoded = model.predict(input_data)[0]

    # Convert encoded class back to LOW / MEDIUM / HIGH.
    prediction = label_encoder.inverse_transform(
        [int(prediction_encoded)]
    )[0]

    probabilities = model.predict_proba(input_data)[0]

    # Probability columns correspond to encoded class order.
    class_indices = list(range(len(label_encoder.classes_)))

    class_labels = label_encoder.inverse_transform(
        class_indices
    )

    probability_map = {
        str(label): float(probability)
        for label, probability in zip(
            class_labels,
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
    print("   PHASE 7 - TUNED XGBOOST RISK ENGINE")
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
    print("     PHASE 7 XGBOOST INTEGRATION TEST")
    print("============================================\n")


if __name__ == "__main__":
    main()