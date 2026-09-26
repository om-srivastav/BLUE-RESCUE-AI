# Verification

## Automated checks

From `backend`: `../.venv/Scripts/python -m pytest -q`. The suite covers mission CRUD, AOI validation, risk bounds/decay/thresholds, directional currents, A* validity and no-path handling, seeded route tradeoff, risk/routing APIs, hazard validation/persistence, affected and unaffected rerouting, resolution, idempotent submission, satellite demo and uploads, image validation, sonar replay and heuristic, structured ML-unavailable responses, local provider contracts, unavailable external adapters, system status, and the current-state report.

From `frontend`: `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build`. The suite checks API error display, planner and hazard interactions, satellite analysis/upload, sonar replay/upload, source cards, report content, and the print action with mocked API responses.

## Manual demonstration

1. Start both apps per `docs/setup.md`, open the frontend, then choose Mission Cyclone Varuna.
2. Verify the **SIMULATED DEMONSTRATION MISSION** and **SCHEMATIC GRID** labels.
3. Switch risk, bathymetry, and waves layers. Toggle current arrows and fictional hazard markers. Click cells to inspect numeric values.
4. Use Survey Base `(19,3)` and Harbor Entrance `(4,32)` or select navigable cells on the grid.
5. Click **Calculate routes**. Both amber shortest and cyan lower modeled-risk paths must appear. Compare computed metrics and the explanation.
6. Click **Recalculate grid** and recompute routes. Static grid values and route geometry should remain deterministic; computation time may vary.
7. Click **ADD HAZARD**, choose a cell on the current cyan path, set **Submerged obstruction**, **HIGH**, and **95%** operator-entered certainty, then save. The backend response should update the nearby risk colors, marker, hazard panel, both routes, comparison metrics, and an impact message without an extra refresh action.
8. Refresh the browser. The manual hazard and latest route plan should load from SQLite.
9. Click **Mark Resolved** for the manual hazard. The record remains listed as resolved, its risk contribution disappears, and routes are recalculated.

The default seeded environment gives a shortest route of approximately 1760.66 modeled meters with mean modeled risk 0.19794 and a lower modeled-risk route of approximately 1819.24 modeled meters with mean modeled risk 0.13755. These are regression references for this deterministic fictional dataset, not performance or safety claims.

A live disposable-database check used the default route and placed a high-severity, 95%-certainty obstruction at `(5,17)` on the previous lower modeled-risk path. Local cell risk rose from `0.17538` to `0.49108`; the backend reported `previous_route_affected=true` and `route_changed=true`. The rerouted path was 1760.66 modeled m with mean risk 0.15499. This mean is above the pre-hazard value because the modeled environment gained a hazard; the service compares it with keeping the prior geometry under the changed field. Resolution restored the local risk to `0.17538`. The resolved manual record persisted across a server restart. The disposable database was removed after verification.

## Scaffold Chunk A walkthrough

1. Open Cyclone Varuna, then **Satellite**. Select bundled demo and run analysis. Before/after images, nonzero change percentage, binary mask, and region list should appear with simulated/classical labels.
2. Upload two same-size PNG/JPEG images using before and after controls, select **My uploads**, and run analysis. Reload; previews should still load from the local cache. Identical images should report zero change. Different dimensions should return `DIMENSION_MISMATCH`.
3. Open **Sonar**. Verify five synthetic frames, annotation overlays, metadata, and Previous/Play/Pause/Next controls. This is a recorded fictional replay.
4. Upload one sonar image and run heuristic analysis. Any reported boxes are `Unknown anomaly`, not object classes. Refresh and confirm the uploaded preview remains cached.
5. Call either analysis endpoint with `detector: "ml"`; expect `MODEL_NOT_CONFIGURED`. Existing risk/routing and hazard features should still work. Sonar annotations do not create hazards.

## Foundation status and report

1. Start backend and frontend per `docs/setup.md`; confirm `/api/health`, `/api/missions`, and the Cyclone Varuna dashboard through the Vite proxy.
2. On the dashboard, inspect **Data sources / system status**. Satellite, sonar, ocean, bathymetry, and routing should show local provenance. External providers and ML models should show not configured, never live.
3. Calculate Survey Base → Harbor Entrance, add a manual hazard on the current lower-risk route, and verify the route recomputes. Resolve it and verify risk and route recompute again. Use a disposable database if you do not want to retain a manual record.
4. Run the bundled satellite analysis, then upload same-size before/after images and run upload analysis. Replay all five sonar frames and run the uploaded-image heuristic. Check labels and masks/overlays.
5. Open **Report**. Check mission and coordinate status, current hazard counts, satellite percentage, sonar source, risk summary/weights, latest route metrics/explanation, provider state, and disclaimer. Refresh after a hazard or route change; the report must reflect current backend state.
6. Select **Print report** and inspect browser print preview or save to PDF. Sidebar, command header, and button should be absent; report sections should be readable on white pages.
7. Check `/api/missions/{id}/system-status` and `/api/missions/{id}/report` directly, then through `http://localhost:5173/api/...`. Non-demo missions should show unavailable local grid/risk/routing values rather than fabricated data.
