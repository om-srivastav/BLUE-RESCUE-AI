# Setup

Requirements: Python 3.11+ and Node.js 24.x (verified with 24.14.1). The locked jsdom test dependency supports Node `^20.19.0 || ^22.13.0 || >=24.0.0`; early Node 20 releases are insufficient.

From the repository root, create a Python environment and install backend dependencies:

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

Open `http://localhost:5173`. The backend serves `http://localhost:8000/api/health` and interactive API documentation at `http://localhost:8000/docs`. The demo mission is inserted at backend startup. SQLite is created at `backend/blue_rescue.db` when started from the backend directory.

Open **Mission Cyclone Varuna** from Missions to use the simulated risk map and route planner. Select the bathymetry or waves layer, toggle current arrows and hazards, then calculate routes with the default Survey Base and Harbor Entrance cells. The local demo requires no provider credentials or remote map tiles.

The mission dashboard also shows **Data sources / system status**. Use **Satellite** for bundled or uploaded before/after comparison, **Sonar** for fictional frame replay or an uploaded-image heuristic, and **Report** for a current snapshot that can be printed from the browser. Uploaded images are stored locally under `backend/data-cache/` by default. External provider credentials and ML weights are not part of this foundation.

For macOS/Linux, use `source .venv/bin/activate` and `python -m ...` in place of the Windows executable paths.

Run checks from `backend` with `../.venv/Scripts/python -m pytest` and from `frontend` with `npm run lint`, `npm run typecheck`, `npm run test`, and `npm run build`.
