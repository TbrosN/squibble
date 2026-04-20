"use client";

import { useEffect, useRef } from "react";
import type { SlideAsset } from "@/types";
import styles from "./SlidePreviewModal.module.css";

type SlidePreviewModalProps = {
  slide: SlideAsset | null;
  onClose: () => void;
};

export function SlidePreviewModal({ slide, onClose }: SlidePreviewModalProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (!slide) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);

    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = 0;
      audio.play().catch(() => {
        // autoplay may be blocked; user can press play
      });
    }

    return () => window.removeEventListener("keydown", onKey);
  }, [slide, onClose]);

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
        {slide.imageUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={slide.imageUrl} alt={slide.line} className={styles.image} />
        )}
        <div className={styles.caption}>{slide.line}</div>
        {slide.audioUrl && (
          <audio
            ref={audioRef}
            className={styles.audio}
            src={slide.audioUrl}
            controls
          />
        )}
      </div>
    </div>
  );
}
