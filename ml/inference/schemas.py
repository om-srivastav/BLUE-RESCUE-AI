from dataclasses import asdict, dataclass
from typing import Literal


AnalysisMode = Literal[
    "TRAINED_ML",
    "CLASSICAL_CV",
    "HEURISTIC",
    "DEMO_ANNOTATION",
]


@dataclass
class DetectionRegion:
    x: int
    y: int
    width: int
    height: int
    label: str
    score: float


@dataclass
class ModelInfo:
    name: str
    version: str
    preprocessing_version: str


@dataclass
class InferenceResult:
    status: str
    task: str
    analysis_mode: AnalysisMode
    detector: str
    width: int
    height: int
    model: ModelInfo | None
    regions: list[DetectionRegion]
    latency_ms: float | None = None
    error_code: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)