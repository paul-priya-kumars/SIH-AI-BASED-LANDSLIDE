import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "database" in data
    assert "environmental_m1_model" in data
    assert "satellite_m3_model" in data
    assert "environment_service" in data
    assert "cache" in data

def test_metrics_endpoint_enabled():
    # Temporarily enable metrics
    original_enable = settings.ENABLE_METRICS
    settings.ENABLE_METRICS = True
    try:
        response = client.get("/api/metrics")
        assert response.status_code == 200
        # Check that content-type is text/plain (Prometheus may return different versions)
        assert response.headers["content-type"].startswith("text/plain")
        # Check that some metrics are present
        text = response.text
        assert "http_requests_total" in text
        assert "http_request_duration_seconds" in text
    finally:
        settings.ENABLE_METRICS = original_enable

def test_metrics_endpoint_disabled():
    original_enable = settings.ENABLE_METRICS
    settings.ENABLE_METRICS = False
    try:
        response = client.get("/api/metrics")
        assert response.status_code == 404
        assert response.text == "Metrics disabled"
    finally:
        settings.ENABLE_METRICS = original_enable

def test_request_logging_middleware_adds_request_id():
    # We can't easily test the logging output without capturing logs, but we can check that the middleware doesn't break.
    response = client.get("/api/health")
    assert response.status_code == 200
    # The middleware should have added a request_id to the request state, but we can't access it from outside.
    # We'll just ensure the request succeeds.

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data

# Test that existing endpoints still work
def test_risk_endpoint():
    response = client.get("/api/risk?latitude=11.4102&longitude=76.6950")
    assert response.status_code == 200
    data = response.json()
    assert "latitude" in data
    assert "longitude" in data
    assert "risk_probability" in data

def test_environment_endpoint():
    response = client.get("/api/environment?latitude=11.4102&longitude=76.6950")
    assert response.status_code == 200
    data = response.json()
    assert "latitude" in data
    assert "longitude" in data
    assert "rainfall" in data

def test_risk_zones_endpoint():
    response = client.get("/api/risk-zones")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "zone_id" in data[0]
        assert "name" in data[0]

def test_alerts_endpoint():
    response = client.get("/api/alerts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "alert_id" in data[0]
        assert "title" in data[0]

def test_reports_endpoint():
    response = client.get("/api/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_route_risk_endpoint():
    response = client.get("/api/route-risk?start=Coonoor&destination=Ooty")
    assert response.status_code == 200
    data = response.json()
    assert "start_location" in data
    assert "destination" in data

def test_ml_predict_endpoint():
    # We'll send a dummy payload with required latitude and longitude
    payload = {
        "latitude": 11.4102,
        "longitude": 76.6950,
        "features": {
            "rainfall": 100.0,
            "slope": 25.0,
            "elevation": 2240.0,
            "ndvi": 0.43
        }
    }
    response = client.post("/api/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_probability" in data
    assert "risk_level" in data
    assert "confidence" in data
    assert "factors" in data
    assert "model_version" in data

def test_health_reports_m1_and_m3_independently():
    """M1 (environmental) and M3 (satellite) must report their own artifact paths."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    for key in ("environmental_m1", "satellite_m3"):
        assert key in data, f"missing {key} in health response"
        entry = data[key]
        assert isinstance(entry, dict), f"{key} must be an object"
        assert set(entry) >= {"status", "path", "available"}
        assert isinstance(entry["status"], str)
        assert entry["path"], f"{key} must report a concrete artifact path"
        assert isinstance(entry["available"], bool)
        # `available` must agree with the reported status (no fabricated availability)
        if entry["available"]:
            assert entry["status"] in ("loaded", "mock")
        else:
            assert entry["status"] in ("not_found", "error")

    # The two models must not share the same artifact path.
    assert data["environmental_m1"]["path"] != data["satellite_m3"]["path"]
    assert data["environmental_m1"]["path"].replace("\\", "/").endswith(
        "phase3/model_training/risk_model.joblib"
    )
    if not os.environ.get("JARVIS_IMAGE_MODEL_PATH"):
        assert data["satellite_m3"]["path"].replace("\\", "/").endswith(
            "phase6/image_analysis/checkpoints/best_model.pth"
        )

    # Legacy flat keys remain consistent with the nested objects.
    assert data["environmental_m1_model"] == data["environmental_m1"]["status"]
    assert data["satellite_m3_model"] == data["satellite_m3"]["status"]