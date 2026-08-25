# Robotics Experiment & Diagnostics Platform

Sistema para ingerir, almacenar, analizar y diagnosticar experimentos de robótica
(inicialmente EKF-SLAM sobre `slam_bot`), detectando automáticamente degradación
de la estimación a partir de telemetría real.

## Arquitectura

```
ROS2 / Gazebo (slam_bot)
        │
        ▼
   rosbag2 (.db3)
        │
        ▼
 Ingestion (C++ / Python)
        │
        ▼
   PostgreSQL
        │
   ┌────┴────┐
   ▼         ▼
Analysis   FastAPI
 Engine     (REST)
   │         │
   └────┬────┘
        ▼
  React / TypeScript
```

## Estructura del repo

```
db/              -> schema SQL + migraciones
backend/         -> FastAPI (Python) - API REST
ingestion/cpp/   -> nodo C++ que lee rosbag2 y escribe a Postgres
frontend/        -> React + TypeScript (semana 5)
.github/workflows/ -> CI
docker-compose.yml
```

## Cómo levantar el entorno de desarrollo (Postgres)

```bash
docker compose up -d db
```

Esto levanta Postgres en `localhost:5432` con el schema ya aplicado
(ver `db/schema.sql`, montado como init script).

## Estado actual (Semana 2)

- [x] Estructura del repo
- [x] Schema de base de datos diseñado
- [x] Docker Compose con Postgres
- [ ] Ingesta C++ desde rosbag2 (Semana 3)
- [ ] API FastAPI (Semana 4)
- [ ] Frontend React (Semana 5)
- [ ] Docker completo + CI (Semana 6)
- [ ] Detector de degradación SLAM (Semana 7)
- [ ] Pulido + demo (Semana 8)

## Decisiones de diseño (para defender en entrevista)

Ver `docs/decisions.md` — se va llenando conforme avanza el proyecto.
Cada decisión no trivial (por qué Postgres, por qué este schema, por qué
esta arquitectura de ingesta) se documenta ahí con el razonamiento, no
solo el resultado.
