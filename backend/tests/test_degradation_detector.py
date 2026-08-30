from app.analysis.degradation import baseline_threshold_detector, TelemetrySample


def flat_samples(n: int, cov_value: float = 0.01) -> list[TelemetrySample]:
    return [
        TelemetrySample(t_seconds=float(i), cov_xx=cov_value, cov_yy=cov_value, cov_tt=cov_value)
        for i in range(n)
    ]


def test_flat_baseline_is_all_normal():
    samples = flat_samples(50, cov_value=0.01)

    results = baseline_threshold_detector(samples)

    assert all(r.status == "normal" for r in results)


def test_early_points_are_normal_regardless_of_value():
    # With fewer than MIN_WINDOW_POINTS behind them, there's no baseline
    # to compare against — they should never be flagged, even if their
    # raw value would look extreme in isolation.
    samples = [
        TelemetrySample(t_seconds=0.0, cov_xx=0.01, cov_yy=0.01, cov_tt=0.01),
        TelemetrySample(t_seconds=1.0, cov_xx=5.0, cov_yy=5.0, cov_tt=5.0),
    ]

    results = baseline_threshold_detector(samples)

    assert all(r.status == "normal" for r in results)
    assert all(r.score is None for r in results)


def test_sharp_sustained_spike_is_flagged_degraded():
    # A short but sustained event (3 consecutive points) — the shape a
    # real sensor dropout or sharp turn actually produces, as opposed to
    # the single-sample noise blip covered by the isolated-spike test.
    samples = flat_samples(30, cov_value=0.01)
    for t in (30.0, 31.0, 32.0):
        samples.append(TelemetrySample(t_seconds=t, cov_xx=0.01, cov_yy=0.01, cov_tt=5.0))
    samples.extend(flat_samples(10, cov_value=0.01))
    for i, s in enumerate(samples[33:], start=33):
        samples[i] = TelemetrySample(t_seconds=float(i), cov_xx=s.cov_xx, cov_yy=s.cov_yy, cov_tt=s.cov_tt)

    results = baseline_threshold_detector(samples)

    assert results[30].status == "degraded"
    assert results[31].status == "degraded"
    # The 3rd point of a sustained cluster can read as less extreme than
    # the first two: by this point, the earlier anomalous samples have
    # entered its own baseline window, raising the window's mean/std and
    # making the deviation look smaller relative to a now-contaminated
    # baseline. This is a known limitation of naive rolling-window
    # detectors — flagged either way, just not necessarily still at the
    # highest severity.
    assert results[32].status in ("warning", "degraded")
    assert results[30].score is not None and results[30].score >= 4.0

    # points well after the spike, once it's out of the window, should
    # settle back to normal
    assert results[-1].status == "normal"


def jittered_samples(n: int, base: float = 0.01, jitter: float = 0.0008) -> list[TelemetrySample]:
    # Alternating small jitter — deterministic (no randomness needed for
    # a reproducible test), but gives the window a realistic non-zero
    # std, unlike perfectly flat synthetic data.
    return [
        TelemetrySample(
            t_seconds=float(i),
            cov_xx=base + (jitter if i % 2 == 0 else -jitter),
            cov_yy=base + (jitter if i % 2 == 0 else -jitter),
            cov_tt=base + (jitter if i % 2 == 0 else -jitter),
        )
        for i in range(n)
    ]


def test_moderate_sustained_deviation_is_flagged_warning_not_degraded():
    samples = jittered_samples(30)
    # Two consecutive moderate deviations — sustained, not an isolated
    # blip, so the temporal-consistency check confirms it. Should cross
    # the warning threshold without reaching degraded.
    samples.append(TelemetrySample(t_seconds=30.0, cov_xx=0.01, cov_yy=0.01, cov_tt=0.014))
    samples.append(TelemetrySample(t_seconds=31.0, cov_xx=0.01, cov_yy=0.01, cov_tt=0.014))

    results = baseline_threshold_detector(samples, warning_z=2.5, degraded_z=100.0)

    assert results[30].status == "warning"
    assert results[31].status == "warning"


