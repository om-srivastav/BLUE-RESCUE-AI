"""Create deterministic fictional Cyclone Varuna grid fixtures."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "demo-data"
ROWS, COLS = 24, 36


def write(relative: str, value: dict) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


depth = []
ocean = []
for row in range(ROWS):
    depth_row = []
    ocean_row = []
    for col in range(COLS):
        center_distance = abs(row - 11.5)
        value = round(9.4 - 0.42 * center_distance + 0.02 * col, 2)
        if 10 <= row <= 13 and 16 <= col <= 20:
            value = 3.7  # fictional shallow obstruction across central corridor
        if row <= 2 and col >= 28:
            value = 3.4
        depth_row.append(value)
        ocean_row.append({
            "wave_height_m": round(0.45 + 0.025 * col + 0.018 * abs(row - 10) + (0.55 if row >= 17 and col >= 20 else 0), 3),
            "u_current_mps": round(0.10 + 0.012 * col - (0.48 if 7 <= row <= 12 and 13 <= col <= 27 else 0), 3),
            "v_current_mps": round(-0.06 + 0.014 * row, 3),
        })
    depth.append(depth_row)
    ocean.append(ocean_row)

write("bathymetry/grid.json", {"rows": ROWS, "cols": COLS, "source_type": "SIMULATED", "dataset": "Cyclone Varuna deterministic demo bathymetry", "depth_m": depth})
write("ocean/environment-grid.json", {"rows": ROWS, "cols": COLS, "source_type": "SIMULATED", "dataset": "Cyclone Varuna deterministic demo ocean", "cells": ocean})
write("missions/cyclone-varuna.json", {
    "name": "Mission Cyclone Varuna", "source_type": "SIMULATED", "coordinate_system": "SCHEMATIC_GRID_NOT_GEOGRAPHIC",
    "cell_size_m": 50, "start": {"row": 19, "col": 3}, "destination": {"row": 4, "col": 32},
    "start_name": "Survey Base", "destination_name": "Harbor Entrance",
    "hazards": [
        {"id": "Hazard 01", "label": "Possible wreckage", "row": 11, "col": 17, "severity": 1.0, "confidence": 0.91, "radius_cells": 6, "source_type": "DEMO_ANNOTATION"},
        {"id": "Hazard 02", "label": "Marine debris", "row": 15, "col": 24, "severity": 0.7, "confidence": 0.83, "radius_cells": 4, "source_type": "DEMO_ANNOTATION"},
        {"id": "Hazard 03", "label": "Unknown anomaly", "row": 8, "col": 26, "severity": 0.65, "confidence": 0.55, "anomaly_score": 0.88, "radius_cells": 4, "source_type": "DEMO_ANNOTATION"},
    ],
})
