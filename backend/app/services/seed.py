from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hazard import Hazard
from app.models.mission import Mission
import json


DEMO_NAME = "Mission Cyclone Varuna"


def seed_demo(db: Session) -> None:
    mission = db.scalar(select(Mission).where(Mission.name == DEMO_NAME))
    if mission is None:
        mission = Mission(
            name=DEMO_NAME,
            description="Fictional coastal harbor recovery scenario. No operational observations are included in Chunk 1.",
            mode="DEMO",
            status="PLANNING",
            source_type="SIMULATED",
        )
        db.add(mission)
        db.flush()
    fixture = json.loads((settings.blue_demo_data_dir / "missions/cyclone-varuna.json").read_text(encoding="utf-8"))
    type_names = {"Possible wreckage": ("WRECKAGE", "CRITICAL"), "Marine debris": ("DEBRIS", "HIGH"), "Unknown anomaly": ("UNKNOWN_ANOMALY", "MEDIUM")}
    for item in fixture["hazards"]:
        identifier = item["id"]
        if db.get(Hazard, identifier) is not None:
            continue
        hazard_type, severity = type_names[item["label"]]
        db.add(Hazard(
            id=identifier, mission_id=mission.id, row=item["row"], col=item["col"],
            hazard_type=hazard_type, label=item["label"], severity=severity,
            severity_factor=item["severity"], confidence=item["confidence"],
            anomaly_score=item.get("anomaly_score"), radius_cells=item["radius_cells"],
            source_type="DEMO_ANNOTATION", status="ACTIVE", notes="Fictional bundled demo annotation",
        ))
    db.commit()
