# BLUE-RESCUE AI — ML System Audit

## Owner

Om Srivastav

Role: ML Data, Evaluation & Integration

Branch: `om/ml-data-evaluation`

---

## Purpose

This document records the actual machine-learning state of BLUE-RESCUE AI before trained models are introduced.

It separates:

- trained machine learning
- classical computer vision
- heuristics
- demo annotations
- deterministic algorithms
- placeholders

No component should be labelled as trained ML unless an actual trained model performs inference.

---

# 1. Satellite Analysis

Current implementation:

`backend/app/services/imagery.py`

Current detector:

`ClassicalChangeDetector`

Current method:

- grayscale conversion
- absolute image difference
- Gaussian blur
- thresholding
- morphological processing
- contour extraction

Classification:

`CLASSICAL COMPUTER VISION`

This is not trained machine learning.

Current ML placeholder:

`MLChangeDetector`

Current state:

`MODEL_NOT_CONFIGURED`

Therefore, BLUE-RESCUE currently has no trained satellite ML model.

---

# 2. Sonar Analysis

## Demo Replay

Current detector:

`DemoAnnotationDetector`

The bundled sonar replay uses authored demo annotations.

Classification:

`DEMO / MISSION REPLAY`

These are not ML predictions.

## Uploaded Sonar Analysis

Current detector:

`HeuristicAnomalyDetector`

Current processing:

- grayscale conversion
- Gaussian blur
- brightness thresholding
- contour extraction
- area-based anomaly score

Classification:

`HEURISTIC`

The anomaly score is not a calibrated ML confidence score.

## Sonar ML Placeholder

Current detector:

`MLSonarDetector`

Current state:

`MODEL_NOT_CONFIGURED`

Therefore, BLUE-RESCUE currently has no trained sonar model.

---

# 3. Risk Engine

Current risk calculation is deterministic.

Inputs include:

- hazards
- bathymetric depth
- waves
- ocean current
- uncertainty

Classification:

`RULE-BASED / DETERMINISTIC`

This should remain deterministic for ML V1.

---

# 4. Routing

Current routing uses A*.

Classification:

`CLASSICAL GRAPH SEARCH`

A* is not machine learning and should remain the routing foundation.

---

# 5. Current ML Gaps

The repository currently has no:

1. trained sonar model
2. trained satellite model
3. training pipeline
4. dataset manifest
5. reproducible dataset split
6. experiment tracking
7. trained model checkpoint used for inference
8. evaluation report
9. model card
10. trained-model backend adapter

---

# 6. ML Priority

## P0 — Sonar Intelligence

Real side-scan-sonar data
→ preprocessing
→ trained model
→ evaluation
→ inference
→ backend-compatible result

## P1 — Satellite Flood / Water Segmentation

## P2 — Satellite Change Detection

## P3 — Sonar Unknown Anomaly Detection

---

# 7. Components That Stay Non-ML Initially

- A* routing
- deterministic risk fusion
- RecoveryCoverage
- RouteTrust
- bathymetry
- ocean data

---

# 8. First ML Success Criterion

Real recorded sonar data
→ reproducible preprocessing
→ trained model
→ measured metrics
→ inference output
→ backend-compatible structured result
→ frontend-visible result

No fabricated accuracy, confidence or geographic coordinates should be used.

---

# 9. Scientific Boundary

ML inference may produce:

- class
- score
- bounding box
- segmentation mask

ML must not invent latitude or longitude.

Geographic hazard creation requires appropriate vessel/sensor metadata and backend geospatial processing.