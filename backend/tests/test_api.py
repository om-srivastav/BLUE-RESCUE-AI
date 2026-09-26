from fastapi.testclient import TestClient
from app.main import app


def test_mission_lifecycle_and_seed():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        missions = client.get("/api/missions").json()
        assert len(missions) == 1
        assert missions[0]["name"] == "Mission Cyclone Varuna"
        assert missions[0]["source_type"] == "SIMULATED"

        created = client.post("/api/missions", json={"name": "Harbor survey", "mode": "REAL_DATA"})
        assert created.status_code == 201
        mission_id = created.json()["id"]
        assert client.get(f"/api/missions/{mission_id}").json()["name"] == "Harbor survey"
        assert client.patch(f"/api/missions/{mission_id}", json={"status": "ACTIVE"}).json()["status"] == "ACTIVE"

        aoi = {"name": "Survey box", "min_latitude": 10, "max_latitude": 11, "min_longitude": 70, "max_longitude": 71}
        assert client.post(f"/api/missions/{mission_id}/aois", json=aoi).status_code == 201
        assert len(client.get(f"/api/missions/{mission_id}/aois").json()) == 1
        assert client.post(f"/api/missions/{mission_id}/aois", json={**aoi, "max_latitude": 9}).status_code == 422
        assert client.delete(f"/api/missions/{mission_id}").status_code == 204
        assert client.get(f"/api/missions/{mission_id}").status_code == 404
