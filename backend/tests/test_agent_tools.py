from app.agent import tools


def test_list_experiments_includes_run_count(db_session, sample_experiment, sample_run_with_telemetry):
    result = tools.list_experiments(db_session)

    matching = [e for e in result if e["id"] == sample_experiment.id]
    assert len(matching) == 1
    assert matching[0]["run_count"] == 1


def test_list_runs_for_existing_experiment(db_session, sample_experiment, sample_run_with_telemetry):
    result = tools.list_runs(db_session, sample_experiment.id)

    assert result["experiment_id"] == sample_experiment.id
    assert len(result["runs"]) == 1
    assert result["runs"][0]["id"] == sample_run_with_telemetry.id


def test_list_runs_for_unknown_experiment(db_session):
    result = tools.list_runs(db_session, 999999)
    assert "error" in result


def test_get_run_summary_reports_ranges_not_raw_points(db_session, sample_run_with_telemetry):
    result = tools.get_run_summary(db_session, sample_run_with_telemetry.id)

    assert result["point_count"] == 2
    assert "x_range_meters" in result
    assert "raw_points" not in result  # never leak the raw array into tool output
    assert len(str(result)) < 500  # sanity check: summary stays small


def test_get_run_summary_for_run_without_telemetry(db_session, empty_run):
    result = tools.get_run_summary(db_session, empty_run.id)
    assert result["point_count"] == 0


def test_get_diagnostics_summary_reports_not_analyzed_before_analysis(db_session, run_with_analyzable_telemetry):
    result = tools.get_diagnostics_summary(db_session, run_with_analyzable_telemetry.id)
    assert result["analyzed"] is False


def test_analyze_run_then_diagnostics_summary_reflects_it(db_session, run_with_analyzable_telemetry):
    run_id = run_with_analyzable_telemetry.id

    analyze_result = tools.analyze_run(db_session, run_id)
    assert analyze_result["flagged_count"] >= 2

    summary = tools.get_diagnostics_summary(db_session, run_id)
    assert summary["analyzed"] is True
    assert summary["flagged_count"] == analyze_result["flagged_count"]
    # capped list, not the full flagged set
    assert len(summary["sample_flagged_timestamps"]) <= 15


def test_analyze_run_for_unknown_run(db_session):
    result = tools.analyze_run(db_session, 999999)
    assert "error" in result
