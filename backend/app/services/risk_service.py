"""
Risk Service (M1 Integration Point)
====================================
NOTE FOR M1 TEAM:
In Phase 1, this service returns realistic mock predictions and heuristic assessments.
In Phase 2, M1 will replace `get_risk_prediction` with real model inference (e.g., ONNX, PyTorch, or ML REST API call).
Keep the method signature and return schema `RiskPredictionResponse` identical to prevent breaking the frontend.
"""

import os
import joblib
from datetime import datetime
from typing import List
import torch
import numpy as np
from ..schemas.risk import RiskPredictionResponse
from ..schemas.batch import BatchCoordinate
from .environment_service import get_environment_data
from ..cache import get_prediction_cache
from ..metrics import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL, CACHE_ERRORS_TOTAL
from ..config import settings
from ..exceptions import ModelNotAvailable, InferenceError
import logging

logger = logging.getLogger(__name__)

# Import our Landslide4sense model components
try:
    from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
    from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor
    LANDSLIDE4SENSE_MODEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import Landslide4sense model components: {e}")
    LANDSLIDE4SENSE_MODEL_AVAILABLE = False

from .m1_model_service import (
    m1_model_service,
    resolve_m1_model_path,
    build_feature_vector_from_environment,
    M1_FEATURE_NAMES,
)

# Global variables for the M1 environmental model (real Phase 3 artifact).
_model = None
_model_loaded = False
_model_path = resolve_m1_model_path()

# Global variables for the M3 (Landslide4Sense) satellite model.
_landsat_model = None
_landsat_preprocessor = None
_landsat_model_loaded = False
_m3_checkpoint_path = os.environ.get("JARVIS_IMAGE_MODEL_PATH") or os.path.join(
    os.path.dirname(__file__), "..", "..", "..",
    "phase6", "image_analysis", "checkpoints", "best_model.pth",
)

def _load_model():
    """Load the real Phase 3 M1 environmental risk model.

    Returns:
        bool: True when the real artifact is loaded; False when it is
        unavailable or the mock path is forced via ``MOCK_M1_ML``.
    """
    global _model, _model_loaded

    if _model_loaded:
        return _model is not None

    _model_loaded = True

    if settings.MOCK_M1_ML:
        logger.info("MOCK_M1_ML enabled - M1 environmental model intentionally bypassed")
        _model = None
        return False

    try:
        _model = m1_model_service.get_model()
        logger.info(f"Real M1 model loaded from {m1_model_service.model_path}")
        return True
    except Exception as e:
        logger.info(f"Real M1 model unavailable ({e}); using heuristic risk")
        _model = None
        return False

def _check_geographic_metadata_available():
    """Check if geographic metadata is available for coordinate-to-image mapping.

    Returns:
        bool: True if geographic metadata is available, False otherwise
    """
    # Based on inspection of the actual dataset, the HDF5 files contain
    # only image data with no apparent geographic metadata (latitude/longitude).
    # The documentation claims patches are georeferenced, but this metadata
    # is not present in the provided dataset files.
    #
    # Since we cannot legitimately map coordinates to specific image patches
    # without geographic metadata, we return False to indicate that
    # coordinate-based image selection is not possible.
    return False


def _load_landsat_model():
    """Load the Landslide4Sense satellite imagery model.

    Returns:
        bool: True if model is loaded successfully, False otherwise
    """
    global _landsat_model, _landsat_preprocessor, _landsat_model_loaded

    if _landsat_model_loaded:
        return _landsat_model is not None

    if not LANDSLIDE4SENSE_MODEL_AVAILABLE:
        logger.info("Landslide4Sense model components not available")
        _landsat_model_loaded = True
        return False

    # No coordinate -> patch mapping exists (the dataset carries no geographic
    # metadata), so the satellite checkpoint can never serve a lat/lon request.
    # Skip loading the ~295MB of weights here; use the dedicated M3 endpoint for
    # explicit patch inference instead.
    if not _check_geographic_metadata_available():
        logger.info(
            "M3 satellite checkpoint intentionally not loaded for coordinate requests "
            "(no coordinate->patch mapping available)"
        )
        _landsat_model_loaded = True
        return False

    try:
        if os.path.exists(_m3_checkpoint_path):
            # Load checkpoint with proper handling for PyTorch 2.6+ weights_only security feature
            try:
                # First try with weights_only=True (secure default)
                checkpoint = torch.load(_m3_checkpoint_path, map_location='cpu', weights_only=True)
            except Exception:
                # If that fails, use weights_only=False since we trust our own checkpoint files
                checkpoint = torch.load(_m3_checkpoint_path, map_location='cpu', weights_only=False)

            # Initialize model
            _landsat_model = UNetResNet34(
                in_channels=checkpoint.get("config", {}).get("in_channels", 14),
                num_classes=checkpoint.get("config", {}).get("num_classes", 1),
                pretrained=False,
            )
            _landsat_model.load_state_dict(checkpoint["model_state_dict"])
            _landsat_model.eval()

            # Initialize preprocessor
            preprocessor_state = checkpoint.get("preprocessor_state", {})
            _landsat_preprocessor = Landslide4SensePreprocessor(
                normalize_bands=preprocessor_state.get("normalize_bands", True),
                band_means=np.array(preprocessor_state["band_means"]) if preprocessor_state.get("band_means") is not None else None,
                band_stds=np.array(preprocessor_state["band_stds"]) if preprocessor_state.get("band_stds") is not None else None,
            )

            logger.info(f"Landslide4Sense model loaded from {_m3_checkpoint_path}")
            _landsat_model_loaded = True
            return True
        else:
            logger.info(f"No Landslide4Sense model found at {_m3_checkpoint_path}")
            _landsat_model_loaded = True
            return False
    except Exception as e:
        logger.error(f"Error loading Landslide4Sense model: {e}")
        _landsat_model = None
        _landsat_preprocessor = None
        _landsat_model_loaded = True
        return False

