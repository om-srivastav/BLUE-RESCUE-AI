# BLUE-RESCUE AI

**See Above. Detect Below. Navigate Smarter.**

BLUE-RESCUE AI is an offline academic maritime disaster-recovery decision-support prototype. It combines a fictional coastal mission, modeled environmental risk, route comparison, operator-entered hazards, classical satellite image difference, and synthetic sonar replay. The interface and report identify what is simulated, uploaded, heuristic, or unavailable.

## What works

- Mission and AOI management in SQLite, plus seeded fictional **Mission Cyclone Varuna**.
- A deterministic 24 × 36 schematic grid with simulated bathymetry, waves, currents, and three authored hazards.
- Configurable risk fusion, A* shortest and lower modeled-risk routes, and persistent manual hazards that trigger automatic rerouting when added or resolved.
- Bundled or uploaded satellite before/after images with a classical CV change mask, percentage, and regions.
- Five-frame synthetic sonar replay with authored annotations, and a heuristic unknown-anomaly baseline for one uploaded image.
- Typed local provider interfaces, a mission data-source status panel, and a current-state printable mission report.

No external provider, geographic map, trained ML model, live sonar connection, or sonar-to-hazard automation is included. The ML adapters return `MODEL_NOT_CONFIGURED`; external provider adapters return `NOT_CONFIGURED`.

## Architecture

React/Vite calls FastAPI under `/api`. FastAPI services use SQLite for missions, hazards, and route calculations; bundled `demo-data/` for fictional grids and imagery; and `backend/data-cache/` for local uploads. Providers in `backend/app/services/providers.py` form small replacement seams around demo inputs. The report reads current backend state on demand. See [architecture](docs/architecture.md), [API](docs/api.md), and [data provenance](docs/data-provenance.md).

## Run locally

Requires Python 3.11+ and Node.js 24.x (verified with 24.14.1). The locked test dependencies require Node 20.19+, 22.13+, or 24+ within their supported release lines. From the repository root on Windows:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs`. No provider credentials are needed. See [setup](docs/setup.md) for macOS/Linux equivalents and database location.

## Demo walkthrough

Open **Missions → Mission Cyclone Varuna**. Calculate Survey Base → Harbor Entrance, inspect both routes, then add a high-severity obstruction on the lower-risk path and watch the backend recompute risk and routes. Resolve the hazard to remove its risk contribution. Open **Satellite** for bundled change detection or uploads, **Sonar** for replay and upload analysis, and **Report** for current metrics and a print view. The **Data sources / system status** cards show provenance and missing integrations. The detailed checklist is in [verification](docs/verification.md).

## Checks

From `backend`, run `..\.venv\Scripts\python -m pytest -q`. From `frontend`, run `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build`. The report and status APIs are covered by backend tests; frontend tests exercise their presentation and print action.

## Project handoff

See [future development](docs/future-development.md) for exact files and contracts for future maps, satellite and ocean providers, bathymetry, sonar ML, risk, routing, and eventual sonar-to-hazard integration. [Limitations](docs/limitations.md) records current scientific constraints. Screenshots have not been captured for this repository; add reviewed screenshots here when available.

**BLUE-RESCUE AI is an academic decision-support prototype. It is not a certified maritime navigation or emergency-response system.**
