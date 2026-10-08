"""
M3 Satellite Image Inference Service (real Landslide4Sense U-Net checkpoint)
============================================================================
Wraps the Phase 6 image-AI loader so the backend can run genuine segmentation
inference on a Landslide4Sense patch.

Artifact
--------
``phase6/image_analysis/checkpoints/best_model.pth``
    ``UNetResNet34`` (ResNet-34 encoder, 14 input channels, 1 output channel)
    trained with BCE+Dice; checkpoint records ``epoch=45`` and
    ``best_val_dice≈0.8032`` plus fitted preprocessing statistics.

Honesty contract
----------------
* ``is_available()`` is True only when the checkpoint genuinely exists *and*
  image AI is enabled *and* loadable.
* ``segment_patch`` never synthesises a prediction: it requires a real
  Landslide4Sense ``.h5`` patch and surfaces loader errors verbatim.
* Coordinate → patch mapping is NOT available (the dataset ships without
  geographic metadata), so this service is never used to attribute a
  satellite risk score to a lat/lon. See :func:`coordinate_mapping_status`.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)

DEFAULT_CHECKPOINT_RELPATH = os.path.join(
    "phase6", "image_analysis", "checkpoints", "best_model.pth"
)


def resolve_m3_checkpoint_path() -> str:
    """Resolve the M3 checkpoint path (``JARVIS_IMAGE_MODEL_PATH`` overrides)."""
    configured = os.environ.get("JARVIS_IMAGE_MODEL_PATH")
    if configured:
        return configured if os.path.isabs(configured) else os.path.join(REPO_ROOT, configured)
    return os.path.join(REPO_ROOT, DEFAULT_CHECKPOINT_RELPATH)


def coordinate_mapping_status() -> Dict[str, Any]:
    """Truthful statement about coordinate → image-patch mapping."""
    return {
        "available": False,
        "reason": (
            "The bundled Landslide4Sense patches carry no geographic metadata "
            "(no lat/lon per patch), so a coordinate cannot be mapped to a "
            "specific satellite patch. M3 inference is therefore exposed only "
            "for explicit patch inputs, never as a per-coordinate risk score."
        ),
    }


class M3InferenceService:
    """Lazy accessor around the Phase 6 model loader for genuine inference."""

    def __init__(self) -> None:
        self._loader: Any = None
        self._load_error: Optional[str] = None

    # -- paths / availability -------------------------------------------
    def checkpoint_path(self) -> str:
        return resolve_m3_checkpoint_path()

    def artifact_present(self) -> bool:
        path = self.checkpoint_path()
        return bool(path) and os.path.isfile(path)

    def _get_loader(self) -> Any:
        if self._loader is not None:
            return self._loader
        try:
            from phase6.image_analysis.models.loader import get_default_model_loader

            self._loader = get_default_model_loader()
        except Exception as exc:  # pragma: no cover - import guard
            self._load_error = f"model loader import failed: {exc}"
            logger.warning("M3 loader unavailable: %s", self._load_error)
            self._loader = None
        return self._loader

    def is_available(self) -> bool:
        if not self.artifact_present():
            return False
        loader = self._get_loader()
        if loader is None:
            return False
        try:
            return bool(loader.is_model_available())
        except Exception as exc:
            self._load_error = str(exc)
            return False

    # -- introspection ---------------------------------------------------
    def describe(self) -> Dict[str, Any]:
        loader = self._get_loader()
        checkpoint_path = self.checkpoint_path()
        base = {
            "available": self.is_available(),
            "artifact_path": checkpoint_path,
            "artifact_present": self.artifact_present(),
            "model_architecture": "UNetResNet34 (ResNet-34 encoder, 14ch in, 1ch out)",
            "coordinate_mapping": coordinate_mapping_status(),
            "error": self._load_error,
        }
        if loader is not None:
            try:
                base.update(
                    {
                        "checkpoint_epoch": getattr(loader, "_checkpoint_epoch", "unknown"),
                        "checkpoint_best_val_dice": getattr(loader, "_checkpoint_best_val_dice", "unknown"),
                    }
                )
            except Exception:
                pass
        return base

    # -- inference -------------------------------------------------------
    def segment_patch(self, h5_path: str) -> Dict[str, Any]:
        """Run real segmentation on a Landslide4Sense ``.h5`` patch."""
        if not os.path.isfile(h5_path):
            raise FileNotFoundError(f"patch not found: {h5_path}")
        if not self.is_available():
            raise RuntimeError(
                f"M3 model not available ({self._load_error or 'checkpoint missing'})"
            )

        import h5py
        import numpy as np
        import torch

        loader = self._get_loader()
        model = loader.load_model()
        preprocessor = loader.get_preprocessor()

        with h5py.File(h5_path, "r") as fh:
            key = "img" if "img" in fh else list(fh.keys())[0]
            patch = fh[key][:]

        processed = preprocessor.preprocess_sample(patch)
        tensor = torch.from_numpy(processed).unsqueeze(0).float()

        with torch.no_grad():
            logits = model(tensor)
            probs = torch.sigmoid(logits)
            if probs.shape[1] == 2:
                probs = probs[:, 1:2, :, :]
            probs_np = probs.squeeze().cpu().numpy()

        return {
            "patch_path": h5_path,
            "patch_shape": list(patch.shape),
            "output_shape": list(probs_np.shape),
            "mean_probability": float(np.mean(probs_np)),
            "max_probability": float(np.max(probs_np)),
            "positive_fraction": float(np.mean(probs_np > 0.5)),
            "threshold": 0.5,
            "checkpoint_path": self.checkpoint_path(),
            "is_mock": False,
        }


m3_inference_service = M3InferenceService()
