export function ProjectContext() {
  return (
    <details className="project-context">
      <summary>About P.A.T.H.: find unusual patterns in public fund disbursals</summary>
      <div>
        <p>
          P.A.T.H. uses unsupervised machine learning to prioritize unusual payments for human
          review. A high anomaly score is a screening signal, not a fraud determination.
        </p>
        <ol>
          <li>An administrator uploads and validates a transaction CSV.</li>
          <li>Run a model in ML Control to rank unusual transactions.</li>
          <li>Open a record from the dashboard or Anomaly Explorer to investigate it.</li>
          <li>
            A reviewer or administrator records a decision and note. Review history shows those
            decisions for the active run.
          </li>
        </ol>
        <p>Unusual ≠ Fraudulent.</p>
      </div>
    </details>
  );
}