def _calculate_mock_factors(latitude: float, longitude: float) -> List[str]:
    # Nilgiris approximate bounding box: 11.2 - 11.6 N, 76.4 - 76.9 E
    factors = []
    if 11.35 <= latitude <= 11.45:
        factors.append("Saturated colluvial regolith on steep slope")
        factors.append("24h cumulative rainfall exceeding 120mm threshold")
    else:
        factors.append("Moderate antecedent moisture index")

    factors.append("Toe erosion near road embankments")
    factors.append("Historical landslide inventory hotspot")
    return factors

def get_risk_prediction(latitude: float, longitude: float) -> RiskPredictionResponse:
    """
    Computes or retrieves landslide risk for a specified geographic coordinate.
    Phase 1: Heuristic mock data based on Nilgiris region coordinates.
    Phase 2: Uses real ML model from M1 if available, otherwise falls back to mock.
    Includes caching layer for performance optimization.
    """
    # Check if caching is enabled
    if not settings.CACHE_ENABLED:
        return _get_risk_prediction_uncached(latitude, longitude)

    # Generate cache key based on normalized coordinates
    # Normalize to 4 decimal places (~11 meters precision)
    lat_key = round(latitude, 4)
    lon_key = round(longitude, 4)
    cache_key = f"risk:{lat_key}:{lon_key}"

    try:
        cache = get_prediction_cache()
        # Try to get from cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            CACHE_HITS_TOTAL.labels(cache_type="risk").inc()
            logger.debug(f"Risk cache hit for key: {cache_key}")
            return cached_result

        # Cache miss
        CACHE_MISSES_TOTAL.labels(cache_type="risk").inc()
        logger.debug(f"Risk cache miss for key: {cache_key}")

        # Compute result - this should NOT be wrapped in the cache error handling
        result = _get_risk_prediction_uncached(latitude, longitude)

        # Store in cache
        cache.set(cache_key, result)
        logger.debug(f"Stored risk result in cache for key: {cache_key}")

        return result
    except Exception as e:
        # If cache fails, log error and fall back to uncached computation
        CACHE_ERRORS_TOTAL.labels(cache_type="risk").inc()
        logger.error(f"Risk cache error: {e}. Falling back to uncached computation.")
        return _get_risk_prediction_uncached(latitude, longitude)


