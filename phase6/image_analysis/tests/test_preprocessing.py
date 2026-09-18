"""
Tests for Landslide4Sense preprocessing infrastructure.

Tests the actual preprocessing implementation including finite value checking.
"""

import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from pathlib import Path

from phase6.image_analysis.preprocessing.landslide4sense import (
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
    print(f"Valid data shape: {valid_data.shape}")
    result = preprocessor.validate_dimensions(valid_data)
    print(f"Validate dimensions result for valid data: {result}")
    assert result == True, f"Expected True for valid data, got {result}"

    # Invalid dimensions
    test_cases = [
        (np.random.rand(64, 64, 14), "(64, 64, 14)"),
        (np.random.rand(128, 128, 7), "(128, 128, 7)"),
        (np.random.rand(128, 128), "(128, 128)"),
        (np.random.rand(128, 128, 14, 1), "(128, 128, 14, 1)")
    ]

    for data, desc in test_cases:
        print(f"Testing invalid dimensions {desc}: shape {data.shape}")
        result = preprocessor.validate_dimensions(data)
        print(f"Validate dimensions result for {desc}: {result}")
        assert result == False, f"Expected False for {desc}, got {result}"


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


def test_preprocess_sample_with_valid_data():
    """Test that preprocess_sample works with valid data."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)  # Disable normalization for simplicity

    # Create valid sample data
    sample_data = np.random.rand(128, 128, 14).astype(np.float32)

    # Process the sample
    processed = preprocessor.preprocess_sample(sample_data)

    # Check output shape and type
    assert processed.shape == (14, 128, 128)  # Channel-first format
    assert processed.dtype == np.float32


def test_preprocess_sample_with_nan_values():
    """Test that preprocess_sample raises ValueError for NaN values."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Create sample data with NaN
    sample_data = np.random.rand(128, 128, 14).astype(np.float32)
    sample_data[0, 0, 0] = np.nan

    # Process the sample - should raise ValueError
    try:
        preprocessor.preprocess_sample(sample_data)
        assert False, "Should have raised ValueError for NaN values"
    except ValueError as e:
        assert "non-finite values" in str(e)


def test_preprocess_sample_with_inf_values():
    """Test that preprocess_sample raises ValueError for Inf values."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Create sample data with Inf
    sample_data = np.random.rand(128, 128, 14).astype(np.float32)
    sample_data[0, 0, 0] = np.inf

    # Process the sample - should raise ValueError
    try:
        preprocessor.preprocess_sample(sample_data)
        assert False, "Should have raised ValueError for Inf values"
    except ValueError as e:
        assert "non-finite values" in str(e)


def test_preprocess_sample_invalid_dimensions():
    """Test that preprocess_sample raises ValueError for invalid dimensions."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Create sample data with invalid dimensions
    sample_data = np.random.rand(64, 64, 14).astype(np.float32)

    # Process the sample - should raise ValueError
    try:
        preprocessor.preprocess_sample(sample_data)
        assert False, "Should have raised ValueError for invalid dimensions"
    except ValueError as e:
        assert "dimensions incorrect" in str(e)


def test_preprocess_sample_invalid_band_count():
    """Test that preprocess_sample raises ValueError for invalid band count."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Create sample data with invalid band count
    sample_data = np.random.rand(128, 128, 7).astype(np.float32)

    # Process the sample - should raise ValueError
    try:
        preprocessor.preprocess_sample(sample_data)
        assert False, "Should have raised ValueError for invalid band count"
    except ValueError as e:
        assert "band count incorrect" in str(e)


def test_preprocess_sample_channel_format_conversion():
    """Test that preprocess_sample correctly handles channel format conversion."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Test with channels-last format (H, W, C)
    sample_data_hwc = np.random.rand(128, 128, 14).astype(np.float32)
    processed_hwc = preprocessor.preprocess_sample(sample_data_hwc)
    assert processed_hwc.shape == (14, 128, 128)  # Should convert to channel-first

    # Test with channels-first format (C, H, W)
    sample_data_chw = np.random.rand(14, 128, 128).astype(np.float32)
    processed_chw = preprocessor.preprocess_sample(sample_data_chw)
    assert processed_chw.shape == (14, 128, 128)  # Should remain channel-first


def test_preprocess_sample_with_normalization():
    """Test that preprocess_sample applies normalization when fitted."""
    preprocessor = Landslide4SensePreprocessor(normalize_bands=True)

    # Create fake training data and fit normalization
    fake_data = np.random.rand(10, 128, 128, 14).astype(np.float32)
    preprocessor.fit_normalization(fake_data)

    # Create sample data
    sample_data = np.random.rand(128, 128, 14).astype(np.float32)

    # Process the sample
    processed = preprocessor.preprocess_sample(sample_data)

    # Check output shape and type
    assert processed.shape == (14, 128, 128)
    assert processed.dtype == np.float32

    # Check that preprocessor is fitted
    assert preprocessor.is_fitted() == True


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
        test_preprocess_sample_with_valid_data,
        test_preprocess_sample_with_nan_values,
        test_preprocess_sample_with_inf_values,
        test_preprocess_sample_invalid_dimensions,
        test_preprocess_sample_invalid_band_count,
        test_preprocess_sample_channel_format_conversion,
        test_preprocess_sample_with_normalization,
        test_preprocessor_repr
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"PASS: {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_func.__name__}: {e}")
            failed += 1

    print(f"\nPreprocessing Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)