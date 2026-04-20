"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { ScriptLine } from "@/types";

export type ScriptEditor = {
  lines: ScriptLine[];
  selectedIds: number[];
  setLines: (lines: ScriptLine[]) => void;
  updateLine: (id: number, patch: Partial<Omit<ScriptLine, "id">>) => void;
  addLine: () => number;
  removeLine: (id: number) => void;
  toggleSelected: (id: number) => void;
  clearSelection: () => void;
  isSelected: (id: number) => boolean;
  isEmpty: boolean;
};

function nextId(lines: ScriptLine[]): number {
  return lines.reduce((max, l) => (l.id > max ? l.id : max), -1) + 1;
}

export function useScriptEditor(initial: ScriptLine[] = []): ScriptEditor {
  const [lines, setLinesState] = useState<ScriptLine[]>(initial);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const nextIdRef = useRef(nextId(initial));

  const setLines = useCallback((next: ScriptLine[]) => {
    setLinesState(next);
    setSelectedIds((prev) => prev.filter((id) => next.some((l) => l.id === id)));
    const candidate = nextId(next);
    if (candidate > nextIdRef.current) nextIdRef.current = candidate;
  }, []);

  const updateLine = useCallback(
    (id: number, patch: Partial<Omit<ScriptLine, "id">>) => {
      setLinesState((prev) =>
        prev.map((l) => (l.id === id ? { ...l, ...patch } : l)),
      );
    },
    [],
  );

  const addLine = useCallback(() => {
    const id = nextIdRef.current;
    nextIdRef.current += 1;
    setLinesState((prev) => [
      ...prev,
      { id, line: "", image_prompt: "" },
    ]);
    return id;
  }, []);

  const removeLine = useCallback((id: number) => {
    setLinesState((prev) => prev.filter((l) => l.id !== id));
    setSelectedIds((prev) => prev.filter((x) => x !== id));
  }, []);

  const toggleSelected = useCallback((id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const clearSelection = useCallback(() => setSelectedIds([]), []);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const isSelected = useCallback(
    (id: number) => selectedSet.has(id),
    [selectedSet],
  );

  return {
    lines,
    selectedIds,
    setLines,
    updateLine,
    addLine,
    removeLine,
    toggleSelected,
    clearSelection,
    isSelected,
    isEmpty: lines.length === 0,
  };
}
