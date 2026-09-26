from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.mission import MissionAOI
from app.repositories import missions as repository
from app.schemas.mission import AOICreate, AOIRead, MissionCreate, MissionRead, MissionUpdate

router = APIRouter(prefix="/missions", tags=["missions"])


def require_mission(db: Session, mission_id: int):
    mission = repository.get_mission(db, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail={"code": "MISSION_NOT_FOUND", "message": "Mission not found"})
    return mission


@router.get("", response_model=list[MissionRead])
def list_missions(db: Session = Depends(get_db)):
    return repository.list_missions(db)


@router.post("", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
def create_mission(payload: MissionCreate, db: Session = Depends(get_db)):
    return repository.create_mission(db, payload)


@router.get("/{mission_id}", response_model=MissionRead)
def get_mission(mission_id: int, db: Session = Depends(get_db)):
    return require_mission(db, mission_id)


@router.patch("/{mission_id}", response_model=MissionRead)
def update_mission(mission_id: int, payload: MissionUpdate, db: Session = Depends(get_db)):
    return repository.update_mission(db, require_mission(db, mission_id), payload)


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    db.delete(require_mission(db, mission_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{mission_id}/aois", response_model=list[AOIRead])
def list_aois(mission_id: int, db: Session = Depends(get_db)):
    return require_mission(db, mission_id).aois


@router.post("/{mission_id}/aois", response_model=AOIRead, status_code=status.HTTP_201_CREATED)
def create_aoi(mission_id: int, payload: AOICreate, db: Session = Depends(get_db)):
    return repository.add_aoi(db, require_mission(db, mission_id), payload)


@router.delete("/{mission_id}/aois/{aoi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_aoi(mission_id: int, aoi_id: int, db: Session = Depends(get_db)):
    require_mission(db, mission_id)
    aoi = db.get(MissionAOI, aoi_id)
    if aoi is None or aoi.mission_id != mission_id:
        raise HTTPException(status_code=404, detail={"code": "AOI_NOT_FOUND", "message": "AOI not found"})
    db.delete(aoi)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
