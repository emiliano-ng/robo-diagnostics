"""Tool functions exposed to the local LLM, plus their JSON-schema
descriptions in Ollama/OpenAI function-calling format.

Every tool returns a SUMMARY, never a raw telemetry array. A run can have
~1000 points — dumping that into a 7B local model's context would blow
past what it can reason over usefully and slow every turn down for no
benefit. The model only needs numbers small enough to reason about in a
sentence (point count, ranges, percentages), not the raw signal.
"""

from sqlalchemy.orm import Session

from app import services


def list_experiments(db: Session) -> list[dict]:
    experiments = services.list_experiments(db)
    return [
        {
            "id": e.id,
            "name": e.name,
            "robot": e.robot,
            "algorithm": e.algorithm,
            "environment": e.environment,
            "run_count": services.experiment_run_count(db, e.id),
        }
        for e in experiments
    ]


def list_runs(db: Session, experiment_id: int) -> dict:
    experiment = services.get_experiment(db, experiment_id)
    if not experiment:
        return {"error": f"No experiment with id {experiment_id}"}

    runs = services.list_runs(db, experiment_id)
    return {
        "experiment_id": experiment_id,
        "runs": [
            {
                "id": r.id,
                "status": r.status,
                "started_at": str(r.started_at) if r.started_at else None,
                "ended_at": str(r.ended_at) if r.ended_at else None,
            }
            for r in runs
        ],
    }


def get_run_summary(db: Session, run_id: int) -> dict:
    run = services.get_run(db, run_id)
    if not run:
        return {"error": f"No run with id {run_id}"}

    points = services.get_trajectory(db, run_id)
    if not points:
        return {"run_id": run_id, "status": run.status, "point_count": 0, "message": "No telemetry ingested for this run yet."}

    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return {
        "run_id": run_id,
        "status": run.status,
        "point_count": len(points),
        "duration_seconds": round(points[-1].t_seconds - points[0].t_seconds, 1),
        "x_range_meters": [round(min(xs), 2), round(max(xs), 2)],
        "y_range_meters": [round(min(ys), 2), round(max(ys), 2)],
    }


def get_diagnostics_summary(db: Session, run_id: int) -> dict:
    run = services.get_run(db, run_id)
    if not run:
        return {"error": f"No run with id {run_id}"}

    diags = services.get_diagnostics(db, run_id)
    if not diags:
        return {
            "run_id": run_id,
            "analyzed": False,
            "message": "This run hasn't been analyzed yet. Call analyze_run first.",
        }

    flagged = [d for d in diags if d.status != "normal"]
    degraded = [d for d in diags if d.status == "degraded"]
    scores = [d.score for d in flagged if d.score is not None]

    return {
        "run_id": run_id,
        "analyzed": True,
        "total_points": len(diags),
        "flagged_count": len(flagged),
        "flagged_pct": round(100 * len(flagged) / len(diags), 1),
        "degraded_count": len(degraded),
        "worst_score": max(scores) if scores else None,
        # Capped to keep the tool result small — enough for the model to
        # cite specific moments without flooding its context.
        "sample_flagged_timestamps": [round(d.t_seconds, 1) for d in flagged[:15]],
    }


def analyze_run(db: Session, run_id: int) -> dict:
    run = services.get_run(db, run_id)
    if not run:
        return {"error": f"No run with id {run_id}"}
    return services.analyze_run(db, run_id)


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_experiments",
            "description": "List all experiments recorded in the platform, with how many runs each has.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_runs",
            "description": "List all runs belonging to a specific experiment, with their status and timing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "experiment_id": {"type": "integer", "description": "The experiment's ID."}
                },
                "required": ["experiment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_run_summary",
            "description": "Get summary statistics for one run: point count, duration, and spatial (x/y) range covered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The run's ID."}
                },
                "required": ["run_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_diagnostics_summary",
            "description": "Get the degradation-detector results for one run: what percentage of points were flagged, worst score, and sample timestamps of flagged points. Returns analyzed=false if the run hasn't been analyzed yet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The run's ID."}
                },
                "required": ["run_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_run",
            "description": "Run the degradation detector against a run's telemetry and persist the results. Use this if get_diagnostics_summary reports analyzed=false, or if the user explicitly asks to (re-)analyze a run.",
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "integer", "description": "The run's ID."}
                },
                "required": ["run_id"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "list_experiments": list_experiments,
    "list_runs": list_runs,
    "get_run_summary": get_run_summary,
    "get_diagnostics_summary": get_diagnostics_summary,
    "analyze_run": analyze_run,
}
