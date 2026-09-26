from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session

from app.api.routes.missions import require_mission
from app.core.database import get_db
from app.services.imagery import (ClassicalChangeDetector, DemoAnnotationDetector, HeuristicAnomalyDetector,
    MLChangeDetector, MLSonarDetector, problem, read_image, replay_metadata,
    save_upload, source_path)

router = APIRouter(prefix="/missions/{mission_id}", tags=["offline imagery analysis"])


class AnalysisRequest(BaseModel):
    source: Literal["demo", "uploaded"] = "demo"
    detector: str = "classical"


def check(db: Session, mission_id: int, source: str | None = None):
    mission = require_mission(db, mission_id)
    if source == "demo" and (mission.name != "Mission Cyclone Varuna" or mission.mode != "DEMO"):
        raise problem("DEMO_DATA_UNAVAILABLE", "Bundled imagery belongs to Mission Cyclone Varuna", 409)
    return mission


@router.get("/satellite/status")
def satellite_status(mission_id: int, db: Session = Depends(get_db)):
    mission = check(db, mission_id)
    return {"demo_available": mission.name == "Mission Cyclone Varuna" and mission.mode == "DEMO",
            "uploaded_before": source_path(mission_id, "satellite", "uploaded", "before").is_file(),
            "uploaded_after": source_path(mission_id, "satellite", "uploaded", "after").is_file(),
            "classical_cv_available": True, "ml_model_configured": False}


@router.post("/satellite/upload")
async def satellite_upload(mission_id: int, role: Literal["before", "after"], file: UploadFile, db: Session = Depends(get_db)):
    check(db, mission_id)
    if file.content_type not in ("image/png", "image/jpeg"):
        raise problem("UNSUPPORTED_MEDIA_TYPE", "Upload a PNG or JPEG")
    save_upload(mission_id, "satellite", role, await file.read(10 * 1024 * 1024 + 1))
    return {"role": role, "source_type": "USER_UPLOAD", "uploaded": True}


@router.post("/satellite/analyze")
def satellite_analyze(mission_id: int, payload: AnalysisRequest, db: Session = Depends(get_db)):
    check(db, mission_id, payload.source)
    if payload.detector == "ml":
        MLChangeDetector().analyze(None, None)
    if payload.detector != "classical":
        raise problem("UNKNOWN_DETECTOR", "Use classical or ml")
    before = read_image(source_path(mission_id, "satellite", payload.source, "before"))
    after = read_image(source_path(mission_id, "satellite", payload.source, "after"))
    return {**ClassicalChangeDetector().analyze(before, after), "source_type": "SIMULATED_DEMO_DATA" if payload.source == "demo" else "USER_UPLOAD"}


@router.get("/satellite/assets/{source}/{role}")
def satellite_asset(mission_id: int, source: Literal["demo", "uploaded"], role: Literal["before", "after"], db: Session = Depends(get_db)):
    check(db, mission_id, source)
    from app.services.imagery import png
    return Response(png(read_image(source_path(mission_id, "satellite", source, role))), media_type="image/png")


@router.get("/sonar/replay")
def sonar_replay(mission_id: int, db: Session = Depends(get_db)):
    check(db, mission_id, "demo")
    return {"source_type": "SIMULATED_DEMO_DATA", "detector": "DEMO_ANNOTATIONS", "frames": [
        {**frame, "annotation_result": DemoAnnotationDetector(frame["name"]).analyze(None),
         "image_url": f"/api/missions/{mission_id}/sonar/assets/demo/{frame['name']}"}
        for frame in replay_metadata()]}


@router.post("/sonar/upload")
async def sonar_upload(mission_id: int, file: UploadFile, db: Session = Depends(get_db)):
    check(db, mission_id)
    if file.content_type not in ("image/png", "image/jpeg"):
        raise problem("UNSUPPORTED_MEDIA_TYPE", "Upload a PNG or JPEG")
    save_upload(mission_id, "sonar", "frame", await file.read(10 * 1024 * 1024 + 1))
    return {"source_type": "USER_UPLOAD", "uploaded": True}


@router.post("/sonar/analyze")
def sonar_analyze(mission_id: int, payload: AnalysisRequest, db: Session = Depends(get_db)):
    check(db, mission_id)
    if payload.detector == "ml":
        MLSonarDetector().analyze(None)
    if payload.source != "uploaded" or payload.detector != "heuristic":
        raise problem("INVALID_ANALYSIS", "Uploaded sonar frames use the heuristic detector")
    return {**HeuristicAnomalyDetector().analyze(read_image(source_path(mission_id, "sonar", "uploaded", "frame"))), "source_type": "USER_UPLOAD"}


@router.get("/sonar/model/status")
def sonar_model_status(mission_id: int, db: Session = Depends(get_db)):
    check(db, mission_id)
    return {"ml_model_configured": False, "code": "MODEL_NOT_CONFIGURED", "heuristic_available": True,
            "uploaded_frame": source_path(mission_id, "sonar", "uploaded", "frame").is_file()}


@router.get("/sonar/assets/{source}/{name}")
def sonar_asset(mission_id: int, source: Literal["demo", "uploaded"], name: str, db: Session = Depends(get_db)):
    check(db, mission_id, source)
    if source == "demo" and name not in {frame["name"] for frame in replay_metadata()}:
        raise problem("FRAME_NOT_FOUND", "Unknown demo frame", 404)
    if source == "uploaded" and name != "frame":
        raise problem("FRAME_NOT_FOUND", "Unknown uploaded frame", 404)
    from app.services.imagery import png
    role = name.removesuffix(".png") if source == "demo" else name
    return Response(png(read_image(source_path(mission_id, "sonar", source, role))), media_type="image/png")
