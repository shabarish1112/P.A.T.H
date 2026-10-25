import { PageHeader } from '../components/PageHeader';
import { useState } from 'react';

import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { Badge } from '../components/Badge';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useDatasets } from '../hooks/data';
import { apiRequest } from '../services/api';

export default function Datasets() {
  const { user } = useAuth();
  const { push } = useToast();
  const state = useDatasets();
  const [file, setFile] = useState(null);
  const [replace, setReplace] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [report, setReport] = useState(null);

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    setUploading(true);
    setReport(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const result = await apiRequest(`/api/datasets/upload?confirm_replace=${replace}`, {
        method: 'POST',
        body: form,
        timeoutMs: 120000,
      });
      setReport(result);
      push(`Dataset activated with ${result.rows_accepted} accepted rows.`, 'success');
      state.retry();
    } catch (error) {
      push(error.message, 'error');
    } finally {
      setUploading(false);
    }
  }

  const columns = [
    { key: 'filename', label: 'Dataset' },
    { key: 'row_count', align: 'right', label: 'Rows' },
    {
      key: 'created_at',
      label: 'Created',
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (row) => (
        <Badge tone={row.is_active ? 'success' : 'muted'}>
          {row.is_active ? 'Active' : 'Archived'}
        </Badge>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Dataset Management"
        description="CSV ingestion validates every row before a new version is activated."
        eyebrow="Controlled ingestion"
      />
      {user?.role === 'admin' ? (
        <div className="dashboard-grid">
          <section className="panel">
            <h2>Upload dataset</h2>
            <p className="panel-description">
              A successfully validated CSV becomes the active dataset.
            </p>
            <form className="upload-form" onSubmit={upload}>
              <div className="upload-area">
                <label>
                  CSV file
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    required
                    onChange={(event) => setFile(event.target.files?.[0] || null)}
                  />
                </label>
                <p className="file-summary">
                  {file ? `${file.name} · CSV file` : 'Select a CSV file to validate.'}
                </p>
              </div>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={replace}
                  onChange={(event) => setReplace(event.target.checked)}
                />{' '}
                Confirm replacement of the current active dataset
              </label>
              <p className="field-help">
                {replace
                  ? 'Replacement confirmed for this upload.'
                  : 'Replacement of an existing active dataset requires confirmation.'}
              </p>
              <button type="submit" className="button primary" disabled={uploading}>
                {uploading ? 'Validating…' : 'Upload and validate'}
              </button>
            </form>
          </section>
          <section className="panel">
            <h2>Validation report</h2>
            {report ? (
              <div className="validation-report" aria-live="polite">
                <strong>
                  {report.rows_accepted} accepted / {report.rows_received} received
                </strong>
                <div className="validation-stats">
                  <div>
                    <span>Accepted</span>
                    <strong>{report.rows_accepted}</strong>
                  </div>
                  <div>
                    <span>Rejected</span>
                    <strong>{report.rows_rejected ?? '—'}</strong>
                  </div>
                </div>
                {report.issues?.length ? (
                  <ul>
                    {report.issues.map((issue) => (
                      <li key={`${issue.row}-${issue.reason}`}>
                        <strong>Row {issue.row}</strong>
                        <p>{issue.reason}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No validation errors.</p>
                )}
              </div>
            ) : (
              <div className="async-state">Upload a CSV to see validation results.</div>
            )}
          </section>
        </div>
      ) : (
        <section className="panel">
          <p>Dataset mutation is restricted to administrators.</p>
        </section>
      )}
      <section className="panel">
        <h2>Dataset history</h2>
        <AsyncState
          loading={state.loading}
          error={state.error}
          empty={!state.data?.items?.length}
          emptyMessage="No datasets have been uploaded."
          onRetry={state.retry}
        >
          <DataTable
            label="Dataset history"
            columns={columns}
            rows={state.data?.items || []}
            rowKey={(row) => row.dataset_id}
          />
        </AsyncState>
      </section>
    </>
  );
}
