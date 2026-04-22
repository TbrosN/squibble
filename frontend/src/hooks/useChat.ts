"use client";

import { useCallback, useRef, useState } from "react";
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
  // Opaque handle for this draft's rolling server-side state (history + the
  // on-disk script buffer the model edits). Null on first turn; server mints
  // one and we echo it back for every subsequent turn.
  const scriptIdRef = useRef<string | null>(null);

  const send = useCallback<ChatController["send"]>(
    async (content, { selectedLines, currentScript }) => {
      const trimmed = content.trim();
      if (!trimmed || sending) return null;

      const userMessage: ChatMessage = { role: "user", content: trimmed };
      setMessages((prev) => [...prev, userMessage]);
      setSending(true);
      setError(null);

      try {
        const result = await apiClient.scriptChat({
          message: trimmed,
          script_id: scriptIdRef.current,
          canvas_lines: currentScript.map((l) => l.line),
          selected_lines: selectedLines,
        });

        scriptIdRef.current = result.script_id;
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.reply || "Updated." },
        ]);
        return result.script;
      } catch (e) {
        const message =
          e instanceof ApiError
            ? e.message
            : "Couldn't reach the assistant. Please try again.";
        setError(message);
        // Roll back the optimistic user message so the log reflects what was
        // actually delivered.
        setMessages((prev) => prev.slice(0, -1));
        return null;
      } finally {
        setSending(false);
      }
    },
    [sending],
  );

  const dismissError = useCallback(() => setError(null), []);

  return { messages, sending, error, send, dismissError };
}
