from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db, make_engine
from app.main import app
from app.services.seed import seed_demo


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'hazards.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    with local_session() as db:
        seed_demo(db)

    def override_db():
        with local_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def demo_id(client: TestClient) -> int:
    return next(m["id"] for m in client.get("/api/missions").json() if m["name"] == "Mission Cyclone Varuna")


def base(client: TestClient) -> str:
    return f"/api/missions/{demo_id(client)}"


def plan(client: TestClient) -> dict:
    path = base(client)
    return client.post(f"{path}/routes/calculate", json={"start": {"row": 19, "col": 3}, "destination": {"row": 4, "col": 32}}).json()


def payload(row: int, col: int, **overrides) -> dict:
    return {"row": row, "col": col, "hazard_type": "SUBMERGED_OBSTRUCTION", "severity": "HIGH", "confidence": 0.95, **overrides}


def test_seeded_hazards_persist_without_duplicates_and_preserve_baseline(client):
    path = base(client)
    hazards = client.get(f"{path}/hazards").json()
    assert [hazard["id"] for hazard in hazards] == ["Hazard 01", "Hazard 02", "Hazard 03"]
    assert all(hazard["source_type"] == "DEMO_ANNOTATION" for hazard in hazards)
    assert all(hazard["created_at"] and hazard["status"] == "ACTIVE" for hazard in hazards)
    route = plan(client)
    assert route["shortest_route"]["distance_m"] == pytest.approx(1760.66, abs=0.02)
    assert route["shortest_route"]["average_risk"] == pytest.approx(0.19794, abs=0.00002)
    assert route["lower_risk_route"]["distance_m"] == pytest.approx(1819.24, abs=0.02)
    assert route["lower_risk_route"]["average_risk"] == pytest.approx(0.13755, abs=0.00002)


def test_validation_and_no_plan_flow(client):
    path = base(client)
    for item in (payload(10, 10, confidence=4.2), payload(10, 10, confidence=-0.1), payload(10, 10, severity="EXTREME"), payload(24, 10), payload(11, 18), payload(10, 10, source_type="ML_INFERENCE")):
        assert client.post(f"{path}/hazards", json=item).status_code == 422
    assert client.post("/api/missions/999999/hazards", json=payload(10, 10)).status_code == 404
    created = client.post(f"{path}/hazards", json=payload(7, 7))
    assert created.status_code == 201
    result = created.json()
    assert result["hazard"]["source_type"] == "MANUAL"
    assert result["impact"]["risk_recalculated"] is True
    assert result["impact"]["route_recalculated"] is False
    assert result["impact"]["reason"] == "No active route plan"
    assert any(h["id"] == result["hazard"]["id"] for h in client.get(f"{path}/hazards").json())
    assert client.get(f"{path}/risk-map").json()["cells"][7][7]["hazard_risk"] > 0


def test_on_route_hazard_reroutes_and_resolution_restores_risk(client):
    path = base(client)
    before = plan(client)
    old = before["lower_risk_route"]
    point = old["coordinates"][len(old["coordinates"]) // 2]
    risk_before = client.get(f"{path}/risk-map").json()["cells"][point["row"]][point["col"]]["total_risk"]
    created = client.post(f"{path}/hazards", json=payload(point["row"], point["col"], client_request_id=str(uuid4())))
    assert created.status_code == 201
    result = created.json()
    hazard = result["hazard"]
    impact = result["impact"]
    assert impact["risk_recalculated"] is True
    assert impact["route_recalculated"] is True
    assert impact["previous_route_affected"] is True
    assert impact["route_changed"] is True
    assert result["risk_map"]["cells"][point["row"]][point["col"]]["total_risk"] > risk_before
    assert impact["previous_route"]["distance_m"] == old["distance_m"]
    assert impact["updated_route"]["distance_m"] == result["routes"]["lower_risk_route"]["distance_m"]
    assert result["routes"]["lower_risk_route"]["average_risk"] <= impact["retained_path_average_risk"]
    assert all(result["risk_map"]["cells"][p["row"]][p["col"]]["navigable"] for p in result["routes"]["lower_risk_route"]["coordinates"])
    assert client.get(f"{path}/routes").json()["lower_risk_route"]["coordinates"] == result["routes"]["lower_risk_route"]["coordinates"]
    assert any(h["id"] == hazard["id"] for h in client.get(f"{path}/hazards").json())

    resolved = client.patch(f"{path}/hazards/{hazard['id']}", json={"status": "RESOLVED"})
    assert resolved.status_code == 200
    cleared = resolved.json()
    assert cleared["hazard"]["status"] == "RESOLVED"
    assert cleared["impact"]["route_recalculated"] is True
    assert cleared["risk_map"]["cells"][point["row"]][point["col"]]["total_risk"] == risk_before
    assert cleared["routes"]["lower_risk_route"]["coordinates"] == old["coordinates"]
    assert client.get(f"{path}/hazards").json()[-1]["status"] == "RESOLVED"


def test_distant_low_hazard_does_not_claim_affected_route(client):
    path = base(client)
    before = plan(client)
    result = client.post(f"{path}/hazards", json=payload(22, 34, severity="LOW", confidence=0.3)).json()
    assert result["impact"]["risk_recalculated"] is True
    assert result["impact"]["route_recalculated"] is True
    assert result["impact"]["previous_route_affected"] is False
    assert result["impact"]["route_changed"] is False
    assert result["routes"]["lower_risk_route"]["coordinates"] == before["lower_risk_route"]["coordinates"]


def test_request_id_prevents_duplicate_submission(client):
    path = base(client)
    request_id = str(uuid4())
    data = payload(7, 7, client_request_id=request_id)
    first = client.post(f"{path}/hazards", json=data)
    second = client.post(f"{path}/hazards", json=data)
    assert first.status_code == second.status_code == 201
    assert first.json()["hazard"]["id"] == second.json()["hazard"]["id"]
    assert len(client.get(f"{path}/hazards").json()) == 4
