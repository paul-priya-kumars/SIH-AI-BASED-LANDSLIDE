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

TUNED_MODEL_FILE = (
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

TARGET_COLUMN = "risk_level"


def main() -> None:

    print("\n============================================")
    print("   PHASE 6 - TUNED XGBOOST EVALUATION")
    print("============================================\n")

    # --------------------------------------------------
    # 1. Check required files
    # --------------------------------------------------

    if not TEST_FILE.exists():
        raise FileNotFoundError(
            f"Test dataset not found: {TEST_FILE}"
        )

    if not TUNED_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Tuned model not found: {TUNED_MODEL_FILE}"
        )

    # --------------------------------------------------
    # 2. Load test dataset
    # --------------------------------------------------

    df = pd.read_csv(TEST_FILE)

    X_test = df[FEATURE_COLUMNS]
    y_test = df[TARGET_COLUMN]

    print(f"Test records : {len(df)}")

    # --------------------------------------------------
    # 3. Load tuned XGBoost model
    # --------------------------------------------------

    saved_model = joblib.load(TUNED_MODEL_FILE)

    model = saved_model["model"]
    label_encoder = saved_model["label_encoder"]

    # --------------------------------------------------
    # 4. Encode test labels
    # --------------------------------------------------

    y_test_encoded = label_encoder.transform(y_test)

    # --------------------------------------------------
    # 5. Generate predictions
    # --------------------------------------------------

    y_pred_encoded = model.predict(X_test)

    # Convert predictions back to original labels
    y_pred = label_encoder.inverse_transform(
        y_pred_encoded.astype(int)
    )

    # --------------------------------------------------
    # 6. Calculate accuracy
    # --------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred,
    )

    print(f"Accuracy     : {accuracy:.4f}")

    # --------------------------------------------------
    # 7. Classification report
    # --------------------------------------------------

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            y_pred,
            labels=label_encoder.classes_,
            zero_division=0,
        )
    )

    # --------------------------------------------------
    # 8. Confusion matrix
    # --------------------------------------------------

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=label_encoder.classes_,
    )

    print("Confusion Matrix:")

    print(
        "             "
        + "  ".join(
            f"{label:<8}"
            for label in label_encoder.classes_
        )
    )

    for label, row in zip(
        label_encoder.classes_,
        cm,
    ):
        print(
            f"{label:<10}"
            + "  ".join(
                f"{value:<8}"
                for value in row
            )
        )

    # --------------------------------------------------
    # 9. Actual vs predicted
    # --------------------------------------------------

    print("\nActual vs Predicted:")

    for actual, predicted in zip(
        y_test,
        y_pred,
    ):
        print(
            f"  Actual: {actual:<7} "
            f"Predicted: {predicted}"
        )

    # --------------------------------------------------
    # 10. Display tuning information
    # --------------------------------------------------

    print("\nTuning information:")

    print(
        f"  CV Macro F1 : "
        f"{saved_model['cv_score']:.4f}"
    )

    print("  Best parameters:")

    for parameter, value in saved_model[
        "best_params"
    ].items():
        print(
            f"    {parameter:<15}: {value}"
        )

    print("\n============================================")
    print("   TUNED XGBOOST EVALUATION COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()