"""
JARVIS Phase 4 - M2 Adapter

Connects Phase 4 to environmental / GIS / weather data.
"""


def get_environment_data(environment_data):
    """
    Validate and return environmental data
    required by the Phase 3 risk engine.
    """

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

    return {
        field: environment_data[field]
        for field in required_fields
    }


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

    result = get_environment_data(test_environment)

    print("\n============================================")
    print("       PHASE 4 - M2 ADAPTER TEST")
    print("============================================")

    print("\nEnvironmental / M2 Data:")

    for key, value in result.items():
        print(f"{key:22}: {value}")

    print("\nM2 adapter: PASSED")

    print("\n============================================")
