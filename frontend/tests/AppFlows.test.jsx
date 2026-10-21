import { StrictMode } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import App from '../src/App';
import { AuthProvider } from '../src/contexts/AuthContext';
import { ToastProvider } from '../src/contexts/ToastContext';
import { clearAccessToken } from '../src/services/api';
import { server } from './testServer';

const user = { id: '1', email: 'admin@example.com', role: 'admin', is_active: true };
const row = { id: 't1', transaction_id: 'TX-1', date: '2026-01-01T00:00:00Z', agency: 'Health',
  scheme: 'Care', vendor: 'Vendor', district: 'District', amount_paise: 10000,
  score: 0.9, rank: 1, risk: 'High', anomaly_score: 0.9, path_insight: { deviation: 2 } };
const metric = { value: 10, previous: 5, delta_percent: 100 };
let role;
let forced;
let refreshCalls;
let mutationError;
let jobStatus;

beforeEach(() => {
  role = 'admin'; forced = false; refreshCalls = 0; mutationError = false; jobStatus = 'completed';
  clearAccessToken();
  server.use(
    http.post('/api/auth/refresh', () => {
      refreshCalls += 1;
      return HttpResponse.json({ access_token: 'restored', user });
    }),
    http.get('/api/auth/me', () => HttpResponse.json({ user: { ...user, role, must_change_password: forced } })),
    http.get('/api/*', ({ request }) => {
      const path = new URL(request.url).pathname;
      if (path === '/api/analytics/summary') return HttpResponse.json({ total_disbursed_paise: metric,
        total_transactions: metric, active_anomalies: metric, flagged_volume_paise: metric, review_capacity: 10 });
      if (path === '/api/analytics/trend') return HttpResponse.json({ points: [
        { bucket: '2026-01', current: 3, previous: 1 }, { bucket: '2026-02', current: 2, previous: 4 }] });
      if (path === '/api/analytics/breakdown') return HttpResponse.json({ items: [{ name: 'Health', count: 3 }] });
      if (path.startsWith('/api/models/jobs/')) return HttpResponse.json({ job_id: 'job1', status: jobStatus, progress: 100, message: 'Result ready' });
      if (path.startsWith('/api/transactions/')) return HttpResponse.json(row);
      if (path === '/api/users') return HttpResponse.json({ items: [{ ...user, created_at: row.date }] });
      if (path === '/api/audit') return HttpResponse.json({ items: [{ id: 'a1', created_at: row.date,
        actor_email: user.email, action: 'user.create', resource_type: 'user', resource_id: '1' }] });
      if (path === '/api/reviews') return HttpResponse.json({ items: [{ id: 'r1', transaction_id: 'TX-1',
        status: 'Escalated', actor_email: user.email, created_at: row.date, note: 'Check source' }] });
      if (path === '/api/datasets') return HttpResponse.json({ items: [{ dataset_id: 'd1', filename: 'records.csv',
        row_count: 1, created_at: row.date, is_active: true }] });
      return HttpResponse.json({ items: [row], estimated_total: 2, next_cursor: 'next' });
    }),
    http.post('/api/*', ({ request }) => {
      if (mutationError) return HttpResponse.json({ detail: 'Action rejected' }, { status: 409 });
      if (new URL(request.url).pathname === '/api/auth/login') return HttpResponse.json({ access_token: 'logged-in', user });
      if (new URL(request.url).pathname === '/api/models/run') return HttpResponse.json({ job_id: 'job1', status: 'queued', progress: 0 });
      return HttpResponse.json({ rows_accepted: 1, rows_received: 1, issues: [], message: 'ok' });
    }),
    http.put('/api/reviews/:id', () => HttpResponse.json({ message: 'recorded' })),
  );
});
afterEach(cleanup);

function mount(path = '/') {
  return render(<StrictMode><MemoryRouter initialEntries={[path]}><AuthProvider><ToastProvider><App /></ToastProvider></AuthProvider></MemoryRouter></StrictMode>);
}

async function open(label) {
  fireEvent.click(await screen.findByRole('link', { name: label, exact: true }));
}

