from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TEST_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "test_dataset.csv"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "model_training"
    / "xgboost_risk_model.joblib"
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

TARGET_COLUMN = "risk_level"

CLASS_NAMES = [
    "LOW",
    "MEDIUM",
    "HIGH",
]


def main() -> None:

    print("\n============================================")
    print("     PHASE 3.4.2 - XGBOOST MODEL EVALUATION")
    print("============================================\n")

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_FILE}"
        )

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"XGBoost model not found: {MODEL_FILE}"
        )

    df = pd.read_csv(TEST_FILE)

    X_test = df[FEATURE_COLUMNS]
    y_test = df[TARGET_COLUMN]

    saved_model = joblib.load(MODEL_FILE)

    model = saved_model["model"]
    label_encoder = saved_model["label_encoder"]

    y_test_encoded = label_encoder.transform(y_test)

    y_pred_encoded = model.predict(X_test)

    y_pred = label_encoder.inverse_transform(
        y_pred_encoded.astype(int)
    )

    accuracy = accuracy_score(
        y_test,
        y_pred,
    )

    print(f"Test records : {len(df)}")
    print(f"Accuracy     : {accuracy:.4f}")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            y_pred,
            labels=CLASS_NAMES,
            zero_division=0,
        )
    )

    print("Confusion Matrix:")

    matrix = confusion_matrix(
        y_test,
        y_pred,
        labels=CLASS_NAMES,
    )

    print("             LOW  MEDIUM  HIGH")

    for actual_class, row in zip(CLASS_NAMES, matrix):
        print(
            f"{actual_class:<12}"
            f"{row[0]:<5}"
            f"{row[1]:<8}"
            f"{row[2]}"
        )

    print("\nActual vs Predicted:")

    for actual, predicted in zip(
        y_test,
        y_pred,
    ):
        print(
            f"  Actual: {actual:<6} "
            f"Predicted: {predicted}"
        )

    print("\n============================================")
    print("     PHASE 3.4.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()