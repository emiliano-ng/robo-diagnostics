"use client";

import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceDot,
  ResponsiveContainer,
} from "recharts";
import type { TelemetryPoint, Diagnostic } from "@/lib/types";

const STATUS_COLOR: Record<string, string> = {
  warning: "#d97706",
  degraded: "#dc2626",
};

export default function CovarianceChart({
  points,
  diagnostics = [],
}: {
  points: TelemetryPoint[];
  diagnostics?: Diagnostic[];
}) {
  const data = points.map((p) => ({
    t: p.t_seconds,
    "var(x)": p.cov_xx,
    "var(y)": p.cov_yy,
    "var(θ)": p.cov_tt,
  }));

  const flagged = diagnostics.filter((d) => d.status !== "normal");

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
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

        {/* Marcadores de puntos señalados por el detector, sobre el eje
            de tiempo (y=0) — amarillo para warning, rojo para degraded. */}
        {flagged.map((d, i) => (
          <ReferenceDot
            key={`${d.t_seconds}-${i}`}
            x={d.t_seconds}
            y={0}
            r={3}
            fill={STATUS_COLOR[d.status]}
            stroke="none"
            ifOverflow="extendDomain"
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
