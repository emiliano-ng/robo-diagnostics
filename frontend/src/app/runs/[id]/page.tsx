import Link from "next/link";
import { getTrajectory } from "@/lib/api";
import TrajectoryChart from "@/components/TrajectoryChart";
import CovarianceChart from "@/components/CovarianceChart";

export const dynamic = "force-dynamic";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const runId = Number(id);
  const points = await getTrajectory(runId);

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
            <h2 className="text-sm font-medium text-neutral-500 uppercase tracking-wide mb-3">
              Covarianza del filtro EKF a lo largo del tiempo
            </h2>
            <p className="text-sm text-neutral-500 mb-3">
              Crecimientos sostenidos aquí son la señal que el detector de
              degradación de la Semana 7 va a aprender a marcar.
            </p>
            <CovarianceChart points={points} />
          </section>

          <p className="text-sm text-neutral-400">{points.length} puntos de telemetría</p>
        </div>
      )}
    </main>
  );
}
