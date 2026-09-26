# Future development handoff

The current foundation is an offline academic prototype. Cyclone Varuna uses a **schematic 24 × 36 grid**, fictional hazards and imagery, and modeled 50 m cells. No real-data adapter, trained model, live sonar feed, or geographic route exists. Work on new capabilities in separate feature branches; preserve the existing deterministic demo and its tests as a regression baseline.

## Map and geographic coordinates

Current UI: `frontend/src/components/mission/DemoPlanner.tsx` renders the schematic grid. `backend/app/services/risk/engine.py` defines `DemoEnvironment`; `backend/app/services/risk/demo.py` builds its API payload. Mission AOIs already store EPSG:4326 bounds in `backend/app/models/mission.py`, but the demo grid's row/column positions have **no measured latitude/longitude**.

For a real map, add a separate georeferenced environment schema with CRS, origin, resolution, and cell-to-coordinate transformation. Then add a Leaflet or equivalent geographic view and maritime base layers in the frontend, render AOIs in geographic coordinates, and translate route cells into measured positions. Validate datums, land masks, and distance calculations. Keep demo grid coordinates visually distinct; do not assign invented latitudes/longitudes to its cells. Update routing distance calculations only after the georeference and scale are verified.

## Satellite sources and change detection

The current classical grayscale/absolute-difference detector and the unavailable `MLChangeDetector` are in `backend/app/services/imagery.py`; `/satellite/*` routes are in `backend/app/api/routes/imagery.py`. `SatelliteProvider` and `LocalSatelliteProvider` in `backend/app/services/providers.py` define the current source seam. Implement an external provider in `ExternalSatelliteProvider` when approved, then connect it through the imagery service after adding configuration, provenance, scene metadata, acquisition timestamps, image alignment, cloud handling, and tests. Sentinel/Copernicus access belongs there, not in frontend components. A future trained change-detection model belongs in `MLChangeDetector`; report its model name/version and validation limits. Current classical masks should remain labelled `CLASSICAL_CV_BASELINE`.

## Sonar ML

Current synthetic replay comes from `LocalSonarProvider` and `DemoAnnotationDetector`; uploaded images use `HeuristicAnomalyDetector`, all in the provider/imagery modules above. The interface is `SonarDetector`. To add a real model:

1. Obtain and prepare a legally usable, documented sonar dataset separately from this demo repository.
2. Train and evaluate the model in a separate, reproducible training project. Keep training code and datasets out of the foundation branch.
3. Store versioned inference weights under `ml/models/` only when intended for distribution; the current `.gitignore` excludes weights by default.
4. Connect weight loading and inference through `MLSonarDetector` in `backend/app/services/imagery.py`. Add configuration to `backend/app/core/config.py` when a model actually exists.
5. Preserve the existing response shape: image dimensions, region boxes, labels, scores, source type, detector identifier, and model version. Keep demo annotations separate from predictions.
6. Evaluate precision/recall, calibration, domain shift, false alarms, and dataset provenance honestly. Do not call heuristic scores ML confidence.

No sonar detection currently creates a hazard. A later, reviewed integration would require **detection → verified geolocation → hazard → existing hazard service → risk recomputation → route recomputation**. That connection is intentionally absent because neither real geolocation nor a validated model exists.

## Ocean and bathymetry providers

`OceanProvider`/`LocalOceanProvider` and `BathymetryProvider`/`LocalBathymetryProvider` are in `backend/app/services/providers.py`. They feed the same `DemoEnvironment` consumed by risk and routing. Future Copernicus Marine or other ocean data belongs in `ExternalOceanProvider`; expected output is a spatial grid of per-cell `wave_height_m`, eastward `u_current_mps`, and northward `v_current_mps` aligned to a documented CRS, time, and resolution. Future numeric GEBCO or another bathymetric source belongs in `ExternalBathymetryProvider`; expected output is a numeric `depth_m` grid aligned cell-for-cell with ocean data. Record vertical datum and uncertainty. The current risk engine rejects mismatched grid dimensions. Do not represent a decorative depth image as numeric bathymetry.

## Risk and routing

Risk formulas and `DemoEnvironment` are in `backend/app/services/risk/engine.py`; defaults, weights, thresholds, and validation are in `backend/app/services/risk/config.py` and `backend/app/schemas/routing.py`. `backend/app/services/risk/demo.py` translates request options and mission hazards into the grid. Prefer feeding validated real inputs through this same risk interface rather than creating a second formula. `backend/tests/test_risk.py`, `test_demo_api.py`, and `test_hazards.py` protect the current behavior.

A* search is in `backend/app/services/routing/astar.py`; route cost, movement assumptions, current-direction penalty, and metrics are in `backend/app/services/routing/service.py` and `risk/engine.py`. The demo uses eight directions, blocks corner cutting, and scales steps by modeled 50 m cells. Replace modeled cell distance with geodesic or projected geographic distance only after a verified spatial grid exists. `backend/tests/test_routing.py` protects route validity and seeded comparison.

## Report, status, and extension discipline

`backend/app/services/report.py` builds an on-demand report; `backend/app/api/routes/report.py` serves `/system-status` and `/report`. `frontend/src/components/mission/DataSourcesPanel.tsx` and `frontend/src/pages/ReportPage.tsx` display them. Extend these whenever a provider becomes available. Report `source_type`, provider, detector method, model configuration, time basis, and limitations from actual backend state. The current report does not save a historical snapshot; it computes current statistics when requested.

Before merging future integrations, add provider contract tests, unit tests for new transformations, HTTP tests, frontend provenance tests, and the exact manual steps to `docs/verification.md`. Keep `docs/data-provenance.md` and `docs/limitations.md` synchronized with actual behavior.
