import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./Button.module.css";

type Variant = "primary" | "ghost" | "success" | "danger";
type Size = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
};

const variantClass: Record<Variant, string> = {
  primary: styles.primary,
  ghost: styles.ghost,
  success: styles.success,
  danger: styles.danger,
};

const sizeClass: Record<Size, string> = {
  sm: styles.sm,
  md: styles.md,
  lg: styles.lg,
};

export function Button({
  variant = "ghost",
  size = "md",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  const classes = [
    styles.button,
    variantClass[variant],
    sizeClass[size],
    className,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <button className={classes} {...rest}>
      {children}
    </button>
  );
}
