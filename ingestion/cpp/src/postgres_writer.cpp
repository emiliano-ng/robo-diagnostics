#include "postgres_writer.hpp"

PostgresWriter::PostgresWriter(const std::string& connection_string)
    : conn_(std::make_unique<pqxx::connection>(connection_string)) {}

int PostgresWriter::create_run(int experiment_id, const std::string& source_bag_path) {
    pqxx::work txn(*conn_);
    auto result = txn.exec_params(
        "INSERT INTO runs (experiment_id, source_bag_path, status, started_at) "
        "VALUES ($1, $2, 'ingesting', now()) RETURNING id",
        experiment_id, source_bag_path
    );
    txn.commit();
    return result[0]["id"].as<int>();
}

void PostgresWriter::insert_telemetry_batch(int run_id, const std::vector<TelemetryRow>& rows) {
    pqxx::work txn(*conn_);
    for (const auto& row : rows) {
        txn.exec_params(
            "INSERT INTO telemetry_points "
            "(run_id, t_seconds, x, y, theta, cov_xx, cov_yy, cov_tt, linear_vel, angular_vel) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) "
            "ON CONFLICT (run_id, t_seconds) DO NOTHING",
            run_id, row.t_seconds, row.x, row.y, row.theta,
            row.cov_xx, row.cov_yy, row.cov_tt, row.linear_vel, row.angular_vel
        );
    }
    txn.commit();
}

void PostgresWriter::mark_run_complete(int run_id) {
    pqxx::work txn(*conn_);
    txn.exec_params(
        "UPDATE runs SET status = 'complete', ended_at = now() WHERE id = $1",
        run_id
    );
    txn.commit();
}
