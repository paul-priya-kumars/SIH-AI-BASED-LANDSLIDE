"""
Tests for Landslide4Sense preprocessing infrastructure.

Tests only the infrastructure interfaces, not actual preprocessing logic
since the dataset is not available in Phase 1.
"""

import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from pathlib import Path

from phase6.image_analysis.preprocessing.landsat4sense import (
    Landslide4SensePreprocessor,
    get_default_preprocessor
)


def test_preprocessor_initialization():
    """Test that the preprocessor initializes correctly."""
    preprocessor = Landslide4SensePreprocessor()
    assert preprocessor.normalize_bands == True
    assert preprocessor.band_means is None
    assert preprocessor.band_stds is None
    assert preprocessor._is_fitted == False


def test_preprocessor_custom_params():
    """Test preprocessor initialization with custom parameters."""
    means = np.array([0.5] * 14)
    stds = np.array([0.2] * 14)
    preprocessor = Landslide4SensePreprocessor(
        normalize_bands=True,
        band_means=means,
        band_stds=stds
    )
    assert preprocessor.normalize_bands == True
    assert np.array_equal(preprocessor.band_means, means)
    assert np.array_equal(preprocessor.band_stds, stds)
    assert preprocessor._is_fitted == True


def test_get_default_preprocessor():
    """Test getting the default preprocessor."""
    preprocessor = get_default_preprocessor()
    assert isinstance(preprocessor, Landslide4SensePreprocessor)
    assert preprocessor.normalize_bands == True


def test_validate_dimensions():
    """Test dimension validation."""
    preprocessor = Landslide4SensePreprocessor()

    # Valid dimensions
    valid_data = np.random.rand(128, 128, 14)
    assert preprocessor.validate_dimensions(valid_data) == True

    # Invalid dimensions
    assert preprocessor.validate_dimensions(np.random.rand(64, 64, 14)) == False
    assert preprocessor.validate_dimensions(np.random.rand(128, 128, 7)) == False
    assert preprocessor.validate_dimensions(np.random.rand(128, 128)) == False
    assert preprocessor.validate_dimensions(np.random.rand(128, 128, 14, 1)) == False


def test_validate_band_count():
    """Test band count validation."""
    preprocessor = Landslide4SensePreprocessor()

    # Valid band count
    assert preprocessor.validate_band_count(np.random.rand(128, 128, 14)) == True
    assert preprocessor.validate_band_count(np.random.rand(64, 64, 14)) == True

    # Invalid band count
    assert preprocessor.validate_band_count(np.random.rand(128, 128, 7)) == False
    assert preprocessor.validate_band_count(np.random.rand(128, 128)) == False


def test_convert_to_float32():
    """Test conversion to float32."""
    preprocessor = Landslide4SensePreprocessor()
    data = np.random.rand(128, 128, 14).astype(np.float64)
    converted = preprocessor.convert_to_float32(data)
    assert converted.dtype == np.float32


def test_preprocessor_not_implemented_methods():
    """Test that methods requiring dataset raise NotImplementedError."""
    preprocessor = Landslide4SensePreprocessor()

    # These should raise NotImplementedError since we don't have the dataset
    try:
        preprocessor.load_sample(Path("/fake/path"))
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected

    try:
        preprocessor.load_label(Path("/fake/path"))
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass  # Expected


def test_fit_normalization():
    """Test fitting normalization statistics."""
    preprocessor = Landslide4SensePreprocessor()

    # Create fake training data
    fake_data = np.random.rand(10, 128, 128, 14)

    # Fit normalization
    preprocessor.fit_normalization(fake_data)

    # Check that statistics were computed
    assert preprocessor._is_fitted == True
    assert preprocessor.band_means is not None
    assert preprocessor.band_stds is not None
    assert len(preprocessor.band_means) == 14
    assert len(preprocessor.band_stds) == 14

    # Check that stds don't contain zeros (to avoid division by zero)
    assert not np.any(preprocessor.band_stds == 0)


def test_preprocess_sample_not_implemented():
    """Test that preprocess_sample raises NotImplementedError in Phase 1."""
    preprocessor = Landslide4SensePreprocessor()

    try:
        preprocessor.preprocess_sample(Path("/fake/path"))
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError as e:
        assert "not implemented in Phase 1" in str(e)


def test_preprocessor_repr():
    """Test string representation of preprocessor."""
    preprocessor = Landslide4SensePreprocessor()
    repr_str = repr(preprocessor)
    assert "Landslide4SensePreprocessor" in repr_str
    assert "normalize_bands=True" in repr_str


def run_all_tests():
    """Run all tests in this module."""
    test_functions = [
        test_preprocessor_initialization,
        test_preprocessor_custom_params,
        test_get_default_preprocessor,
        test_validate_dimensions,
        test_validate_band_count,
        test_convert_to_float32,
        test_preprocessor_not_implemented_methods,
        test_fit_normalization,
        test_preprocess_sample_not_implemented,
        test_preprocessor_repr
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

    print(f"\nPreprocessing Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)