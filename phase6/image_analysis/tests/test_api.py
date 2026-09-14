"""
Tests for Landslide4Sense image AI API skeleton.

Tests the API interface that clearly indicates model unavailability in Phase 1.
"""

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


def test_predict_image_sample_not_implemented():
    """Test image prediction when infrastructure is not implemented."""
    # To test this, we need to mock the model as available
    # but since we're in Phase 1, we expect the not implemented response
    # when everything else is working

    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/fake/existing/model.pth'
    }):
        # Mock the inference engine to simulate model being available
        # but then return not implemented for the actual prediction
        with patch('phase6.image_analysis.api.Landslide4SenseInferenceEngine') as mock_engine_class:
            mock_engine = mock_engine_class.return_value
            mock_engine.is_ready.return_value = True  # Model available

            result = predict_image_sample({"dummy": "data"})

            assert result["success"] == False
            assert result["error"] == "Image inference not implemented in Phase 1"
            assert result["error_code"] == "NOT_IMPLEMENTED_PHASE1"
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
        assert info["model_path"] == "/test/model/path"
        assert info["model_version"] == "test-v1.0"
        assert info["image_ai_enabled"] == False
        assert info["dataset_path"] == "/test/dataset"
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
        test_predict_image_sample_not_implemented,
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