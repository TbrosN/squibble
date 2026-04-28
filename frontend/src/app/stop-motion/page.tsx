"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { Button } from "@/components/shared/Button";
import { GlassPanel } from "@/components/shared/GlassPanel";
import { apiClient } from "@/lib/apiClient";
import type { StopMotionResponse } from "@/types";
import styles from "../page.module.css";

export default function StopMotionPage() {
  const [file, setFile] = useState<File | null>(null);
  const [style, setStyle] = useState("playdoh");
  const [framesPerSecond, setFramesPerSecond] = useState(2);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StopMotionResponse | null>(null);

  const handleFile = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] ?? null);
    setResult(null);
    setError(null);
  }, []);

  const createStopMotion = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!file) {
        setError("Choose a video first.");
        return;
      }

      setBusy(true);
      setError(null);
      setResult(null);

      try {
        const response = await apiClient.createStopMotion(
          file,
          style,
          framesPerSecond,
        );
        setResult(response);
      } catch (e) {
        const message =
          e instanceof Error
            ? e.message
            : "Couldn't restyle the video. Please try again.";
        setError(message);
      } finally {
        setBusy(false);
      }
    },
    [file, framesPerSecond, style],
  );

  const stopMotionPreviewUrl = apiClient.assetUrl(result?.preview_url);
  const stylizedPreviewUrl = apiClient.assetUrl(result?.stylized_preview_url);
  const downloadUrl = apiClient.assetUrl(result?.download_url);

  return (
    <main className={styles.appShell}>
      <div className={styles.topBar}>
        <div className={styles.brand}>
          <span className={styles.brandDot} aria-hidden />
          Squibble
          <span className={styles.stageLabel}>Stop-Motion Studio</span>
        </div>
        <nav className={styles.navLinks} aria-label="Primary navigation">
          <Link className={styles.navLink} href="/">
            Script
          </Link>
          <Link
            className={`${styles.navLink} ${styles.navLinkActive}`}
            href="/stop-motion"
          >
            Stop Motion
          </Link>
        </nav>
        <div className={styles.spacer} />
      </div>

      <section className={styles.stopMotionPage}>
        <GlassPanel className={styles.stopMotionPanel} padding="md">
          <form className={styles.stopMotionForm} onSubmit={createStopMotion}>
            <div className={styles.stopMotionCopy}>
              <p className={styles.stopMotionTitle}>Stop-Motion Restyle</p>
              <p className={styles.stopMotionSub}>
                Upload a clip, pick a material style like lego, yarn, or
                playdoh, and Squibble will rebuild it as a restyled stop-motion
                video with the original audio.
              </p>
            </div>
            <div className={styles.stopMotionControls}>
              <label className={styles.field}>
                <span>Video</span>
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFile}
                  disabled={busy}
                />
              </label>
              <label className={styles.field}>
                <span>Style</span>
                <input
                  type="text"
                  value={style}
                  onChange={(event) => setStyle(event.target.value)}
                  placeholder="playdoh, lego, yarn..."
                  disabled={busy}
                />
              </label>
              <label className={styles.field}>
                <span>Frames per second</span>
                <input
                  type="number"
                  min={1}
                  max={12}
                  value={framesPerSecond}
                  onChange={(event) =>
                    setFramesPerSecond(Number(event.target.value))
                  }
                  disabled={busy}
                />
              </label>
              <Button
                variant="primary"
                size="md"
                type="submit"
                disabled={busy || !file}
              >
                {busy ? "Restyling..." : "Make Stop-Motion"}
              </Button>
            </div>
          </form>

          {error && <p className={styles.stopMotionError}>{error}</p>}

          {result && (
            <div className={styles.stopMotionResult}>
              <div className={styles.stopMotionSummary}>
                Restyled {result.frame_count} stop-motion frames.
              </div>

              <div className={styles.videoPreviewGrid}>
                {stopMotionPreviewUrl && (
                  <div className={styles.videoPreviewCard}>
                    <p>Stop-motion timing preview</p>
                    <video controls src={stopMotionPreviewUrl} />
                  </div>
                )}
                {stylizedPreviewUrl && (
                  <div className={styles.videoPreviewCard}>
                    <p>Stylized video preview</p>
                    <video controls src={stylizedPreviewUrl} />
                  </div>
                )}
              </div>

              {downloadUrl && (
                <a href={downloadUrl} target="_blank" rel="noreferrer">
                  Download restyled video
                </a>
              )}
            </div>
          )}
        </GlassPanel>
      </section>
    </main>
  );
}
