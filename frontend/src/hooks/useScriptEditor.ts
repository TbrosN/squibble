"use client";

import { useCallback, useMemo, useState } from "react";
import type { ScriptLine } from "@/types";

export type ScriptEditor = {
  lines: ScriptLine[];
  selectedIds: number[];
  setLines: (lines: ScriptLine[]) => void;
  updateLine: (id: number, patch: Partial<Omit<ScriptLine, "id">>) => void;
  toggleSelected: (id: number) => void;
  clearSelection: () => void;
  isSelected: (id: number) => boolean;
  isEmpty: boolean;
};

export function useScriptEditor(initial: ScriptLine[] = []): ScriptEditor {
  const [lines, setLinesState] = useState<ScriptLine[]>(initial);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const setLines = useCallback((next: ScriptLine[]) => {
    setLinesState(next);
    setSelectedIds((prev) => prev.filter((id) => next.some((l) => l.id === id)));
  }, []);

  const updateLine = useCallback(
    (id: number, patch: Partial<Omit<ScriptLine, "id">>) => {
      setLinesState((prev) =>
        prev.map((l) => (l.id === id ? { ...l, ...patch } : l)),
      );
    },
    [],
  );

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
    toggleSelected,
    clearSelection,
    isSelected,
    isEmpty: lines.length === 0,
  };
}
