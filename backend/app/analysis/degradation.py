"""Baseline SLAM degradation detector.

Approach: rolling z-score. For each telemetry point, compare its
covariance values against the mean/std of the preceding window — not
against the whole run — so the detector adapts if "normal" itself drifts
over the course of a run, and so a single early spike doesn't permanently
skew what counts as normal for the rest of the run.

This is deliberately the simplest thing that could work, to serve as a
baseline before comparing against a more sophisticated (e.g. ML-based)
detector later — see docs/decisions.md for why that comparison matters.
"""

from dataclasses import dataclass
from statistics import mean, pstdev

DETECTOR_NAME = "baseline_rolling_zscore"

# Below this many preceding points, we don't trust the baseline statistics
# enough to call anything degraded — an early transient with only a
# handful of points behind it isn't evidence of anything, and real runs
# spend their first second or so still converging (EKF settling), which
# would otherwise get flagged as "anomalous" against an unrepresentative
# baseline.
MIN_WINDOW_POINTS = 15

# Avoids division by absurdly tiny numbers when the window has near-zero
# variance. Set relative to the actual scale of EKF covariance values
# observed in practice (roughly 1e-3 to a few units) — 1e-6 was too small
# and produced z-scores in the hundreds from ordinary sensor jitter during
# flat segments.
STD_EPSILON = 1e-4

# Reported/stored scores are capped here for readability — an uncapped
# z-score can read triple digits when a window happens to have near-zero
# variance (see STD_EPSILON above), which is technically "more degraded
# than degraded" but not meaningfully more informative than a score of
# 15. Classification is decided BEFORE capping, so this never changes a
# point's status, only how its score displays.
SCORE_CAP = 50.0


@dataclass
class TelemetrySample:
    t_seconds: float
    cov_xx: float | None
    cov_yy: float | None
    cov_tt: float | None


@dataclass
class DiagnosticResult:
    t_seconds: float
    detector_name: str
    status: str  # "normal" | "warning" | "degraded"
    score: float | None


def _zscore(value: float, window_values: list[float]) -> float:
    m = mean(window_values)
    s = max(pstdev(window_values), STD_EPSILON)
    return abs(value - m) / s


def baseline_threshold_detector(
    samples: list[TelemetrySample],
    window: int = 30,
    warning_z: float = 3.0,
    degraded_z: float = 5.0,
) -> list[DiagnosticResult]:
    """Flag points whose covariance deviates sharply from the preceding
    window across any of the tracked features (x, y, theta variance).

    The reported score is the MAX z-score across features, not the
    average — a spike in a single feature (e.g. only var(theta) during a
    sharp turn) is exactly the kind of localized event we want to catch,
    and averaging it against two calm features would dilute it away.

    A raw per-point z-score classifier alone is too noisy in practice:
    against real slam_bot telemetry it flagged ~25% of all points, mostly
    single-sample blips from ordinary sensor jitter. This function
    requires a deviation to be confirmed by an immediate neighbor (the
    previous or next point) before elevating status above "normal" — a
    real degradation event (sensor dropout, sharp unmodeled turn) shows
    up as a short sustained cluster, not a single isolated sample. This
    is the same lesson as temporal-consistency approaches in change/event
    detection generally: a single-frame spike is cheap to produce from
    noise; a 2+ point run is much less likely to be coincidental.
    """
    raw_z: list[float | None] = []
    features = ("cov_xx", "cov_yy", "cov_tt")

    for i, sample in enumerate(samples):
        window_samples = samples[max(0, i - window):i]

        if len(window_samples) < MIN_WINDOW_POINTS:
            raw_z.append(None)
            continue

        max_z = 0.0
        for feature in features:
            current = getattr(sample, feature)
            window_values = [
                v for v in (getattr(s, feature) for s in window_samples) if v is not None
            ]
            if current is None or len(window_values) < MIN_WINDOW_POINTS:
                continue
            max_z = max(max_z, _zscore(current, window_values))

        raw_z.append(max_z)

    def exceeds(idx: int, threshold: float) -> bool:
        z = raw_z[idx]
        return z is not None and z >= threshold

    results: list[DiagnosticResult] = []
    for i, sample in enumerate(samples):
        z = raw_z[i]
        if z is None:
            results.append(DiagnosticResult(sample.t_seconds, DETECTOR_NAME, "normal", None))
            continue

        prev_exceeds = exceeds(i - 1, warning_z) if i > 0 else False
        next_exceeds = exceeds(i + 1, warning_z) if i < len(samples) - 1 else False
        confirmed = exceeds(i, warning_z) and (prev_exceeds or next_exceeds)

        if confirmed and z >= degraded_z:
            status = "degraded"
        elif confirmed and z >= warning_z:
            status = "warning"
        else:
            status = "normal"

        results.append(DiagnosticResult(sample.t_seconds, DETECTOR_NAME, status, round(min(z, SCORE_CAP), 3)))

    return results
