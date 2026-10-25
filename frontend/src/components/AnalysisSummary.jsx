import { Link } from 'react-router-dom';
import { AsyncState } from './AsyncState';
import { RiskBadge } from './RiskBadge';
import { useAuth } from '../contexts/AuthContext';
import { useInsights } from '../hooks/data';
import { formatMoney } from '../lib';
import { ExplanationNotice, ExplanationText } from './PaymentExplanation';

export function AnalysisSummary() {
  const state = useInsights();
  const { user } = useAuth();
  const data = state.data;
  return (
    <section className="panel analysis-summary" aria-labelledby="analysis-summary-title">
      <div className="panel-header">
        <h2 id="analysis-summary-title">Analysis summary</h2>
        <button
          className="button ghost"
          type="button"
          onClick={state.retry}
          disabled={state.loading}
        >
          Refresh summary
        </button>
      </div>
      <AsyncState
        loading={state.loading}
        error={state.error}
        empty={!data?.status}
        emptyMessage="No analysis summary is available yet."
        onRetry={state.retry}
      >
        {data?.status ? (
          <>
            <p className="analysis-narrative">{data.narrative}</p>
            {data.status === 'no_dataset' ? (
              <div className="summary-actions">
                {user?.role === 'admin' ? (
                  <Link className="button primary" to="/datasets">
                    Upload a dataset
                  </Link>
                ) : (
                  <p className="muted">Ask an administrator to upload the transaction CSV.</p>
                )}
              </div>
            ) : null}
            {data.status === 'not_analyzed' ? (
              <div className="summary-actions">
                <Link className="button primary" to="/control">
                  Run an analysis
                </Link>
                <Link className="button subtle" to="/transactions">
                  View uploaded transactions
                </Link>
              </div>
            ) : null}
            {data.status === 'ready' ? (
              <>
                <ExplanationNotice />
                <h3>Critical records to investigate</h3>
                {data.critical_records?.length ? (
                  <ol className="critical-findings">
                    {data.critical_records.map((record) => (
                      <li key={record.transaction_id}>
                        <div className="finding-heading">
                          <Link
                            className="record-link identifier"
                            to={`/investigation/${encodeURIComponent(record.transaction_id)}`}
                          >
                            Investigate {record.transaction_id}
                          </Link>
                          <span aria-hidden="true">|</span>
                          <RiskBadge risk={record.priority || 'Critical'} />
                          <span>
                            | {record.agency} | {record.vendor} |{' '}
                            {record.amount_display || formatMoney(record.amount_paise)}
                          </span>
                        </div>
                        {record.explanation ? (
                          <ExplanationText explanation={record.explanation} />
                        ) : (
                          <>
                            <p>{record.signals?.join(' ')}</p>
                            {record.check ? <p>{record.check}</p> : null}
                          </>
                        )}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="muted">
                    No records in the returned alerts have Critical priority. Other priorities can
                    still warrant review.
                  </p>
                )}
                {data.critical_count > (data.critical_records?.length || 0) ? (
                  <p className="field-help">
                    Showing {data.critical_records.length} of {data.critical_count} critical
                    records, highest priority first.
                  </p>
                ) : null}
                <div className="summary-actions">
                  <Link className="button subtle" to="/anomalies?risk=Critical">
                    View critical results
                  </Link>
                  <Link className="button ghost" to="/anomalies">
                    Explore all returned alerts
                  </Link>
                </div>
              </>
            ) : null}
          </>
        ) : null}
      </AsyncState>
    </section>
  );
}
