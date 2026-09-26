"""Regenerate the deterministic fictional PNG fixtures (requires backend image deps)."""
import json
from pathlib import Path

import cv2
import numpy as np

root = Path(__file__).resolve().parents[1] / "demo-data"
sat = root / "satellite"
sonar = root / "sonar"
sat.mkdir(parents=True, exist_ok=True)
sonar.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(2026)
base = np.zeros((256, 384, 3), np.uint8)
base[:] = (82, 75, 42)
noise = rng.integers(-9, 10, (256, 384, 1), dtype=np.int16)
base = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
cv2.rectangle(base, (0, 0), (100, 256), (66, 109, 98), -1)
cv2.line(base, (110, 20), (340, 210), (140, 125, 105), 12)
cv2.rectangle(base, (142, 83), (185, 109), (190, 178, 143), -1)
cv2.putText(base, "FICTIONAL DEMO", (8, 245), cv2.FONT_HERSHEY_SIMPLEX, .52, (230, 230, 230), 1)
after = base.copy()
cv2.rectangle(after, (202, 105), (244, 134), (205, 181, 130), -1)
cv2.circle(after, (296, 174), 18, (172, 155, 121), -1)
cv2.imwrite(str(sat / "before.png"), base)
cv2.imwrite(str(sat / "after.png"), after)

frames = []
for i in range(5):
    image = rng.integers(16, 54, (240, 360), dtype=np.uint8)
    for y in range(25, 240, 34):
        cv2.line(image, (0, y), (359, y + i * 2), 65, 1)
    x, y = 75 + i * 48, 98 + (i % 2) * 35
    cv2.ellipse(image, (x, y), (18, 9), 12, 0, 360, 225, -1)
    cv2.GaussianBlur(image, (3, 3), 0, dst=image)
    name = f"frame-{i+1:02}.png"
    cv2.imwrite(str(sonar / name), image)
    frames.append({"name": name, "frame_number": i + 1, "width": 360, "height": 240,
                   "metadata": {"scenario": "Fictional recorded survey replay", "sample_index": i + 1},
                   "annotations": [{"x": x - 20, "y": y - 12, "width": 40, "height": 24,
                                    "label": "Synthetic echo annotation", "source_type": "DEMO_ANNOTATION"}]})
(sonar / "annotations.json").write_text(json.dumps({"frames": frames}, indent=2), encoding="utf-8")
