import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app
from services.dashboard_service import build_dashboard_data


@pytest.fixture()
def client():
    application = create_app()
    application.config.update(TESTING=True)
    with application.test_client() as test_client:
        yield test_client


def test_dashboard_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Smart Waste Collection Management System" in response.data
    assert b"Pre-collection inputs only" in response.data


def test_dashboard_api_has_prediction_and_original_data(client, monkeypatch):
    monkeypatch.delenv("SWC_DATA_MODE", raising=False)
    payload = client.get("/api/dashboard").get_json()
    assert payload["summary"]["total_houses"] == 12
    assert payload["summary"]["ready"] == 9
    assert payload["summary"]["waiting"] == 3
    assert len(payload["history"]) == 12
    assert payload["model"]["training_records"] == 11
    assert payload["model"]["data_mode"] == "FIELD DATA — 12 supplied observations"


def test_prediction_endpoint_returns_model_result(client):
    response = client.post("/api/predict", json={"houses_ready": 9})
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["predicted_delay"] >= 0
    assert payload["estimated_collection"]
    assert "collection_time" not in payload["inputs"]
    assert payload["status"] in {"On Time", "Slight Delay", "Delayed"}


def test_prediction_handles_zero_and_all_ready(client):
    for ready in (0, 12):
        response = client.post("/api/predict", json={"houses_ready": ready})
        assert response.status_code == 200
        assert response.get_json()["inputs"]["houses_ready"] == ready


def test_prediction_rejects_invalid_and_missing_input(client):
    for payload in ({"houses_ready": 99}, {}, {"houses_ready": "not-a-number"}, {"houses_ready": 9, "collection_time": "10:00"}):
        response = client.post("/api/predict", json=payload)
        assert response.status_code == 400
        assert "check the inputs" in response.get_json()["error"]


def test_service_returns_model_metadata_and_baseline():
    dashboard = build_dashboard_data()
    evaluation = dashboard["model"]["evaluation"]
    assert dashboard["model"]["name"] == "Random Forest Regression"
    assert dashboard["model"]["training_records"] == 11
    assert evaluation["available"] is True
    assert "baseline_mae_minutes" in evaluation
