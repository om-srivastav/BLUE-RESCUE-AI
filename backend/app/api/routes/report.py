from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.routes.missions import require_mission
from app.core.database import get_db
from app.schemas.report import MissionReport, SystemStatus
from app.services.report import build_report, system_status

router = APIRouter(prefix="/missions/{mission_id}", tags=["mission status and report"])


@router.get("/system-status", response_model=SystemStatus)
def status(mission_id: int, db: Session = Depends(get_db)):
    return system_status(require_mission(db, mission_id))


@router.get("/report", response_model=MissionReport)
def report(mission_id: int, db: Session = Depends(get_db)):
    return build_report(db, require_mission(db, mission_id))
