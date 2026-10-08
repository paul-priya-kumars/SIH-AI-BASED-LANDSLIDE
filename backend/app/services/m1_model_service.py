"""
M1 Environmental Risk Model Service (REAL model integration)
============================================================
Loads the genuinely trained Phase 3 risk-model artifact and exposes inference.

Artifact
--------
``phase3/model_training/risk_model.joblib``
    ``sklearn.pipeline.Pipeline`` = ``StandardScaler`` -> ``RandomForestClassifier``
    (``n_estimators=100``, ``class_weight="balanced"``, ``random_state=42``),
    produced by ``phase3/model_training/train_model.py`` from
    ``phase3/dataset/train_dataset.csv``.

Feature contract (order matters — it is the order the artifact was fitted with)
-------------------------------------------------------------------------------
1. rainfall_mm        5. temperature_c
2. soil_moisture_pct  6. river_level_m
3. slope_deg          7. vegetation_index
4. elevation_m        8. landslide_history

Honesty contract
----------------
* This service never fabricates availability. If the artifact is missing,
  unreadable, or has an incompatible feature count, ``is_available()`` returns
  ``False`` and ``resolved_path``/``error`` explain exactly why.
* Class labels and probabilities come from the model itself; nothing is
  hard-coded.
* Weights are never modified — the artifact is loaded read-only.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# <repo>/backend/app/services/m1_model_service.py -> <repo>
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)

DEFAULT_MODEL_RELPATH = os.path.join("phase3", "model_training", "risk_model.joblib")

#: Feature order the artifact was trained with. Do not reorder.
M1_FEATURE_NAMES: List[str] = [
    "rainfall_mm",
    "soil_moisture_pct",
    "slope_deg",
    "elevation_m",
    "temperature_c",
    "river_level_m",
    "vegetation_index",
    "landslide_history",
]

#: Mapping from the artifact's own class labels to the API's risk vocabulary.
_M1_CLASS_TO_LEVEL = {
    "LOW": "LOW",
    "MEDIUM": "MODERATE",
    "MODERATE": "MODERATE",
    "HIGH": "HIGH",
    "VERY_HIGH": "VERY_HIGH",
}

MODEL_VERSION = "M1-PHASE3-RF-v1.0"


def resolve_m1_model_path() -> str:
    """Resolve the M1 artifact path (``JARVIS_M1_MODEL_PATH`` overrides)."""
    configured = os.environ.get("JARVIS_M1_MODEL_PATH")
    if configured:
        return configured if os.path.isabs(configured) else os.path.join(REPO_ROOT, configured)
    return os.path.join(REPO_ROOT, DEFAULT_MODEL_RELPATH)


class M1ModelUnavailableError(RuntimeError):
    """Raised when the M1 artifact is not available for inference."""


class M1FeatureUnavailableError(RuntimeError):
    """Raised when one or more required M1 features are missing (never fabricated)."""


def _sha256_prefix(path: str, length: int = 16) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()[:length]
    except Exception:
        return None


class M1ModelService:
    """Lazy, cached accessor for the real M1 environmental risk model."""

    def __init__(self, model_path: Optional[str] = None):
        self._explicit_path = model_path
        self._model: Any = None
        self._loaded = False
        self._error: Optional[str] = None
        self._checksum: Optional[str] = None

    # -- paths -----------------------------------------------------------
    @property
    def model_path(self) -> str:
        return self._explicit_path or resolve_m1_model_path()

    def artifact_present(self) -> bool:
        path = self.model_path
        return bool(path) and os.path.isfile(path)

    # -- loading ---------------------------------------------------------
    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return self._model is not None
        self._loaded = True

        path = self.model_path
        if not self.artifact_present():
            self._error = f"artifact not found: {path}"
            logger.info("M1 model not available (%s)", self._error)
            return False

        try:
            import joblib

            model = joblib.load(path)
        except Exception as exc:  # pragma: no cover - depends on artifact
            self._error = f"failed to load artifact: {exc}"
            logger.error("M1 model load failed: %s", self._error)
            return False

        n_features = getattr(model, "n_features_in_", None)
        if n_features is not None and int(n_features) != len(M1_FEATURE_NAMES):
            self._error = (
                f"feature count mismatch: artifact expects {int(n_features)}, "
                f"service provides {len(M1_FEATURE_NAMES)}"
            )
            logger.error("M1 model rejected: %s", self._error)
            return False

        if not hasattr(model, "predict_proba") and not hasattr(model, "predict"):
            self._error = "artifact exposes neither predict_proba nor predict"
            logger.error("M1 model rejected: %s", self._error)
            return False

        self._model = model
        self._checksum = _sha256_prefix(path)
        self._error = None
        logger.info("Real M1 environmental model loaded from %s", path)
        return True

    def is_available(self) -> bool:
        """True only when the real artifact is present and loadable."""
        return self._ensure_loaded()

    def get_model(self) -> Any:
        """Return the raw loaded artifact (used by the risk service)."""
        if not self._ensure_loaded():
            raise M1ModelUnavailableError(self._error or "M1 model unavailable")
        return self._model

    # -- introspection ---------------------------------------------------
    def describe(self) -> Dict[str, Any]:
        """Truthful metadata for health / model-info endpoints."""
        available = self.is_available()
        classes: List[str] = []
        if available:
            try:
                classes = [str(c) for c in getattr(self._model, "classes_", [])]
            except Exception:
                classes = []
        return {
            "available": available,
            "artifact_path": self.model_path,
            "model_version": MODEL_VERSION,
            "model_type": "sklearn Pipeline(StandardScaler + RandomForestClassifier)" if available else None,
            "feature_order": list(M1_FEATURE_NAMES),
            "classes": classes,
            "checksum_sha256_16": self._checksum,
            "error": None if available else self._error,
        }

    # -- inference -------------------------------------------------------
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run real inference for one feature vector.

        ``features`` must contain every name in :data:`M1_FEATURE_NAMES`.
        Missing/``None`` features raise :class:`M1FeatureUnavailableError` —
        values are never invented.
        """
        if not self._ensure_loaded():
            raise M1ModelUnavailableError(self._error or "M1 model unavailable")

        missing = [
            name
            for name in M1_FEATURE_NAMES
            if features.get(name) is None
        ]
        if missing:
            raise M1FeatureUnavailableError(
                "missing required M1 features (not fabricated): " + ", ".join(missing)
            )

        row = [float(features[name]) for name in M1_FEATURE_NAMES]

        proba = self._model.predict_proba([row])[0]
        classes = [str(c) for c in getattr(self._model, "classes_", [])]
        if not classes or len(classes) != len(proba):
            raise M1ModelUnavailableError("artifact did not expose usable class labels")

        prob_map = {label: float(p) for label, p in zip(classes, proba)}
        predicted = max(prob_map, key=prob_map.get)

        # Documented definition (see docs/RISK_ENGINE.md):
        #   risk_probability = P(class == HIGH)
        #   confidence       = max class probability (real, from the model)
        risk_probability = float(prob_map.get("HIGH", 0.0))

        return {
            "risk_level": _M1_CLASS_TO_LEVEL.get(predicted, predicted),
            "risk_probability": round(max(0.0, min(1.0, risk_probability)), 4),
            "confidence": round(float(max(proba)), 4),
            "probabilities": {k: round(v, 4) for k, v in prob_map.items()},
            "predicted_class": predicted,
            "model_version": MODEL_VERSION,
            "feature_order": list(M1_FEATURE_NAMES),
            "artifact_path": self.model_path,
        }


def build_feature_vector_from_environment(env_data: Any) -> List[float]:
    """Assemble the ordered 8-feature M1 vector from an environment response.

    Raises :class:`M1FeatureUnavailableError` if any required feature is
    missing so that callers fall back honestly instead of inventing values.
    """
    mapping = {
        "rainfall_mm": getattr(env_data, "rainfall", None),
        "soil_moisture_pct": getattr(env_data, "soil_saturation_pct", None),
        "slope_deg": getattr(env_data, "slope", None),
        "elevation_m": getattr(env_data, "elevation", None),
        "temperature_c": getattr(env_data, "temperature", None),
        "river_level_m": getattr(env_data, "river_level_m", None),
        "vegetation_index": getattr(env_data, "ndvi", None),
        "landslide_history": getattr(env_data, "landslide_history", None),
    }
    missing = [name for name in M1_FEATURE_NAMES if mapping.get(name) is None]
    if missing:
        raise M1FeatureUnavailableError(
            "missing required M1 features (not fabricated): " + ", ".join(missing)
        )
    return [float(mapping[name]) for name in M1_FEATURE_NAMES]


# Module-level singleton used by the risk service and health checks.
m1_model_service = M1ModelService()
