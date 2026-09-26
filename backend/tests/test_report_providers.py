import pytest
import cv2
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db, make_engine
from app.main import app
from app.services.providers import (ExternalBathymetryProvider, ExternalOceanProvider,
    ExternalSatelliteProvider, LocalBathymetryProvider, LocalOceanProvider,
    LocalSatelliteProvider, LocalSonarProvider, ProviderNotConfigured)
from app.services.seed import seed_demo


@pytest.fixture
def report_client(tmp_path, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "blue_cache_dir", tmp_path / "cache")
    engine = make_engine(f"sqlite:///{(tmp_path / 'report.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    with session() as db:
        seed_demo(db)
    def override():
        with session() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


def demo_base(client):
    mission_id = next(m["id"] for m in client.get("/api/missions").json() if m["name"] == "Mission Cyclone Varuna")
    return f"/api/missions/{mission_id}"


def test_local_providers_and_external_placeholders():
    satellite = LocalSatelliteProvider().pair(1, "demo")
    assert satellite.provenance.provider == "LOCAL" and satellite.before.is_file() and satellite.after.is_file()
    bathy, ocean = LocalBathymetryProvider().grid(), LocalOceanProvider().grid()
    assert bathy.rows == ocean.rows == 24 and bathy.cols == ocean.cols == 36
    assert bathy.provenance.source_type == ocean.provenance.source_type == "SIMULATED_DEMO_DATA"
    assert len(LocalSonarProvider().replay().frames) == 5
    for adapter, operation in ((ExternalSatelliteProvider(), lambda p: p.pair(1)),
                               (ExternalOceanProvider(), lambda p: p.grid()),
                               (ExternalBathymetryProvider(), lambda p: p.grid())):
        with pytest.raises(ProviderNotConfigured) as error:
            operation(adapter)
        assert error.value.code == "NOT_CONFIGURED"


def test_status_and_report_reflect_current_mission_state(report_client):
    base = demo_base(report_client)
    status = report_client.get(f"{base}/system-status")
    assert status.status_code == 200
    sources = status.json()
    assert sources["satellite"]["provider"] == "LOCAL"
    assert sources["sonar"]["source"] == "MISSION_REPLAY"
    assert sources["external_providers"]["status"] == "NOT_CONFIGURED"
    report = report_client.get(f"{base}/report")
    assert report.status_code == 200
    data = report.json()
    assert data["mission"]["name"] == "Mission Cyclone Varuna"
    assert data["coordinate_status"] == "SCHEMATIC_GRID_NOT_GEOGRAPHIC"
    assert data["satellite"]["analysis_status"] == "COMPUTED_ON_DEMAND"
    assert data["satellite"]["percent_changed"] > 0
    assert data["sonar"]["replay_frames"] == 5
    assert data["hazards"] == {"total": 3, "active": 3, "resolved": 0, "manual": 0, "demo": 3}
    assert data["environment"]["rows"] == 24 and data["risk"]["available"]
    assert data["routing"] is None
    assert "not a certified" in data["disclaimer"]

    route = report_client.post(f"{base}/routes/calculate", json={"start": {"row": 19, "col": 3}, "destination": {"row": 4, "col": 32}}).json()
    updated = report_client.get(f"{base}/report").json()
    assert updated["routing"]["lower_risk_route"]["distance_m"] == route["lower_risk_route"]["distance_m"]
    assert updated["routing"]["comparison"]["explanation"] == route["comparison"]["explanation"]
    assert updated["risk"]["weights"] == {"hazard": 0.4, "depth": 0.2, "wave": 0.15, "current": 0.15, "uncertainty": 0.1}

    mutation = report_client.post(f"{base}/hazards", json={"row": 7, "col": 7, "hazard_type": "DEBRIS", "severity": "LOW", "confidence": 0.8})
    assert mutation.status_code == 201
    final = report_client.get(f"{base}/report").json()
    assert final["hazards"]["total"] == 4 and final["hazards"]["manual"] == 1
    assert final["routing"]["calculated_at"]


def test_non_demo_and_unknown_mission_status(report_client):
    created = report_client.post("/api/missions", json={"name": "Upload-only", "mode": "DEMO"}).json()
    base = f"/api/missions/{created['id']}"
    status = report_client.get(f"{base}/system-status").json()
    assert status["bathymetry"]["status"] == "UNAVAILABLE"
    report = report_client.get(f"{base}/report").json()
    assert report["risk"]["available"] is False and report["routing"] is None
    assert report_client.get("/api/missions/999999/system-status").status_code == 404
    assert report_client.get("/api/missions/999999/report").status_code == 404


def test_report_handles_uploaded_pair_with_mismatched_dimensions(report_client):
    base = demo_base(report_client)
    for role, shape in (("before", (60, 80, 3)), ("after", (80, 80, 3))):
        png = cv2.imencode(".png", np.zeros(shape, np.uint8))[1].tobytes()
        assert report_client.post(f"{base}/satellite/upload?role={role}", files={"file": (f"{role}.png", png, "image/png")}).status_code == 200
    report = report_client.get(f"{base}/report")
    assert report.status_code == 200
    assert report.json()["satellite"]["source"] == "USER_UPLOAD"
    assert report.json()["satellite"]["analysis_status"] == "DIMENSION_MISMATCH"
