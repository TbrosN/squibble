"use client";

import { useCallback, useState } from "react";
import { ApiError, apiClient } from "@/lib/apiClient";
import type { ChatMessage, ScriptLine } from "@/types";

export type ChatController = {
  messages: ChatMessage[];
  sending: boolean;
  error: string | null;
  send: (
    content: string,
    context: { selectedLines: number[]; currentScript: ScriptLine[] },
  ) => Promise<ScriptLine[] | null>;
  dismissError: () => void;
};

export function useChat(): ChatController {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback<ChatController["send"]>(
    async (content, { selectedLines, currentScript }) => {
      const trimmed = content.trim();
      if (!trimmed || sending) return null;

      const userMessage: ChatMessage = { role: "user", content: trimmed };
      const nextHistory = [...messages, userMessage];
      setMessages(nextHistory);
      setSending(true);
      setError(null);

      try {
        const result = await apiClient.scriptChat({
          messages: nextHistory,
          selected_lines: selectedLines,
          current_script: currentScript,
        });

        setMessages([
          ...nextHistory,
          { role: "assistant", content: result.reply || "Updated." },
        ]);
        return result.script;
      } catch (e) {
        const message =
          e instanceof ApiError
            ? e.message
            : "Couldn't reach the assistant. Please try again.";
        setError(message);
        setMessages(nextHistory);
        return null;
      } finally {
        setSending(false);
      }
    },
    [messages, sending],
  );

  const dismissError = useCallback(() => setError(null), []);

  return { messages, sending, error, send, dismissError };
}
