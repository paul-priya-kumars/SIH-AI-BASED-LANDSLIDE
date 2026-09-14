"""
Landslide4Sense Model Loading Abstraction

Provides a unified interface for loading trained Landslide4Sense models.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImageModelNotAvailableError(Exception):
    """Raised when the image AI model is not available."""
    pass


class Landslide4SenseModelLoader:
    """
    Model loading interface for Landslide4Sense U-Net models.

    This abstraction handles:
    - Loading a trained model from a configured path
    - Validating that the model exists
    - Clear error handling when model is not available
    - Model caching where appropriate
    - Model version identification
    """

    def __init__(self,
                 model_path: Optional[Path] = None,
                 model_version: str = "unknown",
                 cache_model: bool = True):
        """
        Initialize the Landslide4Sense model loader.

        Args:
            model_path: Path to the trained model file
            model_version: Version identifier for the model
            cache_model: Whether to cache the loaded model in memory
        """
        self.model_path = model_path
        self.model_version = model_version
        self.cache_model = cache_model
        self._cached_model = None
        self._model_loaded = False

    def is_model_available(self) -> bool:
        """
        Check if the model file exists and is accessible.

        Returns:
            True if model is available, False otherwise
        """
        if self.model_path is None:
            return False
        return self.model_path.exists() and self.model_path.is_file()

    def load_model(self) -> Any:
        """
        Load the trained Landslide4Sense model.

        Returns:
            The loaded model object

        Raises:
            ImageModelNotAvailableError: If the model is not available
            RuntimeError: If there's an error loading the model
        """
        # Return cached model if available and caching is enabled
        if self.cache_model and self._cached_model is not None:
            return self._cached_model

        # Check if model is available
        if not self.is_model_available():
            logger.warning(
                f"Landslide4Sense model not available at {self.model_path}. "
                "Returning controlled error."
            )
            raise ImageModelNotAvailableError(
                f"IMAGE MODEL NOT AVAILABLE: No trained model found at {self.model_path}"
            )

        try:
            # In Phase 1, we don't actually load a model since none exists yet
            # In Phase 2, this would be implemented with torch.load() or similar
            logger.info(
                f"Loading Landslide4Sense model from {self.model_path} "
                f"(version: {self.model_version})"
            )

            # Placeholder for actual model loading
            # In Phase 2, replace with:
            # import torch
            # model = torch.load(self.model_path, map_location='cpu')
            # model.eval()
            model = None  # Placeholder

            # Cache the model if enabled
            if self.cache_model:
                self._cached_model = model
                self._model_loaded = True

            return model

        except Exception as e:
            logger.error(f"Failed to load Landslide4Sense model: {e}")
            raise RuntimeError(f"Error loading image model: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dictionary containing model metadata
        """
        return {
            "model_available": self.is_model_available(),
            "model_path": str(self.model_path) if self.model_path else None,
            "model_version": self.model_version,
            "model_cached": self._cached_model is not None,
            "model_loaded": self._model_loaded
        }

    def clear_cache(self) -> None:
        """Clear the cached model from memory."""
        self._cached_model = None
        self._model_loaded = False
        logger.info("Cleared Landslide4Sense model cache")


def get_default_model_loader() -> Landslide4SenseModelLoader:
    """
    Get a default Landslide4Sense model loader instance.

    Returns:
        Configured model loader that reports model not available
    """
    # Point to a non-existent model directory to clearly indicate
    # that no model is available in Phase 1
    default_model_path = Path("./models/landsat4sense_unet/not_available")
    return Landslide4SenseModelLoader(
        model_path=default_model_path,
        model_version="not_available-phase1",
        cache_model=False
    )