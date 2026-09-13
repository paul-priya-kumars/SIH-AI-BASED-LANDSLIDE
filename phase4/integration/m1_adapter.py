"""
JARVIS Phase 4 - M1 Adapter

Connects Phase 4 to the completed Phase 3
ML Risk Prediction Engine.
"""

import sys
from pathlib import Path


# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase3.risk_engine.predict_risk import predict_risk


def get_ml_risk(environment_data):
    """
    Run the Phase 3 risk prediction engine using
    environmental input data.
    """

    result = predict_risk(
        rainfall_mm=environment_data["rainfall_mm"],
        soil_moisture_pct=environment_data["soil_moisture_pct"],
        slope_deg=environment_data["slope_deg"],
        elevation_m=environment_data["elevation_m"],
        temperature_c=environment_data["temperature_c"],
        river_level_m=environment_data["river_level_m"],
        vegetation_index=environment_data["vegetation_index"],
        landslide_history=environment_data["landslide_history"],
    )

    return result


if __name__ == "__main__":

    test_environment = {
        "rainfall_mm": 180,
        "soil_moisture_pct": 85,
        "slope_deg": 32,
        "elevation_m": 650,
        "temperature_c": 23,
        "river_level_m": 5.2,
        "vegetation_index": 0.35,
        "landslide_history": 1,
    }

    result = get_ml_risk(test_environment)

    print("\n============================================")
    print("       PHASE 4 - M1 ADAPTER TEST")
    print("============================================")

    print("\nM1 / Phase 3 ML Result:")
    print("Risk Level :", result["risk_level"])
    print("Confidence :", f"{result['confidence']:.2%}")

    print("\nM1 adapter: PASSED")

    print("\n============================================")
