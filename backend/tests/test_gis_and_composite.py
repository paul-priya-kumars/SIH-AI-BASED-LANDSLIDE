"""Tests for the M2 GIS provider boundary, composite risk engine and integration API."""
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.composite_risk_service import (
    COMPONENT_WEIGHTS,
    compute_composite_risk,
)
from backend.app.services.gis_provider import (
    RiskZoneSeedGisProvider,
    get_gis_provider,
    set_gis_provider,
)

client = TestClient(app)


def test_gis_provider_is_explicitly_a_demo_adapter():
    provider = get_gis_provider()
    assert provider.is_real is False
    assert "not real GIS" in provider.data_source or "SEED" in provider.data_source


def test_gis_provider_maps_ooty_to_a_zone():
    context = get_gis_provider().find_zone(11.4102, 76.6950)
    assert context.zone_id is not None
    assert context.inside_zone is True
    assert context.provider == "RISK_ZONE_SEED_PROVIDER"
    assert context.is_real is False


def test_gis_provider_is_replaceable():
    class FakeProvider(RiskZoneSeedGisProvider):
        name = "TEST_GIS_PROVIDER"
        is_real = True
        data_source = "test fixture"

    set_gis_provider(FakeProvider())
    try:
        context = get_gis_provider().find_zone(11.4102, 76.6950)
        assert context.provider == "TEST_GIS_PROVIDER"
        assert context.is_real is True
    finally:
        set_gis_provider(None)  # reset to the bundled default adapter


def test_gis_zone_endpoint():
    response = client.get("/api/gis/zone?latitude=11.4102&longitude=76.6950")
    assert response.status_code == 200
    data = response.json()
    assert data["spatial_context"]["zone_id"] is not None
    assert data["provider"]["is_real"] is False


def test_component_weights_are_normalised():
    assert abs(sum(COMPONENT_WEIGHTS.values()) - 1.0) < 1e-9
    assert set(COMPONENT_WEIGHTS) == {"environmental_m1", "spatial_m2", "satellite_m3"}


def test_composite_risk_includes_only_available_components():
    result = compute_composite_risk(11.4102, 76.6950)

    assert result["components"]["environmental_m1"]["available"] is True
    # Without an explicit patch the satellite component is honestly excluded.
    assert result["components"]["satellite_m3"]["available"] is False
    assert "satellite_m3" not in result["components_used"]
    assert "environmental_m1" in result["components_used"]

    assert result["final_risk"]["available"] is True
    assert 0.0 <= result["final_risk"]["probability"] <= 1.0
    assert result["final_risk"]["risk_level"] in {"LOW", "MODERATE", "HIGH", "VERY_HIGH"}


def test_composite_risk_never_fabricates_unavailable_components():
    # A coordinate far outside every seeded zone still resolves a nearest zone
    # in the demo provider, but the satellite component must stay unavailable.
    result = compute_composite_risk(0.0, 0.0)
    assert result["components"]["satellite_m3"]["available"] is False
    assert result["components"]["satellite_m3"]["probability"] is None


def test_composite_risk_endpoint():
    response = client.get("/api/risk/composite?latitude=11.4102&longitude=76.6950")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data and "final_risk" in data
    assert data["components"]["environmental_m1"]["is_real"] is True
    assert data["components"]["spatial_m2"]["is_real"] is False
