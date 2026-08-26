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
import type { TelemetryPoint } from "@/lib/types";

export default function CovarianceChart({ points }: { points: TelemetryPoint[] }) {
  const data = points.map((p) => ({
    t: p.t_seconds,
    "var(x)": p.cov_xx,
    "var(y)": p.cov_yy,
    "var(θ)": p.cov_tt,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
        <XAxis
          dataKey="t"
          type="number"
          name="tiempo (s)"
          tick={{ fontSize: 12 }}
          label={{ value: "segundos", position: "insideBottom", offset: -5, fontSize: 12 }}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value) => (typeof value === "number" ? value.toFixed(5) : value)} />
        <Legend />
        <Line type="monotone" dataKey="var(x)" stroke="#2563eb" dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="var(y)" stroke="#dc2626" dot={false} isAnimationActive={false} />
        <Line type="monotone" dataKey="var(θ)" stroke="#16a34a" dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
