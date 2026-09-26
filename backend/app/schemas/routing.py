from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class GridPoint(BaseModel):
    row: int
    col: int


class RiskWeightInput(BaseModel):
    hazard: float = Field(default=0.40, ge=0, le=1)
    depth: float = Field(default=0.20, ge=0, le=1)
    wave: float = Field(default=0.15, ge=0, le=1)
    current: float = Field(default=0.15, ge=0, le=1)
    uncertainty: float = Field(default=0.10, ge=0, le=1)

    @model_validator(mode="after")
    def total_one(self):
        if abs(sum(self.model_dump().values()) - 1) > 1e-9:
            raise ValueError("Risk weights must sum to 1")
        return self


class RiskOptions(BaseModel):
    weights: RiskWeightInput = Field(default_factory=RiskWeightInput)
    minimum_operational_depth_m: float = Field(default=4.5, gt=0)
    depth_comfort_m: float = Field(default=9.5, gt=0)
    wave_low_m: float = Field(default=0.4, ge=0)
    wave_high_m: float = Field(default=2.0, gt=0)
    current_reference_mps: float = Field(default=1.0, gt=0)
    routing_risk_aggressiveness: float = Field(default=4.0, ge=0, le=20)

    @model_validator(mode="after")
    def thresholds(self):
        if self.depth_comfort_m <= self.minimum_operational_depth_m or self.wave_high_m <= self.wave_low_m:
            raise ValueError("Upper depth and wave thresholds must exceed lower thresholds")
        return self


class RouteRequest(BaseModel):
    start: GridPoint
    destination: GridPoint
    options: RiskOptions = Field(default_factory=RiskOptions)


class RouteRead(BaseModel):
    route_type: str
    coordinates: list[GridPoint]
    distance_m: float
    average_risk: float
    accumulated_risk: float
    minimum_depth_m: float
    hazards_approached: list[str]
    average_wave_height_m: float
    accumulated_wave_exposure_m: float
    average_directional_current_risk: float
    computation_time_ms: float
    distance_basis: str


class RouteComparison(BaseModel):
    distance_difference_m: float
    average_risk_difference: float
    hazards_avoided: list[str]
    minimum_depth_difference_m: float
    explanation: str


class RouteResult(BaseModel):
    shortest_route: RouteRead
    lower_risk_route: RouteRead
    comparison: RouteComparison
    start: GridPoint | None = None
    destination: GridPoint | None = None
    calculated_at: datetime | None = None
