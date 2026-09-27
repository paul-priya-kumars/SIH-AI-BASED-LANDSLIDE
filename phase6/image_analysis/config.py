"""
Configuration for Landslide4Sense Image AI Module.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path


class ImageAIConfig:
    """Configuration manager for Landslide4Sense Image AI."""

    def __init__(self):
        # Model configuration
        self.model_path = Path(
            os.getenv(
                "JARVIS_IMAGE_MODEL_PATH",
                "./models/landslide4sense_unet/not_available"
            )
        )
        self.model_version = os.getenv(
            "JARVIS_IMAGE_MODEL_VERSION",
            "not-available-phase1"
        )

        # AI enable/disable
        self.image_ai_enabled = self._parse_bool(
            os.getenv("JARVIS_IMAGE_AI_ENABLED", "false")
        )

        # Dataset configuration
        self.dataset_path = Path(
            os.getenv(
                "JARVIS_LANDSLIDE4SENSE_DATASET_PATH",
                "./datasets/landslide4sense"
            )
        )

        # Preprocessing configuration
        self.normalize_bands = self._parse_bool(
            os.getenv("JARVIS_IMAGE_NORMALIZE_BANDS", "true")
        )

        # Inference configuration
        self.prediction_threshold = float(
            os.getenv("JARVIS_IMAGE_PREDICTION_THRESHOLD", "0.5")
        )

    def _parse_bool(self, value: str) -> bool:
        """Parse string to boolean."""
        if isinstance(value, bool):
            return value
        return value.lower() in ("true", "1", "yes", "on")

    def get_model_path(self) -> Path:
        """Get the model file path."""
        return self.model_path

    def get_model_version(self) -> str:
        """Get the model version string."""
        return self.model_version

    def is_image_ai_enabled(self) -> bool:
        """Check if image AI is enabled via configuration."""
        return self.image_ai_enabled

    def get_dataset_path(self) -> Path:
        """Get the dataset path."""
        return self.dataset_path

    def get_normalize_bands(self) -> bool:
        """Get whether to normalize bands."""
        return self.normalize_bands

    def get_prediction_threshold(self) -> float:
        """Get the prediction threshold for landslide detection."""
        return self.prediction_threshold

    def is_configured_correctly(self) -> bool:
        """
        Basic validation that configuration is readable.
        Does not verify file existence (that's done elsewhere).
        """
        return True  # Configuration object creation succeeds if we get here

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"ImageAIConfig(model_path={self.model_path}, "
            f"model_version='{self.model_version}', "
            f"image_ai_enabled={self.image_ai_enabled}, "
            f"dataset_path={self.dataset_path})"
        )


# Global configuration instance (singleton pattern)
_config_instance = None


def get_image_ai_config() -> ImageAIConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ImageAIConfig()
    return _config_instance