from dataclasses import replace

from sqlalchemy.orm import Session

from app.repositories.hazards import as_risk_dict, list_hazards
from app.schemas.routing import RiskOptions
from app.services.risk.config import RiskConfig, RiskWeights
from app.services.risk.engine import DemoEnvironment, build_risk_map, load_demo_environment


def configuration(options: RiskOptions) -> RiskConfig:
    return RiskConfig(
        weights=RiskWeights(**options.weights.model_dump()),
        minimum_operational_depth_m=options.minimum_operational_depth_m,
        depth_comfort_m=options.depth_comfort_m,
        wave_low_m=options.wave_low_m,
        wave_high_m=options.wave_high_m,
        current_reference_mps=options.current_reference_mps,
        routing_risk_aggressiveness=options.routing_risk_aggressiveness,
    )


def mission_environment(db: Session, mission_id: int) -> DemoEnvironment:
    return replace(load_demo_environment(), hazards=[as_risk_dict(hazard) for hazard in list_hazards(db, mission_id)])


def map_payload(environment: DemoEnvironment, options: RiskOptions) -> dict:
    config = configuration(options)
    return {
        "rows": environment.rows, "cols": environment.cols, "cell_size_m": environment.cell_size_m,
        "coordinate_system": "SCHEMATIC_GRID_NOT_GEOGRAPHIC", "source_type": "SIMULATED",
        "depth_threshold_label": "SIMULATED_OPERATIONAL_DEPTH_THRESHOLD",
        "minimum_operational_depth_m": config.minimum_operational_depth_m,
        "weights": options.weights.model_dump(), "cells": build_risk_map(environment, config),
        "hazards": environment.hazards, "start": environment.start, "destination": environment.destination,
        "start_name": environment.start_name, "destination_name": environment.destination_name,
        "provenance": {"bathymetry": "BUNDLED SIMULATED DEMO DATA", "ocean": "BUNDLED SIMULATED DEMO DATA", "hazards": "BUNDLED DEMO ANNOTATIONS + OPERATOR-ENTERED MANUAL RECORDS"},
    }
