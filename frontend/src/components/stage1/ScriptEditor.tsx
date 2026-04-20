"use client";

import type { ScriptEditor as ScriptEditorState } from "@/hooks/useScriptEditor";
import { LineBlock } from "./LineBlock";
import styles from "./ScriptEditor.module.css";

type ScriptEditorProps = {
  state: ScriptEditorState;
};

export function ScriptEditor({ state }: ScriptEditorProps) {
  const {
    lines,
    selectedIds,
    isSelected,
    toggleSelected,
    updateLine,
    clearSelection,
    isEmpty,
  } = state;

  if (isEmpty) {
    return (
      <div className={styles.empty}>
        <h2 className={styles.emptyTitle}>Your canvas is empty.</h2>
        <p className={styles.emptySub}>
          Tell the assistant what story you want to tell — a topic, a vibe, a
          character. It'll draft a tight script right here, and you can edit
          any line directly or highlight lines to ask for targeted rewrites.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.editor}>
      {selectedIds.length > 0 && (
        <div className={styles.selectionBar}>
          <span className={styles.selectionLabel}>
            {selectedIds.length === 1
              ? "1 line selected — your next message will target it."
              : `${selectedIds.length} lines selected — your next message will target them.`}
          </span>
          <button
            type="button"
            className={styles.clearButton}
            onClick={clearSelection}
          >
            Clear
          </button>
        </div>
      )}
      {lines.map((line, idx) => (
        <LineBlock
          key={line.id}
          line={line}
          index={idx}
          selected={isSelected(line.id)}
          onToggleSelect={toggleSelected}
          onChange={updateLine}
        />
      ))}
    </div>
  );
}
