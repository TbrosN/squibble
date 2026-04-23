"use client";

import { useEffect, useRef, useState } from "react";

type Options = {
  /** CSS rootMargin string, e.g. "-40px 0px" to trigger before edges meet. */
  rootMargin?: string;
  /** Fraction of the target visible to count as "in view". */
  threshold?: number;
};

/**
 * Lightweight wrapper around `IntersectionObserver` for fade-in/out effects.
 *
 * Defaults to "in view" so the initial render doesn't flash hidden. The
 * observer fires once on observe and corrects the state if the element is
 * actually off-screen.
 */
export function useInView<T extends HTMLElement>({
  rootMargin = "0px",
  threshold = 0,
}: Options = {}) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(true);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          setInView(entry.isIntersecting);
        }
      },
      { rootMargin, threshold },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [rootMargin, threshold]);

  return { ref, inView };
}
