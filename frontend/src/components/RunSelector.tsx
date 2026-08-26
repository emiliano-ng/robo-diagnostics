"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import type { Run } from "@/lib/types";

const statusStyles: Record<Run["status"], string> = {
  complete: "bg-green-100 text-green-700",
  ingesting: "bg-yellow-100 text-yellow-700",
  failed: "bg-red-100 text-red-700",
};

export default function RunSelector({ runs }: { runs: Run[] }) {
  const [selected, setSelected] = useState<number[]>([]);
  const router = useRouter();

  function toggle(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function goCompare() {
    if (selected.length < 2) return;
    router.push(`/compare?ids=${selected.join(",")}`);
  }

  return (
    <div>
      <ul className="divide-y divide-neutral-200 border border-neutral-200 rounded-lg overflow-hidden mb-4">
        {runs.map((run) => (
          <li key={run.id} className="flex items-center gap-3 px-5 py-4">
            <input
              type="checkbox"
              checked={selected.includes(run.id)}
              onChange={() => toggle(run.id)}
              aria-label={`Seleccionar run ${run.id} para comparar`}
              className="h-4 w-4"
            />
            <Link href={`/runs/${run.id}`} className="flex-1 hover:underline">
              Run #{run.id}
              {run.started_at && (
                <span className="text-sm text-neutral-500 ml-2">
                  {new Date(run.started_at).toLocaleString()}
                </span>
              )}
            </Link>
            <span
              className={`text-xs px-2 py-1 rounded-full font-medium ${statusStyles[run.status]}`}
            >
              {run.status}
            </span>
          </li>
        ))}
      </ul>

      <button
        onClick={goCompare}
        disabled={selected.length < 2}
        className="px-4 py-2 rounded-md bg-neutral-900 text-white text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:bg-neutral-700 transition-colors"
      >
        Comparar seleccionados ({selected.length})
      </button>
    </div>
  );
}
