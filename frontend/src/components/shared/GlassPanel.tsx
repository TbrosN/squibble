import type { CSSProperties, HTMLAttributes, ReactNode } from "react";
import styles from "./GlassPanel.module.css";

type GlassPanelProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  radius?: "sm" | "md" | "lg";
  padding?: "none" | "sm" | "md" | "lg";
  style?: CSSProperties;
};

const radiusClass = { sm: styles.sm, md: styles.md, lg: styles.lg };
const padClass = {
  none: "",
  sm: styles.padSm,
  md: styles.padMd,
  lg: styles.padLg,
};

export function GlassPanel({
  children,
  radius = "md",
  padding = "md",
  className = "",
  ...rest
}: GlassPanelProps) {
  const classes = [styles.panel, radiusClass[radius], padClass[padding], className]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  );
}
