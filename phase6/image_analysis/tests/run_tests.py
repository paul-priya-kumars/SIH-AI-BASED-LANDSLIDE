"""
Simple test runner for preprocessing tests.
"""

import sys
import traceback
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent  # land 2 directory (tests -> image_analysis -> phase6 -> land 2)
sys.path.insert(0, str(project_root))


def test_preprocessor_initialization():
    """Test that the preprocessor initializes correctly."""
    from phase6.image_analysis.preprocessing import Landslide4SensePreprocessor
    preprocessor = Landslide4SensePreprocessor()
    assert preprocessor.normalize_bands == True
    assert preprocessor.band_means is None
    assert preprocessor.band_stds is None
    assert preprocessor._is_fitted == False
    print("[PASS] test_preprocessor_initialization")


def test_preprocessor_custom_params():
    """Test preprocessor initialization with custom parameters."""
    import numpy as np
    from phase6.image_analysis.preprocessing import Landslide4SensePreprocessor
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
    print("[PASS] test_preprocessor_custom_params")


def test_get_default_preprocessor():
    """Test getting the default preprocessor."""
    from phase6.image_analysis.preprocessing import get_default_preprocessor
    preprocessor = get_default_preprocessor()
    assert isinstance(preprocessor, Landslide4SensePreprocessor)
    assert preprocessor.normalize_bands == True
    print("[PASS] test_get_default_preprocessor")


def run_all_tests():
    """Run all tests in this module."""
    test_functions = [
        test_preprocessor_initialization,
        test_preprocessor_custom_params,
        test_get_default_preprocessor
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            # traceback.print_exc()  # Commented out to avoid unicode issues
            failed += 1

    print(f"\nPreprocessing Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)