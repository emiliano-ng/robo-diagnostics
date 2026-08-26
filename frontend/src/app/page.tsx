import Link from "next/link";
import { getExperiments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const experiments = await getExperiments();

  return (
    <main className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-semibold mb-1">Robotics Experiment &amp; Diagnostics Platform</h1>
      <p className="text-neutral-500 mb-8">
        Experimentos registrados — selecciona uno para ver sus corridas.
      </p>

      {experiments.length === 0 ? (
        <p className="text-neutral-500">
          No hay experimentos todavía. Ingiere un bag con{" "}
          <code className="bg-neutral-100 px-1.5 py-0.5 rounded">ingest_run</code>.
        </p>
      ) : (
        <ul className="divide-y divide-neutral-200 border border-neutral-200 rounded-lg overflow-hidden">
          {experiments.map((exp) => (
            <li key={exp.id}>
              <Link
                href={`/experiments/${exp.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-neutral-50 transition-colors"
              >
                <div>
                  <p className="font-medium">{exp.name}</p>
                  <p className="text-sm text-neutral-500">
                    {exp.robot} · {exp.algorithm}
                    {exp.environment ? ` · ${exp.environment}` : ""}
                  </p>
                </div>
                <span className="text-sm text-neutral-400">
                  {new Date(exp.created_at).toLocaleDateString()}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
