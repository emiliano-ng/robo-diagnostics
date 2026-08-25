from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    robot: str
    algorithm: str
    environment: str | None
    created_at: datetime


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    status: str
    started_at: datetime | None
    ended_at: datetime | None


class TelemetryPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    t_seconds: float
    x: float
    y: float
    theta: float
    cov_xx: float | None
    cov_yy: float | None
    cov_tt: float | None
    linear_vel: float | None
    angular_vel: float | None
