"""
Unit tests for the batch risk prediction API.
"""
import time
from typing import List
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.risk_service import batch_risk_predict, _get_risk_prediction_uncached
from app.cache import get_prediction_cache, initialize_cache, shutdown_cache
from app.schemas.batch import BatchRiskPredictRequest, BatchRiskPredictResponse
from app.schemas.risk import RiskPredictionResponse

# Initialize test client
client = TestClient(app)


def test_batch_valid_single_coordinate():
    """Test valid single-coordinate batch request."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()

        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 1
        pred = data["predictions"][0]
        assert "latitude" in pred
        assert "longitude" in pred
        assert "risk_probability" in pred
        assert "risk_level" in pred
        assert pred["latitude"] == 11.4102
        assert pred["longitude"] == 76.6950

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_valid_multi_coordinate():
    """Test valid multi-coordinate batch request."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()

        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950},
                    {"latitude": 11.3530, "longitude": 76.7959},
                    {"latitude": 11.4010, "longitude": 76.7220}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 3

        # Check that each prediction has required fields
        for i, pred in enumerate(data["predictions"]):
            assert pred["latitude"] == [
                11.4102, 11.3530, 11.4010
            ][i]
            assert pred["longitude"] == [
                76.6950, 76.7959, 76.7220
            ][i]
            assert "risk_probability" in pred
            assert "risk_level" in pred

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_empty_rejected():
    """Test that empty batch is rejected."""
    response = client.post(
        "/api/batch/risk",
        json={
            "coordinates": []
        }
    )

    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data


def test_batch_larger_than_maximum_rejected():
    """Test that batch larger than maximum is rejected."""
    # Set a small maximum for testing
    original_batch_max = settings.BATCH_MAX_SIZE
    settings.BATCH_MAX_SIZE = 2

    try:
        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950},
                    {"latitude": 11.3530, "longitude": 76.7959},
                    {"latitude": 11.4010, "longitude": 76.7220}
                ]
            }
        )

        assert response.status_code == 400  # Bad request
        data = response.json()
        assert "detail" in data
        assert "exceeds maximum allowed size" in data["detail"]

    finally:
        settings.BATCH_MAX_SIZE = original_batch_max


def test_batch_invalid_latitude_rejected():
    """Test that invalid latitude is rejected."""
    response = client.post(
        "/api/batch/risk",
        json={
            "coordinates": [
                {"latitude": 91.0, "longitude": 76.6950}  # Latitude > 90
            ]
        }
    )

    assert response.status_code == 422  # Validation error

    response = client.post(
        "/api/batch/risk",
        json={
            "coordinates": [
                {"latitude": -91.0, "longitude": 76.6950}  # Latitude < -90
            ]
        }
    )

    assert response.status_code == 422  # Validation error


def test_batch_invalid_longitude_rejected():
    """Test that invalid longitude is rejected."""
    response = client.post(
        "/api/batch/risk",
        json={
            "coordinates": [
                {"latitude": 11.4102, "longitude": 181.0}  # Longitude > 180
            ]
        }
    )

    assert response.status_code == 422  # Validation error

    response = client.post(
        "/api/batch/risk",
        json={
            "coordinates": [
                {"latitude": 11.4102, "longitude": -181.0}  # Longitude < -180
            ]
        }
    )

    assert response.status_code == 422  # Validation error


