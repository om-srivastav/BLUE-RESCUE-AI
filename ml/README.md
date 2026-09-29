# BLUE-RESCUE AI — Machine Learning

This directory contains ML research, dataset tooling, evaluation and inference integration for BLUE-RESCUE AI.

## Current State

The project currently contains:

- classical OpenCV satellite change detection
- heuristic sonar anomaly analysis
- authored sonar demo annotations
- deterministic risk calculation
- A* routing

No trained ML model is currently integrated.

## ML Team

### Sajid
ML Model & Training Lead

### Om
ML Data, Evaluation & Integration Lead

## Development Order

1. Sonar ML baseline
2. Sonar evaluation
3. Sonar inference integration
4. Satellite flood segmentation
5. Satellite change detection
6. Sonar anomaly detection

## Principles

- Never label heuristics as trained ML.
- Never fabricate accuracy.
- Preserve dataset provenance.
- Maintain reproducible train/validation/test splits.
- Never invent geographic coordinates from image predictions.
- Keep A* as the routing foundation.
- Keep risk fusion explainable for V1.
- Keep raw datasets and large weights outside normal Git commits.

See:

- `docs/ml-audit.md`
- `docs/ml-plan.md`
- `docs/dataset-spec-sonar.md`