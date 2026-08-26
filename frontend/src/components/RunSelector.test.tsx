import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RunSelector from "./RunSelector";
import type { Run } from "@/lib/types";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const runs: Run[] = [
  { id: 1, experiment_id: 1, status: "complete", started_at: "2026-01-01T00:00:00Z", ended_at: null },
  { id: 2, experiment_id: 1, status: "complete", started_at: "2026-01-02T00:00:00Z", ended_at: null },
  { id: 3, experiment_id: 1, status: "failed", started_at: null, ended_at: null },
];

describe("RunSelector", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders every run with its status badge", () => {
    render(<RunSelector runs={runs} />);

    expect(screen.getByText(/Run #1/)).toBeInTheDocument();
    expect(screen.getByText(/Run #2/)).toBeInTheDocument();
    expect(screen.getAllByText("complete")).toHaveLength(2);
    expect(screen.getByText("failed")).toBeInTheDocument();
  });

  it("keeps the compare button disabled with fewer than 2 runs selected", async () => {
    const user = userEvent.setup();
    render(<RunSelector runs={runs} />);

    const button = screen.getByRole("button", { name: /Comparar seleccionados/ });
    expect(button).toBeDisabled();

    await user.click(screen.getByLabelText(/Seleccionar run 1/));
    expect(button).toBeDisabled();
  });

  it("enables the compare button once 2 runs are selected and navigates on click", async () => {
    const user = userEvent.setup();
    render(<RunSelector runs={runs} />);

    await user.click(screen.getByLabelText(/Seleccionar run 1/));
    await user.click(screen.getByLabelText(/Seleccionar run 2/));

    const button = screen.getByRole("button", { name: /Comparar seleccionados/ });
    expect(button).toBeEnabled();

    await user.click(button);

    expect(mockPush).toHaveBeenCalledWith("/compare?ids=1,2");
  });

  it("un-selecting a run removes it from the comparison", async () => {
    const user = userEvent.setup();
    render(<RunSelector runs={runs} />);

    const checkbox1 = screen.getByLabelText(/Seleccionar run 1/);
    await user.click(checkbox1);
    await user.click(screen.getByLabelText(/Seleccionar run 2/));
    await user.click(checkbox1); // deselect run 1

    const button = screen.getByRole("button", { name: /Comparar seleccionados/ });
    expect(button).toBeDisabled();
  });
});
