from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.routes.demo_routing import demo_mission
from app.core.database import get_db
from app.repositories.hazards import list_hazards
from app.schemas.hazard import HazardCreate, HazardMutationResult, HazardRead, HazardStatusUpdate
from app.services.hazards.service import create_hazard, update_status

router = APIRouter(prefix="/missions/{mission_id}/hazards", tags=["demo hazards"])


@router.get("", response_model=list[HazardRead])
def hazards_list(mission_id: int, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    return list_hazards(db, mission_id)


@router.post("", response_model=HazardMutationResult, status_code=status.HTTP_201_CREATED)
def hazards_create(mission_id: int, payload: HazardCreate, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    return create_hazard(db, mission_id, payload)


@router.patch("/{hazard_id}", response_model=HazardMutationResult)
def hazards_update(mission_id: int, hazard_id: str, payload: HazardStatusUpdate, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    return update_status(db, mission_id, hazard_id, payload)
