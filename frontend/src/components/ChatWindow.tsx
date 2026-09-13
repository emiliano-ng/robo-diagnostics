"use client";

import { useState, useTransition, useRef, useEffect } from "react";
import { sendChatMessageAction } from "@/app/chat/actions";
import type { ChatMessage } from "@/lib/types";

interface ToolCall {
  function: { name: string; arguments: Record<string, unknown> };
}

function formatToolCall(call: ToolCall): string {
  const args = Object.entries(call.function.arguments || {})
    .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
    .join(", ");
  return `🔧 called ${call.function.name}(${args})`;
}

type DisplayItem =
  | { kind: "user"; content: string; key: string }
  | { kind: "assistant"; content: string; key: string }
  | { kind: "tool"; content: string; key: string };

// Turns the raw message history (which includes system/tool-result
// messages the model needs but a person doesn't) into what actually
// gets rendered: user/assistant bubbles, plus a compact indicator for
// every tool call the agent made along the way. Showing the tool calls
// is what makes it visible that this is really calling functions
// against the platform's own API, not just generating text.
function toDisplayItems(history: ChatMessage[]): DisplayItem[] {
  return history.flatMap((m, i): DisplayItem[] => {
    if (m.role === "user") {
      return [{ kind: "user", content: m.content, key: `u-${i}` }];
    }
    if (m.role === "assistant" && m.tool_calls) {
      const calls = m.tool_calls as ToolCall[];
      return calls.map((call, j) => ({
        kind: "tool" as const,
        content: formatToolCall(call),
        key: `t-${i}-${j}`,
      }));
    }
    if (m.role === "assistant" && m.content) {
      return [{ kind: "assistant", content: m.content, key: `a-${i}` }];
    }
    return [];
  });
}

export default function ChatWindow({
  className = "flex flex-col h-[70vh] border border-neutral-200 rounded-lg overflow-hidden",
}: {
  className?: string;
}) {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isPending, startTransition] = useTransition();
  const bottomRef = useRef<HTMLDivElement>(null);

  const displayItems = toDisplayItems(history);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayItems.length]);

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
    <div className={`${className} bg-white text-neutral-900`} style={{ colorScheme: "light" }}>
      <div className="flex-1 overflow-y-auto p-5 space-y-3">
        {displayItems.length === 0 && (
          <p className="text-neutral-500 text-sm">
            Ask about your experiments and runs — e.g. &quot;which runs have
            the highest degradation?&quot; or &quot;analyze run 2 and tell me
            what you find.&quot;
          </p>
        )}

        {displayItems.map((item) => {
          if (item.kind === "user") {
            return (
              <div
                key={item.key}
                className="max-w-[80%] ml-auto rounded-lg px-4 py-2 text-sm bg-neutral-900 text-white"
              >
                {item.content}
              </div>
            );
          }
          if (item.kind === "tool") {
            return (
              <div
                key={item.key}
                className="max-w-[80%] mr-auto rounded px-3 py-1.5 text-xs font-mono text-neutral-500 bg-neutral-50 border border-neutral-200"
              >
                {item.content}
              </div>
            );
          }
          return (
            <div
              key={item.key}
              className="max-w-[80%] mr-auto rounded-lg px-4 py-2 text-sm bg-neutral-100 text-neutral-900"
            >
              {item.content}
            </div>
          );
        })}

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
          className="flex-1 rounded-md border border-neutral-300 bg-white text-neutral-900 placeholder-neutral-400 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-neutral-400"
          style={{ colorScheme: "light", color: "#171717", backgroundColor: "#ffffff" }}
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
