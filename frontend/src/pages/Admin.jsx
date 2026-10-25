import { PageHeader } from '../components/PageHeader';
import { useCallback, useState } from 'react';

import { Badge } from '../components/Badge';
import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { useToast } from '../contexts/ToastContext';
import { useApi } from '../hooks/useApi';
import { api } from '../services/api';

export default function Admin() {
  const { push } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [role, setRole] = useState('analyst');
  const usersFetcher = useCallback((signal) => api.get('/api/users', { signal }), []);
  const auditFetcher = useCallback((signal) => api.get('/api/audit?limit=100', { signal }), []);
  const users = useApi(usersFetcher, []);
  const audit = useApi(auditFetcher, []);

  async function createUser(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    try {
      await api.post('/api/users', { email, password, role });
      setEmail('');
      setPassword('');
      push('User created.', 'success');
      users.retry();
      audit.retry();
    } catch (error) {
      push(error.message, 'error');
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Access & Audit"
        description="Manage workspace access and inspect recorded security and review events."
        eyebrow="Administration"
      />
      <div className="dashboard-grid admin-grid">
        <section className="panel">
          <h2>Create user</h2>
          <form className="review-form" onSubmit={createUser}>
            <label>
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label>
              Temporary provisioning password
              <input
                type="password"
                required
                minLength={12}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <label>
              Role
              <select
                aria-label="Role"
                value={role}
                onChange={(event) => setRole(event.target.value)}
              >
                <option value="analyst">analyst</option>
                <option value="reviewer">reviewer</option>
                <option value="admin">admin</option>
              </select>
            </label>
            <button className="button primary" type="submit" disabled={busy}>
              {busy ? 'Creating…' : 'Create user'}
            </button>
          </form>
        </section>
        <section className="panel">
          <h2>User management</h2>
          <p className="panel-description">
            Provisioned accounts and their current workspace access.
          </p>
          <AsyncState
            loading={users.loading}
            error={users.error}
            empty={!users.data?.items?.length}
            emptyMessage="No user accounts are available."
            onRetry={users.retry}
          >
            <DataTable
              columns={[
                { key: 'email', label: 'Email' },
                { key: 'role', label: 'Role' },
                {
                  key: 'is_active',
                  label: 'Active',
                  render: (row) => (
                    <Badge tone={row.is_active ? 'success' : 'muted'}>
                      {row.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  ),
                },
              ]}
              rows={users.data?.items || []}
              rowKey={(row) => row.id}
            />
          </AsyncState>
        </section>
      </div>
      <section className="panel panel-secondary">
        <h2>Audit log</h2>
        <p className="panel-description">Read-only security and investigation events.</p>
        <AsyncState
          loading={audit.loading}
          error={audit.error}
          empty={!audit.data?.items?.length}
          emptyMessage="No audit events have been recorded."
          onRetry={audit.retry}
        >
          <DataTable
            columns={[
              {
                key: 'created_at',
                label: 'Time',
                render: (row) => new Date(row.created_at).toLocaleString(),
              },
              { key: 'actor_email', label: 'Actor' },
              { key: 'action', label: 'Action' },
              { key: 'resource_type', label: 'Resource' },
              { key: 'resource_id', label: 'ID' },
            ]}
            rows={audit.data?.items || []}
            rowKey={(row) => row.id}
          />
        </AsyncState>
      </section>
    </>
  );
}
