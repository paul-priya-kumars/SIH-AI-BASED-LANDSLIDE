from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "train_dataset.csv"
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


def main() -> None:

    print("\n============================================")
    print("     PHASE 3.3.2 - XGBOOST MODEL TRAINING")
    print("============================================\n")

    # --------------------------------------------------
    # 1. Check training dataset
    # --------------------------------------------------

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {TRAIN_FILE}"
        )

    # --------------------------------------------------
    # 2. Load dataset
    # --------------------------------------------------

    df = pd.read_csv(TRAIN_FILE)

    print(f"Training dataset : {TRAIN_FILE}")
    print(f"Training records : {len(df)}")

    # --------------------------------------------------
    # 3. Validate features
    # --------------------------------------------------

    missing_features = [
        column
        for column in FEATURE_COLUMNS
        if column not in df.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing feature columns: {missing_features}"
        )

    # --------------------------------------------------
    # 4. Validate target
    # --------------------------------------------------

    if TARGET_COLUMN not in df.columns:
        raise ValueError(
            f"Target column '{TARGET_COLUMN}' not found."
        )

    # --------------------------------------------------
    # 5. Prepare X and y
    # --------------------------------------------------

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # --------------------------------------------------
    # 6. Check missing values
    # --------------------------------------------------

    if X.isnull().any().any():
        raise ValueError(
            "Training features contain missing values."
        )

    if y.isnull().any():
        raise ValueError(
            "Target column contains missing values."
        )

    # --------------------------------------------------
    # 7. Encode target
    # --------------------------------------------------

    label_encoder = LabelEncoder()

    y_encoded = label_encoder.fit_transform(y)

    print("\nTarget encoding:")

    for encoded_value, class_name in enumerate(
        label_encoder.classes_
    ):
        print(
            f"  {class_name} -> {encoded_value}"
        )

    # --------------------------------------------------
    # 8. Create XGBoost model
    # --------------------------------------------------

    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.1,
        subsample=1.0,
        colsample_bytree=1.0,
        random_state=42,
        eval_metric="mlogloss",
    )

    # --------------------------------------------------
    # 9. Train model
    # --------------------------------------------------

    print("\nTraining XGBoost model...")

    model.fit(
        X,
        y_encoded,
    )

    print("Training completed successfully.")

    # --------------------------------------------------
    # 10. Save model + encoder
    # --------------------------------------------------

    MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "model": model,
            "label_encoder": label_encoder,
        },
        MODEL_FILE,
    )

    print(f"\nModel saved      : {MODEL_FILE}")
    print(f"Features         : {len(FEATURE_COLUMNS)}")
    print("Algorithm        : XGBoost")
    print("Trees            : 100")
    print("Max depth        : 3")
    print("Learning rate    : 0.1")

    print("\nTraining classes:")

    for class_name in label_encoder.classes_:
        print(f"  - {class_name}")

    print("\n============================================")
    print("     PHASE 3.3.2 COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()