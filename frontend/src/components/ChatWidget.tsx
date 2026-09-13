"use client";

import { useState } from "react";
import ChatWindow from "./ChatWindow";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-6 w-[380px] max-w-[90vw] z-50 rounded-lg overflow-hidden shadow-2xl border border-neutral-200 bg-white">
          <div className="flex items-center justify-between bg-neutral-900 text-white px-4 py-2.5">
            <span className="text-sm font-medium">Diagnostics Assistant</span>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="text-neutral-400 hover:text-white text-sm leading-none"
            >
              ✕
            </button>
          </div>
          <ChatWindow className="flex flex-col h-[480px]" />
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close diagnostics assistant" : "Open diagnostics assistant"}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-neutral-900 text-white shadow-lg flex items-center justify-center text-xl hover:bg-neutral-700 transition-colors"
      >
        {open ? "✕" : "💬"}
      </button>
    </>
  );
}
