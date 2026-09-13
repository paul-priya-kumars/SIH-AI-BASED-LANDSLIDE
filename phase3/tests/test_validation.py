import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import ValidationError

from phase3.api.risk_api import RiskInput


def test_valid_input():
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

    assert data.rainfall_mm == 180
    assert data.soil_moisture_pct == 85
    assert data.vegetation_index == 0.35
    assert data.landslide_history == 1


def test_missing_required_field():
    try:
        RiskInput(
            rainfall_mm=180,
            soil_moisture_pct=85,
            slope_deg=32,
            elevation_m=650,
            temperature_c=23,
            river_level_m=5.2,
            vegetation_index=0.35,
        )

        raise AssertionError(
            "Missing field was incorrectly accepted."
        )

    except ValidationError:
        pass


def test_invalid_type():
    try:
        RiskInput(
            rainfall_mm="invalid",
            soil_moisture_pct=85,
            slope_deg=32,
            elevation_m=650,
            temperature_c=23,
            river_level_m=5.2,
            vegetation_index=0.35,
            landslide_history=1,
        )

        raise AssertionError(
            "Invalid numeric value was incorrectly accepted."
        )

    except ValidationError:
        pass


def run_all_tests():
    print("\n============================================")
    print("      PHASE 3.12.3 - VALIDATION TESTS")
    print("============================================\n")

    print("Running Valid Input Test...")
    test_valid_input()
    print("Valid Input Test        : PASSED")

    print("\nRunning Missing Field Test...")
    test_missing_required_field()
    print("Missing Field Test      : PASSED")

    print("\nRunning Invalid Type Test...")
    test_invalid_type()
    print("Invalid Type Test       : PASSED")

    print("\n============================================")
    print("       ALL VALIDATION TESTS PASSED")
    print("============================================\n")


if __name__ == "__main__":
    run_all_tests()
