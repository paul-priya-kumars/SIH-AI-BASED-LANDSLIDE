"""Tests for the REAL M1 environmental model (Phase 3 artifact)."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.m1_model_service import (
    M1_FEATURE_NAMES,
    M1FeatureUnavailableError,
    build_feature_vector_from_environment,
    m1_model_service,
    resolve_m1_model_path,
)

client = TestClient(app)

SAMPLE = {
    "rainfall_mm": 180,
    "soil_moisture_pct": 85,
    "slope_deg": 32,
    "elevation_m": 650,
    "temperature_c": 23,
    "river_level_m": 5.2,
    "vegetation_index": 0.35,
    "landslide_history": 1,
}


def test_m1_artifact_resolves_to_the_phase3_model():
    path = resolve_m1_model_path().replace("\\", "/")
    assert path.endswith("phase3/model_training/risk_model.joblib")


def test_m1_model_is_genuinely_loadable():
    assert m1_model_service.is_available() is True


def test_m1_describe_reports_real_metadata():
    described = m1_model_service.describe()
    assert described["available"] is True
    assert described["error"] is None
    assert described["feature_order"] == M1_FEATURE_NAMES
    assert len(described["feature_order"]) == 8
    assert set(described["classes"]) == {"HIGH", "LOW", "MEDIUM"}
    assert described["checksum_sha256_16"]


def test_m1_prediction_contract():
    result = m1_model_service.predict(SAMPLE)
    assert result["risk_level"] in {"LOW", "MODERATE", "HIGH", "VERY_HIGH"}
    assert 0.0 <= result["risk_probability"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert abs(sum(result["probabilities"].values()) - 1.0) < 1e-6
    assert result["predicted_class"] in {"HIGH", "LOW", "MEDIUM"}
    assert result["feature_order"] == M1_FEATURE_NAMES
    assert result["artifact_path"].replace("\\", "/").endswith(
        "phase3/model_training/risk_model.joblib"
    )


def test_m1_never_fabricates_missing_features():
    with pytest.raises(M1FeatureUnavailableError):
        m1_model_service.predict({name: None for name in M1_FEATURE_NAMES})


def test_feature_vector_builder_rejects_incomplete_environment():
    class Env:
        rainfall = 1.0
        soil_saturation_pct = None  # deliberately missing
        slope = 1.0
        elevation = 1.0
        temperature = 1.0
        ndvi = 0.5
        river_level_m = 1.0
        landslide_history = 0

    with pytest.raises(M1FeatureUnavailableError):
        build_feature_vector_from_environment(Env())


def test_risk_endpoint_serves_the_real_model():
    response = client.get("/api/risk?latitude=11.4102&longitude=76.6950")
    assert response.status_code == 200
    data = response.json()
    assert data["is_mock"] is False  # real M1 model, not the heuristic mock
    assert 0.0 <= data["risk_probability"] <= 1.0
    assert data["risk_level"] in {"LOW", "MODERATE", "HIGH", "VERY_HIGH"}
    assert 0.0 <= data["confidence"] <= 1.0
