from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAIN_FILE = (
    PROJECT_ROOT
    / "phase3"
    / "dataset"
    / "train_dataset.csv"
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
    print("     PHASE 6 - XGBOOST VALIDATION & TUNING")
    print("============================================\n")

    # --------------------------------------------------
    # 1. Load training data
    # --------------------------------------------------

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {TRAIN_FILE}"
        )

    df = pd.read_csv(TRAIN_FILE)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # --------------------------------------------------
    # 2. Encode target labels
    # --------------------------------------------------

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print(f"Training records : {len(df)}")
    print(f"Features         : {len(FEATURE_COLUMNS)}")

    print("\nClass distribution:")

    for class_name, count in y.value_counts().items():
        print(f"  {class_name:<8}: {count}")

    # --------------------------------------------------
    # 3. Stratified 3-fold cross-validation
    # --------------------------------------------------

    cv = StratifiedKFold(
        n_splits=3,
        shuffle=True,
        random_state=42,
    )

    print("\nCross-validation:")
    print("  Strategy : StratifiedKFold")
    print("  Folds    : 3")
    print("  Shuffle  : True")
    print("  Random state : 42")

    # --------------------------------------------------
    # 4. Create base XGBoost model
    # --------------------------------------------------

    xgb_model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
    )

    # --------------------------------------------------
    # 5. Define a small parameter grid
    # --------------------------------------------------

    parameter_grid = {
        "n_estimators": [50, 100],
        "max_depth": [2, 3],
        "learning_rate": [0.05, 0.1],
    }

    total_combinations = (
        len(parameter_grid["n_estimators"])
        * len(parameter_grid["max_depth"])
        * len(parameter_grid["learning_rate"])
    )

    print("\nHyperparameter search:")
    print(f"  Combinations : {total_combinations}")
    print("  n_estimators : [50, 100]")
    print("  max_depth    : [2, 3]")
    print("  learning_rate: [0.05, 0.1]")

    # --------------------------------------------------
    # 6. Grid search
    # --------------------------------------------------

    grid_search = GridSearchCV(
        estimator=xgb_model,
        param_grid=parameter_grid,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
    )

    print("\nRunning cross-validation search...")

    grid_search.fit(
        X,
        y_encoded,
    )

    # --------------------------------------------------
    # 7. Display results
    # --------------------------------------------------

    print("\nCross-validation completed.")

    print(
        f"\nBest CV macro F1 : "
        f"{grid_search.best_score_:.4f}"
    )

    print("\nBest parameters:")

    for parameter, value in grid_search.best_params_.items():
        print(f"  {parameter:<15}: {value}")

    # --------------------------------------------------
    # 8. Save tuned model
    # --------------------------------------------------

    TUNED_MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "model": grid_search.best_estimator_,
            "label_encoder": label_encoder,
            "best_params": grid_search.best_params_,
            "cv_score": grid_search.best_score_,
        },
        TUNED_MODEL_FILE,
    )

    print(
        f"\nTuned model saved : "
        f"{TUNED_MODEL_FILE}"
    )

    print("\n============================================")
    print("     PHASE 6 TUNING COMPLETED")
    print("============================================\n")


if __name__ == "__main__":
    main()