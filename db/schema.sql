-- Robotics Experiment & Diagnostics Platform — schema inicial (Semana 2)
--
-- Grain de cada tabla (pregúntate esto en cada tabla — te lo van a preguntar
-- en entrevista):
--   experiments      -> una fila por "tipo de prueba" (ej. "EKF-SLAM indoor v1")
--   runs             -> una fila por CADA ejecución concreta de un experimento
--   telemetry_points -> una fila por (run, timestamp) — el grain más fino
--   diagnostics      -> una fila por (run, timestamp, detector) — salida del
--                        detector de degradación (Semana 7)

CREATE TABLE experiments (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    robot        TEXT NOT NULL,          -- ej. 'slam_bot'
    algorithm    TEXT NOT NULL,          -- ej. 'EKF-SLAM'
    environment  TEXT,                   -- ej. 'gazebo_warehouse_03'
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE runs (
    id              SERIAL PRIMARY KEY,
    experiment_id   INTEGER NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    source_bag_path TEXT,                -- path/nombre del rosbag2 original
    status          TEXT NOT NULL DEFAULT 'ingesting'
                        CHECK (status IN ('ingesting', 'complete', 'failed')),
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_runs_experiment ON runs(experiment_id);

-- Telemetría cruda: una fila por timestamp dentro de un run.
-- Guardamos covarianza diagonal simplificada (xx, yy, theta-theta) — suficiente
-- para el detector de degradación de Semana 7 sin modelar la matriz completa.
CREATE TABLE telemetry_points (
    id             BIGSERIAL PRIMARY KEY,
    run_id         INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    t_seconds      DOUBLE PRECISION NOT NULL,  -- segundos desde el inicio del run
    x              DOUBLE PRECISION NOT NULL,
    y              DOUBLE PRECISION NOT NULL,
    theta          DOUBLE PRECISION NOT NULL,
    cov_xx         DOUBLE PRECISION,
    cov_yy         DOUBLE PRECISION,
    cov_tt         DOUBLE PRECISION,
    linear_vel     DOUBLE PRECISION,
    angular_vel    DOUBLE PRECISION,
    tracking_rate  DOUBLE PRECISION,           -- % de mensajes esperados recibidos
    latency_ms     DOUBLE PRECISION,

    UNIQUE (run_id, t_seconds)
);

-- Índice compuesto: casi todas las queries van a ser "dame la serie de tiempo
-- de este run" -> (run_id, t_seconds) cubre eso directamente.
CREATE INDEX idx_telemetry_run_t ON telemetry_points(run_id, t_seconds);

-- Salida del detector de degradación (Semana 7). Separado de telemetry_points
-- a propósito: distintos detectores pueden correr sobre el mismo run, y no
-- queremos mezclar datos "observados" con datos "inferidos".
CREATE TABLE diagnostics (
    id            BIGSERIAL PRIMARY KEY,
    run_id        INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    t_seconds     DOUBLE PRECISION NOT NULL,
    detector_name TEXT NOT NULL,               -- ej. 'baseline_threshold', 'iforest_v1'
    status        TEXT NOT NULL
                      CHECK (status IN ('normal', 'warning', 'degraded')),
    score         DOUBLE PRECISION,            -- score crudo del detector

    UNIQUE (run_id, t_seconds, detector_name)
);

CREATE INDEX idx_diagnostics_run ON diagnostics(run_id);
