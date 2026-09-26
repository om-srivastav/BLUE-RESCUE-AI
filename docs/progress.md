# SOFTWARE FOUNDATION COMPLETE

**Scaffold Chunk B complete (2026-09-26).** The working foundation has passed final QA and is ready for a reviewed push to `main` after its local initial commit. This file records current state first; milestone notes below describe their historical state at the time.

## Working

- Mission and AOI system, seeded fictional Cyclone Varuna environment, simulated bathymetry/ocean grids, and deterministic risk calculation.
- A* shortest and lower modeled-risk routing, persistent manual hazards, automatic risk/route recalculation when hazards appear or are resolved.
- Classical satellite change detection for bundled and uploaded images; synthetic five-frame sonar replay and uploaded-image heuristic anomaly baseline.
- Typed local satellite, sonar, ocean, and bathymetry provider interfaces. External adapter calls fail with `NOT_CONFIGURED` and no network integration.
- Backend mission system-status and on-demand report endpoints, dashboard provenance/status cards, and a browser-printable report with mission, imagery, hazards, environment, risk, routing, limitations, and disclaimer.

## Intentionally Not Implemented

- Real maps, real geographic routing, real satellite/ocean/bathymetry providers, Sentinel/Copernicus/GEBCO integration.
- Model training, trained sonar or satellite models, real sonar hardware, sonar geolocation, or automatic sonar-to-hazard conversion.
- A report archive or certified operational workflow. `REAL_DATA` and `OFFLINE_CACHED` remain mission metadata modes only.

## Final verification

Backend: 25 tests passed (one upstream Starlette/httpx deprecation warning). Frontend: 11 tests passed; lint, typecheck, and production build passed. Through the live Vite proxy on a disposable database, health and missions loaded; the grid was 24 × 36; baseline routes remained 1760.66 and 1819.24 modeled m; a manual hazard triggered rerouting and the report count rose to four; resolution succeeded. Satellite demo change was 2.06%, sonar replay returned five frames, external status was `NOT_CONFIGURED`, and the report page returned HTTP 200. A browser print-to-PDF render was inspected across three readable A4 pages after correcting print background styling. Disposable state and print files were removed, and the normal backend was restored. Browser pointer interaction beyond the print render was not observed; jsdom tests cover the core page interactions.

Team handoff: `README.md`, `docs/setup.md`, `docs/architecture.md`, `docs/api.md`, `docs/data-provenance.md`, `docs/limitations.md`, `docs/verification.md`, and `docs/future-development.md` describe the current behavior and extension points. The staging dry run excluded generated databases, caches, build output, virtual environments, and model weights.

## Milestone history

## Current state: Scaffold Chunk A — Satellite + Sonar Foundation

**Complete (2026-09-26).** The earlier Chunk 4/5 roadmap in this historical log is superseded by the user-directed scaffold scope. Bundled deterministic fictional satellite before/after PNGs and five synthetic sonar frames with authored annotations are present. Satellite uploads, previews, classical CV change detection, masks, percentages, and regions work offline. Sonar replay, frame controls, metadata/overlays, single image upload, and heuristic unknown-anomaly detection work offline. The satellite and sonar detector interfaces include ML adapters that return structured `MODEL_NOT_CONFIGURED`; no model, external API, or sonar-to-hazard integration was added. Mission navigation links to Dashboard, Satellite, Sonar, Risk / Routing, and a clearly pending Report page. Existing Chunks 1–3 remain in place.

Verification: backend `pytest -q` 21 passed (one upstream Starlette warning). Frontend lint, typecheck, 9 Vitest tests, and production build passed. Live HTTP on a fresh Uvicorn process returned 2.06% changed pixels for the fictional satellite pair, five sonar frames, successful before/after and sonar uploads and analysis, and structured `MODEL_NOT_CONFIGURED` for ML selection. A server restart retained the uploaded assets in an isolated cache; that smoke-test cache was then removed. The development backend was restarted on port 8000 and the Vite proxy served the new satellite status endpoint. The deterministic image fixtures can be regenerated with `scripts/generate_imagery_demo.py`. Browser pointer interaction was not observed because no browser surface was available; the jsdom tests cover analysis and replay controls.

Next at that milestone was Scaffold Chunk B; it is now complete as recorded above.

## Chunk 1 — Project foundation

**Complete (2026-09-26).**

Implemented FastAPI configuration/CORS, SQLite initialization, mission CRUD, AOI API with EPSG:4326 bounds validation, structured missing-resource errors, health endpoint, and idempotent fictional Cyclone Varuna seed. The React/Vite/TypeScript/Tailwind frontend has an overview, mission list/create form, mission dashboard shell, API status, and explicit simulated provenance labels. Setup, architecture, API, and limitations documentation is present.

Verification:

- Backend: `pytest -q` — 1 passed.
- Frontend: `npm run lint` — passed; `npm run typecheck` — passed; `npm run test` — 1 passed; `npm run build` — passed.
- Started Uvicorn and Vite. HTTP checks: frontend `/` returned 200; `/api/health` returned `status: ok` and `database: ok` both directly and through Vite's proxy; `/api/missions` returned seeded Cyclone Varuna with `SIMULATED` source.

