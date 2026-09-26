from datetime import datetime

from pydantic import BaseModel

from app.schemas.mission import MissionRead
from app.schemas.routing import RiskOptions, RouteResult


class SourceStatus(BaseModel):
    provider: str
    source: str
    status: str
    method: str | None = None
    model_status: str | None = None


class SystemStatus(BaseModel):
    mission_id: int
    satellite: SourceStatus
    sonar: SourceStatus
    bathymetry: SourceStatus
    ocean: SourceStatus
    routing: SourceStatus
    external_providers: SourceStatus


class SatelliteReport(BaseModel):
    source: str
    method: str
    analysis_status: str
    percent_changed: float | None = None
    changed_pixels: int | None = None
    region_count: int | None = None


class SonarReport(BaseModel):
    source: str
    replay_frames: int
    uploaded_frame: bool
    detection_method: str
    anomaly_count: int | None = None
    ml_model_status: str


class HazardReport(BaseModel):
    total: int
    active: int
    resolved: int
    manual: int
    demo: int


class EnvironmentReport(BaseModel):
    available: bool
    coordinate_system: str
    bathymetry_source: str
    ocean_source: str
    rows: int | None = None
    cols: int | None = None
    cell_size_m: float | None = None
    parameters: RiskOptions | None = None


class RiskReport(BaseModel):
    available: bool
    navigable_cells: int | None = None
    average_total_risk: float | None = None
    minimum_total_risk: float | None = None
    maximum_total_risk: float | None = None
    weights: dict[str, float] | None = None


class MissionReport(BaseModel):
    generated_at: datetime
    mission: MissionRead
    coordinate_status: str
    system_status: SystemStatus
    satellite: SatelliteReport
    sonar: SonarReport
    hazards: HazardReport
    environment: EnvironmentReport
    risk: RiskReport
    routing: RouteResult | None
    limitations: list[str]
    disclaimer: str
