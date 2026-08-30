"""Run the baseline degradation detector against a real run's telemetry.

Usage:
    python -m app.analysis.run_detector <run_id> [--save]

Without --save, results are only printed — good for validating the
detector against a run with known events (e.g. the var(theta) spikes
already spotted visually around 38s and 73s in slam_run_03) before
trusting it enough to write to the database.
"""

import argparse
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import TelemetryPoint, Diagnostic
from app.analysis.degradation import baseline_threshold_detector, TelemetrySample


def load_samples(run_id: int) -> list[TelemetrySample]:
    db = SessionLocal()
    try:
        points = db.scalars(
            select(TelemetryPoint)
            .where(TelemetryPoint.run_id == run_id)
            .order_by(TelemetryPoint.t_seconds)
        ).all()
        return [
            TelemetrySample(p.t_seconds, p.cov_xx, p.cov_yy, p.cov_tt)
            for p in points
        ]
    finally:
        db.close()


def save_results(run_id: int, results) -> None:
    db = SessionLocal()
    try:
        for r in results:
            db.add(Diagnostic(
                run_id=run_id,
                t_seconds=r.t_seconds,
                detector_name=r.detector_name,
                status=r.status,
                score=r.score,
            ))
        db.commit()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id", type=int)
    parser.add_argument("--save", action="store_true", help="Persist results to the diagnostics table")
    parser.add_argument("--window", type=int, default=30)
    parser.add_argument("--warning-z", type=float, default=3.0)
    parser.add_argument("--degraded-z", type=float, default=5.0)
    args = parser.parse_args()

    samples = load_samples(args.run_id)
    if not samples:
        print(f"No telemetry found for run_id={args.run_id}", file=sys.stderr)
        sys.exit(1)

    results = baseline_threshold_detector(
        samples, window=args.window, warning_z=args.warning_z, degraded_z=args.degraded_z
    )

    flagged = [r for r in results if r.status != "normal"]
    print(f"{len(samples)} points analyzed, {len(flagged)} flagged (warning or degraded)\n")

    for r in flagged:
        print(f"  t={r.t_seconds:7.2f}s  status={r.status:9s}  score={r.score}")

    if args.save:
        save_results(args.run_id, results)
        print(f"\nSaved {len(results)} diagnostic rows for run_id={args.run_id}.")
    else:
        print("\n(dry run — pass --save to persist these results)")


if __name__ == "__main__":
    main()
