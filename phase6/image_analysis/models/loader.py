"""
Model loader abstraction for Landslide4Sense.

Provides interface for checking model availability and loading models.
In Phase 3, loads the actual trained model when available.
"""

import os
import hashlib
import time
from pathlib import Path
from typing import Any, Optional
import torch
import numpy as np

# Try to import the model architecture
try:
    from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
    from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor
    MODEL_ARCHITECTURE_AVAILABLE = True
except ImportError:
    MODEL_ARCHITECTURE_AVAILABLE = False
    UNetResNet34 = None
    Landslide4SensePreprocessor = None


class ImageModelNotAvailableError(Exception):
    """Raised when attempting to use a model that is not available."""
    pass


class Landslide4SenseModelLoader:
    """
    Model loader for Landslide4Sense models.

    Responsibilities:
    - Check whether a configured model file exists
    - Report model availability and version
    - Load models when available and AI is enabled
    - Handle missing models gracefully
    - Avoid loading models when AI is disabled
    - Provide clean error messages when model is not available
    - Cache loaded models for performance

    In Phase 3: Loads the actual trained model from checkpoint when available.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        model_version: str = "unknown",
        cache_model: bool = True
    ):
        """
        Initialize the model loader.

        Args:
            model_path: Path to the model file. If None, uses config default.
            model_version: Version string for the model.
            cache_model: Whether to cache the loaded model in memory.
        """
        # Import here to avoid circular dependencies
        from phase6.image_analysis.config import get_image_ai_config

        config = get_image_ai_config()
        self.model_path = model_path if model_path is not None else config.get_model_path()
        self.model_version = model_version if model_version != "unknown" else config.get_model_version()
        self.cache_model = cache_model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Internal state
        self._cached_model: Any = None
        self._cached_preprocessor: Any = None
        self._model_loaded = False
        self._checkpoint_config: dict = {}

        # For model metadata
        self._checksum: Optional[str] = None
        self._model_version: str = "unknown"
        self._load_time: float = 0.0

        # Calculate metadata if model is available
        if self.is_model_available():
            self._calculate_metadata()

    def _calculate_metadata(self) -> None:
        """Calculate model metadata including checksum, version, and load time."""
        start_time = time.time()

        # Calculate SHA-256 checksum of the model file
        self._checksum = self._calculate_checksum()

        # Create deterministic model version from checkpoint metadata
        self._model_version = self._create_model_version()

        # Measure load time by actually loading the model (if not already cached)
        # We'll load the model to get an accurate load time, but use caching to avoid
        # reloading if already cached
        if self._cached_model is None:
            try:
                self.load_model()
                self._load_time = time.time() - start_time
            except Exception:
                # If loading fails, set load time to 0
                self._load_time = 0.0
        else:
            # If already cached, we can't measure load time accurately without reloading
            # For now, we'll set it to a small value or try to estimate
            self._load_time = 0.001  # Minimal time for cached access

    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum of the model file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(self.model_path, "rb") as f:
                # Read file in chunks to handle large files efficiently
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            # If we can't read the file, return a default value
            return "error_calculating_checksum"

    def _create_model_version(self) -> str:
        """Create a deterministic model version string from checkpoint metadata."""
        if not self._checkpoint_config:
            # Try to load checkpoint to get metadata if not already loaded
            try:
                # Handle PyTorch 2.6+ weights_only security feature
                try:
                    checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=True)
                except Exception:
                    checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
                self._checkpoint_config = checkpoint.get("config", {})
            except Exception:
                # If we can't load the checkpoint, return a basic version
                return f"unknown-{int(time.time())}"

        # Extract version components from checkpoint
        epoch = self._checkpoint_config.get("epoch", 0)
        # Try to get architecture info
        in_channels = self._checkpoint_config.get("in_channels", 14)
        num_classes = self._checkpoint_config.get("num_classes", 1)

        # Create a deterministic version string
        # Format: landslide4sense-epoch{e}-ch{in}-cls{nc}
        return f"landslide4sense-epoch{epoch}-ch{in_channels}-cls{num_classes}"

    def is_model_available(self) -> bool:
        """
        Check if the model file exists and is accessible.

        Returns:
            True if model file exists and AI is enabled, False otherwise
        """
        # Respect AI enable/disable setting
        from phase6.image_analysis.config import get_image_ai_config
        config = get_image_ai_config()
        if not config.is_image_ai_enabled():
            return False

        # Check if file exists
        return self.model_path.exists() and self.model_path.is_file()

    def load_model(self) -> Any:
        """
        Load the model from disk.

        Returns:
            The loaded model object (PyTorch model ready for inference)

        Raises:
            ImageModelNotAvailableError: If model is not available
        """
        # Check if AI is enabled
        from phase6.image_analysis.config import get_image_ai_config
        config = get_image_ai_config()
        if not config.is_image_ai_enabled():
            raise ImageModelNotAvailableError(
                "Image AI is disabled via configuration (JARVIS_IMAGE_AI_ENABLED=false)"
            )

        # Check if model file exists
        if not self.is_model_available():
            raise ImageModelNotAvailableError(
                f"IMAGE MODEL NOT AVAILABLE: Model file not found at {self.model_path}"
            )

        # If caching and already loaded, return cached version
        if self.cache_model and self._cached_model is not None:
            return self._cached_model

        # Load the actual model from checkpoint
        if not MODEL_ARCHITECTURE_AVAILABLE:
            raise ImageModelNotAvailableError(
                f"MODEL ARCHITECTURE NOT AVAILABLE: Required dependencies not found"
            )

        try:
            # Handle PyTorch 2.6+ weights_only security feature
            try:
                # First try with weights_only=True (secure default)
                checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=True)
            except Exception:
                # If that fails, use weights_only=False since we trust our own checkpoint files
                checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)

            # Extract configuration from checkpoint
            config_from_checkpoint = checkpoint.get("config", {})
            self._checkpoint_config = config_from_checkpoint

            # Initialize model with checkpoint configuration
            model = UNetResNet34(
                in_channels=config_from_checkpoint.get("in_channels", 14),
                num_classes=config_from_checkpoint.get("num_classes", 1),
                pretrained=False,
            )
            model.load_state_dict(checkpoint["model_state_dict"])
            model = model.to(self.device)
            model.eval()  # Set to evaluation mode

            # Initialize or reconstruct preprocessor
            preprocessor_state = checkpoint.get("preprocessor_state", {})
            preprocessor = Landslide4SensePreprocessor(
                normalize_bands=preprocessor_state.get("normalize_bands", True),
                band_means=np.array(preprocessor_state["band_means"]) if preprocessor_state.get("band_means") is not None else None,
                band_stds=np.array(preprocessor_state["band_stds"]) if preprocessor_state.get("band_stds") is not None else None,
            )
            # Note: is_fitted is set by the preprocessor based on whether means/stds are provided

            # Cache the model and preprocessor
            self._cached_model = model
            self._cached_preprocessor = preprocessor
            self._model_loaded = True

            # Log loading info (in practice, would use proper logging)
            epoch = checkpoint.get("epoch", "unknown")
            best_val_dice = checkpoint.get("best_val_dice", "unknown")
            print(f"Loaded model from checkpoint: {self.model_path}")
            print(f"Model epoch: {epoch}")
            print(f"Best validation Dice: {best_val_dice}")

            return self._cached_model

        except Exception as e:
            raise ImageModelNotAvailableError(
                f"FAILED TO LOAD MODEL: {str(e)}"
            )

    def get_preprocessor(self) -> Any:
        """
        Get the preprocessor associated with the loaded model.

        Returns:
            The landslide4sense preprocessor fitted with checkpoint statistics

        Raises:
            ImageModelNotAvailableError: If model is not available
        """
        # Ensure model is loaded
        _ = self.load_model()  # This will load the model if not already cached

        if self._cached_preprocessor is None:
            raise ImageModelNotAvailableError(
                "PREPROCESSOR NOT AVAILABLE: Failed to load preprocessor from checkpoint"
            )

        return self._cached_preprocessor

    def get_model_info(self) -> dict:
        """
        Get information about the model configuration and availability.

        Returns:
            Dictionary with model information
        """
        from phase6.image_analysis.config import get_image_ai_config
        config = get_image_ai_config()

        # Calculate checksum if not already done
        if self._checksum is None and self.is_model_available():
            self._checksum = self._calculate_checksum()

        return {
            "model_available": self.is_model_available(),
            "model_path": str(self.model_path),
            "model_version": self.model_version,
            "image_ai_enabled": config.is_image_ai_enabled(),
            "cached_model": self._cached_model is not None,
            "model_loaded": self._model_loaded,
            "checkpoint_epoch": self._checkpoint_config.get("epoch", "unknown") if self._checkpoint_config else "unknown",
            "checkpoint_best_val_dice": self._checkpoint_config.get("best_val_dice", "unknown") if self._checkpoint_config else "unknown",
            # Additional metadata for Phase 4 Step 6
            "checksum": self._checksum,
            "load_time_seconds": self._load_time
        }

    def clear_cache(self) -> None:
        """Clear the cached model and preprocessor from memory."""
        self._cached_model = None
        self._cached_preprocessor = None
        self._model_loaded = False
        self._checkpoint_config = {}

    def __repr__(self) -> str:
        """String representation of the model loader."""
        return (
            f"Landslide4SenseModelLoader("
            f"model_path={self.model_path}, "
            f"model_version='{self.model_version}', "
            f"cache_model={self.cache_model}, "
            f"is_available={self.is_model_available()})"
        )


def get_default_model_loader() -> Landslide4SenseModelLoader:
    """
    Get a default model loader configured via environment variables.

    Returns:
        Configured Landslide4SenseModelLoader instance
    """
    return Landslide4SenseModelLoader()