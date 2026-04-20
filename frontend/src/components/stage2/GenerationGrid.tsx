"use client";

import type { SlideAsset } from "@/types";
import { SlideCard } from "./SlideCard";
import styles from "./GenerationGrid.module.css";

type GenerationGridProps = {
  slides: SlideAsset[];
  onOpenSlide: (slide: SlideAsset) => void;
};

export function GenerationGrid({ slides, onOpenSlide }: GenerationGridProps) {
  return (
    <div className={styles.grid}>
      {slides.map((slide, idx) => (
        <SlideCard
          key={slide.id}
          slide={slide}
          index={idx}
          onOpen={onOpenSlide}
        />
      ))}
    </div>
  );
}
