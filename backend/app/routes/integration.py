"""
Integration routes: M2 GIS boundary, composite risk, and M3 image inference.
===========================================================================
These endpoints surface the real M1/M3 models and the replaceable M2 GIS
provider to the frontend, with explicit availability/provenance so nothing can
be mistaken for real data when it is not.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from ..config import settings
from ..services.composite_risk_service import compute_composite_risk
from ..services.gis_provider import get_gis_provider
from ..services.m3_inference import m3_inference_service
from ..services.m1_model_service import m1_model_service

router = APIRouter(tags=["Integration (M1 / M2 / M3)"])


@router.get("/gis/zone", summary="Map a coordinate to its spatial risk zone (M2 provider)")
def get_gis_zone(
    latitude: float = Query(11.4102, ge=-90.0, le=90.0),
    longitude: float = Query(76.6950, ge=-180.0, le=180.0),
) -> Dict[str, Any]:
    """Return the spatial context for a coordinate via the configured GIS provider."""
    provider = get_gis_provider()
    context = provider.find_zone(latitude, longitude)
    return {
        "spatial_context": context.to_dict(),
        "provider": provider.describe(),
    }


@router.get("/risk/composite", summary="End-to-end composite risk (M1 + M2 + M3)")
def get_composite_risk(
    latitude: float = Query(11.4102, ge=-90.0, le=90.0),
    longitude: float = Query(76.6950, ge=-180.0, le=180.0),
    image_patch_path: str | None = Query(
        None,
        description="Optional explicit Landslide4Sense .h5 patch to include the M3 component.",
    ),
) -> Dict[str, Any]:
    return compute_composite_risk(latitude, longitude, image_patch_path)


@router.get("/ml/models/status", summary="Truthful availability of the M1 and M3 models")
def get_models_status() -> Dict[str, Any]:
    return {
        "environmental_m1": m1_model_service.describe(),
        "satellite_m3": m3_inference_service.describe(),
    }


@router.post("/ml/m3/predict", summary="Run real M3 segmentation on an uploaded Landslide4Sense patch")
async def predict_m3_patch(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Run genuine U-Net inference on an uploaded ``.h5`` patch."""
    if not m3_inference_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "M3 model unavailable",
                "error_code": "MODEL_UNAVAILABLE",
                "details": m3_inference_service.describe(),
            },
        )

    filename = file.filename or "patch.h5"
    if not filename.lower().endswith((".h5", ".hdf5")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected a Landslide4Sense .h5 patch",
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".h5", dir=settings.UPLOAD_DIR)
    os.close(fd)
    try:
        with open(tmp_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
        try:
            return m3_inference_service.segment_patch(tmp_path)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "M3 inference failed", "details": str(exc)},
            )
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
