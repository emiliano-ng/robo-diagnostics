import Link from "next/link";
import { compareRuns } from "@/lib/api";
import CompareTrajectoryChart from "@/components/CompareTrajectoryChart";

export const dynamic = "force-dynamic";

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ ids?: string }>;
}) {
  const { ids } = await searchParams;
  const runIds = (ids ?? "")
    .split(",")
    .map((x) => Number(x.trim()))
    .filter((x) => !Number.isNaN(x));

  if (runIds.length < 2) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-12">
        <Link href="/" className="text-sm text-neutral-500 hover:underline">
          ← Experimentos
        </Link>
        <p className="mt-6 text-neutral-500">
          Selecciona al menos dos runs desde la página de un experimento para compararlos.
        </p>
      </main>
    );
  }

  const data = await compareRuns(runIds);

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <Link href="/" className="text-sm text-neutral-500 hover:underline">
        ← Experimentos
      </Link>
      <h1 className="text-2xl font-semibold mt-2 mb-1">
        Comparación: {runIds.map((id) => `#${id}`).join(" vs ")}
      </h1>
      <p className="text-neutral-500 mb-8">
        Trayectorias superpuestas — busca divergencia entre corridas.
      </p>

      <CompareTrajectoryChart data={data} />
    </main>
  );
}
