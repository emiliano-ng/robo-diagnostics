# Design decisions
## Database schema

**Decision:** split `experiments` / `runs` / `telemetry_points` / `diagnostics`
into 4 tables instead of one flat table.

**Why:**
- `experiments` = the test configuration/type (grain: one row per
  "experiment design"). `runs` = each actual execution (grain: one row
  per real run). Without this split you can't cleanly compare "run 41
  vs run 42 of the same experiment".
- `telemetry_points` is the finest grain (one row per timestamp). It's
  kept separate from `diagnostics` on purpose: telemetry is *observed*
  data, diagnostics is *inferred* data from a detector. Mixing them would
  make it impossible to tell "the robot measured this" apart from "my
  model computed this" — important if you ever run two different
  detectors over the same run and want to compare them.

**Trade-off accepted:** more JOINs for queries that combine all 4 tables,
in exchange for each table having a clear, defensible grain.

**Index chosen:** `(run_id, t_seconds)` on `telemetry_points` — because
the dominant query in the system is "give me the full time series for
this run", almost never "give me all points with x > N across runs".

## Postgres vs. a NoSQL/timeseries alternative

**Decision:** plain PostgreSQL (not InfluxDB/TimescaleDB) for v1.

**Why:** the data is relational by nature (experiment → run → points) and
the expected volume (dozens of runs, each with thousands of points)
doesn't justify the operational complexity of a dedicated timeseries DB
yet. If volume grows significantly, TimescaleDB (a Postgres extension) is
the natural upgrade path without switching engines.

## Ingestion with relative timestamps (t_seconds since run t0)

**Decision:** normalize every message timestamp to "seconds since the
run's first message" instead of storing ROS's absolute epoch.

**Why:** it lets you compare runs aligned by elapsed time ("second 15 of
this run vs. second 15 of that run"), which is exactly what the
degradation detector needs (comparing degradation across runs). Storing
the absolute epoch would make that comparison much more awkward.

**Trade-off:** we lose the real wall-clock time of an event unless we
reconstruct it as `t0 + t_seconds` — acceptable since `runs.started_at`
already stores that reference.

## Testing with rolled-back transactions, not a separate test DB

**Decision:** tests run against the same development Postgres
(`robo_diagnostics`), but each test opens its own transaction that's
rolled back at the end — no real `commit` ever happens.

**Why:** a separate test DB (`robo_diagnostics_test`) is the "cleaner"
option in theory, but adds another setup step (creating the DB, keeping
its schema in sync with development) with no real need at this point in
the project. Rolled-back transactions give the same isolation (no test
pollutes another, nor the real data from already-ingested runs) with
fewer moving parts.

**Trade-off accepted:** if the project ever needs to test transaction-
specific behavior (e.g. what happens when two requests race for the same
row), this approach won't work — a real separate test DB would be needed
then. Not the case yet.

## Frontend: Next.js instead of Vite/CRA

**Decision:** Next.js (App Router) for the frontend, not a plain SPA with
Vite or Create React App.

**Why:** I already use Next.js in my portfolio, so I'm reusing patterns
I already know (folder-based routing, Server Components) instead of
learning a new setup — effort goes into the substance of the project (the
diagnostic charts), not into tooling configuration. Next.js also shows up
consistently in full-stack job postings, making it more recognizable in a
portfolio repo than a generic SPA.

**How it was used:** Server Components fetch directly from the backend
(no loading state to hand-roll); Client Components are used only where
browser interactivity is actually needed (run selection for comparison,
and the Recharts charts, which use hooks internally).

## Still to document as the project progresses

- [ ] Why batch inserts from C++ instead of row-by-row inserts
- [ ] Why REST instead of GraphQL for the API
- [ ] How the baseline vs. ML detector decision was made
- [ ] What wasn't tested, and why