"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { ScriptLine } from "@/types";

export type ScriptEditor = {
  lines: ScriptLine[];
  selectedIds: number[];
  setLines: (lines: ScriptLine[]) => void;
  updateLine: (id: number, patch: Partial<Omit<ScriptLine, "id">>) => void;
  addLine: () => number;
  insertLineAfter: (id: number, text?: string) => number;
  removeLine: (id: number) => void;
  splitLine: (id: number, sentences: string[]) => number[];
  toggleSelected: (id: number) => void;
  selectAll: () => void;
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
    setLinesState((prev) => [...prev, { id, line: "" }]);
    return id;
  }, []);

  const insertLineAfter = useCallback((id: number, text: string = ""): number => {
    const newId = nextIdRef.current;
    nextIdRef.current += 1;
    setLinesState((prev) => {
      const idx = prev.findIndex((l) => l.id === id);
      const newLine: ScriptLine = { id: newId, line: text };
      if (idx === -1) return [...prev, newLine];
      return [...prev.slice(0, idx + 1), newLine, ...prev.slice(idx + 1)];
    });
    return newId;
  }, []);

  const removeLine = useCallback((id: number) => {
    setLinesState((prev) => prev.filter((l) => l.id !== id));
    setSelectedIds((prev) => prev.filter((x) => x !== id));
  }, []);

  // Replace the line at `id` with N lines, one per sentence. The first sentence
  // keeps the original id; remaining sentences get fresh ids inserted directly
  // after. Returns the list of ids for every resulting line.
  const splitLine = useCallback((id: number, sentences: string[]): number[] => {
    const cleaned = sentences.map((s) => s.trim()).filter(Boolean);
    if (cleaned.length === 0) return [];

    // Reserve ids up-front so the updater is pure and StrictMode-safe.
    const newIds: number[] = [id];
    for (let i = 1; i < cleaned.length; i++) {
      newIds.push(nextIdRef.current);
      nextIdRef.current += 1;
    }

    setLinesState((prev) => {
      const idx = prev.findIndex((l) => l.id === id);
      if (idx === -1) return prev;
      const current = prev[idx];
      const replacements: ScriptLine[] = cleaned.map((text, i) =>
        i === 0 ? { ...current, line: text } : { id: newIds[i], line: text },
      );
      return [...prev.slice(0, idx), ...replacements, ...prev.slice(idx + 1)];
    });
    return newIds;
  }, []);

  const toggleSelected = useCallback((id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const selectAll = useCallback(() => {
    setSelectedIds(lines.map((l) => l.id));
  }, [lines]);

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
    insertLineAfter,
    removeLine,
    splitLine,
    toggleSelected,
    selectAll,
    clearSelection,
    isSelected,
    isEmpty: lines.length === 0,
  };
}
