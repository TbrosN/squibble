"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiClient } from "@/lib/apiClient";
import type {
  LineGenerationStatus,
  ScriptLine,
  SlideAsset,
  SSEEvent,
} from "@/types";

export type GenerationPhase =
  | "idle"
  | "starting"
  | "running"
  | "complete"
  | "cancelled"
  | "error";

export type GenerationController = {
  phase: GenerationPhase;
  slides: SlideAsset[];
  jobId: string | null;
  finalUrl: string | null;
  error: string | null;
  start: (script: ScriptLine[]) => Promise<boolean>;
  cancel: () => Promise<void>;
  reset: () => void;
  dismissError: () => void;
};

function buildInitialSlides(script: ScriptLine[]): SlideAsset[] {
  return script.map((line) => ({
    id: line.id,
    line: line.line,
    status: "pending" as LineGenerationStatus,
  }));
}

export function useGeneration(): GenerationController {
  const [phase, setPhase] = useState<GenerationPhase>("idle");
  const [slides, setSlides] = useState<SlideAsset[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [finalUrl, setFinalUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const esRef = useRef<EventSource | null>(null);
  const phaseRef = useRef<GenerationPhase>("idle");
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  const closeStream = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => closeStream();
  }, [closeStream]);

  const reset = useCallback(() => {
    closeStream();
    setPhase("idle");
    setSlides([]);
    setJobId(null);
    setFinalUrl(null);
    setError(null);
  }, [closeStream]);

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case "line_update":
        setSlides((prev) =>
          prev.map((s) =>
            s.id === event.line_id
              ? {
                  ...s,
                  status: event.status,
                  imageUrl: apiClient.assetUrl(event.image_url) ?? s.imageUrl,
                  audioUrl: apiClient.assetUrl(event.audio_url) ?? s.audioUrl,
                  duration: event.duration ?? s.duration,
                }
              : s,
          ),
        );
        break;
      case "complete":
        setFinalUrl(apiClient.assetUrl(event.final_url) ?? null);
        setPhase("complete");
        break;
      case "cancelled":
        setPhase("cancelled");
        break;
      case "error":
        setError(event.message);
        setPhase("error");
        if (typeof event.line_id === "number") {
          setSlides((prev) =>
            prev.map((s) =>
              s.id === event.line_id ? { ...s, status: "error" } : s,
            ),
          );
        }
        break;
    }
  }, []);

  const openStream = useCallback(
    (id: string) => {
      closeStream();
      const es = new EventSource(apiClient.streamUrl(id));
      esRef.current = es;

      es.onmessage = (ev) => {
        try {
          const parsed = JSON.parse(ev.data) as SSEEvent;
          handleEvent(parsed);
        } catch {
          // ignore malformed / keep-alive frames
        }
      };

      es.onerror = () => {
        // If we've already reached a terminal phase, the server closed the
        // stream intentionally and this event is expected.
        const current = phaseRef.current;
        if (
          current === "complete" ||
          current === "cancelled" ||
          current === "error"
        ) {
          return;
        }
        // Otherwise the connection was lost mid-generation. Surface a
        // recovery state so the user isn't stuck on a silent grid.
        if (es.readyState === EventSource.CLOSED) {
          closeStream();
          setError(
            "Lost connection to the generation stream. Head back to the script and try again.",
          );
          setPhase("error");
        }
      };
    },
    [closeStream, handleEvent],
  );

  const start = useCallback<GenerationController["start"]>(
    async (script) => {
      if (phase === "running" || phase === "starting") return false;
      setError(null);
      setFinalUrl(null);
      setSlides(buildInitialSlides(script));
      setPhase("starting");

      try {
        const { job_id } = await apiClient.startGeneration(script);
        setJobId(job_id);
        setPhase("running");
        openStream(job_id);
        return true;
      } catch (e) {
        const message =
          e instanceof ApiError
            ? e.message
            : "Couldn't start generation. Please try again.";
        setError(message);
        setPhase("idle");
        setSlides([]);
        return false;
      }
    },
    [openStream, phase],
  );

  const cancel = useCallback<GenerationController["cancel"]>(async () => {
    if (!jobId) {
      reset();
      return;
    }
    try {
      await apiClient.cancelGeneration(jobId);
    } catch {
      // even if cancel fails on the server, we tear down the UI
    }
    closeStream();
    setPhase("cancelled");
  }, [closeStream, jobId, reset]);

  const dismissError = useCallback(() => setError(null), []);

  return {
    phase,
    slides,
    jobId,
    finalUrl,
    error,
    start,
    cancel,
    reset,
    dismissError,
  };
}
