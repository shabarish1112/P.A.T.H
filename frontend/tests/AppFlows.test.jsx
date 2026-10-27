import { StrictMode } from 'react';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import App from '../src/App';
import { AuthProvider } from '../src/contexts/AuthContext';
import { ToastProvider } from '../src/contexts/ToastContext';
import { clearAccessToken } from '../src/services/api';
import { server } from './testServer';
import investigationFixture from './fixtures/investigation.json';

const user = { id: '1', email: 'admin@example.com', role: 'admin', is_active: true };
const row = {
  id: 't1',
  transaction_id: 'TX-1',
  date: '2026-01-01T00:00:00Z',
  agency: 'Health',
  scheme: 'Care',
  vendor: 'Vendor',
  district: 'District',
  amount_paise: 10000,
  score: 0.9,
  rank: 1,
  risk: 'High',
  anomaly_score: 0.9,
  path_insight: { deviation: 2 },
};
const metric = { value: 10, previous: 5, delta_percent: 100 };
let role;
let forced;
let refreshCalls;
let mutationError;
let jobStatus;
let insightStatus;

beforeEach(() => {
  role = 'admin';
  forced = false;
  refreshCalls = 0;
  mutationError = false;
  jobStatus = 'completed';
  insightStatus = 'ready';
  clearAccessToken();
  server.use(
    http.post('/api/auth/refresh', () => {
      refreshCalls += 1;
      return HttpResponse.json({ access_token: 'restored', user });
    }),
    http.get('/api/auth/me', () =>
      HttpResponse.json({ user: { ...user, role, must_change_password: forced } }),
    ),
    http.get('/api/*', ({ request }) => {
      const path = new URL(request.url).pathname;
      if (path === '/api/analytics/insights')
        return HttpResponse.json({
          status: insightStatus,
          narrative:
            insightStatus === 'ready'
              ? 'P.A.T.H. analyzed 10 public fund disbursal records from records.csv. One returned alert has Critical priority.'
              : insightStatus === 'no_dataset'
                ? 'No active dataset is available yet.'
                : 'The current upload has not been screened yet.',
          critical_count: 1,
          flagged_count: 1,
          transaction_count: 10,
          critical_records:
            insightStatus === 'ready'
              ? [
                  {
                    transaction_id: 'TX-1',
                    agency: 'Health',
                    vendor: 'Vendor',
                    amount_paise: 10000,
                    score: 0.99,
                    signals: ['Payment amount is 4.00 times the vendor average in this dataset.'],
                  },
                ]
              : [],
        });
      if (path === '/api/analytics/summary')
        return HttpResponse.json({
          total_disbursed_paise: metric,
          total_transactions: metric,
          active_anomalies: metric,
          flagged_volume_paise: metric,
          review_capacity: 10,
        });
      if (path === '/api/analytics/trend')
        return HttpResponse.json({
          points: [
            { bucket: '2026-01', current: 3, previous: 1 },
            { bucket: '2026-02', current: 2, previous: 4 },
          ],
        });
      if (path === '/api/analytics/breakdown')
        return HttpResponse.json({ items: [{ name: 'Health', count: 3 }] });
      if (path.startsWith('/api/models/jobs/'))
        return HttpResponse.json({
          job_id: 'job1',
          status: jobStatus,
          progress: 100,
          message: 'Result ready',
        });
      if (path.startsWith('/api/transactions/')) return HttpResponse.json(row);
      if (path === '/api/users')
        return HttpResponse.json({ items: [{ ...user, created_at: row.date }] });
      if (path === '/api/audit')
        return HttpResponse.json({
          items: [
            {
              id: 'a1',
              created_at: row.date,
              actor_email: user.email,
              action: 'user.create',
              resource_type: 'user',
              resource_id: '1',
            },
          ],
        });
      if (path === '/api/reviews')
        return HttpResponse.json({
          items: [
            {
              id: 'r1',
              transaction_id: 'TX-1',
              status: 'Escalated',
              actor_email: user.email,
              created_at: row.date,
              note: 'Check source',
            },
          ],
        });
      if (path === '/api/datasets')
        return HttpResponse.json({
          items: [
            {
              dataset_id: 'd1',
              filename: 'records.csv',
              row_count: 1,
              created_at: row.date,
              is_active: true,
            },
          ],
        });
      return HttpResponse.json({ items: [row], estimated_total: 2, next_cursor: 'next' });
    }),
    http.post('/api/*', ({ request }) => {
      if (mutationError) return HttpResponse.json({ detail: 'Action rejected' }, { status: 409 });
      if (new URL(request.url).pathname === '/api/auth/login')
        return HttpResponse.json({ access_token: 'logged-in', user });
      if (new URL(request.url).pathname === '/api/models/run')
        return HttpResponse.json({ job_id: 'job1', status: 'queued', progress: 0 });
      return HttpResponse.json({ rows_accepted: 1, rows_received: 1, issues: [], message: 'ok' });
    }),
    http.put('/api/reviews/:id', () => HttpResponse.json({ message: 'recorded' })),
  );
});
afterEach(cleanup);

