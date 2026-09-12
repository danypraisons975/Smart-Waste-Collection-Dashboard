import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from services.dashboard_service import build_dashboard_data


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_dashboard_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Smart Waste Collection Management System" in response.data
    assert b"Household status" in response.data


def test_dashboard_api_has_prediction(client):
    response = client.get("/api/dashboard")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["summary"]["total_houses"] == 12
    assert payload["summary"]["ready"] == 9
    assert payload["summary"]["waiting"] == 3
    assert payload["summary"]["predicted_delay"] >= 0
    assert len(payload["history"]) == 12


def test_service_returns_expected_model_metadata():
    dashboard = build_dashboard_data()
    assert dashboard["model"]["name"] == "Random Forest Regression"
    assert dashboard["model"]["training_records"] == 11
    assert dashboard["summary"]["expected_collection"].endswith("AM")
