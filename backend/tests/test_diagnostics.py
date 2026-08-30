def test_analyze_run_persists_diagnostics_and_returns_summary(client, run_with_analyzable_telemetry):
    run_id = run_with_analyzable_telemetry.id

    response = client.post(f"/experiments/runs/{run_id}/diagnostics/analyze")

    assert response.status_code == 200
    summary = response.json()
    assert summary["run_id"] == run_id
    assert summary["detector_name"] == "baseline_rolling_zscore"
    assert summary["total_points"] == 32  # 30 flat + 2-point spike
    assert summary["flagged_count"] >= 2  # at least the sustained spike
    assert 0 < summary["flagged_pct"] < 100


def test_diagnostics_are_retrievable_after_analysis(client, run_with_analyzable_telemetry):
    run_id = run_with_analyzable_telemetry.id
    client.post(f"/experiments/runs/{run_id}/diagnostics/analyze")

    response = client.get(f"/experiments/runs/{run_id}/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 32
    # ordered by time
    assert data[0]["t_seconds"] < data[-1]["t_seconds"]
    # the sustained spike near the end should be flagged
    flagged = [d for d in data if d["status"] != "normal"]
    assert len(flagged) >= 2


def test_analyze_is_idempotent_and_replaces_previous_results(client, run_with_analyzable_telemetry):
    run_id = run_with_analyzable_telemetry.id

    client.post(f"/experiments/runs/{run_id}/diagnostics/analyze")
    client.post(f"/experiments/runs/{run_id}/diagnostics/analyze")  # re-run

    response = client.get(f"/experiments/runs/{run_id}/diagnostics")

    # Re-analyzing must not leave duplicate rows from the previous run.
    assert len(response.json()) == 32


def test_analyze_nonexistent_run_returns_404(client):
    response = client.post("/experiments/runs/999999/diagnostics/analyze")
    assert response.status_code == 404


def test_analyze_run_without_telemetry_returns_400(client, empty_run):
    response = client.post(f"/experiments/runs/{empty_run.id}/diagnostics/analyze")
    assert response.status_code == 400


def test_get_diagnostics_for_nonexistent_run_returns_404(client):
    response = client.get("/experiments/runs/999999/diagnostics")
    assert response.status_code == 404


def test_get_diagnostics_before_analysis_returns_empty_list(client, run_with_analyzable_telemetry):
    # Telemetry exists, but /analyze was never called — diagnostics is a
    # separate table, so this should be an empty list, not an error.
    response = client.get(f"/experiments/runs/{run_with_analyzable_telemetry.id}/diagnostics")
    assert response.status_code == 200
    assert response.json() == []
