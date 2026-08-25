def test_list_experiments_returns_created_experiment(client, sample_experiment):
    response = client.get("/experiments")
    assert response.status_code == 200
    data = response.json()
    assert any(e["id"] == sample_experiment.id for e in data)
    assert any(e["name"] == "Test EKF-SLAM run" for e in data)


def test_list_runs_for_existing_experiment(client, sample_experiment, sample_run_with_telemetry):
    response = client.get(f"/experiments/{sample_experiment.id}/runs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_run_with_telemetry.id
    assert data[0]["status"] == "complete"


def test_list_runs_for_nonexistent_experiment_returns_404(client):
    response = client.get("/experiments/999999/runs")
    assert response.status_code == 404


def test_get_trajectory_returns_points_ordered_by_time(client, sample_run_with_telemetry):
    response = client.get(f"/experiments/runs/{sample_run_with_telemetry.id}/trajectory")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # confirma orden por t_seconds, no por orden de inserción arbitrario
    assert data[0]["t_seconds"] < data[1]["t_seconds"]
    assert data[0]["x"] == 0.0
    assert data[1]["x"] == 0.5


def test_get_trajectory_for_nonexistent_run_returns_404(client):
    response = client.get("/experiments/runs/999999/trajectory")
    assert response.status_code == 404


def test_compare_runs_groups_by_run_id(client, sample_run_with_telemetry):
    run_id = sample_run_with_telemetry.id
    response = client.get(f"/experiments/compare?run_ids={run_id}")
    assert response.status_code == 200
    data = response.json()
    assert str(run_id) in data
    assert len(data[str(run_id)]) == 2


def test_compare_runs_with_unknown_id_returns_404(client, sample_run_with_telemetry):
    run_id = sample_run_with_telemetry.id
    response = client.get(f"/experiments/compare?run_ids={run_id},999999")
    assert response.status_code == 404


def test_compare_runs_rejects_malformed_ids(client):
    response = client.get("/experiments/compare?run_ids=abc,def")
    assert response.status_code == 400
