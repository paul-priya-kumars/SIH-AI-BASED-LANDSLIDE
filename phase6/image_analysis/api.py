"""
API endpoints for Landslide4Sense Image AI module.

Provides REST-like endpoints for health checking, prediction, and model information.
In Phase 3, performs actual inference when model is available and AI is enabled.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import time
import numpy as np
import base64
import tempfile
import os

from phase6.image_analysis.config import get_image_ai_config
from phase6.image_analysis.models.loader import (
    Landslide4SenseModelLoader,
    ImageModelNotAvailableError
)
from phase6.image_analysis.inference.engine import (
    Landslide4SenseInferenceEngine,
    Landslide4SenseInferenceError
)
from phase6.image_analysis.preprocessing.landslide4sense import (
    Landslide4SensePreprocessor
)


# Initialize components (would be dependency injected in a real framework)
_config = get_image_ai_config()
_model_loader = Landslide4SenseModelLoader()
_preprocessor = Landslide4SensePreprocessor()
_inference_engine = Landslide4SenseInferenceEngine(
    preprocessor=_preprocessor,
    model_loader=_model_loader
)


def predict_image_health() -> Dict[str, Any]:
    """
    Health check endpoint for the Image AI service.

    Returns:
        Dictionary with service status information
    """
    config = get_image_ai_config()

    # Determine service status
    if not config.is_image_ai_enabled():
        status = "disabled"
    elif _model_loader.is_model_available():
        status = "online"
    else:
        status = "enabled"  # AI enabled but no model available

    return {
        "service": "JARVIS Landslide4Sense Image AI",
        "status": status,
        "model_available": _model_loader.is_model_available(),
        "model_version": _model_loader.model_version,
        "note": "Phase 3 infrastructure - actual image inference available when model loaded",
        "timestamp": time.time()
    }


def predict_image_sample(image_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prediction endpoint for Landslide4Sense satellite imagery.

    Args:
        image_data: Dictionary containing image data and metadata
                   Expected format: {
                       "image_data": "base64_encoded_string_or_file_path",
                       "metadata": {
                           "timestamp": "ISO_8601_string",
                           "location": {"latitude": float, "longitude": float},
                           "processing_level": "L1C|L2A"
                       }
                   }

    Returns:
        Dictionary with prediction results or error information
    """
    # Check if AI is enabled
    config = get_image_ai_config()
    if not config.is_image_ai_enabled():
        return {
            "success": False,
            "error": "Image AI is disabled via configuration",
            "error_code": "IMAGE_AI_DISABLED",
            "model_available": False,
            "model_version": _model_loader.model_version,
            "timestamp": time.time()
        }

    # Check if model is available
    if not _model_loader.is_model_available():
        return {
            "success": False,
            "error": f"IMAGE MODEL NOT AVAILABLE: {_model_loader.model_path}",
            "error_code": "MODEL_NOT_AVAILABLE",
            "model_available": False,
            "model_path": str(_model_loader.model_path),
            "model_version": _model_loader.model_version,
            "timestamp": time.time()
        }

    # Extract image data and metadata
    image_data_content = image_data.get("image_data")
    metadata = image_data.get("metadata", {})

    if not image_data_content:
        return {
            "success": False,
            "error": "MISSING_IMAGE_DATA: No image data provided",
            "error_code": "MISSING_IMAGE_DATA",
            "model_available": True,
            "model_version": _model_loader.model_version,
            "timestamp": time.time()
        }

    # Handle image data - could be base64 encoded string or file path
    sample_path = None
    temp_file_to_cleanup = None

    try:
        # Check if it's a base64 encoded string
        if isinstance(image_data_content, str) and len(image_data_content) > 100:  # Likely base64
            # Decode base64 and save to temporary file
            try:
                image_bytes = base64.b64decode(image_data_content)
                # Create a temporary file with appropriate extension
                suffix = ".h5"  # Default to HDF5 for Landslide4Sense
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    temp_file.write(image_bytes)
                    sample_path = Path(temp_file.name)
                    temp_file_to_cleanup = sample_path
            except Exception as e:
                return {
                    "success": False,
                    "error": f"BASE64_DECODING_FAILED: Failed to decode base64 image data: {str(e)}",
                    "error_code": "BASE64_DECODING_FAILED",
                    "model_available": True,
                    "model_version": _model_loader.model_version,
                    "timestamp": time.time()
                }
        elif isinstance(image_data_content, str) and os.path.exists(image_data_content):
            # It's a file path
            sample_path = Path(image_data_content)
        else:
            return {
                "success": False,
                "error": "INVALID_IMAGE_DATA: Image data must be a valid file path or base64 encoded string",
                "error_code": "INVALID_IMAGE_DATA",
                "model_available": True,
                "model_version": _model_loader.model_version,
                "timestamp": time.time()
            }

        # Run inference using the inference engine
        inference_result = _inference_engine.run_inference(sample_path)

        # Clean up temporary file if we created one
        if temp_file_to_cleanup and temp_file_to_cleanup.exists():
            try:
                os.unlink(temp_file_to_cleanup)
            except Exception:
                pass  # Best effort cleanup

        # If inference was successful, format the response for the API
        if inference_result.get("success", False):
            # Extract the image-level probability (this is what the API should return)
            image_level_probability = inference_result["image_level_probability"]

            # Determine risk level based on probability thresholds
            # Using the same thresholds as in the risk service for consistency
            if image_level_probability >= 0.75:
                risk_level = "VERY_HIGH"
            elif image_level_probability >= 0.55:
                risk_level = "HIGH"
            elif image_level_probability >= 0.35:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            # Default confidence (can be enhanced based on model uncertainty in future)
            confidence = 0.91

            # Generate some basic factors (in future, could be enhanced with explainable AI)
            factors = [
                "Landslide4Sense satellite imagery analysis",
                f"Model version: {_model_loader.model_version}",
                f"Inference completed successfully"
            ]

            # Add location-based info if available in metadata
            location = metadata.get("location", {})
            if location:
                lat = location.get("latitude")
                lon = location.get("longitude")
                if lat is not None and lon is not None:
                    factors.append(f"Location: {lat:.4f}°N, {lon:.4f}°E")

            return {
                "success": True,
                "landsat_probability": round(image_level_probability, 4),
                "risk_level": risk_level,
                "confidence": confidence,
                "factors": factors,
                "metadata": {
                    "processed_at": time.time(),
                    "model_version": _model_loader.model_version,
                    "inference_time_ms": inference_result.get("processing_time_ms", 0)
                },
                "model_available": True,
                "model_version": _model_loader.model_version,
                "timestamp": time.time()
            }
        else:
            # Inference failed - return the error from the inference engine
            return {
                "success": False,
                "error": inference_result.get("error", "Unknown inference error"),
                "error_code": inference_result.get("error_code", "INFERENCE_ERROR"),
                "model_available": _model_loader.is_model_available(),
                "model_path": str(_model_loader.model_path),
                "model_version": _model_loader.model_version,
                "timestamp": time.time()
            }

    except Exception as e:
        # Clean up temporary file if we created one
        if temp_file_to_cleanup and temp_file_to_cleanup.exists():
            try:
                os.unlink(temp_file_to_cleanup)
            except Exception:
                pass  # Best effort cleanup

        return {
            "success": False,
            "error": f"PREDICTION_FAILED: {str(e)}",
            "error_code": "PREDICTION_FAILED",
            "model_available": _model_loader.is_model_available(),
            "model_version": _model_loader.model_version,
            "timestamp": time.time()
        }


def get_model_info() -> Dict[str, Any]:
    """
    Model information endpoint.

    Returns:
        Dictionary with model and configuration information
    """
    config = get_image_ai_config()
    model_info = _model_loader.get_model_info()
    inference_status = _inference_engine.get_engine_status()

    return {
        "model_available": model_info["model_available"],
        "model_path": model_info["model_path"],
        "model_version": model_info["model_version"],
        "image_ai_enabled": model_info["image_ai_enabled"],
        "dataset_path": str(config.get_dataset_path()),
        "inference_engine_status": "ready" if inference_status["engine_ready"] else "not_ready",
        "preprocessor_configured": inference_status["preprocessor_configured"],
        "timestamp": time.time()
    }