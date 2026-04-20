"use client";

import { useEffect, useRef } from "react";
import type { ScriptLine } from "@/types";
import styles from "./LineBlock.module.css";

type LineBlockProps = {
  line: ScriptLine;
  index: number;
  selected: boolean;
  onToggleSelect: (id: number) => void;
  onChange: (id: number, patch: Partial<Omit<ScriptLine, "id">>) => void;
};

export function LineBlock({
  line,
  index,
  selected,
  onToggleSelect,
  onChange,
}: LineBlockProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [line.line]);

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
          placeholder="Write a line..."
          onChange={(e) => onChange(line.id, { line: e.target.value })}
        />
        {line.image_prompt && (
          <div className={styles.promptHint} title={line.image_prompt}>
            ▸ {line.image_prompt}
          </div>
        )}
      </div>
    </div>
  );
}
