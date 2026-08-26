import type { Experiment, Run, TelemetryPoint, CompareResult } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, body || `Request failed: ${path}`);
  }
  return res.json() as Promise<T>;
}

export function getExperiments(): Promise<Experiment[]> {
  return apiFetch<Experiment[]>("/experiments");
}

export function getRuns(experimentId: number): Promise<Run[]> {
  return apiFetch<Run[]>(`/experiments/${experimentId}/runs`);
}

export function getTrajectory(runId: number): Promise<TelemetryPoint[]> {
  return apiFetch<TelemetryPoint[]>(`/experiments/runs/${runId}/trajectory`);
}

export function compareRuns(runIds: number[]): Promise<CompareResult> {
  return apiFetch<CompareResult>(`/experiments/compare?run_ids=${runIds.join(",")}`);
}

export { ApiError };
