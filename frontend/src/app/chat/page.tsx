import Link from "next/link";
import ChatWindow from "@/components/ChatWindow";

export default function ChatPage() {
  return (
    <main className="max-w-2xl mx-auto px-6 py-12">
      <Link href="/" className="text-sm text-neutral-500 hover:underline">
        ← Experiments
      </Link>
      <h1 className="text-2xl font-semibold mt-2 mb-1">Diagnostics Assistant</h1>
      <p className="text-neutral-500 mb-8">
        A local LLM (via Ollama) with tool access to this platform&apos;s
        data — it can look up experiments, runs, and degradation results,
        and trigger new analysis on request.
      </p>

      <ChatWindow />
    </main>
  );
}
