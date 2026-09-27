"""
Tests for Landslide4Sense model loading infrastructure.

Tests only the infrastructure interfaces, not actual model loading
since no trained model exists in Phase 1.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent  # land 2 directory
sys.path.insert(0, str(project_root))

from phase6.image_analysis.models.loader import (
    Landslide4SenseModelLoader,
    ImageModelNotAvailableError,
    get_default_model_loader
)
from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor


def test_model_loader_initialization():
    """Test that the model loader initializes correctly."""
    # Mock config to return known values
    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.get_model_path.return_value = Path("/default/model/path")
        mock_config.return_value.get_model_version.return_value = "default-version"
        mock_config.return_value.is_image_ai_enabled.return_value = False

        loader = Landslide4SenseModelLoader()
        assert loader.model_path == Path("/default/model/path")
        assert loader.model_version == "default-version"
        assert loader.cache_model == True
        assert loader._cached_model is None
        assert loader._model_loaded == False


def test_model_loader_custom_params():
    """Test model loader initialization with custom parameters."""
    model_path = Path("./test_model.pth")
    loader = Landslide4SenseModelLoader(
        model_path=model_path,
        model_version="test-v1.0",
        cache_model=False
    )
    assert loader.model_path == model_path
    assert loader.model_version == "test-v1.0"
    assert loader.cache_model == False


def test_get_default_model_loader():
    """Test getting the default model loader."""
    loader = get_default_model_loader()
    assert isinstance(loader, Landslide4SenseModelLoader)
    # Should use config defaults
    assert loader.model_version == "not-available-phase1"
    assert loader.cache_model == True  # Default value


def test_is_model_available_false_when_none():
    """Test that is_model_available returns False when path is None."""
    loader = Landslide4SenseModelLoader(model_path=None)
    assert loader.is_model_available() == False


def test_is_model_available_false_when_path_not_exists():
    """Test that is_model_available returns False when path doesn't exist."""
    loader = Landslide4SenseModelLoader(model_path=Path("/non/existent/model.pth"))
    assert loader.is_model_available() == False


def test_is_model_available_true_when_file_exists():
    """Test that is_model_available returns True when file exists."""
    # We won't actually create a file, but we can mock the existence check
    loader = Landslide4SenseModelLoader(model_path=Path("/fake/existing/model.pth"))

    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'is_file', return_value=True):
            # Also need to mock config to return that AI is enabled
            with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
                mock_config.return_value.is_image_ai_enabled.return_value = True
                result = loader.is_model_available()
                assert result == True


def test_load_model_raises_error_when_not_available():
    """Test that load_model raises ImageModelNotAvailableError when model not available."""
    loader = Landslide4SenseModelLoader(model_path=Path("/non/existent/model.pth"))

    # Mock config to enable AI but make model unavailable
    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = True
        with patch.object(Path, 'exists', return_value=False):
            try:
                loader.load_model()
                assert False, "Should have raised ImageModelNotAvailableError"
            except ImageModelNotAvailableError as e:
                assert "IMAGE MODEL NOT AVAILABLE" in str(e)
            except Exception as e:
                # Re-raise any other exceptions to see what they are
                raise


def test_load_model_raises_error_when_disabled():
    """Test that load_model raises error when AI is disabled."""
    loader = Landslide4SenseModelLoader()

    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = False

        try:
            loader.load_model()
            assert False, "Should have raised ImageModelNotAvailableError"
        except ImageModelNotAvailableError as e:
            assert "Image AI is disabled" in str(e)
        except Exception as e:
            # Re-raise any other exceptions to see what they are
            raise


def test_load_model_caching():
    """Test that model caching logic works correctly."""
    loader = Landslide4SenseModelLoader(cache_model=True, model_path=Path("/fake/model.pth"))

    # Test that when no model is cached, loading fails (Phase 1 behavior)
    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = True
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'is_file', return_value=True):
                try:
                    loader.load_model()
                    assert False, "Should have raised ImageModelNotAvailableError"
                except ImageModelNotAvailableError:
                    pass  # Expected in Phase 1

    # Test that cached model is returned when available (simulating Phase 2)
    mock_object = object()  # Simulate a loaded model
    loader._cached_model = mock_object
    loader._model_loaded = True

    # Should return cached model when AI enabled and file exists
    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = True
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'is_file', return_value=True):
                result = loader.load_model()
                assert result == mock_object


def test_load_model_no_caching():
    """Test that model loading works without caching."""
    loader = Landslide4SenseModelLoader(cache_model=False, model_path=Path("/fake/model.pth"))

    # Test that loading fails when no model available (Phase 1 behavior)
    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = True
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'is_file', return_value=True):
                try:
                    loader.load_model()
                    assert False, "Should have raised ImageModelNotAvailableError"
                except ImageModelNotAvailableError:
                    pass  # Expected in Phase 1

    # Test that when cache_model=False, we don't use cached model even if set
    mock_object = object()  # Simulate a loaded model
    loader._cached_model = mock_object
    loader._model_loaded = True

    # Even with cached model set, should still try to load (and fail in Phase 1)
    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = True
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'is_file', return_value=True):
                try:
                    loader.load_model()
                    assert False, "Should have raised ImageModelNotAvailableError"
                except ImageModelNotAvailableError:
                    pass  # Expected in Phase 1 - should not use cached model


def test_get_model_info():
    """Test getting model information."""
    loader = Landslide4SenseModelLoader(
        model_path=Path("./test_model.pth"),
        model_version="test-v1.0"
    )

    info = loader.get_model_info()
    assert isinstance(info, dict)
    assert "model_available" in info
    assert "model_path" in info
    assert "model_version" in info
    assert "image_ai_enabled" in info
    assert "cached_model" in info
    assert "model_loaded" in info

    assert info["model_version"] == "test-v1.0"
    assert info["model_path"] == str(Path("./test_model.pth"))


def test_clear_cache():
    """Test clearing the model cache."""
    loader = Landslide4SenseModelLoader(cache_model=True)

    # Set up a cached model
    loader._cached_model = object()
    loader._model_loaded = True

    # Clear cache
    loader.clear_cache()

    assert loader._cached_model is None
    assert loader._model_loaded == False


def test_get_default_model_loader_properties():
    """Test properties of the default model loader."""
    loader = get_default_model_loader()

    # Should point to non-existent model to clearly indicate unavailability
    assert "not_available" in str(loader.model_path)
    assert loader.model_version == "not-available-phase1"
    assert loader.cache_model == True  # Default value from constructor
    assert loader.is_model_available() == False


def test_model_loader_repr():
    """Test string representation (basic check)."""
    loader = Landslide4SenseModelLoader()
    repr_str = repr(loader)
    assert "Landslide4SenseModelLoader" in repr_str


def run_all_tests():
    """Run all tests in this module."""
    test_functions = [
        test_model_loader_initialization,
        test_model_loader_custom_params,
        test_get_default_model_loader,
        test_is_model_available_false_when_none,
        test_is_model_available_false_when_path_not_exists,
        test_is_model_available_true_when_file_exists,
        test_load_model_raises_error_when_not_available,
        test_load_model_raises_error_when_disabled,
        test_load_model_caching,
        test_load_model_no_caching,
        test_get_model_info,
        test_clear_cache,
        test_get_default_model_loader_properties,
        test_model_loader_repr
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print("PASS: " + test_func.__name__)
            passed += 1
        except Exception as e:
            print("FAIL: " + test_func.__name__ + ": " + str(type(e).__name__) + ": " + str(e))
            failed += 1

    print("\nModel Loader Tests: " + str(passed) + " passed, " + str(failed) + " failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)