def test_batch_duplicate_coordinates_handled_efficiently():
    """Test that duplicate coordinates are handled efficiently (same result objects)."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()

        # Make a request with duplicate coordinates
        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950},
                    {"latitude": 11.4102, "longitude": 76.6950},  # Duplicate
                    {"latitude": 11.3530, "longitude": 76.7959}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 3

        # The first two predictions should be equal (same coordinates)
        pred1 = data["predictions"][0]
        pred2 = data["predictions"][1]
        pred3 = data["predictions"][2]

        assert pred1["latitude"] == pred2["latitude"] == 11.4102
        assert pred1["longitude"] == pred2["longitude"] == 76.6950
        assert pred1["risk_probability"] == pred2["risk_probability"]
        assert pred1["risk_level"] == pred2["risk_level"]

        # Third coordinate should be different
        assert pred3["latitude"] == 11.3530
        assert pred3["longitude"] == 76.7959

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_input_output_ordering_preserved():
    """Test that input/output ordering is preserved."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()

        # Request coordinates in specific order
        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950},  # First
                    {"latitude": 11.3530, "longitude": 76.7959},  # Second
                    {"latitude": 11.4010, "longitude": 76.7220}   # Third
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 3

        # Check that order is preserved
        assert data["predictions"][0]["latitude"] == 11.4102
        assert data["predictions"][0]["longitude"] == 76.6950

        assert data["predictions"][1]["latitude"] == 11.3530
        assert data["predictions"][1]["longitude"] == 76.7959

        assert data["predictions"][2]["latitude"] == 11.4010
        assert data["predictions"][2]["longitude"] == 76.7220

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_service_function_directly():
    """Test the batch_risk_predict service function directly."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()

        # Test with a list of coordinates
        coordinates = [
            {"latitude": 11.4102, "longitude": 76.6950},
            {"latitude": 11.3530, "longitude": 76.7959}
        ]

        # Convert to BatchCoordinate objects (as the function expects)
        from app.schemas.batch import BatchCoordinate
        batch_coords = [BatchCoordinate(**coord) for coord in coordinates]

        predictions = batch_risk_predict(batch_coords)

        assert isinstance(predictions, list)
        assert len(predictions) == 2
        assert all(isinstance(pred, RiskPredictionResponse) for pred in predictions)

        # Check first prediction
        assert predictions[0].latitude == 11.4102
        assert predictions[0].longitude == 76.6950

        # Check second prediction
        assert predictions[1].latitude == 11.3530
        assert predictions[1].longitude == 76.7959

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_cache_hits_reused():
    """Test that cache hits are reused for batch requests."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()
        cache = get_prediction_cache()

        # Pre-populate cache with a known value
        test_lat, test_lon = 11.4102, 76.6950
        lat_key = round(test_lat, 4)
        lon_key = round(test_lon, 4)
        cache_key = f"risk:{lat_key}:{lon_key}"

        # Create a mock prediction to store in cache
        mock_pred = _get_risk_prediction_uncached(test_lat, test_lon)
        cache.set(cache_key, mock_pred)

        # Make batch request that includes the cached coordinate
        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": test_lat, "longitude": test_lon},  # Should hit cache
                    {"latitude": 11.3530, "longitude": 76.7959}     # Should miss cache
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 2

        # Both predictions should be valid
        assert data["predictions"][0]["latitude"] == test_lat
        assert data["predictions"][0]["longitude"] == test_lon
        assert data["predictions"][1]["latitude"] == 11.3530
        assert data["predictions"][1]["longitude"] == 76.7959

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_endpoint_returns_correct_response_schema():
    """Test that batch endpoint returns correct response schema."""
    # Enable cache for testing
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        initialize_cache()

        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950}
                ]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response schema
        assert "predictions" in data
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) == 1

        pred = data["predictions"][0]
        # Check that it conforms to RiskPredictionResponse schema
        assert "latitude" in pred and isinstance(pred["latitude"], float)
        assert "longitude" in pred and isinstance(pred["longitude"], float)
        assert "location_name" in pred and isinstance(pred["location_name"], str)
        assert "risk_probability" in pred and isinstance(pred["risk_probability"], float)
        assert 0.0 <= pred["risk_probability"] <= 1.0
        assert "risk_level" in pred and isinstance(pred["risk_level"], str)
        assert pred["risk_level"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
        assert "confidence" in pred and isinstance(pred["confidence"], float)
        assert 0.0 <= pred["confidence"] <= 1.0
        assert "factors" in pred and isinstance(pred["factors"], list)
        assert "updated_at" in pred
        assert "is_mock" in pred and isinstance(pred["is_mock"], bool)

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        shutdown_cache()


def test_batch_failure_handling():
    """Test that batch handles failures gracefully."""
    # Test with cache enabled but simulate cache failure
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        # Don't initialize cache to simulate cache not being ready
        # This should fall back to uncached computation

        response = client.post(
            "/api/batch/risk",
            json={
                "coordinates": [
                    {"latitude": 11.4102, "longitude": 76.6950}
                ]
            }
        )

        # Should still succeed (fallback to uncached)
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 1

    finally:
        settings.CACHE_ENABLED = original_cache_enabled
        # Only shutdown if we initialized it
        try:
            shutdown_cache()
        except:
            pass  # Ignore if cache wasn't initialized