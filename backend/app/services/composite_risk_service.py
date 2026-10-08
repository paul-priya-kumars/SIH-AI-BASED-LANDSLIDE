"""
Composite (end-to-end) Risk Engine
==================================
Combines the three GeoShield AI risk components for a coordinate:

* **M1 environmental** — real Phase 3 RandomForest model
  (:mod:`backend.app.services.m1_model_service`), feature contract of 8 ordered
  features fed from the M2 environment provider.
* **M2 spatial / GIS** — risk zone resolved through the replaceable
  :class:`backend.app.services.gis_provider.GisProvider`. The bundled provider
  is an explicitly-labelled demo adapter (``is_real=False``).
* **M3 satellite / image** — real Landslide4Sense U-Net
  (:mod:`backend.app.services.m3_inference`). It has **no coordinate → patch
  mapping**, so it only contributes when an explicit patch is supplied.

Composition rule (documented, deterministic, no fabrication)
------------------------------------------------------------
``final_probability`` is the weight-renormalised mean of the component
probabilities that are *actually available* for the request::

    final = Σ(wᵢ · pᵢ) / Σ(wᵢ)      over available components only

Default weights: M1 0.5, M2 0.3, M3 0.2. A component that is unavailable is
excluded from both the numerator and the denominator — it is never replaced by
a made-up value. When **no** component is available, ``final_risk`` is ``None``.

``final_level`` thresholds are explicit and shared with the rest of the
codebase: ``>=0.75 VERY_HIGH``, ``>=0.55 HIGH``, ``>=0.35 MODERATE``, else ``LOW``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .environment_service import get_environment_data
from .gis_provider import get_gis_provider
from .m1_model_service import (
    M1_FEATURE_NAMES,
    build_feature_vector_from_environment,
    m1_model_service,
)

logger = logging.getLogger(__name__)

COMPONENT_WEIGHTS: Dict[str, float] = {
    "environmental_m1": 0.5,
    "spatial_m2": 0.3,
    "satellite_m3": 0.2,
}

LEVEL_THRESHOLDS = ((0.75, "VERY_HIGH"), (0.55, "HIGH"), (0.35, "MODERATE"))


def _probability_to_level(probability: float) -> str:
    for threshold, level in LEVEL_THRESHOLDS:
        if probability >= threshold:
            return level
    return "LOW"


def compute_composite_risk(
    latitude: float,
    longitude: float,
    image_patch_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute the composite risk for a coordinate (see module docstring)."""
    env_data = get_environment_data(latitude, longitude)

    # ---- M1 environmental ------------------------------------------------
    m1_component: Optional[Dict[str, Any]] = None
    m1_error: Optional[str] = None
    try:
        feature_vector = build_feature_vector_from_environment(env_data)
        m1_result = m1_model_service.predict(
            dict(zip(M1_FEATURE_NAMES, feature_vector))
        )
        m1_component = {
            "available": True,
            "is_real": True,
            "probability": m1_result["risk_probability"],
            "level": m1_result["risk_level"],
            "confidence": m1_result["confidence"],
            "probabilities": m1_result["probabilities"],
            "artifact_path": m1_result["artifact_path"],
            "model_version": m1_result["model_version"],
        }
    except Exception as exc:
        m1_error = str(exc)
        m1_component = {"available": False, "is_real": True, "probability": None, "error": m1_error}

    # ---- M2 spatial ------------------------------------------------------
    provider = get_gis_provider()
    spatial_context = provider.find_zone(latitude, longitude)
    spatial_component = {
        "available": spatial_context.zone_id is not None and spatial_context.risk_probability is not None,
        "is_real": provider.is_real,
        "provider": provider.name,
        "data_source": provider.data_source,
        "zone_id": spatial_context.zone_id,
        "name": spatial_context.name,
        "inside_zone": spatial_context.inside_zone,
        "distance_m": spatial_context.distance_m,
        "probability": spatial_context.risk_probability,
        "level": spatial_context.risk_level,
    }

    # ---- M3 satellite ----------------------------------------------------
    satellite_component: Dict[str, Any] = {
        "available": False,
        "is_real": True,
        "probability": None,
        "reason": "No satellite patch supplied; M3 has no coordinate->patch mapping.",
    }
    if image_patch_path:
        try:
            from .m3_inference import m3_inference_service, coordinate_mapping_status

            result = m3_inference_service.segment_patch(image_patch_path)
            satellite_component = {
                "available": True,
                "is_real": True,
                "probability": result["mean_probability"],
                "positive_fraction": result["positive_fraction"],
                "max_probability": result["max_probability"],
                "patch_path": result["patch_path"],
                "checkpoint_path": result["checkpoint_path"],
                "coordinate_mapping": coordinate_mapping_status(),
            }
        except Exception as exc:
            satellite_component = {
                "available": False,
                "is_real": True,
                "probability": None,
                "error": str(exc),
            }

    components = {
        "environmental_m1": m1_component,
        "spatial_m2": spatial_component,
        "satellite_m3": satellite_component,
    }

    # ---- weighted composition over available components ------------------
    weighted_sum = 0.0
    weight_total = 0.0
    used: list = []
    for name, component in components.items():
        probability = component.get("probability")
        if component.get("available") and probability is not None:
            weight = COMPONENT_WEIGHTS[name]
            weighted_sum += weight * float(probability)
            weight_total += weight
            used.append(name)

    final_probability = round(weighted_sum / weight_total, 4) if weight_total > 0 else None
    final_level = _probability_to_level(final_probability) if final_probability is not None else None

    return {
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "location_name": env_data.location_name,
        "components": components,
        "weights": COMPONENT_WEIGHTS,
        "components_used": used,
        "final_risk": {
            "available": final_probability is not None,
            "probability": final_probability,
            "risk_level": final_level,
            "method": "weight_renormalised_mean_over_available_components",
        },
        "environment_is_mock": bool(getattr(env_data, "is_mock", True)),
        "is_mock": False,  # the composition itself is real; provenance is per-component
    }
