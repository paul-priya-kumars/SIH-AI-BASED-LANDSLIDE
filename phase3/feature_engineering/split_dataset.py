from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "engineered_features.csv"
)

TRAIN_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "train_dataset.csv"
)

TEST_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "test_dataset.csv"
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
    print("     PHASE 3.2.3 - DATASET SPLITTING")
    print("============================================\n")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    train_X, test_X, train_y, test_y = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    train_df = train_X.copy()
    train_df[TARGET_COLUMN] = train_y.values

    test_df = test_X.copy()
    test_df[TARGET_COLUMN] = test_y.values

    train_df.to_csv(TRAIN_FILE, index=False)
    test_df.to_csv(TEST_FILE, index=False)

    print(f"Total records : {len(df)}")
    print(f"Training      : {len(train_df)}")
    print(f"Testing       : {len(test_df)}")

    print("\nTraining distribution:")
    print(train_df[TARGET_COLUMN].value_counts())

    print("\nTesting distribution:")
    print(test_df[TARGET_COLUMN].value_counts())

    print("\nTrain/test split: PASSED")
    print(f"Training file : {TRAIN_FILE}")
    print(f"Testing file  : {TEST_FILE}")

    print("\nPHASE 3.2.3 COMPLETED")


if __name__ == "__main__":
    main()