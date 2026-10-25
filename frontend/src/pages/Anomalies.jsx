import { PageHeader } from '../components/PageHeader';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { RiskBadge } from '../components/RiskBadge';
import { RISK_LEVELS } from '../constants';
import { useAnomalies } from '../hooks/data';
import { formatMoney } from '../lib';

export default function Anomalies() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const risk = RISK_LEVELS.includes(searchParams.get('risk')) ? searchParams.get('risk') : '';
  function setRisk(value) {
    setSearchParams(value ? { risk: value } : {});
  }
  const state = useAnomalies({ risk, limit: 500 });
  const columns = [
    { key: 'rank', align: 'right', label: 'Rank' },
    { key: 'transaction_id', label: 'Transaction' },
    { key: 'agency', label: 'Agency' },
    { key: 'vendor', label: 'Vendor' },
    {
      key: 'amount',
      align: 'right',
      label: 'Amount',
      render: (row) => formatMoney(row.amount_paise),
    },
    { key: 'score', align: 'right', label: 'Score', render: (row) => row.score.toFixed(4) },
    { key: 'risk', label: 'Risk', render: (row) => <RiskBadge risk={row.risk} /> },
  ];
  return (
    <>
      <PageHeader
        title="Anomaly Explorer"
        description="Only the configured Top-K cases from the active model run are shown."
        eyebrow="Ranked screening output"
      />
      <section className="panel">
        <div className="toolbar">
          <label>
            Risk
            <select
              aria-label="Risk"
              value={risk}
              onChange={(event) => setRisk(event.target.value)}
            >
              <option value="">All</option>
              {RISK_LEVELS.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
        <AsyncState
          loading={state.loading}
          error={state.error}
          empty={!state.data?.items?.length}
          emptyMessage={
            risk
              ? 'No transactions match this risk filter.'
              : 'No anomaly screening results are available yet.'
          }
          onRetry={state.retry}
        >
          <DataTable
            label="Ranked anomaly results"
            columns={columns}
            rows={state.data?.items || []}
            rowKey={(row) => row.id}
            onRowClick={(row) =>
              navigate(`/investigation/${encodeURIComponent(row.transaction_id)}`)
            }
          />
        </AsyncState>
      </section>
    </>
  );
}
