#pragma once

#include <memory>
#include <string>
#include <pqxx/pqxx>

// Encapsula la escritura a Postgres. Diseño deliberado (para defender en
// entrevista): una sola conexión + transacción por batch de puntos, no una
// transacción por fila — evita el overhead de 1 INSERT por mensaje de ROS
// cuando un bag puede tener decenas de miles de mensajes.
class PostgresWriter {
public:
    explicit PostgresWriter(const std::string& connection_string);

    // Crea (o reutiliza) el registro de `run` para este bag y devuelve su id.
    int create_run(int experiment_id, const std::string& source_bag_path);

    struct TelemetryRow {
        double t_seconds;
        double x, y, theta;
        double cov_xx, cov_yy, cov_tt;
        double linear_vel, angular_vel;
    };

    // Inserta un batch de filas en una sola transacción.
    // Usa ON CONFLICT DO NOTHING sobre (run_id, t_seconds) para que el
    // script sea re-ejecutable sin duplicar datos (idempotencia).
    void insert_telemetry_batch(int run_id, const std::vector<TelemetryRow>& rows);

    void mark_run_complete(int run_id);

private:
    // unique_ptr: el writer es dueño exclusivo de la conexión — RAII se
    // encarga de cerrarla cuando el objeto sale de scope.
    std::unique_ptr<pqxx::connection> conn_;
};