def _get_risk_prediction_uncached(latitude: float, longitude: float) -> RiskPredictionResponse:
    """
    Internal function that computes landslide risk without caching.
    This contains the original logic from get_risk_prediction.
    """
    # Try to load the models (only loads once)
    model_available = _load_model()
    landsat_model_available = _load_landsat_model()

    # Get environmental data for location name and factors (maintain compatibility)
    env_data = get_environment_data(latitude, longitude)

    # Phase 2: Use real Landslide4Sense model if available and geographic metadata is available
    if landsat_model_available and _landsat_model is not None and _landsat_preprocessor is not None and _check_geographic_metadata_available():
        try:
            # No coordinate -> patch mapping exists (the dataset has no
            # geographic metadata), so this branch stays disabled. When a real
            # mapping is added, the patch to analyse is configured explicitly.
            sample_image_path = os.environ.get("JARVIS_SAMPLE_IMAGE_PATH") or os.path.join(
                os.path.dirname(__file__), "..", "..", "..",
                "phase6", "image_analysis", "checkpoints", "sample_patch.h5",
            )

            # Load and preprocess the satellite image
            import h5py
            with h5py.File(sample_image_path, 'r') as f:
                img_data = f['img'][:]  # shape: (128, 128, 14)

            # Preprocess using our Landslide4Sense preprocessor
            img_processed = _landsat_preprocessor.preprocess_sample(img_data)

            # Convert to tensor and add batch dimension
            img_tensor = torch.from_numpy(img_processed).unsqueeze(0)  # (1, C, H, W)

            # Run inference
            with torch.no_grad():
                logits = _landsat_model(img_tensor)
                probs = torch.sigmoid(logits)  # shape: (1, 1, 128, 128) or (1, 2, 128, 128)

                # Handle different output shapes
                if probs.shape[1] == 2:
                    # Binary classification with 2 channels: take probability of positive class (index 1)
                    probs = probs[:, 1:2, :, :]  # shape: (1, 1, 128, 128)
                # If already shape (1, 1, H, W), use as is

                # Convert to numpy and extract image-level probability
                probs_np = probs.squeeze().cpu().numpy()  # shape: (H, W)

                # Derive image-level probability: use maximum probability
                # (indicates if there's ANY high-risk area in the patch)
                image_level_probability = float(np.max(probs_np))

                # Alternative approaches:
                # image_level_probability = float(np.mean(probs_np))  # average risk
                # image_level_probability = float(np.sum(probs_np > 0.5) / probs_np.size)  # fraction above threshold

                # Clamp probability to valid range
                image_level_probability = max(0.0, min(1.0, image_level_probability))

                # Determine risk level based on probability thresholds
                if image_level_probability >= 0.75:
                    risk_level = "VERY_HIGH"
                elif image_level_probability >= 0.55:
                    risk_level = "HIGH"
                elif image_level_probability >= 0.35:
                    risk_level = "MODERATE"
                else:
                    risk_level = "LOW"

                # Confidence is the segmentation peak probability (no hard-coded value)
                confidence = image_level_probability

                # Generate risk factors (combine environmental insights with model prediction)
                factors = _calculate_mock_factors(latitude, longitude)
                # Add model-specific factor
                factors.append("Landslide4Sense satellite imagery analysis")

                location_name = env_data.location_name or "Analyzed Region"

                return RiskPredictionResponse(
                    latitude=round(latitude, 4),
                    longitude=round(longitude, 4),
                    location_name=location_name,
                    risk_probability=round(image_level_probability, 4),
                    risk_level=risk_level,
                    confidence=confidence,
                    factors=factors,
                    updated_at=datetime.utcnow(),
                    is_mock=False  # REAL MODEL IS BEING USED
                )
        except Exception as e:
            logger.error(f"Error during Landslide4Sense prediction: {e}")
            raise InferenceError(model_type="Landslide4Sense")

    # Real M1 environmental model (Phase 3 artifact) — primary path.
    if model_available and _model is not None:
        try:
            features = build_feature_vector_from_environment(env_data)
        except Exception as e:
            logger.warning(f"M1 feature vector unavailable ({e}); using heuristic risk")
            features = None

        if features is not None:
            try:
                proba = _model.predict_proba([features])[0]
                classes = [str(c) for c in getattr(_model, "classes_", [])]
                if not classes or len(classes) != len(proba):
                    raise ValueError("model did not expose usable class labels")

                prob_map = {label: float(p) for label, p in zip(classes, proba)}
                predicted = max(prob_map, key=prob_map.get)

                # Documented in docs/RISK_ENGINE.md:
                #   risk_probability = P(class == HIGH)
                #   confidence       = max class probability (from the model itself)
                risk_probability = max(0.0, min(1.0, float(prob_map.get("HIGH", 0.0))))
                risk_level = {
                    "LOW": "LOW",
                    "MEDIUM": "MODERATE",
                    "MODERATE": "MODERATE",
                    "HIGH": "HIGH",
                    "VERY_HIGH": "VERY_HIGH",
                }.get(predicted, predicted)
                confidence = max(0.0, min(1.0, float(max(proba))))

                # Generate risk factors
                factors = _calculate_mock_factors(latitude, longitude)
                factors.append("Phase 3 RandomForest environmental model (8-feature contract)")

                location_name = env_data.location_name or "Predicted Location"

                return RiskPredictionResponse(
                    latitude=round(latitude, 4),
                    longitude=round(longitude, 4),
                    location_name=location_name,
                    risk_probability=round(risk_probability, 4),
                    risk_level=risk_level,
                    confidence=confidence,
                    factors=factors,
                    updated_at=datetime.utcnow(),
                    is_mock=False  # REAL M1 MODEL IS BEING USED
                )
            except Exception as e:
                logger.error(f"Error during ML prediction: {e}")
                raise InferenceError(model_type="ML")

    # Final fallback to mock implementation (Phase 1 behavior)
    dist_ooty = abs(latitude - 11.41) + abs(longitude - 76.69)

    if dist_ooty < 0.08:
        # High rainfall highland conditions (e.g. Ooty center)
        risk_probability = 0.82
        risk_level = "VERY_HIGH"
        confidence = 0.91
        location_name = "Ooty Valley Escarpment"
    elif dist_ooty < 0.2:
        # Coonoor / Kotagiri corridor
        risk_probability = 0.68
        risk_level = "HIGH"
        confidence = 0.87
        location_name = "Nilgiris Mountain Corridor"
    elif dist_ooty < 0.5:
        # Lower elevation foothills
        risk_probability = 0.44
        risk_level = "MODERATE"
        confidence = 0.84
        location_name = "Lower Ghat Foothills"
    else:
        # Regional plateau
        risk_probability = 0.21
        risk_level = "LOW"
        confidence = 0.89
        location_name = "Regional Plateau"

    return RiskPredictionResponse(
        latitude=round(latitude, 4),
        longitude=round(longitude, 4),
        location_name=location_name,
        risk_probability=round(risk_probability, 4),
        risk_level=risk_level,
        confidence=confidence,
        factors=_calculate_mock_factors(latitude, longitude),
        updated_at=datetime.utcnow(),
        is_mock=True  # MOCK DATA IS BEING USED
    )


