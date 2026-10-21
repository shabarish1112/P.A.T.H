import { useCallback } from 'react';

import { AsyncState } from '../components/AsyncState';
import { LineChart } from '../components/Charts';
import { useApi } from '../hooks/useApi';
import { useTrend } from '../hooks/data';
import { api } from '../services/api';

export default function Analytics() {
  const trend = useTrend();
  const breakdownFetcher = useCallback((signal) => api.get('/api/analytics/breakdown?field=agency&limit=10', { signal }), []);
  const breakdown = useApi(breakdownFetcher, []);
  return <><header className="page-heading"><div><p className="eyebrow">Explainable visual analytics</p><h1>Visual Analytics</h1><p>Visuals support investigation; they are not proof of wrongdoing.</p></div></header><div className="dashboard-grid"><section className="panel span-2"><h2>Flagged-count trend</h2><AsyncState loading={trend.loading} error={trend.error} empty={!trend.data?.points?.length} onRetry={trend.retry}><LineChart points={trend.data?.points || []} /></AsyncState></section><section className="panel"><h2>Top agencies</h2><AsyncState loading={breakdown.loading} error={breakdown.error} empty={!breakdown.data?.items?.length} onRetry={breakdown.retry}><div className="bar-list">{breakdown.data?.items?.map((item) => <div key={item.name}><span>{item.name}</span><strong>{item.count}</strong><div className="bar-track"><span style={{ width: `${Math.min(100, item.count * 4)}%` }} /></div></div>)}</div></AsyncState></section></div></>;
}
