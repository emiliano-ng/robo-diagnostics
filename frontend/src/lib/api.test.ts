import { describe, it, expect, vi, beforeEach } from "vitest";
import { getExperiments, getTrajectory, ApiError } from "./api";

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("getExperiments returns parsed JSON on success", async () => {
    const mockExperiments = [
      { id: 1, name: "Test", robot: "slam_bot", algorithm: "EKF-SLAM", environment: null, created_at: "2026-01-01T00:00:00Z" },
    ];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockExperiments,
    } as Response);

    const result = await getExperiments();

    expect(result).toEqual(mockExperiments);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/experiments"),
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("throws ApiError with the response status when the request fails", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: async () => "Run not found",
    } as Response);

    await expect(getTrajectory(999)).rejects.toMatchObject({
      status: 404,
      message: "Run not found",
    });
  });

  it("throws an instance of ApiError specifically, not a generic Error", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => "",
    } as Response);

    await expect(getTrajectory(1)).rejects.toBeInstanceOf(ApiError);
  });
});
