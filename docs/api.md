# API — current foundation

Base path: `/api`. FastAPI also serves `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Backend and database status |
| GET | `/missions` | List missions |
| POST | `/missions` | Create mission (`name`, `description`, `mode`) |
| GET | `/missions/{id}` | Read mission |
| PATCH | `/missions/{id}` | Update name, description, or status |
| DELETE | `/missions/{id}` | Delete mission and AOIs |
| GET | `/missions/{id}/aois` | List AOIs |
| POST | `/missions/{id}/aois` | Add EPSG:4326 bounding box |
| DELETE | `/missions/{id}/aois/{aoi_id}` | Delete AOI |
| GET | `/missions/{id}/environment` | Simulated per-cell wave and u/v current grid |
| GET | `/missions/{id}/bathymetry` | Simulated per-cell depth grid |
| GET | `/missions/{id}/risk-map` | Default calculated risk cells and demo metadata |
| POST | `/missions/{id}/risk-map/recalculate` | Recalculate with optional risk options JSON |
| POST | `/missions/{id}/routes/calculate` | Calculate and store both routes for grid endpoints |
| GET | `/missions/{id}/routes` | Latest stored route comparison |
| GET | `/missions/{id}/hazards` | Seeded and manual hazards, including resolved records |
| POST | `/missions/{id}/hazards` | Add operator-entered hazard and automatically update risk/routes |
| PATCH | `/missions/{id}/hazards/{hazard_id}` | Set `ACTIVE` or `RESOLVED`; automatically update risk/routes |

Expected missing resources return a structured `detail` with `code` and `message`. Invalid payloads return HTTP 422.

The demo risk, route, and hazard endpoints are available only for the seeded fictional Cyclone Varuna mission; other missions receive `DEMO_ENVIRONMENT_UNAVAILABLE` (409). Route calculation body:

```json
{"start":{"row":19,"col":3},"destination":{"row":4,"col":32}}
```

Optional `options` may configure risk weights (`hazard`, `depth`, `wave`, `current`, `uncertainty`), depth and wave thresholds, current reference speed, and routing risk aggressiveness. Weights must sum to 1. Invalid or blocked endpoints and no-path conditions return structured HTTP 422 errors. `/routes` returns 404 until a route has been calculated.

Create a manual hazard:

```json
{"row":5,"col":17,"hazard_type":"SUBMERGED_OBSTRUCTION","severity":"HIGH","confidence":0.95,"source_type":"MANUAL","client_request_id":"11111111-1111-4111-8111-111111111111"}
```

The optional UUID `client_request_id` makes retries idempotent. The response contains `hazard`, `impact`, the refreshed `risk_map`, and `routes` when an active route plan exists. `impact` includes `risk_recalculated`, `route_recalculated`, `previous_route_affected`, `route_changed`, before/after lower-route summaries, and the previous geometry's average risk evaluated under the new field. Route geometry is compared directly; it is not forced to change. If no plan exists, `routes` is null and `reason` is `No active route plan`.

Resolve or reactivate with `PATCH` body `{"status":"RESOLVED"}` or `{"status":"ACTIVE"}`. There is no delete endpoint: resolved hazards remain inspectable. Invalid location, blocked cell, unknown hazard, and unchanged status return structured errors. FastAPI validation rejects unsupported types/severities and confidence outside `[0,1]` with HTTP 422.

## Scaffold Chunk A imagery API

All paths below follow `/api/missions/{id}`. Demo imagery belongs only to fictional Cyclone Varuna; uploads can belong to any existing mission. Uploads accept one PNG/JPEG per request, at most 10 MB and 4096 pixels per side. Application errors use `detail: {code, message}`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/satellite/status` | Demo and upload availability; model status |
| POST | `/satellite/upload?role=before` or `role=after` | Multipart `file`; normalize and store one image |
| GET | `/satellite/assets/{source}/{role}` | Preview PNG; source is `demo` or `uploaded` |
| POST | `/satellite/analyze` | JSON `{"source":"demo"}` or `{"source":"uploaded","detector":"classical"}` |
| GET | `/sonar/replay` | Five synthetic frames, metadata, annotations, and image URLs |
| GET | `/sonar/assets/{source}/{name}` | Frame PNG |
| POST | `/sonar/upload` | Multipart `file`; store one frame |
| POST | `/sonar/analyze` | JSON `{"source":"uploaded","detector":"heuristic"}` |
| GET | `/sonar/model/status` | Heuristic availability and ML unavailable status |

Satellite analysis returns `changed_pixels`, `percent_changed`, `regions` with pixel bounding boxes, dimensions, a binary `mask_data_url`, detector, and source type. Sonar upload analysis returns `anomaly_count`, an uncalibrated `anomaly_score`, and unclassified bright-region boxes/scores with `HEURISTIC` output provenance. Replay frame annotation results expose `DEMO / MISSION_REPLAY` provenance. `detector: "ml"` returns HTTP 409 `MODEL_NOT_CONFIGURED` for both analyses. Demo sonar annotations are not heuristic or ML detections.

## Mission status and report

| Method | Path | Purpose | Important response fields |
| --- | --- | --- | --- |
| GET | `/missions/{id}/system-status` | Current source/provider availability | `satellite`, `sonar`, `bathymetry`, `ocean`, `routing`, `external_providers`, each with provider/source/status and optional method/model status |
| GET | `/missions/{id}/report` | Current on-demand mission snapshot | `mission`, `coordinate_status`, `satellite`, `sonar`, `hazards`, `environment`, `risk`, `routing`, `system_status`, `limitations`, `disclaimer`, `generated_at` |

The report is read-only and does not persist a historical copy. For the demo mission it computes satellite change and navigable-cell risk at request time, labelled `COMPUTED_ON_DEMAND`; this does **not** claim that an operator previously ran analysis. The latest persisted route is included when available; otherwise `routing` is null. Other missions show unavailable local grid/routing values rather than fictional results. Unknown mission IDs return `MISSION_NOT_FOUND` (404). No external provider endpoints are exposed or described as operational.
