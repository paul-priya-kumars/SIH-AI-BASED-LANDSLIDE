from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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
    print("     PHASE 3.3.1 - ML MODEL TRAINING")
    print("============================================\n")

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {TRAIN_FILE}"
        )

    df = pd.read_csv(TRAIN_FILE)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    model.fit(X, y)

    MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(model, MODEL_FILE)

    print(f"Training records : {len(df)}")
    print(f"Features         : {len(FEATURE_COLUMNS)}")
    print("Algorithm        : Random Forest")
    print("Trees            : 100")
    print(f"Model saved      : {MODEL_FILE}")

    print("\nTraining classes:")
    for label in sorted(y.unique()):
        print(f"  - {label}")

    print("\nPHASE 3.3.1 COMPLETED")


if __name__ == "__main__":
    main()