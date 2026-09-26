from fastapi.testclient import TestClient

from app.main import app


def test_demo_grid_and_route_api():
    with TestClient(app) as client:
        missions = client.get("/api/missions").json()
        demo_id = next(m["id"] for m in missions if m["name"] == "Mission Cyclone Varuna")
        base = f"/api/missions/{demo_id}"
        risk = client.get(f"{base}/risk-map")
        assert risk.status_code == 200
        payload = risk.json()
        assert payload["coordinate_system"] == "SCHEMATIC_GRID_NOT_GEOGRAPHIC"
        assert len(payload["cells"]) == 24
        assert len(payload["cells"][0]) == 36
        assert len(payload["hazards"]) == 3
        assert client.get(f"{base}/environment").json()["cells"][0][0]["wave_height_m"] != client.get(f"{base}/environment").json()["cells"][20][30]["wave_height_m"]
        assert client.get(f"{base}/bathymetry").json()["depth_m"][11][18] == 3.7
        assert client.post(f"{base}/risk-map/recalculate", json={}).json()["cells"] == payload["cells"]
        assert client.get(f"{base}/routes").status_code == 404
        result = client.post(f"{base}/routes/calculate", json={"start": payload["start"], "destination": payload["destination"]})
        assert result.status_code == 200
        assert result.json()["lower_risk_route"]["average_risk"] < result.json()["shortest_route"]["average_risk"]
        assert client.get(f"{base}/routes").json()["comparison"] == result.json()["comparison"]
        assert client.post(f"{base}/routes/calculate", json={"start": {"row": -1, "col": 2}, "destination": payload["destination"]}).json()["detail"]["code"] == "INVALID_START"
        assert client.post(f"{base}/risk-map/recalculate", json={"weights": {"hazard": 0.5}}).status_code == 422
        assert client.get("/api/missions/999999/risk-map").status_code == 404
