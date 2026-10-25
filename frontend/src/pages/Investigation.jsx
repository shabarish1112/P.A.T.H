import { useCallback, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { AsyncState } from '../components/AsyncState';
import { RiskBadge } from '../components/RiskBadge';
import { PageHeader } from '../components/PageHeader';
import { ReviewBadge } from '../components/Badge';
import { REVIEW_STATUSES } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useApi } from '../hooks/useApi';
import { formatMoney, formatPaymentDate } from '../lib';
import { ExplanationText, SignalEvidence, CRITICAL_HELP } from '../components/PaymentExplanation';
import { api } from '../services/api';

export default function Investigation() {
  const params = useParams();
  const transactionId = params.transactionId || '';
  const { user } = useAuth();
  const fetcher = useCallback(
    (signal) =>
      transactionId
        ? api.get(`/api/transactions/${encodeURIComponent(transactionId)}`, { signal })
        : Promise.resolve(null),
    [transactionId],
  );
  const state = useApi(fetcher, [transactionId]);

  if (!transactionId)
    return (
      <>
        <PageHeader
          title="Investigation"
          description="Inspect transaction context, model output, and recorded review state."
        />
        <section className="panel">
          <h2>Select a transaction to investigate</h2>
          <p className="panel-description">
            Search for a transaction or select one from a results table.
          </p>
          <p className="workflow-instructions">
            Start with a critical record in the dashboard summary or Anomaly Explorer. Open it to
            compare the payment with its context, then record a review decision if your role allows
            it.
          </p>
          <TransactionLookup />
          <div className="summary-actions">
            <Link className="button subtle" to="/anomalies?risk=Critical">
              Browse critical results
            </Link>
            <Link className="button ghost" to="/transactions">
              Browse transactions
            </Link>
          </div>
        </section>
      </>
    );

  return (
    <AsyncState
      loading={state.loading}
      error={state.error}
      empty={!state.data}
      onRetry={state.retry}
    >
      {state.data ? (
        <>
          <PageHeader
            title={state.data.transaction_id}
            identifier
            eyebrow="Transaction investigation"
            description={`${state.data.agency} · ${state.data.scheme}`}
            actions={
              <>
                {state.data.risk ? (
                  state.data.risk === 'Critical' ? (
                    <details className="priority-help">
                      <summary>
                        <RiskBadge risk={state.data.risk} />{' '}
                        <span className="sr-only">Priority help</span>
                      </summary>
                      <p>{CRITICAL_HELP}</p>
                    </details>
                  ) : (
                    <RiskBadge risk={state.data.risk} />
                  )
                ) : (
                  <span className="badge badge-muted">
                    {state.data.analysis_status === 'not_selected'
                      ? 'Outside saved alert list'
                      : 'Not screened'}
                  </span>
                )}
                <ReviewBadge status={state.data.review_status} />
              </>
            }
          />
          <section className="panel investigation-explanation" aria-labelledby="why-flagged">
            <h2 id="why-flagged">
              {state.data.analysis_status && state.data.analysis_status !== 'selected'
                ? 'Payment comparisons'
                : 'Why this was flagged'}
            </h2>
            {state.data.analysis_status === 'not_selected' ? (
              <p className="panel-description">
                This payment is outside the saved alert list. The comparisons below come from your
                uploaded records; no score or priority was saved for it.
              </p>
            ) : null}
            {state.data.analysis_status === 'not_analyzed' ? (
              <p className="panel-description">
                These are payment comparisons. Run an analysis to select records for review.
              </p>
            ) : null}
            <ExplanationText explanation={state.data.explanation} />
            {state.data.explanation?.tags?.length ? (
              <p className="muted">{state.data.explanation.tags.join(' · ')}</p>
            ) : null}
          </section>
          <div className="investigation-grid">
            <section className="panel">
              <h2>Transaction context</h2>
              <dl className="detail-grid">
                <div>
                  <dt>Amount</dt>
                  <dd>{formatMoney(state.data.amount_paise)}</dd>
                </div>
                <div>
                  <dt>Vendor</dt>
                  <dd>{state.data.vendor}</dd>
                </div>
                <div>
                  <dt>District</dt>
                  <dd>{state.data.district}</dd>
                </div>
                <div>
                  <dt>Date</dt>
                  <dd>{formatPaymentDate(state.data.date)}</dd>
                </div>
                <div>
                  <dt>Financial year</dt>
                  <dd>{state.data.path_insight?.fiscal_year || 'Not available'}</dd>
                </div>
                {state.data.rank != null ? (
                  <div>
                    <dt>Review order</dt>
                    <dd>
                      #{state.data.rank}
                      {state.data.total_transactions
                        ? ` of ${state.data.total_transactions.toLocaleString('en-IN')}`
                        : ''}
                    </dd>
                  </div>
                ) : null}
                <div>
                  <dt>Score (technical detail)</dt>
                  <dd>
                    {state.data.anomaly_score?.toFixed(4) ??
                      (state.data.analysis_status === 'not_selected'
                        ? 'Not saved outside the alert list'
                        : 'Not scored')}
                  </dd>
                </div>
                <div>
                  <dt>Current review</dt>
                  <dd>{state.data.review_status || 'Pending Review'}</dd>
                </div>
                <div>
                  <dt>Last review update</dt>
                  <dd>
                    {state.data.review_changed_at
                      ? `Last changed by ${state.data.review_actor_email || 'a reviewer'} at ${new Date(state.data.review_changed_at).toLocaleString('en-IN')}`
                      : 'No review decision has been recorded yet.'}
                  </dd>
                </div>
                {state.data.review_note ? (
                  <div>
                    <dt>Recorded note</dt>
                    <dd>{state.data.review_note}</dd>
                  </div>
                ) : null}
              </dl>
            </section>
            <section className="panel">
              <h2>Payment evidence</h2>
              <p className="panel-description">
                Compare this payment with the uploaded records. These comparisons guide review; they
                do not prove a cause.
              </p>
              {state.data.explanation ? (
                <SignalEvidence signals={state.data.explanation.signals} />
              ) : (
                <p className="muted">No payment evidence is available yet.</p>
              )}
            </section>
            {['reviewer', 'admin'].includes(user?.role) &&
            state.data.analysis_status !== 'not_analyzed' ? (
              <section className="panel span-2 review-panel">
                <h2>Record your review</h2>
                <p className="review-disclaimer">
                  Model output prioritizes investigation and does not determine wrongdoing.
                </p>
                <ReviewDecisionForm
                  key={`${transactionId}-${state.data.review_changed_at || 'new'}`}
                  initialNote={state.data.review_note}
                  transactionId={transactionId}
                  initialStatus={state.data.review_status}
                  onSaved={state.retry}
                />
              </section>
            ) : null}
          </div>
        </>
      ) : null}
    </AsyncState>
  );
}

