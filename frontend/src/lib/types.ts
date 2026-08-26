export interface Experiment {
  id: number;
  name: string;
  robot: string;
  algorithm: string;
  environment: string | null;
  created_at: string;
}

export interface Run {
  id: number;
  experiment_id: number;
  status: "ingesting" | "complete" | "failed";
  started_at: string | null;
  ended_at: string | null;
}

export interface TelemetryPoint {
  t_seconds: number;
  x: number;
  y: number;
  theta: number;
  cov_xx: number | null;
  cov_yy: number | null;
  cov_tt: number | null;
  linear_vel: number | null;
  angular_vel: number | null;
}

export type CompareResult = Record<string, TelemetryPoint[]>;
