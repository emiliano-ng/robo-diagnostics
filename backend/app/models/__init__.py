from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Float, TIMESTAMP,
    ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    robot = Column(Text, nullable=False)
    algorithm = Column(Text, nullable=False)
    environment = Column(Text)
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    runs = relationship("Run", back_populates="experiment", cascade="all, delete")


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    source_bag_path = Column(Text)
    status = Column(Text, nullable=False, default="ingesting")
    started_at = Column(TIMESTAMP(timezone=True))
    ended_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('ingesting','complete','failed')", name="ck_run_status"),
    )

    experiment = relationship("Experiment", back_populates="runs")
    telemetry = relationship("TelemetryPoint", back_populates="run", cascade="all, delete")


class TelemetryPoint(Base):
    __tablename__ = "telemetry_points"

    id = Column(BigInteger, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    t_seconds = Column(Float, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    theta = Column(Float, nullable=False)
    cov_xx = Column(Float)
    cov_yy = Column(Float)
    cov_tt = Column(Float)
    linear_vel = Column(Float)
    angular_vel = Column(Float)
    tracking_rate = Column(Float)
    latency_ms = Column(Float)

    __table_args__ = (
        UniqueConstraint("run_id", "t_seconds", name="uq_telemetry_run_t"),
    )

    run = relationship("Run", back_populates="telemetry")


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id = Column(BigInteger, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    t_seconds = Column(Float, nullable=False)
    detector_name = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    score = Column(Float)

    __table_args__ = (
        UniqueConstraint("run_id", "t_seconds", "detector_name", name="uq_diag_run_t_detector"),
        CheckConstraint("status IN ('normal','warning','degraded')", name="ck_diag_status"),
    )
