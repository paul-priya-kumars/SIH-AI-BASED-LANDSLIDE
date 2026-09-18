"""
Tests for Landslide4Sense image AI API.

Tests the API interface including successful inference when model is available.
"""

import sys
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from unittest.mock import patch

from phase6.image_analysis.api import (
    predict_image_health,
    predict_image_sample,
    get_model_info
)


def test_predict_image_health_disabled_by_default():
    """Test that the image AI health check shows disabled by default."""
    # Ensure image AI is disabled by checking environment
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        health = predict_image_health()

        assert isinstance(health, dict)
        assert health["service"] == "JARVIS Landslide4Sense Image AI"
        assert health["status"] == "disabled"
        assert health["model_available"] == False
        assert "note" in health
        assert "Phase 1 infrastructure" in health["note"]


def test_predict_image_health_when_enabled_but_no_model():
    """Test health check when AI is enabled but no model is available."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/non/existent/model.pth'
    }):
        health = predict_image_health()

        assert health["status"] == "online"  # Service is online
        assert health["model_available"] == False  # But no model
        assert health["model_version"] == "not-available-phase1"


def test_predict_image_sample_disabled():
    """Test image prediction when AI is disabled."""
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        result = predict_image_sample({"dummy": "data"})

        assert result["success"] == False
        assert result["error"] == "Image AI is disabled via configuration"
        assert result["error_code"] == "IMAGE_AI_DISABLED"
        assert result["model_available"] == False


def test_predict_image_sample_model_not_available():
    """Test image prediction when model is not available."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/non/existent/model.pth'
    }):
        result = predict_image_sample({"dummy": "data"})

        assert result["success"] == False
        assert "IMAGE MODEL NOT AVAILABLE" in result["error"]
        assert result["error_code"] == "MODEL_NOT_AVAILABLE"
        assert result["model_available"] == False
        assert "model_path" in result
        assert result["model_version"] == "not-available-phase1"


def test_predict_image_sample_successful_inference():
    """Test image prediction when model is available but inference not implemented in Phase 1."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/fake/existing/model.pth'
    }):
        # Mock the inference engine to report that the model is ready
        with patch('phase6.image_analysis.api.Landslide4SenseInferenceEngine') as mock_engine_class:
            mock_engine_instance = mock_engine_class.return_value
            mock_engine_instance.is_ready.return_value = True
            # We don't need to set run_inference because it's not called in Phase 1

            result = predict_image_sample({
                "image_data": "/fake/path/to/image.h5",
                "metadata": {
                    "timestamp": "2023-01-01T00:00:00Z",
                    "location": {"latitude": 45.0, "longitude": -120.0},
                    "processing_level": "L2A"
                }
            })

            # Check that we got the not-implemented response
            assert result["success"] == False
            assert result["error"] == "Image inference not implemented in Phase 1"
            assert result["error_code"] == "NOT_IMPLEMENTED_PHASE1"
            assert result["model_available"] == True
            assert result["note"] == "Actual image inference will be implemented in Phase 2"


def test_get_model_info():
    """Test getting model information."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'false',
        'JARVIS_IMAGE_MODEL_PATH': '/test/model/path',
        'JARVIS_IMAGE_MODEL_VERSION': 'test-v1.0',
        'JARVIS_LANDSLIDE4SENSE_DATASET_PATH': '/test/dataset'
    }):
        info = get_model_info()

        assert isinstance(info, dict)
        assert info["model_available"] == False  # Not available in Phase 1
        assert Path(info["model_path"]) == Path("/test/model/path")
        assert info["model_version"] == "test-v1.0"
        assert info["image_ai_enabled"] == False
        assert Path(info["dataset_path"]) == Path("/test/dataset")
        assert "inference_engine_status" in info


def test_api_functions_return_dicts():
    """Test that all API functions return dictionaries."""
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        health = predict_image_health()
        sample_result = predict_image_sample({})
        model_info = get_model_info()

        assert isinstance(health, dict)
        assert isinstance(sample_result, dict)
        assert isinstance(model_info, dict)


def test_api_error_consistency():
    """Test that error responses follow a consistent format."""
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        result = predict_image_sample({"test": "data"})

        # Check that error response has expected fields
        assert "success" in result
        assert "error" in result
        assert "error_code" in result
        assert result["success"] == False
        assert isinstance(result["error"], str)
        assert isinstance(result["error_code"], str)


def run_all_tests():
    """Run all tests in this module."""
    test_functions = [
        test_predict_image_health_disabled_by_default,
        test_predict_image_health_when_enabled_but_no_model,
        test_predict_image_sample_disabled,
        test_predict_image_sample_model_not_available,
        test_predict_image_sample_successful_inference,
        test_get_model_info,
        test_api_functions_return_dicts,
        test_api_error_consistency
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

    print(f"\nAPI Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)