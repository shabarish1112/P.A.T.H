import { useState } from 'react';

import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
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
      const result = await apiRequest(`/api/datasets/upload?confirm_replace=${replace}`, { method: 'POST', body: form, timeoutMs: 120000 });
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
    { key: 'row_count', label: 'Rows' },
    { key: 'created_at', label: 'Created', render: (row) => new Date(row.created_at).toLocaleString() },
    { key: 'is_active', label: 'Status', render: (row) => (row.is_active ? 'Active' : 'Archived') },
  ];

  return (
    <>
      <header className="page-heading"><div><p className="eyebrow">Controlled ingestion</p><h1>Dataset Management</h1><p>CSV ingestion validates every row before a new version is activated.</p></div></header>
      {user?.role === 'admin' ? <section className="panel"><form className="upload-form" onSubmit={upload}><label>CSV file<input type="file" accept=".csv,text/csv" required onChange={(event) => setFile(event.target.files?.[0] || null)} /></label><label className="checkbox"><input type="checkbox" checked={replace} onChange={(event) => setReplace(event.target.checked)} /> Confirm replacement of the current active dataset</label><button type="submit" className="button primary" disabled={uploading}>{uploading ? 'Validating…' : 'Upload and validate'}</button></form>{report ? <div className="validation-report" aria-live="polite"><strong>{report.rows_accepted} accepted / {report.rows_received} received</strong>{report.issues?.length ? <ul>{report.issues.map((issue) => <li key={`${issue.row}-${issue.reason}`}>Row {issue.row}: {issue.reason}</li>)}</ul> : <p>No validation errors.</p>}</div> : null}</section> : <section className="panel"><p>Dataset mutation is restricted to administrators.</p></section>}
      <section className="panel"><AsyncState loading={state.loading} error={state.error} empty={!state.data?.items?.length} onRetry={state.retry}><DataTable columns={columns} rows={state.data?.items || []} rowKey={(row) => row.dataset_id} /></AsyncState></section>
    </>
  );
}
