from datetime import datetime
from enum import StrEnum
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.routing import RouteResult


class HazardType(StrEnum):
    WRECKAGE = "WRECKAGE"
    DEBRIS = "DEBRIS"
    SUBMERGED_OBSTRUCTION = "SUBMERGED_OBSTRUCTION"
    KNOWN_INFRASTRUCTURE = "KNOWN_INFRASTRUCTURE"
    UNKNOWN_ANOMALY = "UNKNOWN_ANOMALY"
    OTHER = "OTHER"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HazardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class HazardCreate(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    hazard_type: HazardType
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    anomaly_score: float | None = Field(default=None, ge=0, le=1)
    notes: str = Field(default="", max_length=1000)
    source_type: Literal["MANUAL"] = "MANUAL"
    client_request_id: UUID | None = None


class HazardStatusUpdate(BaseModel):
    status: HazardStatus


class HazardRead(BaseModel):
    id: str
    mission_id: int
    row: int
    col: int
    latitude: float | None
    longitude: float | None
    hazard_type: HazardType
    label: str
    severity: Severity
    severity_factor: float
    confidence: float
    anomaly_score: float | None
    radius_cells: float
    source_type: str
    status: HazardStatus
    notes: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RouteSummary(BaseModel):
    distance_m: float
    average_risk: float
    accumulated_risk: float


class HazardImpact(BaseModel):
    risk_recalculated: bool
    route_recalculated: bool
    reason: str | None = None
    previous_route_affected: bool | None = None
    route_changed: bool | None = None
    previous_route: RouteSummary | None = None
    updated_route: RouteSummary | None = None
    retained_path_average_risk: float | None = None
    explanation: str


class HazardMutationResult(BaseModel):
    hazard: HazardRead
    impact: HazardImpact
    risk_map: dict
    routes: RouteResult | None = None
