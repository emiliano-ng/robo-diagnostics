"use server";

import { sendChatMessage, ApiError } from "@/lib/api";
import type { ChatMessage, ChatResponse } from "@/lib/types";

export async function sendChatMessageAction(
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> {
  try {
    return await sendChatMessage(message, history);
  } catch (err) {
    // Without this, a thrown error here leaves the client's
    // useTransition promise rejected with nothing rendered — the chat
    // just looks stuck on "Thinking..." forever. Instead, turn the
    // failure into a normal-looking assistant message so the person
    // using it (especially live, during a demo) gets a clear answer
    // about what to do next, not a silent hang.
    const friendly =
      err instanceof ApiError && err.status === 503
        ? "I can't reach the local language model right now — make sure Ollama is running (`ollama serve`) and try again."
        : "Something went wrong talking to the assistant. Please try again.";

    return {
      reply: friendly,
      history: [
        ...history,
        { role: "user", content: message },
        { role: "assistant", content: friendly },
      ],
    };
  }
}
