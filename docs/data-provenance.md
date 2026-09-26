# Data provenance

| Layer | Source | Meaning |
| --- | --- | --- |
| Cyclone Varuna mission | `SIMULATED` | Fictional demonstration scenario |
| Bathymetry and ocean cells | Bundled simulated JSON | Deterministic numeric demo fields, not measured observations |
| Hazard 01–03 | `DEMO_ANNOTATION` | Fictional bundled labels, not sonar or ML output |
| User-added hazards | `MANUAL` | Operator-entered grid location, type, severity, and certainty |
| Risk grid | Deterministic formula | Derived from active hazards and simulated environment |
| Routes | A* calculation | Derived modeled grid paths, not certified navigation guidance |
| Satellite before/after PNGs | `SIMULATED_DEMO_DATA` | Deterministically generated fictional images |
| Satellite uploads | `USER_UPLOAD` | Local user-provided image pixels; acquisition details unverified |
| Satellite change mask | `CLASSICAL_CV_BASELINE` | Pixel difference and morphology, not ML or damage classification |
| Sonar replay PNGs | `SIMULATED_DEMO_DATA` | Deterministically generated synthetic frames, not live sonar |
| Sonar replay boxes | `DEMO_ANNOTATION` | Authored fixture labels, not detector output |
| Sonar upload | `USER_UPLOAD` | Local user-provided image pixels; acquisition details unverified |
| Sonar uploaded-image boxes | `HEURISTIC_ANOMALY_BASELINE` | Bright-region hints labelled unknown anomaly |

Hazard `created_at` and `updated_at` record local database events. They do not imply a real-world observation time. Manual hazards have no verified operator identity or measured latitude/longitude. Demo row/column locations are schematic. Resolved records remain visible and cease contributing to risk.

## Status vocabulary

- **SIMULATED DEMO DATA**: bundled fictional bathymetry, ocean, satellite, and sonar pixels. The local provider reads them; it does not make them measured data.
- **USER UPLOADED**: pixels saved to the local mission cache. Acquisition location, time, instrument, and ownership are not verified.
- **DEMO ANNOTATION / MISSION REPLAY**: authored sonar boxes in synthetic recorded frames. They are not model predictions or a live feed.
- **HEURISTIC**: simple image-processing output for uploaded sonar. Scores are uncalibrated and regions remain `Unknown anomaly`.
- **LOCAL PROVIDER**: the adapter reads bundled files or the local cache. It makes no external request.
- **MODEL NOT CONFIGURED**: satellite and sonar ML adapters have no trained weights and return no prediction.

The status panel and on-demand report expose these distinctions. Report generation time means the snapshot was assembled then; it does not imply observation time. Satellite change statistics in the report are recomputed from current images and labelled `COMPUTED_ON_DEMAND`.
