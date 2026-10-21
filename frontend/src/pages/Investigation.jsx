import { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';

import { AsyncState } from '../components/AsyncState';
import { RiskBadge } from '../components/RiskBadge';
import { REVIEW_STATUSES } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useApi } from '../hooks/useApi';
import { formatMoney } from '../lib';
import { api } from '../services/api';

export default function Investigation() {
  const params = useParams();
  const transactionId = params.transactionId || '';
  const { user } = useAuth();
  const { push } = useToast();
  const [status, setStatus] = useState('Pending Review');
  const [note, setNote] = useState('');
  const fetcher = useCallback((signal) => transactionId ? api.get(`/api/transactions/${encodeURIComponent(transactionId)}`, { signal }) : Promise.resolve(null), [transactionId]);
  const state = useApi(fetcher, [transactionId]);

  async function saveReview(event) {
    event.preventDefault();
    try {
      await api.put(`/api/reviews/${encodeURIComponent(transactionId)}`, { status, note });
      push('Review action recorded in the audit trail.', 'success');
      state.retry();
    } catch (error) {
      push(error.message, 'error');
    }
  }

  if (!transactionId) return <section className="panel"><p>Search for or select a transaction to open its investigation view.</p></section>;

  return <AsyncState loading={state.loading} error={state.error} empty={!state.data} onRetry={state.retry}>{state.data ? <><header className="page-heading"><div><p className="eyebrow">Transaction investigation</p><h1>{state.data.transaction_id}</h1><p>{state.data.agency} · {state.data.scheme}</p></div><RiskBadge risk={state.data.risk || 'Normal'} /></header><div className="investigation-grid"><section className="panel"><h2>Transaction context</h2><dl className="detail-grid"><div><dt>Amount</dt><dd>{formatMoney(state.data.amount_paise)}</dd></div><div><dt>Vendor</dt><dd>{state.data.vendor}</dd></div><div><dt>District</dt><dd>{state.data.district}</dd></div><div><dt>Date</dt><dd>{new Date(state.data.date).toLocaleString()}</dd></div><div><dt>Anomaly score</dt><dd>{state.data.anomaly_score?.toFixed(4) ?? 'Not scored'}</dd></div><div><dt>Current review</dt><dd>{state.data.review_status || 'Pending Review'}</dd></div></dl></section><section className="panel"><h2>PATH Insight</h2>{state.data.path_insight ? <div className="insight-list">{Object.entries(state.data.path_insight).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{String(value)}</strong></div>)}</div> : <p className="muted">No model explanation is available for this transaction.</p>}</section>{['reviewer', 'admin'].includes(user?.role) ? <section className="panel span-2"><h2>Human validation</h2><form className="review-form" onSubmit={saveReview}><label>Status<select value={status} onChange={(event) => setStatus(event.target.value)}>{REVIEW_STATUSES.map((item) => <option key={item}>{item}</option>)}</select></label><label>Review note<textarea value={note} maxLength={2000} rows="4" onChange={(event) => setNote(event.target.value)} /></label><button type="submit" className="button primary">Record decision</button></form></section> : null}</div></> : null}</AsyncState>;
}
