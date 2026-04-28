"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/shared/Button";
import { CancelButton } from "@/components/shared/CancelButton";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { GlassPanel } from "@/components/shared/GlassPanel";
import { ChatBar } from "@/components/stage1/ChatBar";
import { ScriptEditor } from "@/components/stage1/ScriptEditor";
import { GenerationGrid } from "@/components/stage2/GenerationGrid";
import { SlidePreviewModal } from "@/components/stage2/SlidePreviewModal";
import { useChat } from "@/hooks/useChat";
import { useGeneration } from "@/hooks/useGeneration";
import { useInView } from "@/hooks/useInView";
import { useScriptEditor } from "@/hooks/useScriptEditor";
import { apiClient } from "@/lib/apiClient";
import type { SlideAsset, Stage } from "@/types";
import styles from "./page.module.css";

export default function HomePage() {
  const [stage, setStage] = useState<Stage>("script");
  const [previewSlide, setPreviewSlide] = useState<SlideAsset | null>(null);

  const script = useScriptEditor();
  const chat = useChat();
  const generation = useGeneration();
  // Fade the top bar out the moment any of it leaves the viewport so it
  // mirrors the chat bar's behavior at the bottom.
  const topBar = useInView<HTMLDivElement>({
    rootMargin: "-12px 0px 0px 0px",
  });

  const handleSend = useCallback(
    async (content: string) => {
      const updated = await chat.send(content, {
        selectedLines: script.selectedIds,
        currentScript: script.lines,
      });
      if (updated) {
        script.setLines(updated);
      }
    },
    [chat, script],
  );

  const startGeneration = useCallback(async () => {
    const started = await generation.start(script.lines);
    if (started) setStage("generation");
  }, [generation, script.lines]);

  const backToScript = useCallback(async () => {
    if (generation.phase === "running" || generation.phase === "starting") {
      await generation.cancel();
    }
    generation.reset();
    setPreviewSlide(null);
    setStage("script");
  }, [generation]);

  const cancelGeneration = useCallback(async () => {
    await generation.cancel();
  }, [generation]);

  // When cancellation completes, return the user to Stage 1 with script intact.
  useEffect(() => {
    if (generation.phase === "cancelled" && stage === "generation") {
      const t = setTimeout(() => {
        generation.reset();
        setStage("script");
      }, 400);
      return () => clearTimeout(t);
    }
  }, [generation, stage]);

  const canGenerate =
    stage === "script" &&
    script.lines.length > 0 &&
    script.lines.every((l) => l.line.trim().length > 0) &&
    !chat.sending &&
    generation.phase !== "starting";

  const doneCount = useMemo(
    () => generation.slides.filter((s) => s.status === "done").length,
    [generation.slides],
  );

  return (
    <main className={styles.appShell}>
      <div
        ref={topBar.ref}
        className={`${styles.topBar} ${topBar.inView ? "" : styles.topBarScrolledOut}`}
      >
        <div className={styles.brand}>
          <span className={styles.brandDot} aria-hidden />
          Squibble
          <span className={styles.stageLabel}>
            {stage === "script" ? "Script Studio" : "Generation Studio"}
          </span>
        </div>
        <nav className={styles.navLinks} aria-label="Primary navigation">
          <Link className={`${styles.navLink} ${styles.navLinkActive}`} href="/">
            Script
          </Link>
          <Link className={styles.navLink} href="/stop-motion">
            Stop Motion
          </Link>
        </nav>
        <div className={styles.spacer} />
        {stage === "script" ? (
          <Button
            variant="primary"
            size="md"
            disabled={!canGenerate}
            onClick={startGeneration}
            title={
              canGenerate
                ? "Generate the video"
                : "Write a script first, and make sure every line has content."
            }
          >
            {generation.phase === "starting"
              ? "Starting…"
              : "Generate Video →"}
          </Button>
        ) : (
          <>
            <Button variant="ghost" size="md" onClick={backToScript}>
              ← Back to Script
            </Button>
            {generation.phase === "complete" && generation.jobId && (
              <a
                href={apiClient.downloadUrl(generation.jobId)}
                style={{ textDecoration: "none" }}
              >
                <Button variant="success" size="md">
                  Download Video
                </Button>
              </a>
            )}
            {generation.phase !== "complete" && (
              <CancelButton
                onClick={cancelGeneration}
                disabled={
                  generation.phase !== "running" &&
                  generation.phase !== "starting"
                }
                title={
                  generation.phase === "running" ||
                  generation.phase === "starting"
                    ? "Stop generation"
                    : "Nothing to cancel"
                }
              />
            )}
          </>
        )}
      </div>

      {stage === "script" ? (
        <section className={styles.stage1}>
          <GlassPanel className={styles.canvas} padding="md">
            <ScriptEditor state={script} />
          </GlassPanel>
          <ErrorMessage message={chat.error} onDismiss={chat.dismissError} />
          <ErrorMessage
            message={generation.error}
            onDismiss={generation.dismissError}
          />
          <ChatBar
            messages={chat.messages}
            sending={chat.sending}
            selectedCount={script.selectedIds.length}
            onSend={handleSend}
          />
        </section>
      ) : (
        <section className={styles.stage2}>
          <div className={styles.statusRow}>
            <div>
              <p className={styles.statusTitle}>
                {generation.phase === "starting" && "Warming up the studio…"}
                {generation.phase === "running" &&
                  `Generating… ${doneCount} of ${generation.slides.length} slides ready`}
                {generation.phase === "complete" && "Your video is ready."}
                {generation.phase === "cancelled" && "Generation cancelled."}
                {generation.phase === "error" && "Generation ran into a problem."}
                {generation.phase === "idle" && "Preparing…"}
              </p>
              <p className={styles.statusSub}>
                {generation.phase === "running"
                  ? "Click a finished card to preview its image with audio."
                  : generation.phase === "complete"
                    ? "Download the stitched video, or click any slide to replay it."
                    : "Your script is still safe — use Back to Script any time."}
              </p>
            </div>
            <div className={styles.statusActions} />
          </div>

          <ErrorMessage message={generation.error} />

          <GenerationGrid
            slides={generation.slides}
            onOpenSlide={setPreviewSlide}
          />
        </section>
      )}

      <SlidePreviewModal
        slide={previewSlide}
        onClose={() => setPreviewSlide(null)}
      />
    </main>
  );
}
