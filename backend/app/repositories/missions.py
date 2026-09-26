from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.mission import Mission, MissionAOI
from app.schemas.mission import AOICreate, MissionCreate, MissionUpdate


def list_missions(db: Session) -> list[Mission]:
    return list(db.scalars(select(Mission).options(selectinload(Mission.aois)).order_by(Mission.id.desc())))


def get_mission(db: Session, mission_id: int) -> Mission | None:
    return db.scalar(select(Mission).where(Mission.id == mission_id).options(selectinload(Mission.aois)))


def create_mission(db: Session, payload: MissionCreate) -> Mission:
    mission = Mission(**payload.model_dump(), source_type="SIMULATED" if payload.mode == "DEMO" else "UPLOADED")
    db.add(mission)
    db.commit()
    return get_mission(db, mission.id)  # type: ignore[return-value]


def update_mission(db: Session, mission: Mission, payload: MissionUpdate) -> Mission:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(mission, key, value)
    db.commit()
    return get_mission(db, mission.id)  # type: ignore[return-value]


def add_aoi(db: Session, mission: Mission, payload: AOICreate) -> MissionAOI:
    aoi = MissionAOI(mission_id=mission.id, **payload.model_dump())
    db.add(aoi)
    db.commit()
    db.refresh(aoi)
    return aoi
