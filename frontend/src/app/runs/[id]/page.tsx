import Link from "next/link";
import { getTrajectory, getDiagnostics } from "@/lib/api";
import TrajectoryChart from "@/components/TrajectoryChart";
import CovarianceChart from "@/components/CovarianceChart";
import AnalyzeButton from "@/components/AnalyzeButton";

export const dynamic = "force-dynamic";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const runId = Number(id);
  const [points, diagnostics] = await Promise.all([
    getTrajectory(runId),
    getDiagnostics(runId),
  ]);

  const flaggedCount = diagnostics.filter((d) => d.status !== "normal").length;
  const flaggedPct = diagnostics.length > 0 ? (100 * flaggedCount) / diagnostics.length : 0;

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <Link href="/" className="text-sm text-neutral-500 hover:underline">
        ← Experimentos
      </Link>
      <h1 className="text-2xl font-semibold mt-2 mb-8">Run #{runId}</h1>

      {points.length === 0 ? (
        <p className="text-neutral-500">Este run no tiene telemetría ingerida.</p>
      ) : (
        <div className="space-y-10">
          <section>
            <h2 className="text-sm font-medium text-neutral-500 uppercase tracking-wide mb-3">
              Trayectoria estimada (x, y)
            </h2>
            <TrajectoryChart points={points} />
          </section>

          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-neutral-500 uppercase tracking-wide">
                Covarianza del filtro EKF a lo largo del tiempo
              </h2>
              <AnalyzeButton runId={runId} />
            </div>

            {diagnostics.length === 0 ? (
              <p className="text-sm text-neutral-500 mb-3">
                Aún no se ha analizado este run — dale clic a &quot;Analizar
                degradación&quot; para correr el detector.
              </p>
            ) : (
              <p className="text-sm text-neutral-500 mb-3">
                <span className="font-medium text-neutral-700">
                  {flaggedCount} de {diagnostics.length} puntos
                </span>{" "}
                marcados para revisión ({flaggedPct.toFixed(1)}%). Puntos
                amarillos/rojos sobre el eje de tiempo indican desviación
                confirmada (warning/degraded) respecto al comportamiento
                reciente del filtro.
              </p>
            )}

            <CovarianceChart points={points} diagnostics={diagnostics} />
          </section>

          <p className="text-sm text-neutral-400">{points.length} puntos de telemetría</p>
        </div>
      )}
    </main>
  );
}
