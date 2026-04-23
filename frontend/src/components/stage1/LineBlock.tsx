"use client";

import {
  useEffect,
  useRef,
  type ClipboardEvent,
  type KeyboardEvent,
} from "react";
import { splitIntoSentences } from "@/lib/splitSentences";
import type { ScriptLine } from "@/types";
import styles from "./LineBlock.module.css";

type LineBlockProps = {
  line: ScriptLine;
  index: number;
  selected: boolean;
  onToggleSelect: (id: number) => void;
  onChange: (id: number, patch: Partial<Omit<ScriptLine, "id">>) => void;
  onRemove?: (id: number) => void;
  onPasteMultiline?: (id: number, sentences: string[]) => number[] | void;
  onEnter?: (id: number, before: string, after: string) => void;
  onBackspaceEmpty?: (id: number) => void;
  onSelectAll?: () => void;
};

export function LineBlock({
  line,
  index,
  selected,
  onToggleSelect,
  onChange,
  onRemove,
  onPasteMultiline,
  onEnter,
  onBackspaceEmpty,
  onSelectAll,
}: LineBlockProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [line.line]);

  const handlePaste = (e: ClipboardEvent<HTMLTextAreaElement>) => {
    if (!onPasteMultiline) return;
    const pasted = e.clipboardData.getData("text");
    if (!pasted) return;

    const el = e.currentTarget;
    const start = el.selectionStart ?? el.value.length;
    const end = el.selectionEnd ?? el.value.length;
    const merged =
      el.value.slice(0, start) + pasted + el.value.slice(end);

    const sentences = splitIntoSentences(merged);
    if (sentences.length <= 1) return;

    e.preventDefault();
    onPasteMultiline(line.id, sentences);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl+A selects every line in the script instead of just this textarea.
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "a") {
      if (!onSelectAll) return;
      e.preventDefault();
      onSelectAll();
      return;
    }

    // Enter splits the current line at the caret and creates a new line below.
    // Shift+Enter still inserts a literal newline as an escape hatch.
    if (e.key === "Enter" && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
      if (!onEnter) return;
      e.preventDefault();
      const el = e.currentTarget;
      const caret = el.selectionStart ?? el.value.length;
      const before = el.value.slice(0, caret);
      const after = el.value.slice(el.selectionEnd ?? caret);
      onEnter(line.id, before, after);
      return;
    }

    // Backspace on an already-empty line removes that line entirely.
    if (
      e.key === "Backspace" &&
      !e.metaKey &&
      !e.ctrlKey &&
      !e.altKey &&
      e.currentTarget.value === ""
    ) {
      if (!onBackspaceEmpty) return;
      e.preventDefault();
      onBackspaceEmpty(line.id);
      return;
    }
  };

  return (
    <div className={`${styles.row} ${selected ? styles.selected : ""}`}>
      <button
        type="button"
        className={styles.handle}
        onClick={() => onToggleSelect(line.id)}
        aria-pressed={selected}
        aria-label={selected ? "Deselect line" : "Select line"}
        title={selected ? "Click to deselect" : "Click to include in edit"}
      >
        {index + 1}
      </button>
      <div className={styles.content}>
        <textarea
          ref={textareaRef}
          className={styles.lineText}
          value={line.line}
          rows={1}
          placeholder="Write a line, or paste a whole script..."
          data-line-id={line.id}
          onChange={(e) => onChange(line.id, { line: e.target.value })}
          onPaste={handlePaste}
          onKeyDown={handleKeyDown}
        />
      </div>
      {onRemove && (
        <button
          type="button"
          className={styles.removeButton}
          onClick={() => onRemove(line.id)}
          aria-label="Remove line"
          title="Remove line"
        >
          ×
        </button>
      )}
    </div>
  );
}
