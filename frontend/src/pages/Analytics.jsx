import { PageHeader } from '../components/PageHeader';
import { useCallback } from 'react';

import { AsyncState } from '../components/AsyncState';
import { LineChart } from '../components/Charts';
import { useApi } from '../hooks/useApi';
import { useTrend } from '../hooks/data';
import { api } from '../services/api';

export default function Analytics() {
  const trend = useTrend();
  const breakdownFetcher = useCallback(
    (signal) => api.get('/api/analytics/breakdown?field=agency&limit=10', { signal }),
    [],
  );
  const breakdown = useApi(breakdownFetcher, []);
  return (
    <>
      <PageHeader
        title="Visual Analytics"
        description="Visuals support investigation; they are not proof of wrongdoing."
        eyebrow="Explainable visual analytics"
      />
      <div className="dashboard-grid">
        <section className="panel span-2">
          <h2>Flagged-count trend</h2>
          <AsyncState
            loading={trend.loading}
            error={trend.error}
            empty={!trend.data?.points?.length}
            emptyMessage="No anomaly screening results are available yet."
            onRetry={trend.retry}
          >
            <LineChart points={trend.data?.points || []} />
          </AsyncState>
        </section>
        <section className="panel">
          <h2>Top agencies</h2>
          <AsyncState
            loading={breakdown.loading}
            error={breakdown.error}
            empty={!breakdown.data?.items?.length}
            emptyMessage="No agency breakdown is available yet."
            onRetry={breakdown.retry}
          >
            <div className="bar-list">
              {breakdown.data?.items?.map((item) => (
                <div key={item.name}>
                  <span>{item.name}</span>
                  <strong>{item.count}</strong>
                  <div className="bar-track">
                    <span
                      style={{
                        width: `${Math.min(100, (item.count / Math.max(1, ...breakdown.data.items.map((entry) => entry.count))) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </AsyncState>
        </section>
      </div>
    </>
  );
}
