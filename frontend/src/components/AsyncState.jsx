export function AsyncState({
  loading,
  error,
  empty,
  emptyMessage = 'No records are available yet.',
  onRetry,
  children,
}) {
  if (loading) {
    return (
      <div className="async-state" role="status" aria-live="polite" aria-busy="true">
        <span className="spinner" aria-hidden="true" /> Loading…
      </div>
    );
  }
  if (error) {
    return (
      <div className="async-state error" role="alert">
        <strong>Could not load this data.</strong>
        <span>{error.message}</span>
        {onRetry ? (
          <button type="button" className="button subtle" onClick={onRetry}>
            Retry
          </button>
        ) : null}
      </div>
    );
  }
  if (empty) {
    return <div className="async-state">{emptyMessage}</div>;
  }
  return children;
}
