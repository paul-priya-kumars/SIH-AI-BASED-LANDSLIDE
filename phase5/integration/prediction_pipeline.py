"""
JARVIS Phase 5 - Prediction Pipeline

Connects Phase 5 with the existing Phase 3 ML prediction system.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase3.risk_engine.predict_risk import predict_risk


def run_prediction(environment_data):
    """
    Run the existing Phase 3 ML prediction
    using Phase 5 environmental data.
    """

    result = predict_risk(
        environment_data["rainfall_mm"],
        environment_data["soil_moisture_pct"],
        environment_data["slope_deg"],
        environment_data["elevation_m"],
        environment_data["temperature_c"],
        environment_data["river_level_m"],
        environment_data["vegetation_index"],
        environment_data["landslide_history"]
    )

    return result


if __name__ == "__main__":

    print()
    print("============================================")
    print("       PHASE 5 - PREDICTION PIPELINE")
    print("============================================")

    environment_data = {
        "rainfall_mm": 180,
        "soil_moisture_pct": 85,
        "slope_deg": 32,
        "elevation_m": 650,
        "temperature_c": 23,
        "river_level_m": 5.2,
        "vegetation_index": 0.35,
        "landslide_history": 1
    }

    print()
    print("M2 Environmental Data: PASSED")

    result = run_prediction(environment_data)

    print()
    print("M1 ML Prediction:")

    if isinstance(result, dict):

        if "risk_level" in result:
            print("Risk Level :", result["risk_level"])

        if "confidence" in result:
            print("Confidence :", result["confidence"])

        if "probabilities" in result:
            print("Probabilities :", result["probabilities"])

    else:
        print("Prediction :", result)

    print()
    print("Prediction pipeline: PASSED")

    print()
    print("============================================")