from dataclasses import replace

import pytest

from app.services.risk.config import RiskConfig, RiskWeights
from app.services.risk.engine import (
    build_risk_map,
    current_risk,
    depth_risk,
    directional_current_risk,
    hazard_components,
    load_demo_environment,
    wave_risk,
)


def test_weights_and_thresholds_are_validated():
    with pytest.raises(ValueError):
        RiskWeights(hazard=0.5)
    with pytest.raises(ValueError):
        RiskWeights(hazard=-0.1, depth=0.7)
    with pytest.raises(ValueError):
        RiskConfig(minimum_operational_depth_m=10, depth_comfort_m=9)


def test_risk_scores_and_navigation_are_bounded():
    environment = load_demo_environment()
    config = RiskConfig()
    grid = build_risk_map(environment, config)
    assert len(grid) == 24 and len(grid[0]) == 36
    assert all(0 <= cell[key] <= 1 for line in grid for cell in line for key in ("hazard_risk", "depth_risk", "wave_risk", "current_risk", "uncertainty_risk", "total_risk"))
    assert not grid[11][18]["navigable"]
    assert grid[19][3]["navigable"]
    assert grid[11][18]["depth_m"] < config.minimum_operational_depth_m
    changed = build_risk_map(environment, replace(config, minimum_operational_depth_m=3.0))
    assert changed[11][18]["navigable"]


def test_hazard_decays_and_unknown_adds_uncertainty():
    hazards = load_demo_environment().hazards
    near, _ = hazard_components(11, 17, hazards)
    medium, _ = hazard_components(11, 21, hazards)
    far, _ = hazard_components(0, 0, hazards)
    assert near > medium > far == 0
    _, unknown_uncertainty = hazard_components(8, 26, hazards)
    assert unknown_uncertainty > 0


def test_depth_wave_and_current_components():
    config = RiskConfig()
    assert depth_risk(4.6, config) > depth_risk(9, config)
    assert wave_risk(1.6, config) > wave_risk(0.5, config)
    assert current_risk(0, 0, config) == 0
    assert directional_current_risk(-0.8, 0, 0, 1, config) > directional_current_risk(0.8, 0, 0, 1, config)
    assert directional_current_risk(0, 0.8, -1, 0, config) < directional_current_risk(0, 0.8, 1, 0, config)
