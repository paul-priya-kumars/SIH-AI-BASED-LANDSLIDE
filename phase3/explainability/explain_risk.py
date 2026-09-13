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


FEATURE_NAMES = [
    "rainfall_mm",
    "soil_moisture_pct",
    "slope_deg",
    "elevation_m",
    "temperature_c",
    "river_level_m",
    "vegetation_index",
    "landslide_history",
]


DISPLAY_NAMES = {
    "rainfall_mm": "Rainfall",
    "soil_moisture_pct": "Soil Moisture",
    "slope_deg": "Slope",
    "elevation_m": "Elevation",
    "temperature_c": "Temperature",
    "river_level_m": "River Level",
    "vegetation_index": "Vegetation Index",
    "landslide_history": "Landslide History",
}


def load_model():
    """Load the trained Random Forest model."""

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Risk model not found: {MODEL_FILE}"
        )

    return joblib.load(MODEL_FILE)


def get_feature_importance(model):
    """Get sorted feature importance values."""

    classifier = model.named_steps["classifier"]

    importances = classifier.feature_importances_

    feature_importance = []

    for feature, importance in zip(
        FEATURE_NAMES,
        importances,
    ):
        feature_importance.append(
            {
                "feature": feature,
                "name": DISPLAY_NAMES[feature],
                "importance": float(importance),
            }
        )

    feature_importance.sort(
        key=lambda item: item["importance"],
        reverse=True,
    )

    return feature_importance


def predict_risk(model, input_data):
    """Predict risk level."""

    dataframe = pd.DataFrame(
        [input_data],
        columns=FEATURE_NAMES,
    )

    prediction = model.predict(dataframe)[0]

    return str(prediction)


def generate_explanation(
    risk_level,
    feature_importance,
    input_data,
):
    """Generate a human-readable explanation."""

    top_factors = feature_importance[:3]

    explanation = []

    explanation.append(
        f"Current predicted risk level: {risk_level}."
    )

    explanation.append(
        "The strongest model feature signals are:"
    )

    for factor in top_factors:
        feature = factor["feature"]
        name = factor["name"]
        importance = factor["importance"]

        value = input_data[feature]

        explanation.append(
            f"- {name}: {value} "
            f"(model importance "
            f"{importance * 100:.2f}%)."
        )

    explanation.append(
        "These are model feature-importance signals "
        "and should not be interpreted as proof of "
        "real-world causation."
    )

    return explanation


def main():
    print("\n============================================")
    print("    PHASE 3.7.2 - HUMAN READABLE RISK")
    print("============================================\n")

    model = load_model()

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

    risk_level = predict_risk(
        model,
        test_input,
    )

    feature_importance = get_feature_importance(
        model
    )

    explanation = generate_explanation(
        risk_level,
        feature_importance,
        test_input,
    )

    print("Risk Level:")
    print(f"  {risk_level}")

    print("\nRisk Explanation:")

    for line in explanation:
        print(f"  {line}")

    print("\n============================================")
    print("    PHASE 3.7.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()
