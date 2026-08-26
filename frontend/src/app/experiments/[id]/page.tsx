import Link from "next/link";
import { getRuns } from "@/lib/api";
import RunSelector from "@/components/RunSelector";

export const dynamic = "force-dynamic";

export default async function ExperimentRunsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const experimentId = Number(id);
  const runs = await getRuns(experimentId);

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <Link href="/" className="text-sm text-neutral-500 hover:underline">
        ← Experimentos
      </Link>
      <h1 className="text-2xl font-semibold mt-2 mb-1">Corridas del experimento #{experimentId}</h1>
      <p className="text-neutral-500 mb-8">
        Selecciona dos o más para comparar sus trayectorias.
      </p>

      {runs.length === 0 ? (
        <p className="text-neutral-500">Este experimento todavía no tiene corridas ingeridas.</p>
      ) : (
        <RunSelector runs={runs} />
      )}
    </main>
  );
}
