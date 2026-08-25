import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import engine, get_db
from app.models import Base, Experiment, Run, TelemetryPoint


@pytest.fixture(scope="session", autouse=True)
def _ensure_schema():
    # Idempotente: no rompe nada si las tablas ya existen (las crea
    # schema.sql en desarrollo normal). Nos asegura que los tests puedan
    # correr incluso en un entorno limpio (ej. CI) sin depender del
    # init script de Docker.
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session():
    """Una conexión + transacción por test. Todo lo que el test haga se
    revierte al final — nunca toca tus datos reales de desarrollo."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection)
    session = TestingSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_experiment(db_session):
    experiment = Experiment(
        name="Test EKF-SLAM run",
        robot="slam_bot",
        algorithm="EKF-SLAM",
        environment="test_env",
    )
    db_session.add(experiment)
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


@pytest.fixture()
def sample_run_with_telemetry(db_session, sample_experiment):
    run = Run(experiment_id=sample_experiment.id, status="complete")
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    points = [
        TelemetryPoint(
            run_id=run.id, t_seconds=0.0, x=0.0, y=0.0, theta=0.0,
            cov_xx=0.01, cov_yy=0.01, cov_tt=0.01,
        ),
        TelemetryPoint(
            run_id=run.id, t_seconds=1.0, x=0.5, y=0.1, theta=0.05,
            cov_xx=0.02, cov_yy=0.02, cov_tt=0.02,
        ),
    ]
    db_session.add_all(points)
    db_session.commit()
    return run
