"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "FLOODRIX"
    assert data["model_loaded"] is True


def test_health_endpoint_v1_alias(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is True


def test_model_info_endpoint(client):
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "feature_columns" in data
    assert len(data["feature_columns"]) >= 8
    assert "test_metrics" in data
    assert "risk_bands" in data


def test_predict_segments_single_and_batch(client):
    # Single segment
    single_payload = {
        "segments": [
            {
                "segment_id": "seg_ernakulam_01",
                "latitude": 9.98,
                "longitude": 76.28,
                "rainfall_1h": 12.0,
                "rainfall_6h": 40.0,
                "rainfall_24h": 90.0,
                "elevation": 5.0,
                "historical_flood_frequency": 3,
                "flood_zone": "high",
            }
        ]
    }
    res = client.post("/predict/segments", json=single_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_segments"] == 1
    assert len(data["segments"]) == 1
    pred = data["segments"][0]
    assert pred["segment_id"] == "seg_ernakulam_01"
    assert 0.0 <= pred["flood_probability"] <= 1.0
    assert pred["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "latency_ms" in data

    # Batch of 500 segments
    batch_500 = {
        "segments": [
            {
                "segment_id": f"batch_{i}",
                "latitude": 9.5 + (i % 30) * 0.05,
                "longitude": 76.0 + (i % 20) * 0.05,
                "rainfall_1h": float(5 + (i % 15)),
                "rainfall_6h": float(20 + (i % 30)),
                "rainfall_24h": float(60 + (i % 50)),
                "elevation": float(4 + (i % 20)),
                "historical_flood_frequency": i % 5,
                "flood_zone": "medium",
            }
            for i in range(500)
        ]
    }
    res_batch = client.post("/predict/segments", json=batch_500)
    assert res_batch.status_code == 200
    data_batch = res_batch.json()
    assert data_batch["total_segments"] == 500
    assert len(data_batch["segments"]) == 500


def test_predict_route_risk(client):
    payload = {
        "route_id": "route_nh66_kochi_alappuzha",
        "segments": [
            {
                "segment_id": f"seg_{i}",
                "latitude": 9.98 - i * 0.08,
                "longitude": 76.28 + (i % 2) * 0.01,
                "rainfall_1h": 15.0,
                "rainfall_6h": 45.0,
                "rainfall_24h": 105.0,
                "elevation": 3.0,
                "historical_flood_frequency": 4,
                "flood_zone": "high",
            }
            for i in range(6)
        ],
    }

    res = client.post("/predict/route", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["route_id"] == "route_nh66_kochi_alappuzha"
    assert 0.0 <= data["route_risk"] <= 1.0
    assert 0.0 <= data["max_segment_risk"] <= 1.0
    assert data["recommended_action"] in ["GO", "REROUTE", "WAIT"]
    assert len(data["segments"]) == 6
    assert "worst_segments" in data
    assert "risk_independence_note" in data


def test_predict_invalid_payload_returns_422(client):
    # Non-monotonic rainfall
    bad_payload = {
        "segments": [
            {
                "segment_id": "bad",
                "latitude": 10.0,
                "longitude": 76.3,
                "rainfall_1h": 50.0,
                "rainfall_6h": 20.0,  # 1h > 6h
                "rainfall_24h": 60.0,
                "elevation": 10.0,
                "historical_flood_frequency": 1,
                "flood_zone": "low",
            }
        ]
    }
    res = client.post("/predict/segments", json=bad_payload)
    assert res.status_code == 422


def test_plan_route_logistics_v1(client):
    payload = {
        "origin": {"latitude": 9.98, "longitude": 76.28},
        "destination": {"latitude": 10.52, "longitude": 76.21},
        "cargo_type": "MEDICINE",
    }
    res = client.post("/api/v1/routes/plan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommended_route" in data
    assert "alternative_routes" in data
    assert data["recommended_route"]["decision"] in ["GO", "REROUTE", "WAIT"]


def test_weather_endpoints_v1(client):
    res_curr = client.get("/api/v1/weather/current?latitude=10.0&longitude=76.3")
    assert res_curr.status_code == 200
    curr_data = res_curr.json()
    assert "rainfall_1h" in curr_data
    assert "rainfall_24h" in curr_data

    res_fc = client.get("/api/v1/weather/forecast?latitude=10.0&longitude=76.3")
    assert res_fc.status_code == 200
    assert len(res_fc.json()["forecast"]) > 0


def test_closures_and_simulation_v1(client):
    res_closures = client.get("/api/v1/closures")
    assert res_closures.status_code == 200
    assert len(res_closures.json()["closures"]) > 0

    sim_payload = {
        "route_id": "test_r1",
        "rainfall_multiplier": 2.5,
        "inject_closure": True,
    }
    res_sim = client.post("/api/v1/simulation/run", json=sim_payload)
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert sim_data["simulated_decision"] == "REROUTE"
    assert sim_data["simulated_risk"] >= sim_data["original_risk"]
