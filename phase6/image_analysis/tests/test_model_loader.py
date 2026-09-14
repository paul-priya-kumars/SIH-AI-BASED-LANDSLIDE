"""
Tests for Landslide4Sense model loading infrastructure.

Tests only the infrastructure interfaces, not actual model loading
since no trained model exists in Phase 1.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase6.image_analysis.models.loader import (
    Landslide4SenseModelLoader,
    ImageModelNotAvailableError,
    get_default_model_loader
)


def test_model_loader_initialization():
    """Test that the model loader initializes correctly."""
    loader = Landslide4SenseModelLoader()
    assert loader.model_path is None
    assert loader.model_version == "unknown"
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
    assert loader.model_version == "not-available-phase1"
    assert loader.cache_model == False


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
            assert loader.is_model_available() == True


def test_load_model_raises_error_when_not_available():
    """Test that load_model raises ImageModelNotAvailableError when model not available."""
    loader = Landslide4SenseModelLoader(model_path=Path("/non/existent/model.pth"))

    try:
        loader.load_model()
        assert False, "Should have raised ImageModelNotAvailableError"
    except ImageModelNotAvailableError as e:
        assert "IMAGE MODEL NOT AVAILABLE" in str(e)


def test_load_model_caching():
    """Test that model caching works correctly."""
    loader = Landslide4SenseModelLoader(cache_model=True)

    # Mock the model loading to avoid actually loading a model
    mock_object = object()  # Simple object to represent a model

    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'is_file', return_value=True):
            # Mock the actual loading mechanism
            with patch.object(loader, 'load_model', return_value=mock_object) as mock_load:
                # First call
                model1 = loader.load_model()
                assert model1 == mock_object
                assert loader._cached_model == mock_object
                assert loader._model_loaded == True
                assert mock_load.call_count == 1

                # Second call should use cache
                model2 = loader.load_model()
                assert model2 == mock_object
                assert loader._cached_model == mock_object
                assert mock_load.call_count == 1  # Still only called once


def test_load_model_no_caching():
    """Test that model loading works without caching."""
    loader = Landslide4SenseModelLoader(cache_model=False)

    mock_object = object()  # Simple object to represent a model

    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'is_file', return_value=True):
            # Mock the actual loading mechanism
            with patch.object(loader, 'load_model', return_value=mock_object) as mock_load:
                # First call
                model1 = loader.load_model()
                assert model1 == mock_object
                assert loader._cached_model is None  # Not cached
                assert loader._model_loaded == True
                assert mock_load.call_count == 1

                # Second call should call load_model again
                model2 = loader.load_model()
                assert model2 == mock_object
                assert mock_load.call_count == 2


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
    assert "model_cached" in info
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
    assert loader.cache_model == False
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
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1

    print(f"\nModel Loader Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)