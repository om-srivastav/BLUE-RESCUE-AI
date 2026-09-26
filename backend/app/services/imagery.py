"""Offline image analysis. All scores are illustrative research baselines."""
from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
from fastapi import HTTPException

from app.core.config import settings
from app.services.providers import LocalSatelliteProvider, LocalSonarProvider

MAX_BYTES = 10 * 1024 * 1024
DEMO_NAME = "Mission Cyclone Varuna"


def problem(code: str, message: str, status: int = 422) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def decode_image(data: bytes) -> np.ndarray:
    if not data or len(data) > MAX_BYTES:
        raise problem("INVALID_IMAGE_SIZE", "Image must be between 1 byte and 10 MB")
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.shape[0] > 4096 or image.shape[1] > 4096:
        raise problem("INVALID_IMAGE", "Upload a valid PNG or JPEG no larger than 4096 pixels per side")
    return image


def png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise problem("IMAGE_ENCODING_FAILED", "Could not encode image", 500)
    return encoded.tobytes()


def data_url(image: np.ndarray) -> str:
    return "data:image/png;base64," + base64.b64encode(png(image)).decode("ascii")


def uploaded_path(mission_id: int, family: str, role: str) -> Path:
    return settings.blue_cache_dir / "imagery" / str(mission_id) / family / f"{role}.png"


def demo_path(family: str, role: str) -> Path:
    return settings.blue_demo_data_dir / family / f"{role}.png"


def source_path(mission_id: int, family: str, source: str, role: str) -> Path:
    if family == "satellite":
        pair = LocalSatelliteProvider().pair(mission_id, source)
        return pair.before if role == "before" else pair.after
    if source == "demo":
        return demo_path(family, role)
    if source == "uploaded":
        return uploaded_path(mission_id, family, role)
    raise problem("INVALID_SOURCE", "Source must be demo or uploaded")


def read_image(path: Path) -> np.ndarray:
    if not path.is_file():
        raise problem("IMAGE_NOT_FOUND", "Requested image is not available", 404)
    return decode_image(path.read_bytes())


def save_upload(mission_id: int, family: str, role: str, data: bytes) -> Path:
    image = decode_image(data)
    path = uploaded_path(mission_id, family, role)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png(image))
    return path


class SatelliteChangeDetector(ABC):
    @abstractmethod
    def analyze(self, before: np.ndarray, after: np.ndarray) -> dict: ...


class ClassicalChangeDetector(SatelliteChangeDetector):
    def analyze(self, before: np.ndarray, after: np.ndarray) -> dict:
        if before.shape != after.shape:
            raise problem("DIMENSION_MISMATCH", "Before and after images must have the same dimensions")
        a = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        difference = cv2.absdiff(a, b)
        smoothed = cv2.GaussianBlur(difference, (5, 5), 0)
        _, mask = cv2.threshold(smoothed, 30, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        count = int(cv2.countNonZero(mask))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            if cv2.contourArea(contour) < 20:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            regions.append({"x": x, "y": y, "width": w, "height": h, "area_pixels": int(cv2.contourArea(contour))})
        return {"detector": "CLASSICAL_CV_BASELINE", "changed_pixels": count,
                "percent_changed": round(100 * count / mask.size, 3), "regions": regions,
                "mask_data_url": data_url(mask), "width": int(mask.shape[1]), "height": int(mask.shape[0])}


class MLChangeDetector(SatelliteChangeDetector):
    def analyze(self, before: np.ndarray, after: np.ndarray) -> dict:
        raise problem("MODEL_NOT_CONFIGURED", "No satellite ML model is configured", 409)


class SonarDetector(ABC):
    @abstractmethod
    def analyze(self, image: np.ndarray) -> dict: ...


class HeuristicAnomalyDetector(SonarDetector):
    def analyze(self, image: np.ndarray) -> dict:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, bright = cv2.threshold(blurred, 185, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            area = cv2.contourArea(contour)
            if area < 25:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            regions.append({"x": x, "y": y, "width": w, "height": h,
                            "label": "Unknown anomaly", "score": round(min(1.0, area / 500), 3)})
        return {"detector": "HEURISTIC_ANOMALY_BASELINE", "output_source": "HEURISTIC",
                "regions": regions, "anomaly_count": len(regions),
                "anomaly_score": max((r["score"] for r in regions), default=0.0),
                "width": int(gray.shape[1]), "height": int(gray.shape[0])}


class DemoAnnotationDetector(SonarDetector):
    def __init__(self, frame_name: str):
        self.frame_name = frame_name

    def analyze(self, image: np.ndarray) -> dict:
        frame = next((item for item in replay_metadata() if item["name"] == self.frame_name), None)
        if frame is None:
            raise problem("FRAME_NOT_FOUND", "Unknown demo frame", 404)
        return {"detector": "DEMO_ANNOTATIONS", "output_source": "DEMO / MISSION_REPLAY",
                "regions": frame["annotations"], "frame_name": self.frame_name}


class MLSonarDetector(SonarDetector):
    def analyze(self, image: np.ndarray) -> dict:
        raise problem("MODEL_NOT_CONFIGURED", "No sonar ML model is configured", 409)


def replay_metadata() -> list[dict]:
    return [frame.model_dump() for frame in LocalSonarProvider().replay().frames]
