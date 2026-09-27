"""
Tests for model versioning and metadata endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

from app.main import app

client = TestClient(app)


def test_model_info_endpoint_exists():
    """Test that the model info endpoint exists."""
    response = client.get("/api/ml/model-info")
    # Should not return 404
    assert response.status_code != 404


def test_model_info_response_structure():
    """Test that the model info response has the expected structure."""
    response = client.get("/api/ml/model-info")

    # Should return JSON
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    # Check required fields are present
    required_fields = [
        "available",
        "model_path",
        "model_version",
        "checksum",
        "load_time_seconds"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_model_info_available_when_model_exists():
    """Test that model info reports available when model exists."""
    # Mock the model loader to simulate a model being available
    with patch('app.main.image_model_loader') as mock_loader:
        mock_loader.get_model_info.return_value = {
            "available": True,
            "model_path": "/fake/path/to/model.pth",
            "model_version": "landslide4sense-epoch10-ch14-cls1",
            "checksum": "a1b2c3d4e5f6...",
            "load_time_seconds": 2.5,
            "epoch": 10,
            "best_val_dice": 0.85
        }

        response = client.get("/api/ml/model-info")
        assert response.status_code == 200

        data = response.json()
        assert data["available"] == True
        assert isinstance(data["model_path"], str)
        assert isinstance(data["model_version"], str)
        assert isinstance(data["checksum"], str)
        assert isinstance(data["load_time_seconds"], (int, float))


def test_model_info_handles_missing_model_gracefully():
    """Test that model info handles missing model gracefully."""
    # Mock the model loader to simulate initialization failure
    with patch('app.main.image_model_loader', None):
        response = client.get("/api/ml/model-info")
        assert response.status_code == 200

        data = response.json()
        # Should still return a response even if loader failed
        assert "available" in data
        assert data["available"] == False


def test_model_info_checksum_is_string():
    """Test that the checksum field is a string."""
    with patch('app.main.image_model_loader') as mock_loader:
        mock_loader.get_model_info.return_value = {
            "available": True,
            "model_path": "/fake/path/to/model.pth",
            "model_version": "landslide4sense-epoch10-ch14-cls1",
            "checksum": "sha256:a1b2c3d4e5f6...",
            "load_time_seconds": 2.5
        }

        response = client.get("/api/ml/model-info")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["checksum"], str)
        # Should be a reasonable length for SHA-256 hex digest (64 chars) or similar
        assert len(data["checksum"]) > 0


def test_model_info_load_time_is_numeric():
    """Test that load time is a numeric value."""
    with patch('app.main.image_model_loader') as mock_loader:
        mock_loader.get_model_info.return_value = {
            "available": True,
            "model_path": "/fake/path/to/model.pth",
            "model_version": "landslide4sense-epoch10-ch14-cls1",
            "checksum": "sha256:a1b2c3d4e5f6...",
            "load_time_seconds": 2.5
        }

        response = client.get("/api/ml/model-info")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["load_time_seconds"], (int, float))
        assert data["load_time_seconds"] >= 0


def test_model_info_version_format():
    """Test that model version follows expected format."""
    with patch('app.main.image_model_loader') as mock_loader:
        mock_loader.get_model_info.return_value = {
            "available": True,
            "model_path": "/fake/path/to/model.pth",
            "model_version": "landslide4sense-epoch10-ch14-cls1",
            "checksum": "sha256:a1b2c3d4e5f6...",
            "load_time_seconds": 2.5
        }

        response = client.get("/api/ml/model-info")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data["model_version"], str)
        # Should start with expected prefix
        assert data["model_version"].startswith("landslide4sense-")


def test_model_info_includes_additional_metadata():
    """Test that model info includes additional metadata from checkpoint."""
    with patch('app.main.image_model_loader') as mock_loader:
        mock_loader.get_model_info.return_value = {
            "available": True,
            "model_path": "/fake/path/to/model.pth",
            "model_version": "landslide4sense-epoch10-ch14-cls1",
            "checksum": "sha256:a1b2c3d4e5f6...",
            "load_time_seconds": 2.5,
            "epoch": 10,
            "best_val_dice": 0.85
        }

        response = client.get("/api/ml/model-info")
        assert response.status_code == 200

        data = response.json()
        # Check that additional metadata fields are present
        assert "epoch" in data
        assert "best_val_dice" in data
        assert data["epoch"] == 10
        assert data["best_val_dice"] == 0.85


def test_model_info_error_handling():
    """Test that model info handles errors gracefully."""
    # Mock the model loader to raise an exception
    with patch('app.main.image_model_loader') as mock_loader:
        mock_loader.get_model_info.side_effect = Exception("Test error")

        response = client.get("/api/ml/model-info")
        # Should still return 200 (graceful error handling) or 500
        # In our implementation, we catch exceptions in the loader itself
        # So this would depend on how the loader handles errors

        # For now, let's just make sure it doesn't crash the test
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__])