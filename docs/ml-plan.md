# BLUE-RESCUE AI — Machine Learning Plan

## ML Team

### Sajid — ML Model & Training Lead

Responsibilities:

- model architecture
- model training
- transfer learning
- hyperparameter tuning
- checkpoint selection
- inference optimization

### Om — ML Data, Evaluation & Integration Lead

Responsibilities:

- ML system audit
- dataset specification
- dataset validation
- preprocessing
- train/validation/test splitting
- evaluation
- experiment tracking
- inference contracts
- backend integration
- ML documentation

---

# Core Rule

Every ML model must answer:

1. What problem does it solve?
2. What data trains it?
3. Where does its output affect BLUE-RESCUE?

---

# P0 — Sonar Intelligence

## Problem

Identify underwater targets or anomalous regions from side-scan sonar imagery.

## Input

Side-scan sonar image.

## Possible Output

- segmentation mask
- bounding box
- target class
- confidence score

## Initial Approach

Use the simplest supervised approach supported by the selected dataset.

Preferred first baseline:

`U-Net segmentation`

## Evaluation

- IoU
- Dice/F1
- Precision
- Recall
- false-negative analysis

---

# P1 — Satellite Flood Segmentation

Input:

Satellite image.

Output:

Water/flood segmentation mask.

Baseline:

U-Net or another lightweight segmentation model.

Metrics:

- IoU
- Dice
- Precision
- Recall

---

# P2 — Satellite Change Detection

Input:

Pre-disaster image + post-disaster image.

Output:

Change mask.

Possible later approach:

- Siamese U-Net
- dedicated change-detection network

---

# P3 — Sonar Anomaly Detection

Possible methods:

- autoencoder
- one-class anomaly detection
- PatchCore-like approach

---

# Non-ML Components

Keep deterministic initially:

- A* routing
- risk fusion
- RouteTrust
- RecoveryCoverage
- bathymetry
- ocean data

---

# First End-to-End ML Goal

Real sonar dataset
→ preprocessing
→ trained model
→ evaluation
→ inference
→ structured result
→ backend
→ frontend