from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


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

TARGET_COLUMN = "risk_level"


def main() -> None:
    print("\n============================================")
    print("     PHASE 3.4.1 - MODEL EVALUATION")
    print("============================================\n")

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_FILE}"
        )

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_FILE}"
        )

    test_df = pd.read_csv(TEST_FILE)

    model = joblib.load(MODEL_FILE)

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    print(f"Test records : {len(test_df)}")
    print(f"Accuracy     : {accuracy:.4f}")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )

    labels = ["LOW", "MEDIUM", "HIGH"]

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=labels,
    )

    print("Confusion Matrix:")
    print("             LOW  MEDIUM  HIGH")

    for label, row in zip(labels, matrix):
        print(
            f"{label:<10} "
            f"{row[0]:>3} "
            f"{row[1]:>7} "
            f"{row[2]:>5}"
        )

    print("\nActual vs Predicted:")

    for actual, predicted in zip(
        y_test,
        predictions,
    ):
        print(
            f"  Actual: {actual:<6} "
            f"Predicted: {predicted}"
        )

    print("\n============================================")
    print("     PHASE 3.4.1 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()