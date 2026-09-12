"use server";

import { sendChatMessage } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export async function sendChatMessageAction(message: string, history: ChatMessage[]) {
  const result = await sendChatMessage(message, history);
  return result;
}
