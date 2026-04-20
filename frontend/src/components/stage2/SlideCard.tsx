"use client";

import type { SlideAsset } from "@/types";
import styles from "./SlideCard.module.css";

type SlideCardProps = {
  slide: SlideAsset;
  index: number;
  onOpen: (slide: SlideAsset) => void;
};

const STATUS_LABEL: Record<SlideAsset["status"], string> = {
  pending: "Waiting",
  generating: "Generating",
  done: "Ready",
  error: "Failed",
};

const STATUS_CLASS: Record<SlideAsset["status"], string> = {
  pending: "",
  generating: styles.statusGenerating,
  done: styles.statusDone,
  error: styles.statusError,
};

const AUDIO_LABEL: Record<SlideAsset["status"], string> = {
  pending: "Audio queued",
  generating: "Generating audio…",
  done: "Audio ready",
  error: "Audio failed",
};

export function SlideCard({ slide, index, onOpen }: SlideCardProps) {
  const canOpen = slide.status === "done" && !!slide.imageUrl && !!slide.audioUrl;

  return (
    <button
      type="button"
      className={styles.card}
      onClick={() => canOpen && onOpen(slide)}
      aria-disabled={!canOpen}
    >
      <div className={styles.imageWrap}>
        {slide.imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={slide.imageUrl} alt={slide.line} className={styles.image} />
        ) : (
          <div className={styles.shimmer} aria-hidden />
        )}
        <span
          className={`${styles.statusOverlay} ${STATUS_CLASS[slide.status]}`}
        >
          {STATUS_LABEL[slide.status]}
        </span>
        <span className={styles.lineIndex}>{index + 1}</span>
      </div>
      <div className={styles.body}>
        <div className={styles.lineText}>{slide.line}</div>
        <div className={styles.audioRow}>
          <span className={`${styles.audioDot} ${styles[slide.status]}`} aria-hidden />
          <span>{AUDIO_LABEL[slide.status]}</span>
          {slide.duration ? (
            <span style={{ marginLeft: "auto", opacity: 0.7 }}>
              {slide.duration.toFixed(1)}s
            </span>
          ) : null}
        </div>
      </div>
    </button>
  );
}
