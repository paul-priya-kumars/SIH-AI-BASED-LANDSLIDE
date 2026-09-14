"""
Tests for Landslide4Sense inference infrastructure.

Tests only the infrastructure interfaces, not actual inference logic
since no trained model exists in Phase 1.
"""

import numpy as np
from pathlib import Path
from unittest.mock import patch

from phase6.image_analysis.inference.engine import (
    Landslide4SenseInferenceEngine,
    Landslide4SenseInferenceError
)
from phase6.image_analysis.models.loader import ImageModelNotAvailableError
from phase6.image_analysis.preprocessing.landsat4sense import Landslide4SensePreprocessor
from phase6.image_analysis.models.loader import Landslide4SenseModelLoader


def test_inference_engine_initialization():
    """Test that the inference engine initializes correctly."""
    engine = Landslide4SenseInferenceEngine()
    assert isinstance(engine.preprocessor, Landslide4SensePreprocessor)
    assert isinstance(engine.model_loader, Landslide4SenseModelLoader)


def test_inference_engine_custom_components():
    """Test inference engine initialization with custom components."""
    preprocessor = Landslide4SensePreprocessor()
    model_loader = Landslide4SenseModelLoader()

    engine = Landslide4SenseInferenceEngine(
        preprocessor=preprocessor,
        model_loader=model_loader
    )
    assert engine.preprocessor == preprocessor
    assert engine.model_loader == model_loader


def test_is_ready_false_when_model_not_available():
    """Test that is_ready returns False when model is not available."""
    engine = Landslide4SenseInferenceEngine()
    # By default, the model loader points to a non-existent model
    assert engine.is_ready() == False


def test_is_ready_true_when_model_available():
    """Test that is_ready returns True when model is available."""
    engine = Landslide4SenseInferenceEngine()

    # Mock the model loader to simulate availability
    with patch.object(engine.model_loader, 'is_model_available', return_value=True):
        assert engine.is_ready() == True


def test_run_inference_raises_error_when_model_not_available():
    """Test that run_inference raises ImageModelNotAvailableError when model not available."""
    engine = Landslide4SenseInferenceEngine()

    try:
        engine.run_inference(Path("/fake/sample.tif"))
        assert False, "Should have raised ImageModelNotAvailableError"
    except ImageModelNotAvailableError as e:
        assert "IMAGE MODEL NOT AVAILABLE" in str(e)


def test_run_inference_raises_error_on_inference_failure():
    """Test that run_inference raises Landslide4SenseInferenceError on failure."""
    engine = Landslide4SenseInferenceEngine()

    # Mock the model loader to simulate availability
    with patch.object(engine.model_loader, 'is_model_available', return_value=True):
        # Mock the preprocessor to raise an error during preprocessing
        with patch.object(engine.preprocessor, 'preprocess_sample',
                         side_effect=Exception("Preprocessing failed")):

            try:
                engine.run_inference(Path("/fake/sample.tif"))
                assert False, "Should have raised Landslide4SenseInferenceError"
            except Landslide4SenseInferenceError as e:
                assert "Inference failed" in str(e)


def test_get_engine_status():
    """Test getting engine status."""
    engine = Landslide4SenseInferenceEngine()
    status = engine.get_engine_status()

    assert isinstance(status, dict)
    assert "engine_ready" in status
    assert "preprocessor_configured" in status
    assert "model_loader_info" in status
    assert "can_run_inference" in status

    assert status["preprocessor_configured"] == True
    assert status["can_run_inference"] == status["engine_ready"]


def test_engine_ready_reflects_model_availability():
    """Test that engine_ready correctly reflects model availability."""
    engine = Landslide4SenseInferenceEngine()

    # When model is not available
    with patch.object(engine.model_loader, 'is_model_available', return_value=False):
        assert engine.get_engine_status()["engine_ready"] == False
        assert engine.get_engine_status()["can_run_inference"] == False

    # When model is available
    with patch.object(engine.model_loader, 'is_model_available', return_value=True):
        assert engine.get_engine_status()["engine_ready"] == True
        assert engine.get_engine_status()["can_run_inference"] == True


def test_inference_error_inheritance():
    """Test that Landslide4SenseInferenceError is a proper exception."""
    assert issubclass(Landslide4SenseInferenceError, Exception)

    try:
        raise Landslide4SenseInferenceError("Test error")
    except Landslide4SenseInferenceError as e:
        assert str(e) == "Test error"


def test_inference_engine_repr():
    """Test string representation (basic check)."""
    engine = Landslide4SenseInferenceEngine()
    repr_str = repr(engine)
    assert "Landslide4SenseInferenceEngine" in repr_str


def run_all_tests():
    """Run all tests in this module."""
    test_functions = [
        test_inference_engine_initialization,
        test_inference_engine_custom_components,
        test_is_ready_false_when_model_not_available,
        test_is_ready_true_when_model_available,
        test_run_inference_raises_error_when_model_not_available,
        test_run_inference_raises_error_on_inference_failure,
        test_get_engine_status,
        test_engine_ready_reflects_model_availability,
        test_inference_error_inheritance,
        test_inference_engine_repr
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

    print(f"\nInference Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)