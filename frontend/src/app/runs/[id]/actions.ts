"use server";

import { revalidatePath } from "next/cache";
import { analyzeRun as analyzeRunApi } from "@/lib/api";

export async function analyzeRunAction(runId: number) {
  await analyzeRunApi(runId);
  // Re-fetch this run's page server-side so the new diagnostics show up
  // immediately, without the client needing to manually refetch anything.
  revalidatePath(`/runs/${runId}`);
}