function TransactionLookup() {
  const [id, setId] = useState('');
  const navigate = useNavigate();
  function submit(event) {
    event.preventDefault();
    if (id.trim()) navigate(`/investigation/${encodeURIComponent(id.trim())}`);
  }
  return (
    <form className="transaction-lookup" onSubmit={submit}>
      <label>
        Transaction ID
        <input
          value={id}
          onChange={(event) => setId(event.target.value)}
          maxLength={64}
          required
          placeholder="For example, TX-000001"
        />
      </label>
      <button type="submit" className="button primary">
        Open investigation
      </button>
    </form>
  );
}

function ReviewDecisionForm({ transactionId, initialStatus, initialNote, onSaved }) {
  const { push } = useToast();
  const [status, setStatus] = useState(initialStatus || 'Pending Review');
  const [note, setNote] = useState(initialNote || '');
  const [saving, setSaving] = useState(false);
  async function saveReview(event) {
    event.preventDefault();
    if (saving) return;
    setSaving(true);
    try {
      await api.put(`/api/reviews/${encodeURIComponent(transactionId)}`, { status, note });
      push('Review action recorded in the audit trail.', 'success');
      onSaved();
    } catch (error) {
      push(error.message, 'error');
    } finally {
      setSaving(false);
    }
  }
  return (
    <form className="review-form" onSubmit={saveReview}>
      <label>
        Status
        <select
          aria-label="Status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {REVIEW_STATUSES.map((item) => (
            <option key={item} value={item}>
              {{
                'Confirmed Finding': 'Confirm for investigation',
                'False Alert': 'Mark as explained',
                Escalated: 'Escalate',
                'Pending Review': 'Pending Review',
              }[item] || item}
            </option>
          ))}
        </select>
      </label>
      <p className="field-help">
        Confirm for investigation keeps the record open for follow-up. Mark as explained records a
        supported explanation. Escalate requests further attention.
      </p>
      <label>
        Review note
        <textarea
          value={note}
          maxLength={2000}
          rows="4"
          onChange={(event) => setNote(event.target.value)}
        />
      </label>
      <div className="summary-actions">
        <button type="submit" className="button primary" disabled={saving}>
          {saving ? 'Recording…' : 'Record decision'}
        </button>
        <Link className="button subtle" to="/queue">
          View review history
        </Link>
      </div>
    </form>
  );
}
