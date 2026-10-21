import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { RiskBadge } from '../components/RiskBadge';
import { RISK_LEVELS } from '../constants';
import { useAnomalies } from '../hooks/data';
import { formatMoney } from '../lib';

export default function Anomalies() {
  const navigate = useNavigate();
  const [risk, setRisk] = useState('');
  const state = useAnomalies({ risk, limit: 500 });
  const columns = [
    { key: 'rank', label: 'Rank' },
    { key: 'transaction_id', label: 'Transaction' },
    { key: 'agency', label: 'Agency' },
    { key: 'vendor', label: 'Vendor' },
    { key: 'amount', label: 'Amount', render: (row) => formatMoney(row.amount_paise) },
    { key: 'score', label: 'Score', render: (row) => row.score.toFixed(4) },
    { key: 'risk', label: 'Risk', render: (row) => <RiskBadge risk={row.risk} /> },
  ];
  return (
    <>
      <header className="page-heading"><div><p className="eyebrow">Ranked screening output</p><h1>Anomaly Explorer</h1><p>Only the configured Top-K cases from the active model run are shown.</p></div></header>
      <section className="panel"><div className="toolbar"><label>Risk<select value={risk} onChange={(event) => setRisk(event.target.value)}><option value="">All</option>{RISK_LEVELS.map((item) => <option key={item}>{item}</option>)}</select></label></div>
        <AsyncState loading={state.loading} error={state.error} empty={!state.data?.items?.length} onRetry={state.retry}><DataTable columns={columns} rows={state.data?.items || []} rowKey={(row) => row.id} onRowClick={(row) => navigate(`/investigation/${encodeURIComponent(row.transaction_id)}`)} /></AsyncState>
      </section>
    </>
  );
}
