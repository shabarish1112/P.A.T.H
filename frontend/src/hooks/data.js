import { useCallback } from 'react';

import { api } from '../services/api';
import { useApi } from './useApi';

export function useInsights() {
  const fetcher = useCallback((signal) => api.get('/api/analytics/insights', { signal }), []);
  return useApi(fetcher, []);
}

export function useSummary() {
  const fetcher = useCallback((signal) => api.get('/api/analytics/summary', { signal }), []);
  return useApi(fetcher, []);
}

export function useTrend() {
  const fetcher = useCallback((signal) => api.get('/api/analytics/trend', { signal }), []);
  return useApi(fetcher, []);
}

export function useTransactions({ query = '', cursor = '', limit = 50 } = {}) {
  const fetcher = useCallback(
    (signal) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (cursor) params.set('cursor', cursor);
      if (query) params.set('q', query);
      return api.get(`/api/transactions?${params.toString()}`, { signal });
    },
    [query, cursor, limit],
  );
  return useApi(fetcher, [query, cursor, limit]);
}

export function useAnomalies({ risk = '', limit = 200 } = {}) {
  const fetcher = useCallback(
    (signal) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (risk) params.set('risk', risk);
      return api.get(`/api/anomalies?${params.toString()}`, { signal });
    },
    [risk, limit],
  );
  return useApi(fetcher, [risk, limit]);
}

export function useReviews(limit = 200) {
  const fetcher = useCallback(
    (signal) => api.get(`/api/reviews?limit=${limit}`, { signal }),
    [limit],
  );
  return useApi(fetcher, [limit]);
}

export function useDatasets() {
  const fetcher = useCallback((signal) => api.get('/api/datasets', { signal }), []);
  return useApi(fetcher, []);
}
