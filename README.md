# Robotics Experiment & Diagnostics Platform

**Live demo:** [frontend](https://robo-diagnostics-frontend.thankfulmoss-0a7f7ee4.canadacentral.azurecontainerapps.io) · [API docs](https://robo-diagnostics-backend.thankfulmoss-0a7f7ee4.canadacentral.azurecontainerapps.io/docs)

> Note: to control cloud costs, the database is stopped between active
> demo sessions. If the live links above are unresponsive, that's why —
> everything below still works fully from a local clone.

A system to ingest, store, analyze, and diagnose robotics experiments, currently built on top of [`slam_bot`](https://github.com/emiliano-ng/SLAM-bot),
an EKF-SLAM implementation built from scratch— that automatically flags
likely localization degradation from real telemetry data.

## Architecture

```
ROS2 / Gazebo (slam_bot)
        │
        ▼
   rosbag2 (.db3)
        │
        ▼
 Ingestion (C++)
        │
        ▼
   PostgreSQL
        │
   ┌────┴────┐
   ▼         ▼
Analysis   FastAPI
 Engine     (REST)
   │         │
   └────┬────┘
        ▼
  React / TypeScript
```

## How it works today

1. `slam_bot` runs EKF-SLAM in Gazebo and publishes filter pose + covariance
   on `/slam/pose_covariance`.
2. A run is recorded with `ros2 bag record`.
3. A **C++** ingestion node (`ingestion/cpp/`) reads the bag, deserializes
   the messages, and writes telemetry to Postgres in idempotent batches
   (`ON CONFLICT DO NOTHING`, so the same bag can be re-ingested without
   duplicating data).
4. A **FastAPI REST API** (`backend/`) exposes that data: list experiments,
   list an experiment's runs, fetch a run's full trajectory, compare the
   trajectories of several runs, and trigger/read degradation analysis.
5. A **degradation detector** (`backend/app/analysis/`) flags points whose
   EKF covariance deviates sharply and persistently from recent behavior —
   a rolling z-score with a temporal-consistency check, tuned and validated
   against real `slam_bot` telemetry (see `docs/decisions.md`).
6. A **Next.js frontend** (`frontend/`) browses experiments and runs, plots
   trajectory and covariance over time with the detector's flagged points
   overlaid, supports side-by-side run comparisons, and can trigger a new
   analysis with one click.

The whole stack (database, backend, frontend) can be run together with a
single `docker compose up`.

## Repo structure

```
db/                 -> SQL schema
backend/            -> FastAPI (Python) — REST API, degradation detector, tests
ingestion/cpp/      -> C++ node that reads rosbag2 and writes to Postgres
frontend/           -> Next.js (TypeScript) frontend + tests
.github/workflows/  -> CI (backend and frontend tests on every push)
docker-compose.yml
docs/decisions.md   -> design decisions log, with the reasoning behind each one
```

## Running it

### Option A — full stack with Docker Compose (closest to production)

```bash
docker compose up --build
```

This builds and starts the database, backend, and frontend together.
Open `http://localhost:3000`.

### Option B — manual, for faster local iteration

**1. Database:**

```bash
docker compose up -d db
```

**2. Backend:**

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://robo:robo_dev_password@localhost:5432/robo_diagnostics"
uvicorn app.main:app --reload
```

Interactive docs at `http://127.0.0.1:8000/docs`.

**3. Frontend:**

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Opens at `http://localhost:3000`.

> Don't run Option A and Option B at the same time — they'll fight over
> ports 3000 and 8000.

### Tests

Backend:

```bash
cd backend
pytest -v
```

Runs against a real Postgres instance (not a mock/SQLite) using
transactions that roll back after each test — see `docs/decisions.md`
for why.

Frontend:

```bash
cd frontend
npm test
```

### Ingesting a real bag

Requires a ROS2 workspace with `ingestion/cpp` symlinked in as a package
and built with `colcon`:

```bash
ingest_run <path_to_bag> <experiment_id> "postgresql://robo:robo_dev_password@localhost:5432/robo_diagnostics"
```

### Running degradation analysis on a run

From the UI: open a run's page and click "Analyze degradation".

From the API directly:

```bash
curl -X POST http://127.0.0.1:8000/experiments/runs/<run_id>/diagnostics/analyze
```

Or standalone, without the API, useful for quick experimentation with
detector parameters:

```bash
cd backend
python -m app.analysis.run_detector <run_id>          # dry run, prints only
python -m app.analysis.run_detector <run_id> --save    # persists results
```

## Current status

- [x] Database schema (`experiments` → `runs` → `telemetry_points` → `diagnostics`)
- [x] Real C++ ingestion from rosbag2 (tested end-to-end with real `slam_bot` data)
- [x] FastAPI REST API: list experiments/runs, trajectory, run comparison
- [x] Structured logging, DB-down handling, and a real `/health` check
- [x] SLAM degradation detector: rolling z-score + temporal-consistency
      confirmation, tuned and validated against real telemetry
- [x] Next.js frontend: experiment/run browser, trajectory + covariance
      charts with degradation overlay, run comparison, one-click analysis
- [x] Automated tests (backend + frontend) running in CI (GitHub Actions)
- [x] Full stack containerized with Docker Compose
- [x] Deployed to Azure (Container Apps + PostgreSQL Flexible Server)
- [ ] Comparison against a second (ML-based) detector
- [ ] Final documentation, recorded demo, deployment

## Design decisions

See [`docs/decisions.md`](docs/decisions.md), every non-trivial decision
(why Postgres, why this schema, why testing with transactions instead of a
separate database, a Docker bug found and fixed, how the degradation
detector went from 25% false positives to a defensible baseline, etc.) is
documented there with the reasoning, not just the outcome.