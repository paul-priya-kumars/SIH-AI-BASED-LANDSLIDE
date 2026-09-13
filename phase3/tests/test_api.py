import sys
from pathlib import Path

# Add the JARVIS project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase3.api.risk_api import (
    root,
    health,
    predict_risk_api,
    RiskInput,
)


def test_root():
    result = root()

    assert result["service"] == "JARVIS Phase 3 Risk API"
    assert result["status"] == "online"
    assert result["version"] == "1.0.0"


def test_health():
    result = health()

    assert result["status"] == "healthy"
    assert result["phase"] == "3"
    assert result["component"] == "risk_prediction_api"


def test_prediction_api():
    data = RiskInput(
        rainfall_mm=180,
        soil_moisture_pct=85,
        slope_deg=32,
        elevation_m=650,
        temperature_c=23,
        river_level_m=5.2,
        vegetation_index=0.35,
        landslide_history=1,
    )

    result = predict_risk_api(data)

    assert result["success"] is True
    assert "risk" in result

    risk = result["risk"]

    assert risk["risk_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    assert set(risk["probabilities"].keys()) == {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    probability_total = sum(
        risk["probabilities"].values()
    )

    assert abs(probability_total - 1.0) < 0.0001

    assert 0.0 <= risk["confidence"] <= 1.0


def run_all_tests():
    print("\n============================================")
    print("       PHASE 3.12.2 - API TESTS")
    print("============================================\n")

    print("Running Root Endpoint Test...")
    test_root()
    print("Root Endpoint Test      : PASSED")

    print("\nRunning Health Endpoint Test...")
    test_health()
    print("Health Endpoint Test    : PASSED")

    print("\nRunning Prediction API Test...")
    test_prediction_api()
    print("Prediction API Test     : PASSED")

    print("\n============================================")
    print("       ALL API TESTS PASSED")
    print("============================================\n")


if __name__ == "__main__":
    run_all_tests()
