"use client";

import { useCallback } from "react";
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
    addLine,
    insertLineAfter,
    removeLine,
    splitLine,
    selectAll,
    clearSelection,
    isEmpty,
  } = state;

  const focusLine = useCallback((id: number, caret: "start" | "end") => {
    requestAnimationFrame(() => {
      const el = document.querySelector<HTMLTextAreaElement>(
        `[data-line-id="${id}"]`,
      );
      if (!el) return;
      el.focus();
      const pos = caret === "end" ? el.value.length : 0;
      el.setSelectionRange(pos, pos);
    });
  }, []);

  const handleAddLine = useCallback(() => {
    const id = addLine();
    focusLine(id, "end");
  }, [addLine, focusLine]);

  const handleEnter = useCallback(
    (id: number, before: string, after: string) => {
      updateLine(id, { line: before });
      const newId = insertLineAfter(id, after);
      focusLine(newId, "start");
    },
    [updateLine, insertLineAfter, focusLine],
  );

  const handleBackspaceEmpty = useCallback(
    (id: number) => {
      const idx = lines.findIndex((l) => l.id === id);
      if (idx === -1) return;
      const neighbor = idx > 0 ? lines[idx - 1] : lines[idx + 1];
      removeLine(id);
      if (neighbor) focusLine(neighbor.id, "end");
    },
    [lines, removeLine, focusLine],
  );

  const handlePasteMultiline = useCallback(
    (id: number, sentences: string[]) => {
      const ids = splitLine(id, sentences);
      const lastId = ids[ids.length - 1];
      if (lastId === undefined) return ids;
      // Move focus/caret to the end of the final sentence so the user can keep typing.
      focusLine(lastId, "end");
      return ids;
    },
    [splitLine, focusLine],
  );

  if (isEmpty) {
    return (
      <div className={styles.empty}>
        <h2 className={styles.emptyTitle}>Your canvas is empty.</h2>
        <p className={styles.emptySub}>
          Tell the assistant what story you want to tell — a topic, a vibe, a
          character. It'll draft a tight script right here. Or start typing
          your first line directly — paste a full script and we'll split it
          into lines by sentence.
        </p>
        <button
          type="button"
          className={styles.primaryAddButton}
          onClick={handleAddLine}
        >
          + Start writing or paste a script
        </button>
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
          onRemove={removeLine}
          onPasteMultiline={handlePasteMultiline}
          onEnter={handleEnter}
          onBackspaceEmpty={handleBackspaceEmpty}
          onSelectAll={selectAll}
        />
      ))}
      <button
        type="button"
        className={styles.addLineButton}
        onClick={handleAddLine}
      >
        + Add line
      </button>
    </div>
  );
}
