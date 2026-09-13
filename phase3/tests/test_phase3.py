import sys
from pathlib import Path

# Add the JARVIS project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from phase3.risk_engine.predict_risk import predict_risk
from phase3.route_analysis.analyze_routes import (
    analyze_routes,
    find_safest_route,
)
from phase3.rerouting.dynamic_reroute import dynamic_reroute


def test_risk_prediction():
    result = predict_risk(
        rainfall_mm=180,
        soil_moisture_pct=85,
        slope_deg=32,
        elevation_m=650,
        temperature_c=23,
        river_level_m=5.2,
        vegetation_index=0.35,
        landslide_history=1,
    )

    assert result["risk_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    assert set(result["probabilities"].keys()) == {
        "LOW",
        "MEDIUM",
        "HIGH",
    }

    probability_total = sum(
        result["probabilities"].values()
    )

    assert abs(probability_total - 1.0) < 0.0001

    assert 0.0 <= result["confidence"] <= 1.0


def test_route_analysis():
    routes = {
        "Route A": {
            "distance": 5,
            "risk": 30,
        },
        "Route B": {
            "distance": 8,
            "risk": 85,
        },
        "Route C": {
            "distance": 6,
            "risk": 55,
        },
    }

    analyzed = analyze_routes(routes)

    assert analyzed["Route A"]["risk_level"] == "LOW"
    assert analyzed["Route B"]["risk_level"] == "HIGH"
    assert analyzed["Route C"]["risk_level"] == "MEDIUM"

    safest = find_safest_route(analyzed)

    assert safest == "Route A"


def test_dynamic_rerouting():
    routes = {
        "Route A": {
            "distance": 5,
            "risk": 30,
        },
        "Route B": {
            "distance": 8,
            "risk": 85,
        },
        "Route C": {
            "distance": 6,
            "risk": 55,
        },
    }

    result = dynamic_reroute(
        routes,
        "Route B",
    )

    assert result["rerouted"] is True

    assert result["current_route"] == "Route B"

    assert result["recommended_route"] == "Route A"

    assert (
        result["reason"]
        == "Current route is high risk."
    )


def test_no_safe_route():
    routes = {
        "Route A": {
            "distance": 5,
            "risk": 85,
        },
        "Route B": {
            "distance": 8,
            "risk": 90,
        },
        "Route C": {
            "distance": 6,
            "risk": 78,
        },
    }

    result = dynamic_reroute(
        routes,
        "Route A",
    )

    assert result["rerouted"] is False

    assert result["current_route"] == "Route A"

    assert result["recommended_route"] is None

    assert (
        result["reason"]
        == "No safe alternative route available."
    )


def run_all_tests():
    print("\n============================================")
    print("       PHASE 3.12.1 - AUTOMATED TESTS")
    print("============================================\n")

    print("Running Risk Prediction Test...")
    test_risk_prediction()
    print("Risk Prediction Test    : PASSED")

    print("\nRunning Route Analysis Test...")
    test_route_analysis()
    print("Route Analysis Test     : PASSED")

    print("\nRunning Dynamic Rerouting Test...")
    test_dynamic_rerouting()
    print("Dynamic Rerouting Test  : PASSED")

    print("\nRunning No Safe Route Test...")
    test_no_safe_route()
    print("No Safe Route Test      : PASSED")

    print("\n============================================")
    print("       ALL PHASE 3 TESTS PASSED")
    print("============================================\n")


if __name__ == "__main__":
    run_all_tests()
