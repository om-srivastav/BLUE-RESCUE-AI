"""Small typed seams around bundled data; external providers are intentionally unavailable."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from app.core.config import settings


class ProviderNotConfigured(Exception):
    code = "NOT_CONFIGURED"

    def __init__(self, family: str):
        super().__init__(f"{family} external provider is not configured")
        self.family = family


class ProviderInfo(BaseModel):
    provider: str = "LOCAL"
    source_type: str
    status: str = "AVAILABLE"


class SatellitePair(BaseModel):
    before: Path
    after: Path
    provenance: ProviderInfo


class OceanCell(BaseModel):
    wave_height_m: float
    u_current_mps: float
    v_current_mps: float


class OceanGrid(BaseModel):
    rows: int = Field(gt=0)
    cols: int = Field(gt=0)
    cells: list[list[OceanCell]]
    provenance: ProviderInfo


class BathymetryGrid(BaseModel):
    rows: int = Field(gt=0)
    cols: int = Field(gt=0)
    depth_m: list[list[float]]
    provenance: ProviderInfo


class SonarAnnotation(BaseModel):
    x: int
    y: int
    width: int
    height: int
    label: str
    source_type: str


class SonarFrameMetadata(BaseModel):
    scenario: str
    sample_index: int


class SonarFrame(BaseModel):
    name: str
    frame_number: int
    width: int
    height: int
    metadata: SonarFrameMetadata
    annotations: list[SonarAnnotation]


class SonarReplay(BaseModel):
    frames: list[SonarFrame]
    provenance: ProviderInfo


class SatelliteProvider(Protocol):
    def pair(self, mission_id: int, source: str) -> SatellitePair: ...


class OceanProvider(Protocol):
    def grid(self) -> OceanGrid: ...


class BathymetryProvider(Protocol):
    def grid(self) -> BathymetryGrid: ...


class SonarProvider(Protocol):
    def replay(self) -> SonarReplay: ...


class LocalSatelliteProvider:
    def pair(self, mission_id: int, source: str = "demo") -> SatellitePair:
        if source == "demo":
            folder = settings.blue_demo_data_dir / "satellite"
            provenance = ProviderInfo(source_type="SIMULATED_DEMO_DATA")
        elif source == "uploaded":
            folder = settings.blue_cache_dir / "imagery" / str(mission_id) / "satellite"
            provenance = ProviderInfo(source_type="USER_UPLOAD")
        else:
            raise ValueError("Source must be demo or uploaded")
        return SatellitePair(before=folder / "before.png", after=folder / "after.png", provenance=provenance)


class LocalOceanProvider:
    def grid(self) -> OceanGrid:
        payload = json.loads((settings.blue_demo_data_dir / "ocean" / "environment-grid.json").read_text(encoding="utf-8"))
        return OceanGrid(rows=payload["rows"], cols=payload["cols"], cells=payload["cells"],
                         provenance=ProviderInfo(source_type="SIMULATED_DEMO_DATA"))


class LocalBathymetryProvider:
    def grid(self) -> BathymetryGrid:
        payload = json.loads((settings.blue_demo_data_dir / "bathymetry" / "grid.json").read_text(encoding="utf-8"))
        return BathymetryGrid(rows=payload["rows"], cols=payload["cols"], depth_m=payload["depth_m"],
                              provenance=ProviderInfo(source_type="SIMULATED_DEMO_DATA"))


class LocalSonarProvider:
    def replay(self) -> SonarReplay:
        payload = json.loads((settings.blue_demo_data_dir / "sonar" / "annotations.json").read_text(encoding="utf-8"))
        return SonarReplay(frames=payload["frames"], provenance=ProviderInfo(source_type="MISSION_REPLAY"))


class ExternalSatelliteProvider:
    def pair(self, mission_id: int, source: str = "external") -> SatellitePair:
        raise ProviderNotConfigured("Satellite")


class ExternalOceanProvider:
    def grid(self) -> OceanGrid:
        raise ProviderNotConfigured("Ocean")


class ExternalBathymetryProvider:
    def grid(self) -> BathymetryGrid:
        raise ProviderNotConfigured("Bathymetry")
