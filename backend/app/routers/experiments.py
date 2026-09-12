from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import services
from app.schemas import ExperimentOut, RunOut, TelemetryPointOut, DiagnosticOut, AnalysisSummaryOut

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return services.list_experiments(db)


@router.get("/{experiment_id}/runs", response_model=list[RunOut])
def list_runs(experiment_id: int, db: Session = Depends(get_db)):
    experiment = services.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return services.list_runs(db, experiment_id)


@router.get("/runs/{run_id}/trajectory", response_model=list[TelemetryPointOut])
def get_trajectory(run_id: int, db: Session = Depends(get_db)):
    run = services.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return services.get_trajectory(db, run_id)


@router.get("/compare")
def compare_runs(
    run_ids: str = Query(..., description="Comma-separated run IDs, e.g. '1,2,3'"),
    db: Session = Depends(get_db),
):
    try:
        ids = [int(x) for x in run_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="run_ids must be comma-separated integers")

    if not ids:
        raise HTTPException(status_code=400, detail="At least one run_id is required")

    result = {}
    for run_id in ids:
        run = services.get_run(db, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        points = services.get_trajectory(db, run_id)
        result[run_id] = [TelemetryPointOut.model_validate(p) for p in points]

    return result


@router.post("/runs/{run_id}/diagnostics/analyze", response_model=AnalysisSummaryOut)
def analyze_run(run_id: int, db: Session = Depends(get_db)):
    run = services.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    result = services.analyze_run(db, run_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail="This run has no telemetry to analyze")

    return AnalysisSummaryOut(**result)


@router.get("/runs/{run_id}/diagnostics", response_model=list[DiagnosticOut])
def get_diagnostics(run_id: int, db: Session = Depends(get_db)):
    run = services.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return services.get_diagnostics(db, run_id)
