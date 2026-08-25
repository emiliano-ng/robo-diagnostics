# Decisiones de diseño

Registro vivo — cada vez que tomes una decisión no trivial, agrégala aquí
con el "por qué", no solo el "qué". Esto es lo que te va a permitir defender
el proyecto en entrevista sin titubear.

## 2026 — Semana 2: Schema de base de datos

**Decisión:** separar `experiments` / `runs` / `telemetry_points` / `diagnostics`
en 4 tablas en vez de una sola tabla plana.

**Por qué:**
- `experiments` = la configuración/tipo de prueba (grain: una fila por
  "diseño de experimento"). `runs` = cada ejecución concreta (grain: una
  fila por corrida real). Sin esta separación no puedes comparar "run 41
  vs run 42 del mismo experimento" limpiamente.
- `telemetry_points` es el grain más fino (una fila por timestamp). Se
  mantiene separado de `diagnostics` a propósito: telemetría es dato
  *observado*, diagnostics es dato *inferido* por un detector. Mezclarlos
  haría imposible distinguir "esto lo midió el robot" de "esto lo calculó
  mi modelo" — importante si algún día corres dos detectores distintos
  sobre el mismo run y quieres compararlos.

**Trade-off aceptado:** más JOINs para queries que combinan las 4 tablas,
a cambio de que cada tabla tenga un grain claro y defendible.

**Índice elegido:** `(run_id, t_seconds)` en `telemetry_points` — porque
la query dominante del sistema es "dame la serie de tiempo completa de
este run", casi nunca "dame todos los puntos con x > N a través de runs".

## 2026 — Semana 2: Postgres vs. alternativa NoSQL/timeseries

**Decisión:** PostgreSQL plano (no InfluxDB/TimescaleDB) para v1.

**Por qué:** los datos son relacionales por naturaleza (experiment → run →
puntos) y el volumen esperado (decenas de runs, cada uno con miles de
puntos) no justifica la complejidad operativa de un timeseries DB dedicado
todavía. Si el volumen crece mucho, TimescaleDB (extensión de Postgres) es
el upgrade natural sin cambiar de motor.

## Semana 3: Ingesta con timestamps relativos (t_seconds desde t0 del run)

**Decisión:** normalizar cada timestamp de mensaje a "segundos desde el
primer mensaje del run" en vez de guardar el epoch absoluto de ROS.

**Por qué:** permite comparar runs entre sí alineados por tiempo transcurrido
("segundo 15 de este run vs. segundo 15 de aquel run"), que es exactamente
lo que necesita la Semana 7 (comparación de degradación entre corridas).
Guardar el epoch absoluto haría esa comparación mucho más incómoda.

**Trade-off:** perdemos la hora de reloj real del evento salvo que la
reconstruyamos sumando `t0 + t_seconds` — aceptable porque `runs.started_at`
ya guarda esa referencia.

## Pendiente de documentar conforme avances

- [ ] Por qué batch inserts desde C++ en vez de insert por fila
- [ ] Por qué REST y no GraphQL para la API
- [ ] Cómo decidiste el detector baseline vs. el detector ML (semana 7)
- [ ] Qué NO testeaste y por qué