function mount(path = '/workspace') {
  return render(
    <StrictMode>
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </AuthProvider>
      </MemoryRouter>
    </StrictMode>,
  );
}

async function open(label) {
  fireEvent.click(
    within(screen.getByRole('navigation', { name: 'Page navigation' })).getByRole('link', {
      name: label,
      exact: true,
    }),
  );
}

describe('real application flows with mocked HTTP boundaries', () => {
  it('restores once under StrictMode and navigates through populated analytics views', async () => {
    mount();
    await waitFor(() => expect(screen.getAllByText('+100.00% vs previous run')).toHaveLength(4), {
      timeout: 3000,
    });
    expect(refreshCalls).toBe(1);
    await open('Visual Analytics');
    expect(await screen.findByText('Health')).toBeInTheDocument();
    await open('Review history');
    expect(await screen.findByText('Check source')).toBeInTheDocument();
    await open('Investigation');
    expect(await screen.findByText(/Search for a transaction or select one/)).toBeInTheDocument();
    expect(screen.queryByRole('search')).not.toBeInTheDocument();
    await open('Transactions');
    fireEvent.click(await screen.findByText('TX-1'));
    expect(await screen.findByText('Transaction context')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'Escalated' } });
    fireEvent.change(screen.getByLabelText('Review note'), {
      target: { value: 'Inspect records' },
    });
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
    fireEvent.change(screen.getByLabelText('Temporary provisioning password'), {
      target: { value: 'A-long-test-password!' },
    });
    fireEvent.change(screen.getByLabelText('Role'), { target: { value: 'reviewer' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Create user' }).closest('form'));
    expect(await screen.findByText('User created.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss notification' }));
    expect(screen.queryByText('User created.')).not.toBeInTheDocument();
    mutationError = true;
    fireEvent.submit(screen.getByRole('button', { name: 'Create user' }).closest('form'));
    expect(await screen.findByText('Action rejected')).toBeInTheDocument();
    mutationError = false;
    await open('Datasets');
    await screen.findByText('records.csv');
    fireEvent.change(screen.getByLabelText('CSV file'), {
      target: { files: [new File(['x'], 'records.csv', { type: 'text/csv' })] },
    });
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
    expect(
      await screen.findByText('Model run completed.', {}, { timeout: 4000 }),
    ).toBeInTheDocument();
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
    fireEvent.change(screen.getByLabelText('Current password'), {
      target: { value: 'old-test-password!' },
    });
    fireEvent.change(screen.getByLabelText('New password'), {
      target: { value: 'new-test-password!' },
    });
    fireEvent.change(screen.getByLabelText('Confirm new password'), {
      target: { value: 'different-password!' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Change password' }).closest('form'));
    expect(screen.getByRole('alert')).toHaveTextContent('New passwords must match.');
    fireEvent.change(screen.getByLabelText('Confirm new password'), {
      target: { value: 'new-test-password!' },
    });
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
    expect(screen.getByRole('dialog', { name: 'Primary navigation' })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open navigation' })).toHaveFocus();
    fireEvent.click(screen.getByRole('button', { name: 'Open navigation' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close navigation' }));
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }));
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'long-test-password!' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByRole('heading', { name: 'Executive Dashboard' })).toBeInTheDocument();
  });
});

describe('guided analysis and human review', () => {
  it('takes a critical finding through investigation to recorded history', async () => {
    const decisions = [];
    server.use(
      http.put('/api/reviews/:id', async ({ request, params }) => {
        const body = await request.json();
        decisions.push({
          id: 'new-review',
          transaction_id: params.id,
          actor_email: user.email,
          created_at: row.date,
          ...body,
        });
        return HttpResponse.json(decisions[0]);
      }),
      http.get('/api/reviews', () => HttpResponse.json({ items: decisions })),
    );
    mount();
    expect(await screen.findByText(/P.A.T.H. analyzed 10 public fund/)).toBeInTheDocument();
    expect(screen.getByText(/4.00 times the vendor average/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: 'Investigate TX-1' }));
    await screen.findByText('Transaction context');
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'False Alert' } });
    fireEvent.change(screen.getByLabelText('Review note'), {
      target: { value: 'Verified the source invoice.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Record decision' }));
    await screen.findByText(/Review action recorded/);
    fireEvent.click(await screen.findByRole('link', { name: 'View review history' }));
    expect(await screen.findByText('Verified the source invoice.')).toBeInTheDocument();
    expect(screen.getByText('False Alert', { selector: '.badge' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: 'TX-1' }));
    expect(await screen.findByText('Transaction context')).toBeInTheDocument();
  });

  it('explains missing data, onboarding, and the next upload action', async () => {
    insightStatus = 'no_dataset';
    mount();
    expect(await screen.findByRole('link', { name: 'Upload a dataset' })).toBeInTheDocument();
    fireEvent.click(screen.getByText(/About P.A.T.H.:/));
    expect(screen.getByText(/uses unsupervised machine learning/)).toBeInTheDocument();
  });

  it('offers model execution for an uploaded but unprocessed dataset', async () => {
    insightStatus = 'not_analyzed';
    mount();
    fireEvent.click(await screen.findByRole('link', { name: 'Run an analysis' }));
    expect(
      await screen.findByRole('heading', { name: 'ML Anomaly Control Center' }),
    ).toBeInTheDocument();
  });

  it('shows guided review history instead of fabricated events and supports transaction lookup', async () => {
    server.use(http.get('/api/reviews', () => HttpResponse.json({ items: [] })));
    mount('/queue');
    expect(await screen.findByText('No review decisions have been recorded.')).toBeInTheDocument();
    expect(
      screen.getByText(/transaction ID, reviewer, status, note, and time/),
    ).toBeInTheDocument();
    await open('Investigation');
    fireEvent.change(screen.getByLabelText('Transaction ID'), { target: { value: 'TX-1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Open investigation' }));
    expect(await screen.findByText('Transaction context')).toBeInTheDocument();
  });

  it('opens the critical risk filter from the summary and handles no critical records', async () => {
    server.use(
      http.get('/api/analytics/insights', () =>
        HttpResponse.json({
          status: 'ready',
          narrative: 'Screening completed.',
          critical_count: 0,
          critical_records: [],
        }),
      ),
    );
    mount();
    expect(await screen.findByText(/No records in the returned alerts/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: 'View critical results' }));
    expect(await screen.findByLabelText('Risk')).toHaveValue('Critical');
  });
});

