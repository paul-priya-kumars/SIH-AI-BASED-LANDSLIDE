"""
Configuration for Landslide4Sense Image AI Module

Handles configuration via environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional


class ImageAIConfig:
    """
    Configuration class for Landslide4Sense image AI components.
    """

    # Environment variable names
    ENV_MODEL_PATH = "JARVIS_IMAGE_MODEL_PATH"
    ENV_MODEL_VERSION = "JARVIS_IMAGE_MODEL_VERSION"
    ENV_IMAGE_AI_ENABLED = "JARVIS_IMAGE_AI_ENABLED"
    ENV_DATASET_PATH = "JARVIS_LANDSLIDE4SENSE_DATASET_PATH"

    # Default values
    DEFAULT_MODEL_PATH = "./models/not_available"
    DEFAULT_MODEL_VERSION = "not-available-phase1"
    DEFAULT_IMAGE_AI_ENABLED = False
    DEFAULT_DATASET_PATH = "./datasets/landsat4sense"

    def get_model_path(self) -> Path:
        """Get the configured model path."""
        return Path(os.getenv(self.ENV_MODEL_PATH, self.DEFAULT_MODEL_PATH))

    def get_model_version(self) -> str:
        """Get the configured model version."""
        return os.getenv(self.ENV_MODEL_VERSION, self.DEFAULT_MODEL_VERSION)

    def is_image_ai_enabled(self) -> bool:
        """Check if image AI is enabled via configuration."""
        return os.getenv(
            self.ENV_IMAGE_AI_ENABLED, str(self.DEFAULT_IMAGE_AI_ENABLED)
        ).lower() in ("true", "1", "yes", "on")

    def get_dataset_path(self) -> Path:
        """Get the configured dataset path."""
        return Path(os.getenv(self.ENV_DATASET_PATH, self.DEFAULT_DATASET_PATH))

    def is_configured_correctly(self) -> bool:
        """
        Check if the configuration is valid.

        Returns:
            True if configuration appears valid, False otherwise
        """
        # In Phase 1, we expect the model to NOT be available
        # This method is more for validation in later phases
        return True

    def __str__(self) -> str:
        """String representation of the configuration."""
        return (
            f"ImageAIConfig(\n"
            f"  model_path={self.get_model_path()},\n"
            f"  model_version='{self.get_model_version()}',\n"
            f"  image_ai_enabled={self.is_image_ai_enabled()},\n"
            f"  dataset_path={self.get_dataset_path()}\n"
            f")"
        )


# Global configuration instance
config = ImageAIConfig()


def get_image_ai_config() -> ImageAIConfig:
    """
    Get the global image AI configuration instance.

    Returns:
        The configured ImageAIConfig object
    """
    return config