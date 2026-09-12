"use client";

import { useState, useTransition, useRef, useEffect } from "react";
import { sendChatMessageAction } from "@/app/chat/actions";
import type { ChatMessage } from "@/lib/types";

export default function ChatWindow() {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isPending, startTransition] = useTransition();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Only user/assistant turns are shown to the person — system and tool
  // messages exist for the model's benefit, not for display.
  const visibleMessages = history.filter((m) => m.role === "user" || m.role === "assistant");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [visibleMessages.length]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || isPending) return;

    setInput("");
    startTransition(async () => {
      const result = await sendChatMessageAction(message, history);
      setHistory(result.history);
    });
  }

  return (
    <div className="flex flex-col h-[70vh] border border-neutral-200 rounded-lg overflow-hidden">
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {visibleMessages.length === 0 && (
          <p className="text-neutral-500 text-sm">
            Ask about your experiments and runs — e.g. &quot;which runs have
            the highest degradation?&quot; or &quot;analyze run 2 and tell me
            what you find.&quot;
          </p>
        )}

        {visibleMessages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
              m.role === "user"
                ? "ml-auto bg-neutral-900 text-white"
                : "mr-auto bg-neutral-100 text-neutral-900"
            }`}
          >
            {m.content}
          </div>
        ))}

        {isPending && (
          <div className="mr-auto bg-neutral-100 text-neutral-500 rounded-lg px-4 py-2 text-sm">
            Thinking...
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-neutral-200 p-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isPending}
          className="flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400"
        />
        <button
          type="submit"
          disabled={isPending || !input.trim()}
          className="px-4 py-2 rounded-md bg-neutral-900 text-white text-sm font-medium disabled:opacity-40 hover:bg-neutral-700 transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
