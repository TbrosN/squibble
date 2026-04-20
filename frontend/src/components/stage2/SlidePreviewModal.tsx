"use client";

import { useEffect, useRef, useState } from "react";
import type { SlideAsset } from "@/types";
import styles from "./SlidePreviewModal.module.css";

type SlidePreviewModalProps = {
  slide: SlideAsset | null;
  onClose: () => void;
};

export function SlidePreviewModal({ slide, onClose }: SlidePreviewModalProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!slide) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);

    const audio = audioRef.current;
    setProgress(0);
    setPlaying(false);
    if (audio) {
      audio.currentTime = 0;
      audio.play().catch(() => {
        // autoplay may be blocked; user can tap to play
      });
    }

    return () => window.removeEventListener("keydown", onKey);
  }, [slide, onClose]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => {});
    } else {
      audio.pause();
    }
  };

  if (!slide) return null;

  return (
    <div
      className={styles.backdrop}
      role="dialog"
      aria-modal="true"
      aria-label="Slide preview"
      onClick={onClose}
    >
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close preview"
        >
          ×
        </button>
        <button
          type="button"
          className={styles.stage}
          onClick={slide.audioUrl ? togglePlay : undefined}
          aria-label={playing ? "Pause audio" : "Play audio"}
          disabled={!slide.audioUrl}
        >
          {slide.imageUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={slide.imageUrl}
              alt={slide.line}
              className={styles.image}
            />
          )}
          <div className={styles.scrim} aria-hidden />
          {slide.audioUrl && (
            <div
              className={`${styles.playBadge} ${playing ? styles.playing : ""}`}
              aria-hidden
            >
              {playing ? (
                <span className={styles.pauseGlyph}>
                  <span />
                  <span />
                </span>
              ) : (
                <span className={styles.playGlyph} />
              )}
            </div>
          )}
          <div className={styles.captionOverlay}>
            <p className={styles.caption}>{slide.line}</p>
            {slide.audioUrl && (
              <div
                className={styles.progressTrack}
                role="progressbar"
                aria-valuenow={Math.round(progress * 100)}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div
                  className={styles.progressFill}
                  style={{ width: `${progress * 100}%` }}
                />
              </div>
            )}
          </div>
        </button>
        {slide.audioUrl && (
          <audio
            ref={audioRef}
            src={slide.audioUrl}
            preload="auto"
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
            onEnded={() => setPlaying(false)}
            onTimeUpdate={(e) => {
              const el = e.currentTarget;
              if (el.duration > 0) setProgress(el.currentTime / el.duration);
            }}
          />
        )}
      </div>
    </div>
  );
}
