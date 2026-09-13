from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "phase3" / "dataset" / "development_dataset.csv"
OUTPUT_FILE = PROJECT_ROOT / "phase3" / "dataset" / "prepared_dataset.csv"


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

VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}


def load_dataset() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {INPUT_FILE}")

    return pd.read_csv(INPUT_FILE)


def validate_dataset(df: pd.DataFrame) -> None:
    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Dataset is empty.")

    missing_values = df[required_columns].isnull().sum()

    if missing_values.any():
        raise ValueError(
            f"Missing values detected:\n{missing_values[missing_values > 0]}"
        )

    for column in FEATURE_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(
                f"Feature '{column}' must contain numeric values."
            )

    invalid_risk_levels = set(df[TARGET_COLUMN]) - VALID_RISK_LEVELS

    if invalid_risk_levels:
        raise ValueError(
            f"Invalid risk levels: {invalid_risk_levels}"
        )


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()

    prepared[TARGET_COLUMN] = (
        prepared[TARGET_COLUMN]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return prepared


def main() -> None:
    print("\n============================================")
    print("     PHASE 3.1.3 - DATA PREPARATION")
    print("============================================\n")

    print(f"Input dataset : {INPUT_FILE}")

    df = load_dataset()

    print(f"Rows loaded   : {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    validate_dataset(df)

    prepared = prepare_dataset(df)

    prepared.to_csv(OUTPUT_FILE, index=False)

    print("\nDataset validation: PASSED")
    print(f"Prepared rows     : {len(prepared)}")
    print(f"Prepared columns  : {len(prepared.columns)}")
    print(f"Output dataset    : {OUTPUT_FILE}")

    print("\nRisk distribution:")
    print(prepared[TARGET_COLUMN].value_counts())

    print("\nPHASE 3.1.3 COMPLETED")


if __name__ == "__main__":
    main()