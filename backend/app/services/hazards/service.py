from math import hypot
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.hazard import Hazard
from app.models.mission import utc_now
from app.models.route import RouteCalculation
from app.repositories.hazards import by_request_id, get_hazard
from app.schemas.hazard import HazardCreate, HazardMutationResult, HazardRead, HazardStatusUpdate
from app.schemas.routing import RiskOptions
from app.services.risk.demo import configuration, map_payload, mission_environment
from app.services.risk.engine import build_risk_map
from app.services.routing.service import calculate_routes, route_stats


SEVERITY_FACTOR = {"LOW": 0.35, "MEDIUM": 0.60, "HIGH": 0.82, "CRITICAL": 1.0}
FRIENDLY_TYPE = {
    "WRECKAGE": "Possible wreckage", "DEBRIS": "Marine debris",
    "SUBMERGED_OBSTRUCTION": "Submerged obstruction",
    "KNOWN_INFRASTRUCTURE": "Known infrastructure", "UNKNOWN_ANOMALY": "Unknown anomaly",
    "OTHER": "Other hazard",
}
MANUAL_RADIUS_CELLS = 5.0
AFFECTED_WEIGHTED_CONTRIBUTION = 0.02


def latest_plan(db: Session, mission_id: int) -> RouteCalculation | None:
    return db.scalar(select(RouteCalculation).where(RouteCalculation.mission_id == mission_id).order_by(RouteCalculation.id.desc()))


def _summary(route: dict) -> dict:
    return {key: route[key] for key in ("distance_m", "average_risk", "accumulated_risk")}


def _affected(old_path: list[dict], hazard: Hazard, hazard_weight: float) -> bool:
    strength = hazard_weight * hazard.severity_factor * hazard.confidence
    return any(
        strength * max(0.0, 1 - hypot(point["row"] - hazard.row, point["col"] - hazard.col) / hazard.radius_cells) >= AFFECTED_WEIGHTED_CONTRIBUTION
        for point in old_path
    )


def _impact_explanation(hazard: Hazard, status: str, affected: bool, changed: bool, previous: dict, updated: dict, retained_risk: float) -> str:
    action = "added" if status == "ACTIVE" else "resolved"
    overlap = "The previous lower modeled-risk path crossed this hazard's influence area." if affected else "The previous lower modeled-risk path did not materially overlap this hazard's influence area."
    geometry = "A* selected a different path." if changed else "A* retained the same path."
    return (
        f"{hazard.label} was {action}. {overlap} {geometry} "
        f"Modeled distance changed from {previous['distance_m']:.0f} to {updated['distance_m']:.0f} m; "
        f"average modeled risk changed from {previous['average_risk']:.3f} to {updated['average_risk']:.3f}. "
        f"Keeping the previous geometry under the updated risk field would have average modeled risk {retained_risk:.3f}."
    )


def _recalculate(db: Session, mission_id: int, hazard: Hazard) -> HazardMutationResult:
    previous = latest_plan(db, mission_id)
    options = RiskOptions.model_validate(previous.result.get("_risk_options", {})) if previous else RiskOptions()
    environment = mission_environment(db, mission_id)
    risk_map = map_payload(environment, options)
    impact: dict = {"risk_recalculated": True, "route_recalculated": False, "reason": "No active route plan", "previous_route_affected": None, "route_changed": None, "previous_route": None, "updated_route": None, "explanation": "Risk grid updated. No active route plan was available to recalculate."}
    routes = None
    if previous:
        config = configuration(options)
        grid = risk_map["cells"]
        old_route = previous.result["lower_risk_route"]
        start = previous.start
        destination = previous.destination
        routes = calculate_routes(grid, environment, (start["row"], start["col"]), (destination["row"], destination["col"]), config)
        routes.update({"start": start, "destination": destination, "calculated_at": utc_now().isoformat(), "_risk_options": options.model_dump()})
        old_points = [(point["row"], point["col"]) for point in old_route["coordinates"]]
        retained = route_stats(old_points, grid, environment, config, "PREVIOUS_GEOMETRY_REEVALUATED", 0)
        affected = _affected(old_route["coordinates"], hazard, config.weights.hazard)
        changed = old_route["coordinates"] != routes["lower_risk_route"]["coordinates"]
        updated = routes["lower_risk_route"]
        impact = {
            "risk_recalculated": True, "route_recalculated": True, "reason": None,
            "previous_route_affected": affected, "route_changed": changed,
            "previous_route": _summary(old_route), "updated_route": _summary(updated),
            "retained_path_average_risk": retained["average_risk"],
            "explanation": _impact_explanation(hazard, hazard.status, affected, changed, old_route, updated, retained["average_risk"]),
        }
        db.add(RouteCalculation(mission_id=mission_id, start=start, destination=destination, result=routes))
    result = HazardMutationResult.model_validate({"hazard": HazardRead.model_validate(hazard), "impact": impact, "risk_map": risk_map, "routes": routes})
    if hazard.client_request_id and hazard.last_action is None:
        hazard.last_action = result.model_dump(mode="json")
    db.commit()
    return result


def create_hazard(db: Session, mission_id: int, payload: HazardCreate) -> HazardMutationResult:
    request_id = str(payload.client_request_id) if payload.client_request_id else None
    if request_id:
        existing = by_request_id(db, mission_id, request_id)
        if existing and existing.last_action:
            return HazardMutationResult.model_validate(existing.last_action)
    environment = mission_environment(db, mission_id)
    if payload.row >= environment.rows or payload.col >= environment.cols:
        raise HTTPException(status_code=422, detail={"code": "HAZARD_OUTSIDE_GRID", "message": "Hazard location is outside the simulated grid"})
    if environment.depth[payload.row][payload.col] < RiskOptions().minimum_operational_depth_m:
        raise HTTPException(status_code=422, detail={"code": "HAZARD_LOCATION_BLOCKED", "message": "Select a navigable demo cell for a manual hazard"})
    hazard = Hazard(
        id=str(uuid4()), mission_id=mission_id, row=payload.row, col=payload.col,
        hazard_type=payload.hazard_type.value, label=FRIENDLY_TYPE[payload.hazard_type.value],
        severity=payload.severity.value, severity_factor=SEVERITY_FACTOR[payload.severity.value],
        confidence=payload.confidence, anomaly_score=payload.anomaly_score,
        radius_cells=MANUAL_RADIUS_CELLS, source_type="MANUAL", status="ACTIVE",
        notes=payload.notes, client_request_id=request_id,
    )
    try:
        db.add(hazard)
        db.flush()
        return _recalculate(db, mission_id, hazard)
    except IntegrityError as error:
        db.rollback()
        if request_id:
            existing = by_request_id(db, mission_id, request_id)
            if existing and existing.last_action:
                return HazardMutationResult.model_validate(existing.last_action)
        raise error
    except Exception:
        db.rollback()
        raise


def update_status(db: Session, mission_id: int, hazard_id: str, payload: HazardStatusUpdate) -> HazardMutationResult:
    hazard = get_hazard(db, mission_id, hazard_id)
    if hazard is None:
        raise HTTPException(status_code=404, detail={"code": "HAZARD_NOT_FOUND", "message": "Hazard not found"})
    if hazard.status == payload.status.value:
        raise HTTPException(status_code=409, detail={"code": "HAZARD_STATUS_UNCHANGED", "message": "Hazard already has this status"})
    try:
        hazard.status = payload.status.value
        hazard.updated_at = utc_now()
        db.flush()
        return _recalculate(db, mission_id, hazard)
    except Exception:
        db.rollback()
        raise
