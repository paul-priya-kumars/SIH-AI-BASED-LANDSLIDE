"""
JARVIS Phase 4 - M2 Adapter

Connects Phase 4 to environmental / GIS / weather data.
Supports both real data and mock data for development/testing.
"""

import os
from pathlib import Path
import sys

# Add JARVIS project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Import mock data provider
try:
    from .m2_mock import get_mock_environment_data
except ImportError:
    # Try alternative import method when run as script
    try:
        from m2_mock import get_mock_environment_data
    except ImportError:
        # Fallback if mock data provider is not available
        def get_mock_environment_data(location="default"):
            raise ImportError("M2 mock data provider not available")


def get_environment_data(environment_data=None):
    """
    Get environmental data for the Phase 3 risk engine.

    Supports two modes:
    1. Real data mode: Validates and returns provided environmental data
    2. Mock data mode: Returns simulated environmental data when no real data is provided

    The mode is controlled by the M2_DATA_MODE environment variable:
    - M2_DATA_MODE=real: Use provided real data (default behavior)
    - M2_DATA_MODE=mock: Generate and use mock data
    - M2_DATA_MODE=auto: Use mock data if no data provided, otherwise use real data (default)

    Args:
        environment_data: Dictionary of environmental data (ignored in mock mode unless M2_DATA_MODE=real)

    Returns:
        Dictionary containing environmental data required by M1 model,
        clearly marked as mock data when in mock mode.

    Raises:
        ValueError: If required fields are missing in real data mode
    """

    # Determine mode from environment variable
    m2_data_mode = os.environ.get("M2_DATA_MODE", "auto").lower()

    # Auto mode: use mock data if no data provided, otherwise use real data
    if m2_data_mode == "auto":
        if environment_data is None:
            m2_data_mode = "mock"
        else:
            m2_data_mode = "real"

    # Mock data mode
    if m2_data_mode == "mock":
        # Generate mock data with default location
        mock_data = get_mock_environment_data("default")

        # Ensure it has all required fields
        required_fields = [
            "rainfall_mm",
            "soil_moisture_pct",
            "slope_deg",
            "elevation_m",
            "temperature_c",
            "river_level_m",
            "vegetation_index",
            "landslide_history",
        ]

        # Validate that mock data has all required fields
        missing_fields = [
            field for field in required_fields
            if field not in mock_data
        ]

        if missing_fields:
            raise ValueError(
                f"Mock data missing required fields: {', '.join(missing_fields)}"
            )

        return mock_data

    # Real data mode
    elif m2_data_mode == "real":
        if environment_data is None:
            raise ValueError(
                "Environmental data is required when M2_DATA_MODE=real"
            )

        required_fields = [
            "rainfall_mm",
            "soil_moisture_pct",
            "slope_deg",
            "elevation_m",
            "temperature_c",
            "river_level_m",
            "vegetation_index",
            "landslide_history",
        ]

        missing_fields = [
            field for field in required_fields
            if field not in environment_data
        ]

        if missing_fields:
            raise ValueError(
                f"Missing environmental fields: {', '.join(missing_fields)}"
            )

        # Mark real data appropriately
        result = {
            field: environment_data[field]
            for field in required_fields
        }

        result["data_source"] = "M2_REAL"
        result["is_mock"] = False

        return result

    else:
        raise ValueError(
            f"Invalid M2_DATA_MODE: {m2_data_mode}. "
            f"Must be 'real', 'mock', or 'auto'"
        )


if __name__ == "__main__":

    print("\n============================================")
    print("       PHASE 4 - M2 ADAPTER TEST")
    print("============================================")

    # Test 1: Default behavior (auto mode with no data -> mock)
    print("\n1. Auto Mode (No Data Provided) -> Mock Data:")
    os.environ.pop("M2_DATA_MODE", None)  # Reset to auto mode
    result = get_environment_data(None)
    for key, value in result.items():
        if key not in ["data_source", "is_mock"]:
            print(f"   {key:<20}: {value}")
    print(f"   {'data_source':<20}: {result.get('data_source', 'N/A')}")
    print(f"   {'is_mock':<20}: {result.get('is_mock', 'N/A')}")
    print()

    # Test 2: Explicit mock mode
    print("2. Explicit Mock Mode:")
    os.environ["M2_DATA_MODE"] = "mock"
    result = get_environment_data(None)
    for key, value in result.items():
        if key not in ["data_source", "is_mock"]:
            print(f"   {key:<20}: {value}")
    print(f"   {'data_source':<20}: {result.get('data_source', 'N/A')}")
    print(f"   {'is_mock':<20}: {result.get('is_mock', 'N/A')}")
    print()

    # Test 3: Real data mode with valid data
    print("3. Real Data Mode with Valid Data:")
    os.environ["M2_DATA_MODE"] = "real"
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
    result = get_environment_data(test_environment)
    for key, value in result.items():
        if key not in ["data_source", "is_mock"]:
            print(f"   {key:<20}: {value}")
    print(f"   {'data_source':<20}: {result.get('data_source', 'N/A')}")
    print(f"   {'is_mock':<20}: {result.get('is_mock', 'N/A')}")
    print()

    # Test 4: Auto mode with data provided -> real data
    print("4. Auto Mode (Data Provided) -> Real Data:")
    os.environ.pop("M2_DATA_MODE", None)  # Reset to auto mode
    result = get_environment_data(test_environment)
    for key, value in result.items():
        if key not in ["data_source", "is_mock"]:
            print(f"   {key:<20}: {value}")
    print(f"   {'data_source':<20}: {result.get('data_source', 'N/A')}")
    print(f"   {'is_mock':<20}: {result.get('is_mock', 'N/A')}")
    print()

    print("M2 adapter: PASSED")
    print("\n============================================")