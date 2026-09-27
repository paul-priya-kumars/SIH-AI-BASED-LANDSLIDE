"""
Tests for Landslide4Sense inference infrastructure.

Tests only the infrastructure interfaces, not actual inference logic
since no trained model exists in Phase 1.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent  # land 2 directory (tests -> image_analysis -> phase6 -> land 2)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from phase6.image_analysis.inference.engine import (
    Landslide4SenseInferenceEngine,
    Landslide4SenseInferenceError
)
from phase6.image_analysis.models.loader import ImageModelNotAvailableError
from phase6.image_analysis.models.loader import Landslide4SenseModelLoader
from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor


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


def test_is_ready_false_when_ai_disabled():
    """Test that is_ready returns False when AI is disabled."""
    engine = Landslide4SenseInferenceEngine()

    with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
        mock_config.return_value.is_image_ai_enabled.return_value = False
        assert engine.is_ready() == False


def test_is_ready_true_when_model_available():
    """Test that is_ready returns True when model is available."""
    engine = Landslide4SenseInferenceEngine()

    # Mock the model loader to simulate availability
    with patch.object(engine.model_loader, 'is_model_available', return_value=True):
        # Also need to ensure AI is enabled
        with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
            mock_config.return_value.is_image_ai_enabled.return_value = True
            assert engine.is_ready() == True


def test_run_inference_returns_error_when_ai_disabled():
    """Test that run_inference returns error when AI is disabled."""
    engine = Landslide4SenseInferenceEngine()

    # Mock that the input file exists to pass initial validation
    with patch.object(Path, 'exists', return_value=True):
        with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
            mock_config.return_value.is_image_ai_enabled.return_value = False

            result = engine.run_inference(Path("/fake/sample.tif"))

            assert result["success"] == False
            assert result["error_code"] == "IMAGE_AI_DISABLED"
            assert "Image AI is disabled" in result["error"]


def test_run_inference_returns_error_when_model_not_available():
    """Test that run_inference returns error when model not available."""
    engine = Landslide4SenseInferenceEngine()

    # Mock that the input file exists to pass initial validation
    with patch.object(Path, 'exists', return_value=True):
        # Mock that AI is enabled (so we go past the AI disabled check)
        with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
            mock_config.return_value.is_image_ai_enabled.return_value = True
            result = engine.run_inference(Path("/fake/sample.tif"))

            assert result["success"] == False
            assert result["error_code"] == "MODEL_NOT_AVAILABLE"
            assert "IMAGE MODEL NOT AVAILABLE" in result["error"]


def test_run_inference_returns_error_when_not_implemented():
    """Test that run_inference returns sample loading error when file not found."""
    engine = Landslide4SenseInferenceEngine()

    # Mock that the input file exists to pass initial validation
    with patch.object(Path, 'exists', return_value=True):
        # Mock that AI is enabled and model is available (so we get past those checks)
        with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
            mock_config.return_value.is_image_ai_enabled.return_value = True
            with patch.object(engine.model_loader, 'is_model_available', return_value=True):
                # Mock the preprocessor.load_sample to raise FileNotFoundError
                with patch.object(engine.preprocessor, 'load_sample') as mock_load_sample:
                    mock_load_sample.side_effect = FileNotFoundError('Sample file not found: /fake/sample.tif')

                    result = engine.run_inference(Path("/fake/sample.tif"))

                    assert result["success"] == False
                    assert result["error_code"] == "SAMPLE_LOADING_FAILED"
                    assert "Sample file not found" in result["error"]

def test_run_inference_returns_error_on_invalid_path():
    """Test that run_inference handles invalid input paths."""
    engine = Landslide4SenseInferenceEngine()

    # Test with non-existent path
    result = engine.run_inference(Path("/non/existent/file.tif"))

    assert result["success"] == False
    assert result["error_code"] == "INPUT_FILE_NOT_FOUND"
    assert "Input file not found" in result["error"]


def test_get_engine_status():
    """Test getting engine status."""
    engine = Landslide4SenseInferenceEngine()
    status = engine.get_engine_status()

    assert isinstance(status, dict)
    assert "engine_ready" in status
    assert "preprocessor_configured" in status
    assert "preprocessor_fitted" in status
    assert "model_loader_info" in status
    assert "can_run_inference" in status
    assert "image_ai_enabled" in status

    # Preprocessor should always be configured in our implementation
    assert status["preprocessor_configured"] == True
    # Can run inference should equal engine ready
    assert status["can_run_inference"] == status["engine_ready"]


def test_engine_ready_reflects_model_availability():
    """Test that engine_ready correctly reflects model availability."""
    engine = Landslide4SenseInferenceEngine()

    # When model is not available
    with patch.object(engine.model_loader, 'is_model_available', return_value=False):
        with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
            mock_config.return_value.is_image_ai_enabled.return_value = True
            assert engine.get_engine_status()["engine_ready"] == False
            assert engine.get_engine_status()["can_run_inference"] == False

    # When model is available and AI enabled
    with patch.object(engine.model_loader, 'is_model_available', return_value=True):
        with patch('phase6.image_analysis.config.get_image_ai_config') as mock_config:
            mock_config.return_value.is_image_ai_enabled.return_value = True
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
        test_is_ready_false_when_ai_disabled,
        test_is_ready_true_when_model_available,
        test_run_inference_returns_error_when_ai_disabled,
        test_run_inference_returns_error_when_model_not_available,
        test_run_inference_returns_error_when_not_implemented,
        test_run_inference_returns_error_on_invalid_path,
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
            print("[PASS] " + test_func.__name__)
            passed += 1
        except Exception as e:
            print("[FAIL] " + test_func.__name__ + ": " + str(e))
            failed += 1

    print(f"\nInference Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)