def batch_risk_predict(coordinates: List[BatchCoordinate]) -> List[RiskPredictionResponse]:
    """
    Process a batch of latitude/longitude coordinates for risk prediction.
    Uses caching to avoid redundant computations for duplicate or previously computed coordinates.

    Args:
        coordinates: List of BatchCoordinate objects containing latitude and longitude

    Returns:
        List of RiskPredictionResponse objects in the same order as input coordinates
    """
    if not coordinates:
        return []

    # Check if caching is enabled
    if not settings.CACHE_ENABLED:
        # If caching is disabled, compute all predictions uncached
        return [_get_risk_prediction_uncached(coord.latitude, coord.longitude) for coord in coordinates]

    try:
        cache = get_prediction_cache()
        results = [None] * len(coordinates)  # Pre-allocate results list
        uncached_coords = []  # List to store coordinates that need computation
        uncached_indices = []  # Indices of uncached coordinates

        # First pass: check cache for all coordinates
        for i, coord in enumerate(coordinates):
            # Generate cache key based on normalized coordinates (same as get_risk_prediction)
            lat_key = round(coord.latitude, 4)
            lon_key = round(coord.longitude, 4)
            cache_key = f"risk:{lat_key}:{lon_key}"

            try:
                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    # Cache hit
                    CACHE_HITS_TOTAL.labels(cache_type="risk").inc()
                    results[i] = cached_result
                else:
                    # Cache miss
                    CACHE_MISSES_TOTAL.labels(cache_type="risk").inc()
                    uncached_coords.append(coord)
                    uncached_indices.append(i)
            except Exception as e:
                # If cache fails for this coordinate, treat as cache miss and log error
                CACHE_ERRORS_TOTAL.labels(cache_type="risk").inc()
                logger.error(f"Risk cache error for key {cache_key}: {e}. Treating as cache miss.")
                uncached_coords.append(coord)
                uncached_indices.append(i)

        # Second pass: compute predictions for uncached coordinates
        if uncached_coords:
            # Compute predictions for all uncached coordinates
            uncached_results = [_get_risk_prediction_uncached(coord.latitude, coord.longitude)
                              for coord in uncached_coords]

            # Store results in cache and fill in the results list
            for i, (coord, result) in enumerate(zip(uncached_coords, uncached_results)):
                idx = uncached_indices[i]
                # Generate cache key again for storage
                lat_key = round(coord.latitude, 4)
                lon_key = round(coord.longitude, 4)
                cache_key = f"risk:{lat_key}:{lon_key}"

                try:
                    # Store in cache
                    cache.set(cache_key, result)
                    results[idx] = result
                except Exception as e:
                    # If cache fails to store, still return the result but log error
                    CACHE_ERRORS_TOTAL.labels(cache_type="risk").inc()
                    logger.error(f"Failed to store risk result in cache for key {cache_key}: {e}")
                    results[idx] = result  # Still return the computed result

        return results

    except Exception as e:
        # If overall cache processing fails, log the error and re-raise so endpoint can handle it
        logger.error(f"Batch risk cache processing failed: {e}")
        CACHE_ERRORS_TOTAL.labels(cache_type="risk").inc()
        raise