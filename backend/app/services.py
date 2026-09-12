"""Shared business logic, independent of how it's exposed (REST endpoint
or agent tool). Both the FastAPI routers and the agent's tool functions
call into this module instead of duplicating SQLAlchemy queries — a
change to how "list runs" works only needs to happen once.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func

from app.models import Experiment, Run, TelemetryPoint, Diagnostic
from app.analysis.degradation import baseline_threshold_detector, TelemetrySample, DETECTOR_NAME


def list_experiments(db: Session) -> list[Experiment]:
    return db.scalars(select(Experiment).order_by(Experiment.created_at.desc())).all()


def get_experiment(db: Session, experiment_id: int) -> Experiment | None:
    return db.get(Experiment, experiment_id)


def list_runs(db: Session, experiment_id: int) -> list[Run]:
    return db.scalars(
        select(Run).where(Run.experiment_id == experiment_id).order_by(Run.created_at)
    ).all()


def get_run(db: Session, run_id: int) -> Run | None:
    return db.get(Run, run_id)


def get_trajectory(db: Session, run_id: int) -> list[TelemetryPoint]:
    return db.scalars(
        select(TelemetryPoint)
        .where(TelemetryPoint.run_id == run_id)
        .order_by(TelemetryPoint.t_seconds)
    ).all()


def get_diagnostics(db: Session, run_id: int) -> list[Diagnostic]:
    return db.scalars(
        select(Diagnostic)
        .where(Diagnostic.run_id == run_id)
        .order_by(Diagnostic.t_seconds)
    ).all()


def analyze_run(db: Session, run_id: int) -> dict:
    """Runs the baseline detector against a run's stored telemetry and
    persists results, replacing any previous results from the same
    detector. Returns a summary dict — shared shape used by both the
    REST endpoint and the agent tool.
    """
    points = get_trajectory(db, run_id)
    if not points:
        return {"error": "no_telemetry", "run_id": run_id}

    samples = [TelemetrySample(p.t_seconds, p.cov_xx, p.cov_yy, p.cov_tt) for p in points]
    results = baseline_threshold_detector(samples)

    db.execute(
        delete(Diagnostic).where(
            Diagnostic.run_id == run_id, Diagnostic.detector_name == DETECTOR_NAME
        )
    )
    db.add_all([
        Diagnostic(
            run_id=run_id, t_seconds=r.t_seconds, detector_name=r.detector_name,
            status=r.status, score=r.score,
        )
        for r in results
    ])
    db.commit()

    flagged = sum(1 for r in results if r.status != "normal")
    return {
        "run_id": run_id,
        "detector_name": DETECTOR_NAME,
        "total_points": len(results),
        "flagged_count": flagged,
        "flagged_pct": round(100 * flagged / len(results), 1),
    }


def experiment_run_count(db: Session, experiment_id: int) -> int:
    return db.scalar(select(func.count(Run.id)).where(Run.experiment_id == experiment_id)) or 0