describe('understandable investigation workflow', () => {
  it('shows evidence, date-only context and persists a plain-language review action', async () => {
    let current = { ...investigationFixture };
    let saved;
    server.use(
      http.get('/api/transactions/TX-002562', () => HttpResponse.json(current)),
      http.put('/api/reviews/TX-002562', async ({ request }) => {
        saved = await request.json();
        current = {
          ...current,
          review_status: saved.status,
          review_note: saved.note,
          review_actor_email: 'reviewer@example.com',
          review_changed_at: '2026-10-25T10:00:00Z',
        };
        return HttpResponse.json(current);
      }),
    );
    mount('/investigation/TX-002562');
    expect(await screen.findByText(investigationFixture.explanation.headline)).toBeInTheDocument();
    expect(screen.getByText('14 Apr 2024')).toBeInTheDocument();
    expect(screen.getByText('2024-25')).toBeInTheDocument();
    expect(screen.getByText('#1 of 4,000')).toBeInTheDocument();
    expect(screen.getByText('First payment on record')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Confirm for investigation' })).toHaveValue(
      'Confirmed Finding',
    );
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'False Alert' } });
    fireEvent.change(screen.getByLabelText('Review note'), {
      target: { value: 'Checked the invoice.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Record decision' }));
    expect(await screen.findByText(/Last changed by reviewer@example.com/)).toBeInTheDocument();
    expect(saved).toEqual({ status: 'False Alert', note: 'Checked the invoice.' });
    expect(screen.getByLabelText('Review note')).toHaveValue('Checked the invoice.');
  });
});

describe('investigation outside the saved alert list', () => {
  it('shows available evidence without inventing model results', async () => {
    server.use(
      http.get('/api/transactions/TX-002562', () =>
        HttpResponse.json({
          ...investigationFixture,
          analysis_status: 'not_selected',
          risk: null,
          anomaly_score: null,
          rank: null,
        }),
      ),
    );
    mount('/investigation/TX-002562');
    expect(await screen.findByRole('heading', { name: 'Payment comparisons' })).toBeInTheDocument();
    expect(screen.getByText('Outside saved alert list', { exact: true })).toBeInTheDocument();
    expect(
      screen.getByText('Not saved outside the alert list', { exact: true }),
    ).toBeInTheDocument();
    expect(screen.getByText('First payment on record')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Payment evidence' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Why this was flagged' })).not.toBeInTheDocument();
  });
  it('shows comparisons before a run and does not offer an unavailable review mutation', async () => {
    server.use(
      http.get('/api/transactions/TX-002562', () =>
        HttpResponse.json({
          ...investigationFixture,
          analysis_status: 'not_analyzed',
          risk: null,
          anomaly_score: null,
          rank: null,
        }),
      ),
    );
    mount('/investigation/TX-002562');
    expect(
      await screen.findByText(
        'These are payment comparisons. Run an analysis to select records for review.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Payment evidence' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Record decision' })).not.toBeInTheDocument();
  });
});
