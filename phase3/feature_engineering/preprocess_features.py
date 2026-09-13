from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "engineered_features.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "scaled_features.csv"
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
    print("     PHASE 3.2.2 - FEATURE PREPROCESSING")
    print("============================================\n")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    scaler = StandardScaler()

    scaled_values = scaler.fit_transform(X)

    scaled_features = pd.DataFrame(
        scaled_values,
        columns=FEATURE_COLUMNS
    )

    scaled_features[TARGET_COLUMN] = y.values

    scaled_features.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Rows processed : {len(df)}")
    print(f"Features       : {len(FEATURE_COLUMNS)}")
    print(f"Output file    : {OUTPUT_FILE}")

    print("\nFeature means after scaling:")

    for column in FEATURE_COLUMNS:
        mean_value = scaled_features[column].mean()
        print(f"  {column}: {mean_value:.6f}")

    print("\nPHASE 3.2.2 COMPLETED")


if __name__ == "__main__":
    main()