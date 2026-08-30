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

## Frontend testing: Vitest + React Testing Library, focused on behavior

**Decision:** test the API client's error handling (`lib/api.ts`) and the
one component with real interaction logic (`RunSelector`), not the chart
components.

**Why:** the charts are thin presentational wrappers around Recharts —
testing them would mean testing Recharts' own rendering, which adds
little value. The API client and `RunSelector` are where actual logic
lives (parsing errors into a typed `ApiError`, tracking selection state,
building the right URL to navigate to), so that's where bugs would
actually show up.

## Containerizing the full stack with Docker Compose

**Decision:** all three services (`db`, `backend`, `frontend`) run
together via a single `docker compose up`, with the frontend built using
Next.js's `standalone` output mode.

**Why `standalone`:** it produces a much smaller image — only the
`server.js` file and the subset of `node_modules` actually needed at
runtime, instead of copying the whole project (including devDependencies)
into the image.

**Why the frontend calls the backend as `http://backend:8000`, not
`localhost:8000`:** all data fetching happens in Server Components, which
run inside the frontend's own container. Each container has its own
isolated `localhost`, so `127.0.0.1:8000` inside the frontend container
would never reach the backend container. Docker Compose's internal DNS
resolves service names (`backend`) to the right container automatically.

**Bug found and fixed — Next.js standalone + Docker HOSTNAME binding:**
the frontend container failed to start with
`Error: getaddrinfo EAI_AGAIN <container_id>`. Root cause: Docker
automatically sets a `HOSTNAME` environment variable on every container,
equal to its container ID. Next.js's `standalone` server.js reads
`process.env.HOSTNAME` to decide which address to bind to, and tried to
resolve the container ID as if it were a real hostname — which fails,
since it isn't DNS-resolvable. Fixed by explicitly setting
`ENV HOSTNAME=0.0.0.0` in the final Docker stage, so Next.js binds to all
interfaces regardless of what Docker sets automatically.

## The degradation detector: from "too noisy to use" to a defensible baseline

**Decision:** a rolling z-score detector over EKF covariance (`cov_xx`,
`cov_yy`, `cov_tt`), comparing each point against the mean/std of the
preceding window — not the whole run — so "normal" can drift over the
course of a run without permanently skewing the baseline.

**Why this over jumping straight to ML:** without human-labeled ground
truth (nobody has annotated which seconds of a real run were "actually"
degraded), a more sophisticated model has nothing meaningful to be
validated against — it would just produce a different set of guesses, not
a provably better one. A simple, inspectable baseline you can reason
about point-by-point is the more honest place to start.

**Two real bugs found by testing against actual `slam_bot` data (not
just synthetic data) — this is why both were tested:**

1. **Epsilon too small relative to the real data's scale.** The initial
   implementation used `STD_EPSILON = 1e-6` to avoid dividing by zero
   when a window has near-zero variance. Against synthetic data this
   looked fine. Against real telemetry (covariance values around
   `1e-3`–`1`), it produced absurd scores (200–300) whenever a window
   happened to be nearly flat and a completely ordinary sensor jitter
   came through. Fixed by raising the floor to `1e-4`, matching the
   actual scale of the signal, and separately capping the *reported*
   score at 50 for readability — capping never changes classification,
   since anything above `degraded_z` was already unambiguously flagged.

2. **No temporal consistency requirement.** A raw point-by-point
   classifier flagged ~25% of all 944 points in a real run — useless for
   a human reviewer, since it's mostly single-sample noise blips, not
   real events. Fixed by requiring a deviation to be confirmed by an
   immediate neighbor (previous or next point) before elevating status
   above "normal". A real event (sensor dropout, sharp unmodeled turn)
   shows up as a short sustained cluster; a coincidental noise spike
   does not. This brought the flagged rate down to ~13%, with the
   confirmed clusters lining up with the two anomalies already spotted
   *visually* in the covariance chart before the detector existed
   (~38s, ~70–73s) — independent validation that the detector is
   catching real signal, not just noise at a different rate.

**Known remaining limitation:** without ground-truth labels, 13% is a
reasonable stopping point, not a provably optimal one — some flagged
clusters may correspond to ordinary covariance changes during turns
rather than genuine degradation. Distinguishing "operationally normal
maneuvering" from "a problem worth a human's attention" is exactly the
kind of judgment call that would need a domain expert's labels to
resolve properly — the detector's honest framing is "this deviated from
recent behavior, worth a look", not "this is confirmed degradation".

## Analysis triggered via a Server Action, not a client-side fetch

**Decision:** the "Analyze degradation" button on the run page calls a
Next.js Server Action (`analyzeRunAction`, `"use server"`), which then
calls the backend — instead of the button doing a `fetch()` directly
from the browser.

**Why:** in the Docker Compose deployment, the frontend reaches the
backend via the internal Docker network at `http://backend:8000` — a
hostname that only resolves *inside* Docker's network, never from the
user's actual browser. Since all `NEXT_PUBLIC_*` values get baked into
the JavaScript bundle at build time (including whatever code runs in the
browser), a client-side fetch to that address would work in local
development (where `.env.local` points at `127.0.0.1:8000`) but silently
fail once deployed via Docker Compose. Server Actions always execute on
the Next.js server itself, which does have correct network access to
`backend:8000` — so the same code works in both environments without an
environment-specific branch.

**How it stays in sync with the page:** the Server Action calls
`revalidatePath()` after a successful analysis, so the Server Component
re-fetches fresh diagnostics on the next render — no manual client-side
refetch logic needed.

## Still to document as the project progresses

- [ ] Why batch inserts from C++ instead of row-by-row inserts
- [ ] Why REST instead of GraphQL for the API
- [ ] What wasn't tested, and why