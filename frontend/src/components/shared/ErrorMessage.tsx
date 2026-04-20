import styles from "./ErrorMessage.module.css";

type ErrorMessageProps = {
  message: string | null | undefined;
  onDismiss?: () => void;
};

export function ErrorMessage({ message, onDismiss }: ErrorMessageProps) {
  if (!message) return null;
  return (
    <div role="alert" className={styles.wrap}>
      <span className={styles.dot} aria-hidden />
      <span>{message}</span>
      {onDismiss && (
        <button
          type="button"
          className={styles.close}
          onClick={onDismiss}
          aria-label="Dismiss error"
        >
          ×
        </button>
      )}
    </div>
  );
}
