from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "prepared_dataset.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "engineered_features.csv"
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


def load_prepared_dataset() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Prepared dataset not found: {INPUT_FILE}"
        )

    return pd.read_csv(INPUT_FILE)


def validate_feature_ranges(df: pd.DataFrame) -> None:
    if (df["rainfall_mm"] < 0).any():
        raise ValueError("Rainfall cannot be negative.")

    if (df["soil_moisture_pct"] < 0).any() or (
        df["soil_moisture_pct"] > 100
    ).any():
        raise ValueError(
            "Soil moisture must be between 0 and 100."
        )

    if (df["slope_deg"] < 0).any():
        raise ValueError("Slope cannot be negative.")

    if (df["elevation_m"] < 0).any():
        raise ValueError("Elevation cannot be negative.")

    if (df["river_level_m"] < 0).any():
        raise ValueError("River level cannot be negative.")

    if (df["vegetation_index"] < 0).any() or (
        df["vegetation_index"] > 1
    ).any():
        raise ValueError(
            "Vegetation index must be between 0 and 1."
        )

    if not df["landslide_history"].isin([0, 1]).all():
        raise ValueError(
            "landslide_history must contain only 0 or 1."
        )


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    validate_feature_ranges(df)

    features = df[FEATURE_COLUMNS].copy()

    return features


def create_target(df: pd.DataFrame) -> pd.Series:
    return df[TARGET_COLUMN].copy()


def main() -> None:
    print("\n============================================")
    print("     PHASE 3.2.1 - FEATURE ENGINEERING")
    print("============================================\n")

    df = load_prepared_dataset()

    print(f"Input rows       : {len(df)}")
    print(f"Input columns    : {len(df.columns)}")

    X = create_features(df)
    y = create_target(df)

    engineered = X.copy()
    engineered[TARGET_COLUMN] = y

    engineered.to_csv(OUTPUT_FILE, index=False)

    print("\nFeature validation: PASSED")
    print(f"Feature count    : {len(X.columns)}")
    print(f"Target column    : {TARGET_COLUMN}")
    print(f"Output dataset   : {OUTPUT_FILE}")

    print("\nFeatures:")
    for column in X.columns:
        print(f"  - {column}")

    print("\nTarget distribution:")
    print(y.value_counts())

    print("\nPHASE 3.2.1 COMPLETED")


if __name__ == "__main__":
    main()