"""Read-only, on-demand mission snapshot for the status panel and printable report."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.mission import Mission, utc_now
from app.models.route import RouteCalculation
from app.repositories.hazards import list_hazards
from app.schemas.report import (EnvironmentReport, HazardReport, MissionReport, RiskReport,
                                SatelliteReport, SonarReport, SourceStatus, SystemStatus)
from app.schemas.routing import RiskOptions
from app.services.imagery import ClassicalChangeDetector, HeuristicAnomalyDetector, read_image, source_path
from app.services.providers import LocalBathymetryProvider, LocalOceanProvider, LocalSatelliteProvider, LocalSonarProvider
from app.services.risk.demo import configuration, mission_environment
from app.services.risk.engine import build_risk_map


DISCLAIMER = "BLUE-RESCUE AI is an academic decision-support prototype. It is not a certified maritime navigation or emergency-response system."


def is_demo(mission: Mission) -> bool:
    return mission.name == "Mission Cyclone Varuna" and mission.mode == "DEMO" and mission.source_type == "SIMULATED"


def system_status(mission: Mission) -> SystemStatus:
    satellite = LocalSatelliteProvider().pair(mission.id, "uploaded")
    uploaded_pair = satellite.before.is_file() and satellite.after.is_file()
    uploaded_sonar = source_path(mission.id, "sonar", "uploaded", "frame").is_file()
    demo = is_demo(mission)
    return SystemStatus(
        mission_id=mission.id,
        satellite=SourceStatus(provider="LOCAL", source="USER_UPLOAD" if uploaded_pair else "SIMULATED_DEMO_DATA" if demo else "NONE",
                               status="AVAILABLE" if uploaded_pair or demo else "UNAVAILABLE", method="CLASSICAL_CV_BASELINE", model_status="MODEL_NOT_CONFIGURED"),
        sonar=SourceStatus(provider="LOCAL", source="MISSION_REPLAY + USER_UPLOAD" if demo and uploaded_sonar else "MISSION_REPLAY" if demo else "USER_UPLOAD" if uploaded_sonar else "NONE",
                           status="AVAILABLE" if demo or uploaded_sonar else "UNAVAILABLE", method="HEURISTIC_ANOMALY_BASELINE" if uploaded_sonar else "DEMO_ANNOTATIONS" if demo else None,
                           model_status="MODEL_NOT_CONFIGURED"),
        bathymetry=SourceStatus(provider="LOCAL", source="SIMULATED_DEMO_DATA" if demo else "NONE", status="AVAILABLE" if demo else "UNAVAILABLE"),
        ocean=SourceStatus(provider="LOCAL", source="SIMULATED_DEMO_DATA" if demo else "NONE", status="AVAILABLE" if demo else "UNAVAILABLE"),
        routing=SourceStatus(provider="LOCAL", source="LOCAL_COMPUTATION" if demo else "NONE", status="AVAILABLE" if demo else "UNAVAILABLE", method="A_STAR" if demo else None),
        external_providers=SourceStatus(provider="EXTERNAL", source="NONE", status="NOT_CONFIGURED"),
    )


def build_report(db: Session, mission: Mission) -> MissionReport:
    status = system_status(mission)
    demo = is_demo(mission)
    hazards = list_hazards(db, mission.id)
    latest = db.scalar(select(RouteCalculation).where(RouteCalculation.mission_id == mission.id).order_by(RouteCalculation.id.desc()))
    options = RiskOptions.model_validate(latest.result.get("_risk_options", {})) if latest and demo else RiskOptions()

    satellite = SatelliteReport(source=status.satellite.source, method="CLASSICAL_CV_BASELINE", analysis_status="UNAVAILABLE")
    if status.satellite.status == "AVAILABLE":
        pair = LocalSatelliteProvider().pair(mission.id, "uploaded" if status.satellite.source == "USER_UPLOAD" else "demo")
        try:
            result = ClassicalChangeDetector().analyze(read_image(pair.before), read_image(pair.after))
            satellite = SatelliteReport(source=pair.provenance.source_type, method=result["detector"],
                                        analysis_status="COMPUTED_ON_DEMAND", percent_changed=result["percent_changed"],
                                        changed_pixels=result["changed_pixels"], region_count=len(result["regions"]))
        except HTTPException as error:
            satellite = SatelliteReport(source=pair.provenance.source_type, method="CLASSICAL_CV_BASELINE",
                                        analysis_status=error.detail.get("code", "ANALYSIS_UNAVAILABLE"))

    replay_frames = len(LocalSonarProvider().replay().frames) if demo else 0
    uploaded_sonar = source_path(mission.id, "sonar", "uploaded", "frame").is_file()
    sonar = SonarReport(source=status.sonar.source, replay_frames=replay_frames, uploaded_frame=uploaded_sonar,
                        detection_method=status.sonar.method or "NONE", ml_model_status="MODEL_NOT_CONFIGURED")
    if uploaded_sonar:
        result = HeuristicAnomalyDetector().analyze(read_image(source_path(mission.id, "sonar", "uploaded", "frame")))
        sonar.anomaly_count = result["anomaly_count"]

    environment = EnvironmentReport(available=False, coordinate_system="NO_GRID", bathymetry_source="NONE", ocean_source="NONE")
    risk = RiskReport(available=False)
    routing = None
    if demo:
        bathy = LocalBathymetryProvider().grid()
        ocean = LocalOceanProvider().grid()
        environment = EnvironmentReport(available=True, coordinate_system="SCHEMATIC_GRID_NOT_GEOGRAPHIC",
                                        bathymetry_source=bathy.provenance.source_type, ocean_source=ocean.provenance.source_type,
                                        rows=bathy.rows, cols=bathy.cols, cell_size_m=50.0, parameters=options)
        grid = build_risk_map(mission_environment(db, mission.id), configuration(options))
        navigable = [cell["total_risk"] for row in grid for cell in row if cell["navigable"]]
        risk = RiskReport(available=True, navigable_cells=len(navigable), average_total_risk=round(sum(navigable) / len(navigable), 5),
                          minimum_total_risk=min(navigable), maximum_total_risk=max(navigable), weights=options.weights.model_dump())
        if latest:
            routing = {**latest.result, "start": latest.start, "destination": latest.destination, "calculated_at": latest.created_at}

    return MissionReport(
        generated_at=utc_now(), mission=mission, coordinate_status="SCHEMATIC_GRID_NOT_GEOGRAPHIC" if demo else "AOI_METADATA_ONLY",
        system_status=status, satellite=satellite, sonar=sonar,
        hazards=HazardReport(total=len(hazards), active=sum(h.status == "ACTIVE" for h in hazards),
                             resolved=sum(h.status == "RESOLVED" for h in hazards),
                             manual=sum(h.source_type == "MANUAL" for h in hazards), demo=sum(h.source_type == "DEMO_ANNOTATION" for h in hazards)),
        environment=environment, risk=risk, routing=routing,
        limitations=["Simulated grid coordinates and modeled distances are not geographic measurements.",
                     "Satellite pixel differences are a classical baseline, not damage identification.",
                     "Sonar replay annotations are fictional; uploaded-image heuristic is not object classification.",
                     "No external data provider or trained ML model is configured."], disclaimer=DISCLAIMER,
    )
