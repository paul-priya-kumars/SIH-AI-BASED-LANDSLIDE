"""
ML Integration Contract Route (M1 Contract)
===========================================
This endpoint documents and stubs the contract interface designed for M1 (AI/ML Prediction Team).
In Phase 2, M1 will replace this mock handler with the actual neural network / gradient-boosted model inference.
"""

from fastapi import APIRouter
from ..schemas.risk import MLPredictRequest, MLPredictResponse
import os
import joblib
import logging

# Global variable for model
_model = None
_model_loaded = False
_model_path = os.path.join(os.path.dirname(__file__), "..", "models", "landslide_model.pkl")

# Logger
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/ml", tags=["M1 - Machine Learning Contract"])

def _load_model():
    """Load the M1 ML model if available."""
    global _model, _model_loaded

    if _model_loaded:
        return _model is not None

    try:
        if os.path.exists(_model_path):
            _model = joblib.load(_model_path)
            logger.info(f"ML model loaded from {_model_path}")
            _model_loaded = True
            return True
        else:
            logger.info(f"No ML model found at {_model_path}, using mock predictions")
            _model_loaded = True
            return False
    except Exception as e:
        logger.error(f"Error loading ML model: {e}. Falling back to mock predictions.")
        _model_loaded = True
        _model = None
        return False

@router.post(
    "/predict",
    response_model=MLPredictResponse,
    summary="M1 Integration Contract: Predict landslide risk from features"
)
def predict_landslide_risk(payload: MLPredictRequest) -> MLPredictResponse:
    """
    Contract endpoint for M1 ML model inference.

    * Phase 1 (M3): Stubs response with heuristic prediction based on input rainfall and slope features.
    * Phase 2 (M1): Uses actual model inference (e.g., CatBoost, XGBoost, or PyTorch).
    """
    # Try to load the model (only loads once)
    model_available = _load_model()

    if model_available and _model is not None:
        # Use real ML model for prediction
        try:
            # Extract features from payload
            rainfall = float(payload.features.get("rainfall", 100.0))
            slope = float(payload.features.get("slope", 25.0))
            elevation = float(payload.features.get("elevation", 2240.0))
            ndvi = float(payload.features.get("ndvi", 0.43))

            # Prepare features for the model
            features = [[rainfall, slope, elevation, ndvi]]

            # Get prediction probability
            if hasattr(_model, "predict_proba"):
                risk_probability = float(_model.predict_proba(features)[0][1])  # Probability of positive class
            else:
                # Fallback for models without predict_proba
                risk_probability = float(_model.predict(features)[0])

            # Clamp probability to valid range
            risk_probability = max(0.0, min(1.0, risk_probability))

            # Determine risk level based on probability thresholds
            if risk_probability >= 0.75:
                risk_level = "VERY_HIGH"
            elif risk_probability >= 0.55:
                risk_level = "HIGH"
            elif risk_probability >= 0.35:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            # Default confidence (can be enhanced based on model)
            confidence = 0.91

            # Generate risk factors based on input features
            factors = []
            if rainfall > 120:
                factors.append("24h cumulative rainfall exceeding 120mm threshold")
            if slope > 30:
                factors.append("Slope gradient exceeding 30 degrees")
            if elevation > 2000:
                factors.append("High elevation area (>2000m)")
            if ndvi < 0.3:
                factors.append("Low vegetation density (NDVI < 0.3)")

            # Ensure we have at least some factors
            if not factors:
                factors = ["Environmental factors within normal ranges"]

            return MLPredictResponse(
                risk_probability=risk_probability,
                risk_level=risk_level,
                confidence=confidence,
                factors=factors,
                model_version="M1-REAL-v1.0"  # Indicates real model is being used
            )
        except Exception as e:
            logger.error(f"Error during ML prediction in ml_contract: {e}. Falling back to mock predictions.")
            # Fall through to mock implementation below

    # Fallback to mock implementation (Phase 1 behavior)
    rainfall = float(payload.features.get("rainfall", 100.0))
    slope = float(payload.features.get("slope", 25.0))

    # Heuristic formula for mock contract demonstration
    score = (rainfall / 200.0) * 0.6 + (slope / 60.0) * 0.4
    risk_prob = min(max(round(score, 2), 0.05), 0.98)

    if risk_prob >= 0.75:
        risk_level = "VERY_HIGH"
    elif risk_prob >= 0.55:
        risk_level = "HIGH"
    elif risk_prob >= 0.35:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return MLPredictResponse(
        risk_probability=risk_prob,
        risk_level=risk_level,
        confidence=0.91,
        factors=[
            f"Precipitation feature: {rainfall}mm",
            f"Terrain gradient: {slope}°",
            "M1 mock prediction contract active"
        ],
        model_version="M1-MOCK-v1.0"
    )