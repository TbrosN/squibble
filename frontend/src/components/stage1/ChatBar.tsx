"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { Button } from "@/components/shared/Button";
import { useInView } from "@/hooks/useInView";
import type { ChatMessage } from "@/types";
import styles from "./ChatBar.module.css";

type ChatBarProps = {
  messages: ChatMessage[];
  sending: boolean;
  selectedCount: number;
  onSend: (content: string) => void;
};

export function ChatBar({
  messages,
  sending,
  selectedCount,
  onSend,
}: ChatBarProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastAssistant = [...messages]
    .reverse()
    .find((m) => m.role === "assistant");
  // Trigger the fade slightly inside the viewport so the user actually sees
  // the animation finish before the bar is fully on screen.
  const { ref, inView } = useInView<HTMLDivElement>({
    rootMargin: "0px 0px -40px 0px",
  });

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
  }, [value]);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || sending) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const placeholder =
    selectedCount > 0
      ? `Tell me how to change ${selectedCount === 1 ? "this line" : `these ${selectedCount} lines`}…`
      : messages.length === 0
        ? "Describe the video you want to make…"
        : "Ask for edits, or keep shaping the script…";

  return (
    <div
      ref={ref}
      className={`${styles.wrap} ${inView ? "" : styles.scrolledOut}`}
    >
      {lastAssistant && (
        <div className={styles.assistantReply} role="status">
          {lastAssistant.content}
        </div>
      )}
      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
      >
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder={placeholder}
          value={value}
          rows={1}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
        />
        <Button
          type="submit"
          variant="primary"
          size="md"
          className={styles.sendButton}
          disabled={sending || value.trim().length === 0}
        >
          {sending ? <span className={styles.spinner} aria-hidden /> : "Send"}
        </Button>
      </form>
      <div className={styles.hint}>
        ⏎ to send · ⇧+⏎ for newline · Click to select lines
      </div>
    </div>
  );
}
