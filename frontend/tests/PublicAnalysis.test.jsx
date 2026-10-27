import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';

import App from '../src/App';
import { server } from './testServer';

vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({ user: null, loading: false, authenticated: false, logout: vi.fn() }),
}));
afterEach(cleanup);

function mount(path = '/') {
  server.use(
    http.get('/api/public/limits', () => HttpResponse.json({ max_upload_mb: 4, max_rows: 4000 })),
  );
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe('public analysis', () => {
  it('opens the homepage without login and offers optional accounts', async () => {
    mount();
    expect(screen.getByRole('heading', { name: /Find the unusual/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Create account' })).toHaveAttribute('href', '/signup');
    expect(screen.getByRole('link', { name: 'Log in' })).toHaveAttribute('href', '/login');
    expect(await screen.findByText(/4,000 rows/)).toBeInTheDocument();
  });

  it('uploads as a guest, displays results and provides download', async () => {
    const result = {
      analysis_id: 'a'.repeat(32),
      rows_accepted: 12,
      rows_rejected: 0,
      issues: [],
      expires_at: '2027-01-01T00:00:00Z',
      alerts: [
        {
          rank: 1,
          transaction_id: 'TX-PUBLIC',
          agency: 'A',
          amount_paise: 10000,
          score: 0.9,
          risk: 'High',
        },
      ],
    };
    server.use(
      http.post('/api/public/analyze', () => HttpResponse.json(result, { status: 201 })),
      http.get('/api/public/analyses/:id', () => HttpResponse.json(result)),
    );
    mount();
    await screen.findByText(/4,000 rows/);
    fireEvent.change(screen.getByLabelText('Transaction CSV'), {
      target: { files: [new File(['csv'], 'data.csv', { type: 'text/csv' })] },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Upload and analyze' }).closest('form'));
    expect(await screen.findByText('TX-PUBLIC')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Download results (JSON)' })).toBeEnabled();
  });

  it('explains an expired result instead of redirecting to login', async () => {
    server.use(
      http.get('/api/public/analyses/:id', () =>
        HttpResponse.json({ detail: 'Result not found or expired.' }, { status: 404 }),
      ),
    );
    mount('/results/' + 'b'.repeat(32));
    expect(await screen.findByRole('alert')).toHaveTextContent('expired');
    expect(screen.getByRole('heading', { name: /Find the unusual/ })).toBeInTheDocument();
  });
});
