"use client";

import { useTransition } from "react";
import { analyzeRunAction } from "@/app/runs/[id]/actions";

export default function AnalyzeButton({ runId }: { runId: number }) {
  const [isPending, startTransition] = useTransition();

  return (
    <button
      onClick={() => startTransition(() => analyzeRunAction(runId))}
      disabled={isPending}
      className="px-3 py-1.5 rounded-md bg-neutral-900 text-white text-sm font-medium disabled:opacity-50 hover:bg-neutral-700 transition-colors"
    >
      {isPending ? "Analizando..." : "Analizar degradación"}
    </button>
  );
}
