from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes.missions import require_mission
from app.core.database import get_db
from app.models.route import RouteCalculation
from app.schemas.routing import RiskOptions, RouteRequest, RouteResult
from app.services.risk.engine import build_risk_map, load_demo_environment
from app.services.risk.demo import configuration, map_payload, mission_environment
from app.services.routing.astar import RouteError
from app.services.routing.service import calculate_routes
from app.models.mission import utc_now

router = APIRouter(prefix="/missions/{mission_id}", tags=["demo risk and routing"])


def demo_mission(db: Session, mission_id: int):
    mission = require_mission(db, mission_id)
    if mission.name != "Mission Cyclone Varuna" or mission.mode != "DEMO" or mission.source_type != "SIMULATED":
        raise HTTPException(status_code=409, detail={"code": "DEMO_ENVIRONMENT_UNAVAILABLE", "message": "Bundled grid is available only for Mission Cyclone Varuna"})
    return mission


@router.get("/environment")
def environment(mission_id: int, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    environment = load_demo_environment()
    return {"rows": environment.rows, "cols": environment.cols, "source_type": "SIMULATED", "coordinate_system": "SCHEMATIC_GRID_NOT_GEOGRAPHIC", "cells": environment.ocean}


@router.get("/bathymetry")
def bathymetry(mission_id: int, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    environment = load_demo_environment()
    return {"rows": environment.rows, "cols": environment.cols, "source_type": "SIMULATED", "coordinate_system": "SCHEMATIC_GRID_NOT_GEOGRAPHIC", "depth_m": environment.depth}


@router.get("/risk-map")
def risk_map(mission_id: int, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    return map_payload(mission_environment(db, mission_id), RiskOptions())


@router.post("/risk-map/recalculate")
def recalculate_risk_map(mission_id: int, options: RiskOptions, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    return map_payload(mission_environment(db, mission_id), options)


@router.post("/routes/calculate", response_model=RouteResult)
def routes_calculate(mission_id: int, payload: RouteRequest, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    environment = mission_environment(db, mission_id)
    config = configuration(payload.options)
    grid = build_risk_map(environment, config)
    try:
        result = calculate_routes(grid, environment, (payload.start.row, payload.start.col), (payload.destination.row, payload.destination.col), config)
    except RouteError as error:
        raise HTTPException(status_code=422, detail={"code": error.code, "message": str(error)}) from error
    result.update({"start": payload.start.model_dump(), "destination": payload.destination.model_dump(), "calculated_at": utc_now().isoformat(), "_risk_options": payload.options.model_dump()})
    db.add(RouteCalculation(mission_id=mission_id, start=payload.start.model_dump(), destination=payload.destination.model_dump(), result=result))
    db.commit()
    return result


@router.get("/routes", response_model=RouteResult)
def latest_routes(mission_id: int, db: Session = Depends(get_db)):
    demo_mission(db, mission_id)
    calculation = db.scalar(select(RouteCalculation).where(RouteCalculation.mission_id == mission_id).order_by(RouteCalculation.id.desc()))
    if calculation is None:
        raise HTTPException(status_code=404, detail={"code": "ROUTES_NOT_CALCULATED", "message": "Calculate routes for this mission first"})
    return {**calculation.result, "start": calculation.start, "destination": calculation.destination, "calculated_at": calculation.created_at}
