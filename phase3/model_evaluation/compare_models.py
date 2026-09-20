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

RANDOM_FOREST_MODEL = (
    PROJECT_ROOT
    / "phase3"
    / "model_training"
    / "risk_model.joblib"
)

XGBOOST_MODEL = (
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


def evaluate_random_forest(X_test, y_test):
    model = joblib.load(RANDOM_FOREST_MODEL)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    return predictions, accuracy


def evaluate_xgboost(X_test, y_test):
    saved_model = joblib.load(XGBOOST_MODEL)

    model = saved_model["model"]
    label_encoder = saved_model["label_encoder"]

    predictions_encoded = model.predict(X_test)

    predictions = label_encoder.inverse_transform(
        predictions_encoded.astype(int)
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    return predictions, accuracy


def print_model_report(
    model_name,
    y_test,
    predictions,
    accuracy,
):
    print("\n--------------------------------------------")
    print(f"{model_name}")
    print("--------------------------------------------")

    print(f"Accuracy : {accuracy:.4f}")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            labels=CLASS_NAMES,
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=CLASS_NAMES,
    )

    print("Confusion Matrix:")
    print("             LOW  MEDIUM  HIGH")

    for label, row in zip(CLASS_NAMES, matrix):
        print(
            f"{label:<12}"
            f"{row[0]:<5}"
            f"{row[1]:<8}"
            f"{row[2]}"
        )


def main():

    print("\n============================================")
    print("     PHASE 5 - MODEL COMPARISON")
    print("============================================\n")

    # --------------------------------------------------
    # 1. Check required files
    # --------------------------------------------------

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_FILE}"
        )

    if not RANDOM_FOREST_MODEL.exists():
        raise FileNotFoundError(
            f"Random Forest model not found: "
            f"{RANDOM_FOREST_MODEL}"
        )

    if not XGBOOST_MODEL.exists():
        raise FileNotFoundError(
            f"XGBoost model not found: "
            f"{XGBOOST_MODEL}"
        )

    # --------------------------------------------------
    # 2. Load test dataset
    # --------------------------------------------------

    test_df = pd.read_csv(TEST_FILE)

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]

    print(f"Test records : {len(test_df)}")
    print(f"Features     : {len(FEATURE_COLUMNS)}")

    # --------------------------------------------------
    # 3. Evaluate Random Forest
    # --------------------------------------------------

    rf_predictions, rf_accuracy = evaluate_random_forest(
        X_test,
        y_test,
    )

    # --------------------------------------------------
    # 4. Evaluate XGBoost
    # --------------------------------------------------

    xgb_predictions, xgb_accuracy = evaluate_xgboost(
        X_test,
        y_test,
    )

    # --------------------------------------------------
    # 5. Print individual reports
    # --------------------------------------------------

    print_model_report(
        "RANDOM FOREST",
        y_test,
        rf_predictions,
        rf_accuracy,
    )

    print_model_report(
        "XGBOOST",
        y_test,
        xgb_predictions,
        xgb_accuracy,
    )

    # --------------------------------------------------
    # 6. Actual vs predictions
    # --------------------------------------------------

    print("\n============================================")
    print("ACTUAL VS PREDICTED")
    print("============================================")

    for actual, rf_pred, xgb_pred in zip(
        y_test,
        rf_predictions,
        xgb_predictions,
    ):
        print(
            f"Actual: {actual:<7}"
            f"Random Forest: {rf_pred:<7}"
            f"XGBoost: {xgb_pred}"
        )

    # --------------------------------------------------
    # 7. Summary
    # --------------------------------------------------

    print("\n============================================")
    print("MODEL ACCURACY SUMMARY")
    print("============================================")

    print(
        f"Random Forest : {rf_accuracy:.4f}"
    )

    print(
        f"XGBoost       : {xgb_accuracy:.4f}"
    )

    print("\nNote:")
    print(
        "The current test set contains only "
        f"{len(test_df)} records."
    )

    print(
        "These results are suitable for pipeline "
        "verification but are not sufficient "
        "to establish real-world model accuracy."
    )

    print("\n============================================")
    print("     PHASE 5 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()