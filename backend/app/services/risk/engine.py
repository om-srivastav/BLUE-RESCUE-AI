import json
from dataclasses import dataclass
from math import hypot
from pathlib import Path

from app.core.config import settings
from app.services.providers import LocalBathymetryProvider, LocalOceanProvider
from app.services.risk.config import RiskConfig


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def depth_risk(depth_m: float, config: RiskConfig) -> float:
    return clamp((config.depth_comfort_m - depth_m) / (config.depth_comfort_m - config.minimum_operational_depth_m))


def wave_risk(wave_height_m: float, config: RiskConfig) -> float:
    return clamp((wave_height_m - config.wave_low_m) / (config.wave_high_m - config.wave_low_m))


def current_risk(u: float, v: float, config: RiskConfig) -> float:
    """Neutral heading estimate for a map cell; routing substitutes heading-aware risk."""
    return clamp(hypot(u, v) / (2 * config.current_reference_mps))


def directional_current_risk(u: float, v: float, dr: int, dc: int, config: RiskConfig) -> float:
    """0 for assisting flow, 0.5 for cross flow, 1 for opposing flow at reference speed."""
    magnitude = hypot(u, v)
    if magnitude == 0:
        return 0.0
    # Grid row increases south; v is positive north. dc is positive east.
    alignment = (u * dc - v * dr) / (magnitude * hypot(dr, dc))
    return clamp((magnitude / config.current_reference_mps) * (1 - alignment) / 2)


def hazard_components(row: int, col: int, hazards: list[dict]) -> tuple[float, float]:
    hazard_score = 0.0
    uncertainty = 0.0
    for hazard in hazards:
        if hazard.get("status", "ACTIVE") != "ACTIVE":
            continue
        distance = hypot(row - hazard["row"], col - hazard["col"])
        radius = hazard["radius_cells"]
        if distance >= radius:
            continue
        decay = 1 - distance / radius
        confidence = hazard["confidence"]
        severity_factor = hazard["severity_factor"] if "severity_factor" in hazard else hazard["severity"]
        hazard_score += severity_factor * confidence * decay
        if hazard.get("hazard_type") == "UNKNOWN_ANOMALY" or hazard["label"] == "Unknown anomaly":
            anomaly_score = hazard.get("anomaly_score")
            uncertainty += (anomaly_score if anomaly_score is not None else 1 - confidence) * decay
        else:
            uncertainty += (1 - confidence) * severity_factor * decay
    return clamp(hazard_score), clamp(uncertainty)


@dataclass(frozen=True)
class DemoEnvironment:
    rows: int
    cols: int
    depth: list[list[float]]
    ocean: list[list[dict]]
    hazards: list[dict]
    start: dict
    destination: dict
    start_name: str
    destination_name: str
    cell_size_m: float


def load_demo_environment(data_dir: Path | None = None) -> DemoEnvironment:
    directory = data_dir or settings.blue_demo_data_dir
    if data_dir is None:
        bathy = LocalBathymetryProvider().grid().model_dump()
        ocean = LocalOceanProvider().grid().model_dump()
    else:
        bathy = json.loads((directory / "bathymetry/grid.json").read_text(encoding="utf-8"))
        ocean = json.loads((directory / "ocean/environment-grid.json").read_text(encoding="utf-8"))
    mission = json.loads((directory / "missions/cyclone-varuna.json").read_text(encoding="utf-8"))
    rows, cols = bathy["rows"], bathy["cols"]
    if rows != ocean["rows"] or cols != ocean["cols"] or len(bathy["depth_m"]) != rows or len(ocean["cells"]) != rows:
        raise ValueError("Bundled bathymetry and ocean grids do not align")
    if any(len(line) != cols for line in bathy["depth_m"]) or any(len(line) != cols for line in ocean["cells"]):
        raise ValueError("Bundled grid row length mismatch")
    return DemoEnvironment(rows, cols, bathy["depth_m"], ocean["cells"], mission["hazards"], mission["start"], mission["destination"], mission["start_name"], mission["destination_name"], mission["cell_size_m"])


def build_risk_map(environment: DemoEnvironment, config: RiskConfig) -> list[list[dict]]:
    grid = []
    weights = config.weights
    for row in range(environment.rows):
        line = []
        for col in range(environment.cols):
            depth = environment.depth[row][col]
            ocean = environment.ocean[row][col]
            hazard, uncertainty = hazard_components(row, col, environment.hazards)
            depth_score = depth_risk(depth, config)
            wave_score = wave_risk(ocean["wave_height_m"], config)
            current_score = current_risk(ocean["u_current_mps"], ocean["v_current_mps"], config)
            total = clamp(weights.hazard * hazard + weights.depth * depth_score + weights.wave * wave_score + weights.current * current_score + weights.uncertainty * uncertainty)
            line.append({"row": row, "col": col, "depth_m": depth, **ocean, "hazard_risk": round(hazard, 5), "depth_risk": round(depth_score, 5), "wave_risk": round(wave_score, 5), "current_risk": round(current_score, 5), "uncertainty_risk": round(uncertainty, 5), "total_risk": round(total, 5), "navigable": depth >= config.minimum_operational_depth_m})
        grid.append(line)
    return grid
