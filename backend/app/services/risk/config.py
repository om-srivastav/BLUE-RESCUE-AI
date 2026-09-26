from dataclasses import dataclass, field
from math import isclose


@dataclass(frozen=True)
class RiskWeights:
    hazard: float = 0.40
    depth: float = 0.20
    wave: float = 0.15
    current: float = 0.15
    uncertainty: float = 0.10

    def __post_init__(self) -> None:
        values = (self.hazard, self.depth, self.wave, self.current, self.uncertainty)
        if any(not 0 <= value <= 1 for value in values) or not isclose(sum(values), 1.0, abs_tol=1e-9):
            raise ValueError("Risk weights must each be in [0, 1] and sum to 1")


@dataclass(frozen=True)
class RiskConfig:
    weights: RiskWeights = field(default_factory=RiskWeights)
    minimum_operational_depth_m: float = 4.5
    depth_comfort_m: float = 9.5
    wave_low_m: float = 0.4
    wave_high_m: float = 2.0
    current_reference_mps: float = 1.0
    cell_size_m: float = 50.0
    routing_risk_aggressiveness: float = 4.0

    def __post_init__(self) -> None:
        if not (0 < self.minimum_operational_depth_m < self.depth_comfort_m):
            raise ValueError("Depth thresholds must be positive and increasing")
        if not (0 <= self.wave_low_m < self.wave_high_m):
            raise ValueError("Wave thresholds must be increasing")
        if self.current_reference_mps <= 0 or self.cell_size_m <= 0 or self.routing_risk_aggressiveness < 0:
            raise ValueError("Current scale and cell size must be positive; routing aggressiveness must be nonnegative")