Current limitations: dashboard analysis modules are intentionally labelled as planned. No observation, risk, or routing data is claimed. `REAL_DATA` and `OFFLINE_CACHED` are metadata modes only until later chunks. Automated schema migrations are not yet required for the initial schema.

## Chunk 2 — demo geographic/risk/routing core

**Complete (2026-09-26).**

Implemented versioned deterministic 24 × 36 fictional bathymetry, spatial wave/u/v current grids, three fictional hazard annotations, a configurable normalized risk service, and transparent 8-way A*. Cells below the simulated 4.5 m operational depth threshold are blocked. A shortest-distance path and a lower modeled-risk path are calculated from the requested grid endpoints, with statistics, computed explanation, and latest route result stored in SQLite. The Cyclone Varuna dashboard now includes a working grid planner with risk/bathymetry/wave layers, sampled current arrows, hazard markers, cell inspection, endpoint selection, and simultaneous route overlays. All coordinates and distances are clearly labelled schematic/simulated.

Default demo result: shortest 1760.66 modeled m, mean modeled risk 0.19794; lower modeled-risk 1819.24 modeled m, mean modeled risk 0.13755. The alternative avoids the influence radius of fictional Hazard 03 and has a lower directional current penalty. No completed route coordinate arrays are bundled.

Verification:

- Backend full suite: 11 passed (one upstream Starlette/httpx deprecation warning).
- Frontend lint, typecheck, Vitest (2 passed, including a planner interaction test), and production build passed. Vite/Vitest required execution outside the sandbox because sandboxed esbuild could not read `vite.config.ts` on this Windows path.
- Started Uvicorn and Vite. Live HTTP via Vite's proxy returned the 24 × 36 risk map and three hazards; `POST /routes/calculate` returned the distances and risks above. Vite served the planner source module with HTTP 200.
- A browser surface was unavailable to this agent (`cua.getState()` returned no browsers), so visual pointer interaction was not observed. A jsdom interaction test exercised grid loading, layer switching, route calculation, and comparison display. The manual acceptance walkthrough is in `docs/verification.md`.

Current limits: no real geographic coordinates, satellite/sonar processing, manual hazards, automatic rerouting, or real-data providers. These belong to later chunks. A* is a transparent routing algorithm, not ML, and no route is represented as safe.

## Next

## Chunk 3 — Hazards + Dynamic Rerouting

**Complete (2026-09-26).**

Added SQLite `Hazard` records for the three fixed fictional annotations and operator-entered manual hazards. Seed is idempotent and preserves resolved status. Controlled type, severity, confidence, grid position, status, provenance, and local timestamps are exposed by GET/POST/PATCH APIs. Manual location must be inside the schematic grid and navigable under the simulated depth threshold. The frontend provides ADD HAZARD mode, cell selection, a confirmed form, source/severity markers, hazard cards, resolution, and notifications driven by the backend impact response.

One backend service now handles hazard mutation, risk-grid recomputation, and route recalculation using stored route endpoints and options in a SQLite transaction. It reports whether the previous lower modeled-risk path materially overlapped the hazard influence area, whether A* actually changed the path, before/after metrics, and the old geometry's exposure under the new field. No route is fabricated when no plan exists. A client request UUID makes create retries idempotent. Resolved hazards remain inspectable and stop contributing risk. Existing route records and mission data are retained; startup `create_all` adds the hazard table to existing SQLite databases.

Verification:

- Existing pre-hazard result preserved: shortest 1760.66 modeled m, average risk 0.19794; lower modeled-risk 1819.24 modeled m, average risk 0.13755.
- Backend full suite: 16 passed (one upstream Starlette/httpx deprecation warning). Frontend: lint, typecheck, 6 Vitest tests, and production build passed.
- Live disposable SQLite test via the Vite proxy: three seeded hazards loaded. Adding a HIGH, 95%-certainty obstruction at cell `(5,17)` on the lower modeled-risk path raised that cell's risk from 0.17538 to 0.49108. The backend reported `previous_route_affected=true` and `route_changed=true`; the recalculated lower modeled-risk route measured 1760.66 modeled m at average risk 0.15499. Its absolute mean risk increased relative to the pre-hazard world, which is expected after adding a hazard; the service separately compares against retaining the old geometry under the updated field. Resolving the hazard restored cell risk to 0.17538 and recalculated the route. The manual resolved record persisted through a server restart. The disposable database was removed, and the normal database still has three seeded hazards and zero manual test hazards.
- The browser UI surface was unavailable to the agent (`cua.getState()` returned no browsers). Frontend interaction tests exercised add mode, map cell selection, form submission, impact notification, map risk update, cancellation, resolution, and remount loading of persisted data. Manual walkthrough steps are in `docs/verification.md`.

Current limitations: no measured geographic hazard positions, authenticated operator identity, sonar-derived hazards, or satellite/sonar pipelines. Severity and affected-route thresholds are academic scenario parameters. A* results are modeled decision support, not navigation certification.

## Next

Superseded by the Scaffold Chunk A state at the top of this file.
