"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { CompareResult } from "@/lib/types";

const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"];

export default function CompareTrajectoryChart({ data }: { data: CompareResult }) {
  const runIds = Object.keys(data);

  // Merge por índice de punto (asumiendo trayectorias de forma comparable;
  // suficiente para visualizar divergencia de forma general).
  const maxLen = Math.max(...runIds.map((id) => data[id].length));
  const merged = Array.from({ length: maxLen }, (_, i) => {
    const row: Record<string, number | undefined> = { idx: i };
    for (const runId of runIds) {
      row[`run_${runId}_x`] = data[runId][i]?.x;
      row[`run_${runId}_y`] = data[runId][i]?.y;
    }
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={420}>
      <LineChart data={merged} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
        <XAxis dataKey="idx" tick={{ fontSize: 12 }} label={{ value: "punto #", position: "insideBottom", offset: -5, fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} label={{ value: "y (m)", angle: -90, position: "insideLeft", fontSize: 12 }} />
        <Tooltip formatter={(value) => (typeof value === "number" ? value.toFixed(3) : value)} />
        <Legend />
        {runIds.map((runId, i) => (
          <Line
            key={runId}
            type="monotone"
            dataKey={`run_${runId}_y`}
            name={`Run #${runId}`}
            stroke={COLORS[i % COLORS.length]}
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
