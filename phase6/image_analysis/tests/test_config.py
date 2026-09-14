"""
Tests for Landslide4Sense image AI configuration.

Tests configuration loading and validation.
"""

import os
from pathlib import Path
from unittest.mock import patch

from phase6.image_analysis.config import ImageAIConfig, get_image_ai_config


def test_config_initialization():
    """Test that configuration initializes with default values."""
    # Clear relevant environment variables to test defaults
    env_vars_to_clear = [
        "JARVIS_IMAGE_MODEL_PATH",
        "JARVIS_IMAGE_MODEL_VERSION",
        "JARVIS_IMAGE_AI_ENABLED",
        "JARVIS_LANDSLIDE4SENSE_DATASET_PATH"
    ]

    # Temporarily clear environment variables
    old_env = {}
    for var in env_vars_to_clear:
        if var in os.environ:
            old_env[var] = os.environ[var]
            del os.environ[var]

    try:
        config = ImageAIConfig()

        assert config.model_path == Path("./models/landsat4sense_unet/not_available")
        assert config.model_version == "not-available-phase1"
        assert config.image_ai_enabled == False
        assert config.dataset_path == Path("./datasets/landsat4sense")
    finally:
        # Restore environment variables
        for var, value in old_env.items():
            os.environ[var] = value


def test_config_from_environment():
    """Test that configuration reads from environment variables."""
    test_model_path = "/custom/model/path"
    test_model_version = "custom-v2.0"
    test_enabled = "true"
    test_dataset_path = "/custom/dataset/path"

    with patch.dict(os.environ, {
        "JARVIS_IMAGE_MODEL_PATH": test_model_path,
        "JARVIS_IMAGE_MODEL_VERSION": test_model_version,
        "JARVIS_IMAGE_AI_ENABLED": test_enabled,
        "JARVIS_LANDSLIDE4SENSE_DATASET_PATH": test_dataset_path
    }):
        config = ImageAIConfig()

        assert config.model_path == Path(test_model_path)
        assert config.model_version == test_model_version
        assert config.image_ai_enabled == True
        assert config.dataset_path == Path(test_dataset_path)


def test_config_boolean_parsing():
    """Test that boolean configuration values are parsed correctly."""
    test_cases = [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("", False),  # Empty string defaults to False
    ]

    for value, expected in test_cases:
        with patch.dict(os.environ, {"JARVIS_IMAGE_AI_ENABLED": value}):
            config = ImageAIConfig()
            assert config.image_ai_enabled == expected, \
                f"Failed for value '{value}': expected {expected}, got {config.image_ai_enabled}"


def test_get_image_ai_config():
    """Test getting the global configuration instance."""
    config1 = get_image_ai_config()
    config2 = get_image_ai_config()

    # Should return the same instance (singleton pattern)
    assert config1 is config2
    assert isinstance(config1, ImageAIConfig)


def test_config_methods():
    """Test configuration accessor methods."""
    with patch.dict(os.environ, {
        "JARVIS_IMAGE_MODEL_PATH": "/test/model/path",
        "JARVIS_IMAGE_MODEL_VERSION": "test-1.0",
        "JARVIS_IMAGE_AI_ENABLED": "true",
        "JARVIS_LANDSLIDE4SENSE_DATASET_PATH": "/test/dataset/path"
    }):
        config = ImageAIConfig()

        assert config.get_model_path() == Path("/test/model/path")
        assert config.get_model_version() == "test-1.0"
        assert config.is_image_ai_enabled() == True
        assert config.get_dataset_path() == Path("/test/dataset/path")


def test_config_is_configured_correctly():
    """Test the configuration validation method."""
    config = ImageAIConfig()
    # This should return True for basic validation
    assert config.is_configured_correctly() == True


def test_config_str_representation():
    """Test string representation of configuration."""
    config = ImageAIConfig()
    config_str = str(config)

    assert "ImageAIConfig" in config_str
    assert "model_path" in config_str
    assert "model_version" in config_str
    assert "image_ai_enabled" in config_str
    assert "dataset_path" in config_str


def run_all_tests():
    """Run all tests in this module."""
    test_functions = [
        test_config_initialization,
        test_config_from_environment,
        test_config_boolean_parsing,
        test_get_image_ai_config,
        test_config_methods,
        test_config_is_configured_correctly,
        test_config_str_representation
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1

    print(f"\nConfiguration Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)