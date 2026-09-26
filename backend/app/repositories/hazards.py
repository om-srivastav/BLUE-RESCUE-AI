from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hazard import Hazard


def list_hazards(db: Session, mission_id: int) -> list[Hazard]:
    return list(db.scalars(select(Hazard).where(Hazard.mission_id == mission_id).order_by(Hazard.created_at, Hazard.id)))


def get_hazard(db: Session, mission_id: int, hazard_id: str) -> Hazard | None:
    return db.scalar(select(Hazard).where(Hazard.mission_id == mission_id, Hazard.id == hazard_id))


def by_request_id(db: Session, mission_id: int, request_id: str) -> Hazard | None:
    return db.scalar(select(Hazard).where(Hazard.mission_id == mission_id, Hazard.client_request_id == request_id))


def as_risk_dict(hazard: Hazard) -> dict:
    return {
        "id": hazard.id, "row": hazard.row, "col": hazard.col,
        "hazard_type": hazard.hazard_type, "label": hazard.label,
        "severity": hazard.severity, "severity_factor": hazard.severity_factor,
        "confidence": hazard.confidence, "anomaly_score": hazard.anomaly_score,
        "radius_cells": hazard.radius_cells, "source_type": hazard.source_type,
        "status": hazard.status, "created_at": hazard.created_at.isoformat() if hazard.created_at else None,
    }
