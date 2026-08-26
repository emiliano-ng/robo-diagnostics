# Robotics Experiment & Diagnostics Platform

A system to ingest, store, analyze, and diagnose robotics experiments
—currently built on top of [`slam_bot`](https://github.com/emiliano-ng/SLAM-bot),
an EKF-SLAM implementation built from scratch— with the end goal of
automatically detecting localization estimate degradation from real
telemetry data.

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
   list an experiment's runs, fetch a run's full trajectory, and compare
   the trajectories of several runs at once.
5. A **Next.js frontend** (`frontend/`) browses experiments and runs, and
   plots trajectory and EKF covariance over time, including side-by-side
   run comparisons.

## Repo structure

```
db/                 -> SQL schema
backend/            -> FastAPI (Python) — REST API + tests
ingestion/cpp/      -> C++ node that reads rosbag2 and writes to Postgres
frontend/           -> Next.js (TypeScript) frontend
.github/workflows/  -> CI (backend tests on every push)
docker-compose.yml
docs/decisions.md   -> design decisions log, with the reasoning behind each one
```

## Running it locally

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

**4. Tests:**

```bash
cd backend
pytest -v
```

Run against a real Postgres instance (not a mock/SQLite) using transactions
that roll back after each test — see `docs/decisions.md` for why.

**5. Ingesting a real bag** (requires a ROS2 workspace with `ingestion/cpp`
symlinked in as a package and built with `colcon`):

```bash
ingest_run <path_to_bag> <experiment_id> "postgresql://robo:robo_dev_password@localhost:5432/robo_diagnostics"
```

## Current status

- [x] Database schema (`experiments` → `runs` → `telemetry_points` → `diagnostics`)
- [x] Real C++ ingestion from rosbag2 (tested end-to-end with real `slam_bot` data)
- [x] FastAPI REST API: list experiments/runs, trajectory, run comparison
- [x] Automated tests running in CI (GitHub Actions)
- [x] Next.js frontend: experiment/run browser, trajectory + covariance charts, run comparison
- [ ] Full stack Dockerization + extended CI
- [ ] SLAM degradation detector (statistical + ML comparison)
- [ ] Final documentation, recorded demo, deployment

## Design decisions

See [`docs/decisions.md`](docs/decisions.md) — every non-trivial decision
(why Postgres, why this schema, why testing with transactions instead of a
separate database, etc.) is documented there with the reasoning, not just
the outcome.