import { AsyncState } from '../components/AsyncState';
import { LineChart } from '../components/Charts';
import { useSummary, useTrend } from '../hooks/data';
import { formatMoney, formatNumber, formatPercent } from '../lib';

function MetricCard({ label, metric, money = false }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{money ? formatMoney(metric?.value) : formatNumber(metric?.value)}</strong>
      <small>
        {metric?.delta_percent == null
          ? 'No comparison run'
          : `${formatPercent(metric.delta_percent)} vs previous run`}
      </small>
    </article>
  );
}

export default function Dashboard() {
  const summary = useSummary();
  const trend = useTrend();

  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">Today</p>
          <h1>Executive Dashboard</h1>
          <p>Operational screening overview for the active dataset and model run.</p>
        </div>
      </header>
      <AsyncState
        loading={summary.loading}
        error={summary.error}
        empty={!summary.data}
        onRetry={summary.retry}
      >
        {summary.data ? (
          <div className="metric-grid">
            <MetricCard label="Total disbursed" metric={summary.data.total_disbursed_paise} money />
            <MetricCard label="Transactions" metric={summary.data.total_transactions} />
            <MetricCard label="Active anomalies" metric={summary.data.active_anomalies} />
            <MetricCard label="Flagged volume" metric={summary.data.flagged_volume_paise} money />
          </div>
        ) : null}
      </AsyncState>
      <div className="dashboard-grid">
        <section className="panel span-2">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Signal trend</p>
              <h2>Flagged activity</h2>
            </div>
            <div className="legend">
              <span className="dot current" />
              Current <span className="dot previous" />
              Previous
            </div>
          </div>
          <AsyncState
            loading={trend.loading}
            error={trend.error}
            empty={!trend.data?.points?.length}
            onRetry={trend.retry}
          >
            <LineChart points={trend.data?.points || []} />
          </AsyncState>
        </section>
        <section className="panel">
          <p className="eyebrow">Review capacity</p>
          <h2>{summary.data?.review_capacity || 0}</h2>
          <p className="muted">Top-K alerts available to reviewers in the active cycle.</p>
          <div className="principle-card compact">
            <span className="principle-dot" /> Unusual ≠ Fraudulent
          </div>
        </section>
      </div>
    </>
  );
}
