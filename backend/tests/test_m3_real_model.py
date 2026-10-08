"""Tests for the REAL M3 satellite (Landslide4Sense U-Net) model."""
import os

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.m3_inference import (
    coordinate_mapping_status,
    m3_inference_service,
    resolve_m3_checkpoint_path,
)

client = TestClient(app)


def _write_patch(path: str) -> None:
    import h5py

    rng = np.random.default_rng(1234)
    with h5py.File(path, "w") as fh:
        fh.create_dataset("img", data=rng.random((128, 128, 14)))


def test_m3_checkpoint_resolves_to_the_expected_artifact():
    path = resolve_m3_checkpoint_path().replace("\\", "/")
    assert path.endswith("phase6/image_analysis/checkpoints/best_model.pth")


def test_m3_checkpoint_exists_and_loads():
    assert os.path.isfile(resolve_m3_checkpoint_path())
    assert m3_inference_service.is_available() is True


def test_m3_coordinate_mapping_is_honestly_unavailable():
    status = coordinate_mapping_status()
    assert status["available"] is False
    assert status["reason"]  # a concrete explanation, not an empty claim


def test_m3_inference_contract_on_a_real_patch(tmp_path):
    patch = tmp_path / "patch.h5"
    _write_patch(str(patch))

    result = m3_inference_service.segment_patch(str(patch))

    assert result["output_shape"] == [128, 128]
    assert 0.0 <= result["mean_probability"] <= 1.0
    assert 0.0 <= result["max_probability"] <= 1.0
    assert 0.0 <= result["positive_fraction"] <= 1.0
    assert result["is_mock"] is False
    assert result["checkpoint_path"].replace("\\", "/").endswith(
        "phase6/image_analysis/checkpoints/best_model.pth"
    )


def test_m3_inference_rejects_missing_patch():
    with pytest.raises(FileNotFoundError):
        m3_inference_service.segment_patch("does_not_exist.h5")


def test_m3_predict_endpoint_runs_real_inference(tmp_path):
    patch = tmp_path / "upload.h5"
    _write_patch(str(patch))

    with open(patch, "rb") as fh:
        response = client.post(
            "/api/ml/m3/predict",
            files={"file": ("upload.h5", fh, "application/octet-stream")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["is_mock"] is False
    assert body["output_shape"] == [128, 128]


def test_m3_predict_endpoint_rejects_non_h5():
    response = client.post(
        "/api/ml/m3/predict",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_models_status_reports_both_models_available():
    response = client.get("/api/ml/models/status")
    assert response.status_code == 200
    data = response.json()
    assert data["environmental_m1"]["available"] is True
    assert data["satellite_m3"]["available"] is True
    assert data["satellite_m3"]["coordinate_mapping"]["available"] is False