describe('real application flows with mocked HTTP boundaries', () => {
  it('restores once under StrictMode and navigates through populated analytics views', async () => {
    mount();
    await waitFor(() => expect(screen.getAllByText('+100.00% vs previous run')).toHaveLength(4));
    expect(refreshCalls).toBe(1);
    await open('Visual Analytics');
    expect(await screen.findByText('Health')).toBeInTheDocument();
    await open('Review Queue');
    expect(await screen.findByText('Check source')).toBeInTheDocument();
    await open('Investigation');
    expect(await screen.findByText(/Search for or select a transaction/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Search transaction ID'), { target: { value: 'TX-1' } });
    fireEvent.submit(screen.getByRole('search'));
    expect(await screen.findByText('Transaction context')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'Escalated' } });
    fireEvent.change(screen.getByLabelText('Review note'), { target: { value: 'Inspect records' } });
    fireEvent.click(screen.getByRole('button', { name: 'Record decision' }));
    expect(await screen.findByText(/Review action recorded/)).toBeInTheDocument();
  });

  it('searches transactions, paginates and opens anomaly rows', async () => {
    mount('/transactions');
    const tx = await screen.findByText('TX-1');
    fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'TX' } });
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    fireEvent.keyDown(tx.closest('tr'), { key: 'Enter' });
    expect(await screen.findByText('Transaction context')).toBeInTheDocument();
    await open('Anomaly Explorer');
    await screen.findByText('TX-1');
    fireEvent.change(screen.getByLabelText('Risk'), { target: { value: 'High' } });
    fireEvent.click(screen.getByText('TX-1'));
    expect(await screen.findByText('Transaction context')).toBeInTheDocument();
  });

  it('creates users, reports errors and uploads datasets', async () => {
    mount('/admin');
    await screen.findByRole('heading', { name: 'Create user' });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'new@example.com' } });
    fireEvent.change(screen.getByLabelText('Temporary provisioning password'), { target: { value: 'A-long-test-password!' } });
    fireEvent.change(screen.getByLabelText('Role'), { target: { value: 'reviewer' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Create user' }).closest('form'));
    expect(await screen.findByText('User created.')).toBeInTheDocument();
    mutationError = true;
    fireEvent.submit(screen.getByRole('button', { name: 'Create user' }).closest('form'));
    expect(await screen.findByText('Action rejected')).toBeInTheDocument();
    mutationError = false;
    await open('Datasets');
    await screen.findByText('records.csv');
    fireEvent.change(screen.getByLabelText('CSV file'), { target: { files: [new File(['x'], 'records.csv', { type: 'text/csv' })] } });
    fireEvent.click(screen.getByLabelText(/Confirm replacement/));
    fireEvent.submit(screen.getByRole('button', { name: 'Upload and validate' }).closest('form'));
    expect(await screen.findByText('No validation errors.')).toBeInTheDocument();
    mutationError = true;
    fireEvent.submit(screen.getByRole('button', { name: 'Upload and validate' }).closest('form'));
    await waitFor(() => expect(screen.getAllByText('Action rejected').length).toBeGreaterThan(0));
  });

  it('runs models and polls completion and failure', async () => {
    mount('/control');
    await screen.findByRole('heading', { name: 'ML Anomaly Control Center' });
    fireEvent.change(screen.getByLabelText('Model'), { target: { value: 'eif' } });
    fireEvent.change(screen.getByLabelText('Alert budget (Top-K)'), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText('Trees'), { target: { value: '50' } });
    fireEvent.click(screen.getByLabelText('Generate optional UMAP sample'));
    fireEvent.click(screen.getByRole('button', { name: 'Run model' }));
    expect(await screen.findByText('Model run completed.', {}, { timeout: 4000 })).toBeInTheDocument();
    jobStatus = 'failed';
    fireEvent.click(screen.getByRole('button', { name: 'Run model' }));
    await screen.findByText('failed', {}, { timeout: 4000 });
    mutationError = true;
    fireEvent.click(screen.getByRole('button', { name: 'Run model' }));
    expect(await screen.findByText('Action rejected')).toBeInTheDocument();
  });

  it('forces a reset user to change password and returns to sign in', async () => {
    forced = true;
    mount();
    await screen.findByRole('heading', { name: 'Change password' });
    fireEvent.change(screen.getByLabelText('Current password'), { target: { value: 'old-test-password!' } });
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'new-test-password!' } });
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'different-password!' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Change password' }).closest('form'));
    expect(screen.getByRole('alert')).toHaveTextContent('New passwords must match.');
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'new-test-password!' } });
    mutationError = true;
    fireEvent.submit(screen.getByRole('button', { name: 'Change password' }).closest('form'));
    expect(await screen.findByText('Action rejected')).toBeInTheDocument();
    mutationError = false;
    fireEvent.submit(screen.getByRole('button', { name: 'Change password' }).closest('form'));
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('hides administration from analysts and supports logout', async () => {
    role = 'analyst';
    mount('/admin');
    await screen.findByRole('heading', { name: 'Executive Dashboard' });
    expect(screen.queryByRole('link', { name: 'Access & Audit' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Open navigation' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close navigation' }));
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }));
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-test-password!' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByRole('heading', { name: 'Executive Dashboard' })).toBeInTheDocument();
  });
});
