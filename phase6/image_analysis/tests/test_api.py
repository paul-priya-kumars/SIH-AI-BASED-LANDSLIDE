"""
Tests for Landslide4Sense image AI API skeleton.

Tests the API interface that clearly indicates model unavailability in Phase 1.
import numpy as np
"""

import sys
import os
import importlib
from pathlib import Path
from unittest.mock import patch

# Add the project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent  # land 2 directory (tests -> image_analysis -> phase6 -> land 2)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _reload_api():
    """Reload the API and config modules to pick up environment changes."""
    import phase6.image_analysis.config as config_module
    # Reset the config singleton
    config_module._config_instance = None
    importlib.reload(config_module)

    import phase6.image_analysis.api as api_module
    importlib.reload(api_module)
    return api_module


def test_predict_image_health_disabled_by_default():
    """Test that the image AI health check shows disabled by default."""
    # Ensure image AI is disabled by checking environment
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        api = _reload_api()
        health = api.predict_image_health()

        assert isinstance(health, dict)
        assert health["service"] == "JARVIS Landslide4Sense Image AI"
        assert health["status"] == "disabled"
        assert health["model_available"] == False
        assert "note" in health
        assert "Phase 3 infrastructure" in health["note"]

def test_predict_image_health_when_enabled_but_no_model():
    """Test health check when AI is enabled but no model is available."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/non/existent/model.pth'
    }):
        api = _reload_api()
        health = api.predict_image_health()
        print(f"DEBUG health: {health}")

        assert health["status"] == "enabled"  # Service is online
        assert health["model_available"] == False  # But no model
        assert health["model_version"] == "not-available-phase1"


def test_predict_image_sample_disabled():
    """Test image prediction when AI is disabled."""
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        api = _reload_api()
        result = api.predict_image_sample({"dummy": "data"})

        assert result["success"] == False
        assert result["error"] == "Image AI is disabled via configuration"
        assert result["error_code"] == "IMAGE_AI_DISABLED"
        assert result["model_available"] == False
        assert result["model_version"] == "not-available-phase1"


def test_predict_image_sample_model_not_available():
    """Test image prediction when model is not available."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/non/existent/model.pth'
    }):
        api = _reload_api()
        result = api.predict_image_sample({"dummy": "data"})
        print(f"DEBUG result: {result}")

        assert result["success"] == False
        assert "IMAGE MODEL NOT AVAILABLE" in result["error"]
        assert result["error_code"] == "MODEL_NOT_AVAILABLE"
        assert result["model_available"] == False
        assert "model_path" in result
        assert result["model_version"] == "not-available-phase1"


def test_predict_image_sample_not_implemented():
    """Test that predict_image_sample works correctly when model is available and AI is enabled."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'true',
        'JARVIS_IMAGE_MODEL_PATH': '/fake/existing/model.pth'
    }):
        api = _reload_api()
        # Mock the model loader to report model as available
        with patch('phase6.image_analysis.models.loader.Landslide4SenseModelLoader.is_model_available', return_value=True):
            # Mock os.path.exists to return True for our fake path
            with patch('os.path.exists', return_value=True):
                # Mock Path.exists to return True for our fake path
                with patch('pathlib.Path.exists', return_value=True):
                    import numpy as np
                    from unittest.mock import MagicMock
                    # Mock the preprocessor instance's load_sample and preprocess_sample methods
                    api._preprocessor.load_sample = MagicMock(return_value=np.random.rand(128, 128, 14).astype(np.float32))
                    api._preprocessor.preprocess_sample = MagicMock(return_value=np.random.rand(14, 128, 128).astype(np.float32))
                    # Mock the inference engine instance's run_inference method to return a successful result
                    api._inference_engine.run_inference = MagicMock(return_value={
                        "success": True,
                        "image_level_probability": 0.7,
                        "pixel_probabilities": [0.7] * (128*128),
                        "processing_time_ms": 100
                    })

                    result = api.predict_image_sample({
                        "image_data": "/fake/path/to/image.tif",
                        "metadata": {
                            "timestamp": "2026-09-15T10:00:00Z",
                            "location": {"latitude": 45.0, "longitude": -120.0},
                            "processing_level": "L2A"
                        }
                    })

                    assert result["success"] == True
                    assert result["landsat_probability"] == 0.7
                    assert result["risk_level"] == "HIGH"  # Since 0.7 >= 0.55
                    assert result["confidence"] == 0.91  # Default confidence
                    assert "factors" in result
                    assert "metadata" in result

def test_get_model_info():
    """Test getting model information."""
    with patch.dict('os.environ', {
        'JARVIS_IMAGE_AI_ENABLED': 'false',
        'JARVIS_IMAGE_MODEL_PATH': '/test/model/path',
        'JARVIS_IMAGE_MODEL_VERSION': 'test-v1.0',
        'JARVIS_LANDSLIDE4SENSE_DATASET_PATH': '/test/dataset'
    }):
        api = _reload_api()
        info = api.get_model_info()
        print(f"DEBUG info: {info}")

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
        api = _reload_api()
        health = api.predict_image_health()
        sample_result = api.predict_image_sample({})
        model_info = api.get_model_info()

        assert isinstance(health, dict)
        assert isinstance(sample_result, dict)
        assert isinstance(model_info, dict)


def test_api_error_consistency():
    """Test that error responses follow a consistent format."""
    with patch.dict('os.environ', {'JARVIS_IMAGE_AI_ENABLED': 'false'}):
        api = _reload_api()
        result = api.predict_image_sample({"test": "data"})

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
            print("[PASS] " + test_func.__name__)
            passed += 1
        except Exception as e:
            print("[FAIL] " + test_func.__name__ + ": " + str(e))
            failed += 1

    print(f"\nAPI Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)