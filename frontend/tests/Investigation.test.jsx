import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import Investigation from '../src/pages/Investigation';

const { put } = vi.hoisted(() => ({ put: vi.fn().mockResolvedValue({}) }));
vi.mock('../src/contexts/AuthContext', () => ({ useAuth: () => ({ user: { role: 'reviewer' } }) }));
vi.mock('../src/contexts/ToastContext', () => ({ useToast: () => ({ push: vi.fn() }) }));
vi.mock('../src/services/api', () => ({ api: { get: vi.fn(), put } }));
vi.mock('../src/hooks/useApi', () => ({
  useApi: () => ({
    data: {
      transaction_id: 'TX/1',
      agency: 'A',
      scheme: 'S',
      vendor: 'V',
      district: 'D',
      date: '2026-01-01T00:00:00Z',
      amount_paise: 10000,
      risk: 'High',
      anomaly_score: 0.9,
      review_status: null,
      path_insight: { amount_vs_agency_mean: 2.1 },
    },
    loading: false,
    error: null,
    retry: vi.fn(),
  }),
}));

describe('Investigation', () => {
  it('records reviewer decision', async () => {
    render(
      <MemoryRouter initialEntries={['/investigation/TX%2F1']}>
        <Routes>
          <Route path="/investigation/:transactionId" element={<Investigation />} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'Escalated' } });
    fireEvent.change(screen.getByLabelText('Review note'), {
      target: { value: 'Needs another reviewer.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Record decision' }));
    expect(put).toHaveBeenCalled();
  });
});