def test_zero_variance_window_does_not_crash_on_matching_value():
    # A perfectly flat window (std = 0) followed by an identical value
    # must not raise a ZeroDivisionError and must score as normal.
    samples = flat_samples(25, cov_value=0.02)

    results = baseline_threshold_detector(samples)

    assert results[-1].status == "normal"


def test_isolated_single_point_spike_is_downgraded_to_normal():
    # A single-sample blip — surrounded by otherwise flat data — should
    # NOT be confirmed as an anomaly, even though its raw z-score alone
    # would clear the threshold. This is the fix for the real over-
    # flagging problem found against slam_run_03 (25% of all points
    # flagged from isolated single-sample noise).
    samples = flat_samples(30, cov_value=0.01)
    samples.append(TelemetrySample(t_seconds=30.0, cov_xx=0.01, cov_yy=0.01, cov_tt=5.0))
    samples.extend(flat_samples(10, cov_value=0.01))
    for i, s in enumerate(samples[31:], start=31):
        samples[i] = TelemetrySample(t_seconds=float(i), cov_xx=s.cov_xx, cov_yy=s.cov_yy, cov_tt=s.cov_tt)

    results = baseline_threshold_detector(samples)

    # The raw score is still reported (transparency — nothing hidden)...
    assert results[30].score is not None and results[30].score > 5.0
    # ...but status is NOT elevated, because no neighboring point confirms it.
    assert results[30].status == "normal"


def test_sustained_two_point_cluster_is_confirmed_and_flagged():
    samples = flat_samples(30, cov_value=0.01)
    # Two consecutive spiking points — a real sustained event, not noise.
    samples.append(TelemetrySample(t_seconds=30.0, cov_xx=0.01, cov_yy=0.01, cov_tt=5.0))
    samples.append(TelemetrySample(t_seconds=31.0, cov_xx=0.01, cov_yy=0.01, cov_tt=5.0))
    samples.extend(flat_samples(10, cov_value=0.01))
    for i, s in enumerate(samples[32:], start=32):
        samples[i] = TelemetrySample(t_seconds=float(i), cov_xx=s.cov_xx, cov_yy=s.cov_yy, cov_tt=s.cov_tt)

    results = baseline_threshold_detector(samples)

    assert results[30].status == "degraded"
    assert results[31].status == "degraded"


def test_detector_name_is_attached_to_every_result():
    samples = flat_samples(10)

    results = baseline_threshold_detector(samples)

    assert all(r.detector_name == "baseline_rolling_zscore" for r in results)


def test_tiny_realistic_jitter_on_near_flat_window_does_not_blow_up_score():
    # Regression test for a real bug found against actual slam_bot data:
    # with a near-zero window std and STD_EPSILON too small (1e-6), a
    # perfectly ordinary sensor jitter produced absurd scores (200-300)
    # instead of a reasonable one. Covariance values here are on the same
    # order of magnitude as real EKF output (~0.01).
    samples = flat_samples(30, cov_value=0.0100)
    # A tiny, realistic bump — not a real anomaly, just float-level noise.
    samples.append(TelemetrySample(t_seconds=30.0, cov_xx=0.01, cov_yy=0.01, cov_tt=0.0101))

    results = baseline_threshold_detector(samples)

    assert results[30].score is not None
    assert results[30].score < 20, (
        f"score={results[30].score} — a tiny bump should not produce a triple-digit z-score"
    )


def test_extreme_deviation_score_is_capped_but_still_classified_correctly():
    samples = flat_samples(30, cov_value=0.01)
    # A genuinely enormous jump — the kind that, uncapped, would produce
    # a triple-digit z-score against an almost-zero-variance baseline.
    samples.append(TelemetrySample(t_seconds=30.0, cov_xx=0.01, cov_yy=0.01, cov_tt=500.0))
    samples.append(TelemetrySample(t_seconds=31.0, cov_xx=0.01, cov_yy=0.01, cov_tt=500.0))

    results = baseline_threshold_detector(samples)

    assert results[30].status == "degraded"
    assert results[30].score is not None and results[30].score <= 50.0
