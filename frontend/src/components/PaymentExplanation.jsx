export const CRITICAL_HELP =
  'Critical = in the top 1% of risk scores in this run. It is not a confirmed finding.';

export function ExplanationNotice({ includeCritical = true }) {
  return (
    <p className="insight-disclaimer">
      Unusual does not mean fraudulent. {includeCritical ? CRITICAL_HELP : null}
    </p>
  );
}

export function ExplanationText({ explanation }) {
  if (!explanation)
    return <p className="muted">No explanation is available. Run an analysis first.</p>;
  return (
    <>
      <p className="analysis-narrative">{explanation.headline}</p>
      {explanation.support ? <p>{explanation.support}</p> : null}
      <p className="check-first">{explanation.check_first}</p>
    </>
  );
}

export function SignalEvidence({ signals = [] }) {
  return (
    <div className="evidence-list">
      {signals.map((signal) => (
        <article
          className={`evidence-row ${signal.ratio == null ? 'evidence-context' : 'evidence-comparison'}`}
          key={signal.key}
        >
          <div className="finding-heading">
            <h3>{signal.label}</h3>
            <span className={`badge evidence-${signal.strength}`}>{signal.tag}</span>
          </div>
          <dl className="evidence-values">
            <div>
              <dt>{signal.ratio == null ? 'Context' : 'Average payment amount'}</dt>
              <dd>{signal.baseline_text}</dd>
            </div>
            <div>
              <dt>{signal.ratio == null ? 'Recorded value' : 'Selected transaction amount'}</dt>
              <dd>{signal.value_text}</dd>
            </div>
            {signal.ratio != null ? (
              <div>
                <dt>Multiple</dt>
                <dd>{signal.multiple_text}</dd>
              </div>
            ) : null}
          </dl>
          {signal.ratio != null ? (
            <meter
              min="0"
              max="10"
              value={Math.min(signal.ratio, 10)}
              aria-label={`${signal.label}: ${signal.tag}`}
            />
          ) : null}
          <details className="evidence-help">
            <summary>What this means</summary>
            <p>{signal.help_text}</p>
          </details>
        </article>
      ))}
    </div>
  );
}
