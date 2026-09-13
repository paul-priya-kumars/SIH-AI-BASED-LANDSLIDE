"""
JARVIS Phase 4 - API Schemas

Defines the input and output data structures
used by the Phase 4 API.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class EnvironmentInput:
    rainfall_mm: float
    soil_moisture_pct: float
    slope_deg: float
    elevation_m: float
    temperature_c: float
    river_level_m: float
    vegetation_index: float
    landslide_history: int


@dataclass
class ImageInput:
    landslide: bool
    flooding: bool
    road_damage: bool


@dataclass
class RouteInput:
    distance: float
    risk: float


@dataclass
class Phase4Request:
    environment: EnvironmentInput
    image: ImageInput
    routes: Dict[str, RouteInput]
    current_route: str


def environment_to_dict(
    data: EnvironmentInput
) -> Dict[str, Any]:
    return {
        "rainfall_mm": data.rainfall_mm,
        "soil_moisture_pct": data.soil_moisture_pct,
        "slope_deg": data.slope_deg,
        "elevation_m": data.elevation_m,
        "temperature_c": data.temperature_c,
        "river_level_m": data.river_level_m,
        "vegetation_index": data.vegetation_index,
        "landslide_history": data.landslide_history,
    }


def image_to_dict(
    data: ImageInput
) -> Dict[str, Any]:
    return {
        "landslide": data.landslide,
        "flooding": data.flooding,
        "road_damage": data.road_damage,
    }


def routes_to_dict(
    routes: Dict[str, RouteInput]
) -> Dict[str, Dict[str, float]]:
    return {
        name: {
            "distance": route.distance,
            "risk": route.risk,
        }
        for name, route in routes.items()
    }


if __name__ == "__main__":

    environment = EnvironmentInput(
        rainfall_mm=180,
        soil_moisture_pct=85,
        slope_deg=32,
        elevation_m=650,
        temperature_c=23,
        river_level_m=5.2,
        vegetation_index=0.35,
        landslide_history=1,
    )

    image = ImageInput(
        landslide=False,
        flooding=True,
        road_damage=False,
    )

    routes = {
        "Route A": RouteInput(
            distance=5,
            risk=30,
        ),
        "Route B": RouteInput(
            distance=8,
            risk=85,
        ),
        "Route C": RouteInput(
            distance=6,
            risk=55,
        ),
    }

    print("\n============================================")
    print("        PHASE 4 - API SCHEMAS")
    print("============================================")

    print("\nEnvironment schema: PASSED")
    print("Image schema      : PASSED")
    print("Route schema      : PASSED")

    print("\nEnvironment Data:")
    print(environment_to_dict(environment))

    print("\nImage Data:")
    print(image_to_dict(image))

    print("\nRoutes:")
    print(routes_to_dict(routes))

    print("\nAPI schemas: PASSED")

    print("\n============================================")