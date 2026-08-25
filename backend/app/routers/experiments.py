from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models import Experiment, Run, TelemetryPoint
from app.schemas import ExperimentOut, RunOut, TelemetryPointOut

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return db.scalars(select(Experiment).order_by(Experiment.created_at.desc())).all()


@router.get("/{experiment_id}/runs", response_model=list[RunOut])
def list_runs(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db.scalars(
        select(Run).where(Run.experiment_id == experiment_id).order_by(Run.created_at)
    ).all()


@router.get("/runs/{run_id}/trajectory", response_model=list[TelemetryPointOut])
def get_trajectory(run_id: int, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return db.scalars(
        select(TelemetryPoint)
        .where(TelemetryPoint.run_id == run_id)
        .order_by(TelemetryPoint.t_seconds)
    ).all()


@router.get("/compare")
def compare_runs(
    run_ids: str = Query(..., description="Comma-separated run IDs, e.g. '1,2,3'"),
    db: Session = Depends(get_db),
):
    """Devuelve la trayectoria de cada run solicitado, agrupada por run_id.

    Base para la vista de comparación del frontend (Semana 5):
    'Experiment 41 vs 42 vs 43'.
    """
    try:
        ids = [int(x) for x in run_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="run_ids must be comma-separated integers")

    if not ids:
        raise HTTPException(status_code=400, detail="At least one run_id is required")

    result = {}
    for run_id in ids:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        points = db.scalars(
            select(TelemetryPoint)
            .where(TelemetryPoint.run_id == run_id)
            .order_by(TelemetryPoint.t_seconds)
        ).all()

        result[run_id] = [TelemetryPointOut.model_validate(p) for p in points]

    return result
