type AppErrorFallbackProps = {
  error: unknown;
  resetError: () => void;
};

export function AppErrorFallback({ error, resetError }: AppErrorFallbackProps) {
  const message = error instanceof Error ? error.message : "Unknown render error";

  return (
    <div className="empty-state">
      <p>Something went wrong while rendering the review app.</p>
      <p className="muted-copy">{message}</p>
      <button className="primary-button" onClick={resetError} type="button">
        Try again
      </button>
    </div>
  );
}
