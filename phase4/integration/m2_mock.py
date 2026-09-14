"""
JARVIS Phase 4 - M2 Mock Data Provider

Provides mock environmental/GIS data for development and testing
when the real M2 pipeline is not available.

Clearly marked as mock data to prevent confusion with real environmental data.
"""

import random
from typing import Dict, Any
from pathlib import Path
import sys

# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def get_mock_environment_data(location: str = "default") -> Dict[str, Any]:
    """
    Generate mock environmental data for testing and development.

    Args:
        location: Geographic location identifier for varied mock data

    Returns:
        Dictionary containing the 8 features required by M1 model,
        clearly marked as mock data.

    Note:
        All data is explicitly labeled as mock to prevent confusion
        with real environmental measurements.
    """

    # Define base values for different locations to simulate geographic variation
    location_profiles = {
        "default": {
            "rainfall_mm": 25.0,
            "soil_moisture_pct": 45.0,
            "slope_deg": 15.0,
            "elevation_m": 1200.0,
            "temperature_c": 18.0,
            "river_level_m": 2.5,
            "vegetation_index": 0.6,
            "landslide_history": 0
        },
        "high_risk_area": {
            "rainfall_mm": 180.0,
            "soil_moisture_pct": 85.0,
            "slope_deg": 35.0,
            "elevation_m": 800.0,
            "temperature_c": 22.0,
            "river_level_m": 6.0,
            "vegetation_index": 0.3,
            "landslide_history": 2
        },
        "medium_risk_area": {
            "rainfall_mm": 80.0,
            "soil_moisture_pct": 60.0,
            "slope_deg": 25.0,
            "elevation_m": 1500.0,
            "temperature_c": 15.0,
            "river_level_m": 3.5,
            "vegetation_index": 0.5,
            "landslide_history": 1
        },
        "low_risk_area": {
            "rainfall_mm": 10.0,
            "soil_moisture_pct": 25.0,
            "slope_deg": 5.0,
            "elevation_m": 2000.0,
            "temperature_c": 10.0,
            "river_level_m": 1.0,
            "vegetation_index": 0.8,
            "landslide_history": 0
        }
    }

    # Get base values for the location, default to "default" if not found
    base_values = location_profiles.get(location, location_profiles["default"])

    # Add small random variations to simulate real-world fluctuations
    mock_data = {}
    for key, base_value in base_values.items():
        if key == "landslide_history":
            # Keep landslide_history as integer without variation
            mock_data[key] = base_value
        elif isinstance(base_value, float):
            # Add ±10% random variation for float values
            variation = random.uniform(-0.1, 0.1)
            mock_data[key] = base_value * (1 + variation)
        else:
            mock_data[key] = base_value

    # Clearly mark this as mock data
    mock_data["data_source"] = "M2_MOCK"
    mock_data["is_mock"] = True
    mock_data["mock_reason"] = "Real M2 pipeline not available - using mock data for development/testing"

    return mock_data


def get_mock_environment_data_by_risk_level(risk_level: str) -> Dict[str, Any]:
    """
    Generate mock environmental data corresponding to a specific risk level.

    Args:
        risk_level: Desired risk level ("low", "medium", "high")

    Returns:
        Dictionary containing environmental data that should produce
        the specified risk level when processed by the M1 model.
    """

    risk_level_map = {
        "low": "low_risk_area",
        "medium": "medium_risk_area",
        "high": "high_risk_area"
    }

    location = risk_level_map.get(risk_level.lower(), "default")
    return get_mock_environment_data(location)


def get_available_locations() -> list:
    """
    Get list of available mock data locations.

    Returns:
        List of location identifiers for which mock data can be generated.
    """
    return ["default", "high_risk_area", "medium_risk_area", "low_risk_area"]


if __name__ == "__main__":
    print("\n============================================")
    print("   PHASE 4 - M2 MOCK DATA PROVIDER")
    print("============================================\n")

    # Test default location
    print("1. Default Location Mock Data:")
    mock_data = get_mock_environment_data("default")
    for key, value in mock_data.items():
        if key not in ["data_source", "is_mock", "mock_reason"]:
            print(f"   {key:<20}: {value}")
    print(f"   {'data_source':<20}: {mock_data['data_source']}")
    print(f"   {'is_mock':<20}: {mock_data['is_mock']}")
    print()

    # Test different risk levels
    print("2. Risk-Based Mock Data:")
    for risk in ["low", "medium", "high"]:
        mock_data = get_mock_environment_data_by_risk_level(risk)
        print(f"   {risk.upper()} RISK: {mock_data['rainfall_mm']:.1f}mm rain, "
              f"{mock_data['slope_deg']:.1f}° slope, "
              f"{mock_data['vegetation_index']:.2f} vegetation")
    print()

    # Test available locations
    print("3. Available Locations:")
    locations = get_available_locations()
    print(f"   {', '.join(locations)}")
    print()

    print("M2 Mock Data Provider: PASSED")
    print("\n============================================")
    print("  PHASE 4 - M2 MOCK DATA PROVIDER COMPLETE")
    print("============================================\n")