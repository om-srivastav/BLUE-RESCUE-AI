from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MissionMode(StrEnum):
    DEMO = "DEMO"
    REAL_DATA = "REAL_DATA"
    OFFLINE_CACHED = "OFFLINE_CACHED"


class SourceType(StrEnum):
    DEMO = "DEMO"
    SIMULATED = "SIMULATED"
    UPLOADED = "UPLOADED"
    REAL_DATASET = "REAL_DATASET"
    MISSION_REPLAY = "MISSION_REPLAY"
    LATEST_AVAILABLE = "LATEST_AVAILABLE"
    NEAR_REAL_TIME = "NEAR_REAL_TIME"
    FORECAST = "FORECAST"
    CACHED = "CACHED"
    HEURISTIC = "HEURISTIC"
    ML_INFERENCE = "ML_INFERENCE"
    SIMULATED_GEOREFERENCE = "SIMULATED_GEOREFERENCE"
    STATIC_REFERENCE = "STATIC_REFERENCE"
    MANUAL = "MANUAL"


class DataProvenance(BaseModel):
    source_type: SourceType
    provider: str | None = None
    dataset: str | None = None
    observed_at: datetime | None = None
    valid_at: datetime | None = None
    fetched_at: datetime | None = None
    cached_at: datetime | None = None
    age_seconds: float | None = None
    model_name: str | None = None
    model_version: str | None = None
    notes: str | None = None


class MissionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    mode: MissionMode = MissionMode.DEMO


class MissionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    status: str | None = Field(default=None, min_length=1, max_length=20)


class AOICreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    min_latitude: float = Field(ge=-90, le=90)
    max_latitude: float = Field(ge=-90, le=90)
    min_longitude: float = Field(ge=-180, le=180)
    max_longitude: float = Field(ge=-180, le=180)
    crs: str = "EPSG:4326"

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.crs != "EPSG:4326" or self.min_latitude >= self.max_latitude or self.min_longitude >= self.max_longitude:
            raise ValueError("AOI requires EPSG:4326 and increasing latitude/longitude bounds")
        return self


class AOIRead(AOICreate):
    id: int
    mission_id: int
    model_config = ConfigDict(from_attributes=True)


class MissionRead(BaseModel):
    id: int
    name: str
    description: str
    mode: MissionMode
    status: str
    source_type: SourceType
    created_at: datetime
    updated_at: datetime
    aois: list[AOIRead]
    model_config = ConfigDict(from_attributes=True)
