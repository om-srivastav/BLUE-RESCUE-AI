import io

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db, make_engine
from app.main import app
from app.services.imagery import ClassicalChangeDetector, HeuristicAnomalyDetector
from app.services.seed import seed_demo


@pytest.fixture
def imagery_client(tmp_path, monkeypatch):
    engine = make_engine(f"sqlite:///{(tmp_path / 'imagery.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    with session() as db:
        seed_demo(db)
    def override():
        with session() as db:
            yield db
    monkeypatch.setattr(settings, "blue_cache_dir", tmp_path / "cache")
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


def path(client):
    mission_id = next(m["id"] for m in client.get("/api/missions").json() if m["name"] == "Mission Cyclone Varuna")
    return f"/api/missions/{mission_id}"


def image_bytes(with_square=False):
    image = np.zeros((80, 100, 3), np.uint8)
    if with_square:
        cv2.rectangle(image, (30, 20), (55, 45), (240, 240, 240), -1)
    return cv2.imencode(".png", image)[1].tobytes()


def test_satellite_demo_and_ml_placeholder(imagery_client):
    p = path(imagery_client)
    assert imagery_client.get(f"{p}/satellite/status").json()["demo_available"]
    assert imagery_client.get(f"{p}/satellite/assets/demo/before").status_code == 200
    result = imagery_client.post(f"{p}/satellite/analyze", json={"source": "demo"}).json()
    assert result["detector"] == "CLASSICAL_CV_BASELINE"
    assert result["source_type"] == "SIMULATED_DEMO_DATA"
    assert result["percent_changed"] > 0
    assert result["regions"]
    ml = imagery_client.post(f"{p}/satellite/analyze", json={"detector": "ml"})
    assert ml.status_code == 409 and ml.json()["detail"]["code"] == "MODEL_NOT_CONFIGURED"


def test_satellite_upload_validation_and_change(imagery_client):
    p = path(imagery_client)
    for role, data in (("before", image_bytes()), ("after", image_bytes(True))):
        response = imagery_client.post(f"{p}/satellite/upload?role={role}", files={"file": (f"{role}.png", io.BytesIO(data), "image/png")})
        assert response.status_code == 200
    result = imagery_client.post(f"{p}/satellite/analyze", json={"source": "uploaded"}).json()
    assert result["source_type"] == "USER_UPLOAD" and result["changed_pixels"] > 0
    assert imagery_client.get(f"{p}/satellite/status").json()["uploaded_after"]
    invalid = imagery_client.post(f"{p}/satellite/upload?role=before", files={"file": ("x.txt", b"not an image", "text/plain")})
    assert invalid.status_code == 422
    assert imagery_client.post(f"{p}/satellite/upload?role=before", files={"file": ("x.png", b"broken", "image/png")}).status_code == 422
    assert imagery_client.post(f"{p}/satellite/analyze", json={"source": "unknown"}).status_code == 422


def test_identical_images_have_no_change():
    image = np.zeros((80, 100, 3), np.uint8)
    result = ClassicalChangeDetector().analyze(image, image.copy())
    assert result["percent_changed"] == 0 and result["regions"] == []
    with pytest.raises(Exception) as mismatch:
        ClassicalChangeDetector().analyze(image, np.zeros((81, 100, 3), np.uint8))
    assert mismatch.value.detail["code"] == "DIMENSION_MISMATCH"


def test_sonar_replay_upload_heuristic_and_ml_placeholder(imagery_client):
    p = path(imagery_client)
    replay = imagery_client.get(f"{p}/sonar/replay").json()
    assert len(replay["frames"]) == 5
    assert all(f["annotations"][0]["source_type"] == "DEMO_ANNOTATION" for f in replay["frames"])
    assert all(f["annotation_result"]["output_source"] == "DEMO / MISSION_REPLAY" for f in replay["frames"])
    assert imagery_client.get(replay["frames"][0]["image_url"]).status_code == 200
    assert imagery_client.post(f"{p}/sonar/analyze", json={"source": "uploaded", "detector": "heuristic"}).status_code == 404
    assert imagery_client.post(f"{p}/sonar/upload", files={"file": ("frame.png", image_bytes(True), "image/png")}).status_code == 200
    result = imagery_client.post(f"{p}/sonar/analyze", json={"source": "uploaded", "detector": "heuristic"}).json()
    assert result["detector"] == "HEURISTIC_ANOMALY_BASELINE" and result["anomaly_count"] >= 1
    assert result["output_source"] == "HEURISTIC" and result["anomaly_score"] > 0
    assert all(r["label"] == "Unknown anomaly" for r in result["regions"])
    assert imagery_client.get(f"{p}/sonar/model/status").json()["ml_model_configured"] is False
    ml = imagery_client.post(f"{p}/sonar/analyze", json={"source": "uploaded", "detector": "ml"})
    assert ml.status_code == 409 and ml.json()["detail"]["code"] == "MODEL_NOT_CONFIGURED"


def test_unknown_mission_rejected(imagery_client):
    assert imagery_client.get("/api/missions/999999/satellite/status").status_code == 404
    assert imagery_client.get("/api/missions/999999/sonar/replay").status_code == 404
