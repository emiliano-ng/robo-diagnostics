"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { TelemetryPoint } from "@/lib/types";

export default function TrajectoryChart({ points }: { points: TelemetryPoint[] }) {
  // x vs y (no t_seconds aquí) para dibujar la forma real de la trayectoria,
  // no una serie de tiempo.
  const data = points.map((p) => ({ x: p.x, y: p.y }));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
        <XAxis dataKey="x" type="number" name="x (m)" tick={{ fontSize: 12 }} />
        <YAxis dataKey="y" type="number" name="y (m)" tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value) => (typeof value === "number" ? value.toFixed(3) : value)}
          labelFormatter={() => ""}
        />
        <Line
          type="monotone"
          dataKey="y"
          stroke="#2563eb"
          dot={false}
          strokeWidth={1.5}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
