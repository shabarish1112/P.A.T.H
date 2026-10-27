import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { api, apiRequest } from '../services/api';
import { MODEL_OPTIONS } from '../constants';

const columns = 'transaction_id,date,agency,scheme,vendor,district,amount,sanctioned_amount';
const sample =
  columns +
  '\n' +
  Array.from(
    { length: 12 },
    (_, i) =>
      `SAMPLE-${i + 1},2026-01-${String(i + 1).padStart(2, '0')},Example agency,Example scheme,Vendor ${i % 3},Example district,${i === 11 ? 900000 : 1000 + i * 50},1000000`,
  ).join('\n');

function download(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function PublicAnalysis() {
  const { user, logout } = useAuth();
  const { analysisId } = useParams();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('if');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [limits, setLimits] = useState(null);
  const [limitError, setLimitError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    api
      .get('/api/public/limits', { signal: controller.signal })
      .then((data) => {
        if (!Number.isFinite(data.max_upload_mb) || !Number.isFinite(data.max_rows))
          throw new Error('Invalid service limits');
        setLimits(data);
      })
      .catch((e) => {
        if (e.name !== 'AbortError') setLimitError(true);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!analysisId) {
      setResult(null);
      return undefined;
    }
    const controller = new AbortController();
    setResult(null);
    setLoading(true);
    setError('');
    api
      .get(`/api/public/analyses/${analysisId}`, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setResult(data);
      })
      .catch((e) => {
        if (e.name !== 'AbortError') setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [analysisId]);

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (!file || !limits) return;
    if (file.size > limits.max_upload_mb * 1024 * 1024) {
      setError(`Choose a CSV smaller than ${limits.max_upload_mb} MB.`);
      return;
    }
    setBusy(true);
    try {
      const body = new FormData();
      body.append('file', file);
      const data = await apiRequest(`/api/public/analyze?model=${model}`, {
        method: 'POST',
        body,
        timeoutMs: 290000,
      });
      setResult(data);
      navigate(`/results/${data.analysis_id}`);
    } catch (e) {
      setError(
        e.name === 'TimeoutError' || e.name === 'AbortError'
          ? 'The analysis timed out. Try a smaller CSV.'
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    try {
      await logout();
    } catch {
      setError('Sign out could not be completed. Please retry.');
    }
  }

  return (
    <div className="public-shell">
      <a className="public-skip" href="#public-main">
        Skip to analysis
      </a>
      <header className="public-header">
        <Link to="/" className="public-brand">
          <span className="path-mark">P</span>
          <strong>P.A.T.H.</strong>
        </Link>
        <nav aria-label="Account navigation" className="public-actions">
          {user ? (
            <>
              <span className="public-account">{user.email}</span>
              {['admin', 'analyst', 'reviewer'].includes(user.role) && (
                <Link className="button secondary" to="/workspace">
                  Staff workspace
                </Link>
              )}
              <button className="button ghost" type="button" onClick={signOut}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link className="button ghost" to="/login">
                Log in
              </Link>
              <Link className="button primary" to="/signup">
                Create account
              </Link>
            </>
          )}
        </nav>
      </header>
      <main id="public-main" className="public-main">
        <section className="public-hero">
          <p className="eyebrow">PUBLIC ANOMALY TRACKING HUB</p>
          <h1>
            Find the unusual.
            <br />
            <span>Understand what needs a closer look.</span>
          </h1>
          <p className="lead">
            Upload a transaction CSV, screen it with machine learning, and download ranked results.
            No account required.
          </p>
          <div className="public-steps" aria-label="Analysis steps">
            <span>01 · Upload</span>
            <span>02 · Analyze</span>
            <span>03 · Explore results</span>
          </div>
        </section>
        <div className="public-grid">
          <section className="public-card" aria-labelledby="upload-title">
            <p className="eyebrow">START HERE</p>
            <h2 id="upload-title">Analyze your data</h2>
            <p>
              Unusual ≠ Fraudulent. Results prioritize human review and do not prove wrongdoing.
            </p>
            <form onSubmit={submit} className="public-form" aria-busy={busy}>
              <label htmlFor="guest-file">Transaction CSV</label>
              <input
                id="guest-file"
                type="file"
                accept=".csv,text/csv"
                required
                disabled={busy}
                onChange={(event) => {
                  setFile(event.target.files?.[0] || null);
                  setError('');
                }}
              />
              <label htmlFor="guest-model">Screening model</label>
              <select
                id="guest-model"
                value={model}
                disabled={busy}
                onChange={(event) => setModel(event.target.value)}
              >
                {MODEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="muted">
                {limits
                  ? `Up to ${limits.max_upload_mb} MB and ${limits.max_rows.toLocaleString()} rows. Six analyses per hour per network address.`
                  : 'Checking upload limits…'}
              </p>
              {limitError && (
                <p role="alert">Cannot reach the analysis service. Reload the page to retry.</p>
              )}
              <button
                className="button primary wide"
                disabled={busy || !file || !limits}
                type="submit"
              >
                {busy ? 'Analyzing your CSV…' : 'Upload and analyze'}
              </button>
              {busy && (
                <p role="status">
                  Processing your data. This can take a few minutes; keep this page open.
                </p>
              )}
            </form>
            <button
              className="button ghost"
              type="button"
              onClick={() => download(sample, 'path-synthetic-example.csv', 'text/csv')}
            >
              Download example CSV
            </button>
            <details>
              <summary>Required CSV columns</summary>
              <code className="public-columns">{columns}</code>
              <p>
                Use ISO dates (2026-01-22) and amounts in rupees. The example contains synthetic
                data.
              </p>
            </details>
            <p className="public-privacy">
              Ranked results are stored for 24 hours and accessible only from this browser. Raw CSV
              files are not saved. Accounts are optional; permanent history is not available yet.
            </p>
          </section>
          <section
            className="public-card public-results"
            aria-labelledby="results-title"
            aria-busy={loading}
          >
            <p className="eyebrow">YOUR ANALYSIS</p>
            <h2 id="results-title">Results</h2>
            {error && (
              <p className="inline-error" role="alert">
                {error}
              </p>
            )}
            {loading && <p role="status">Loading your results…</p>}
            {!result && !loading && (
              <div className="public-empty">
                <span aria-hidden="true">◎</span>
                <h3>Your next insight starts with a CSV.</h3>
                <p>Upload your data or download the example to try the complete flow.</p>
              </div>
            )}
            {result && (
              <>
                <div className="public-stats">
                  <div>
                    <strong>{result.rows_accepted.toLocaleString()}</strong>
                    <span>Valid rows analyzed</span>
                  </div>
                  <div>
                    <strong>{result.rows_rejected}</strong>
                    <span>Rows excluded</span>
                  </div>
                  <div>
                    <strong>{result.alerts.length}</strong>
                    <span>Ranked candidates</span>
                  </div>
                </div>
                <p>
                  Highest-scoring candidates, in rank order. Risk labels are relative to your
                  uploaded data.
                </p>
                <button
                  className="button secondary"
                  type="button"
                  onClick={() =>
                    download(
                      JSON.stringify(result, null, 2),
                      'path-analysis.json',
                      'application/json',
                    )
                  }
                >
                  Download results (JSON)
                </button>
                <div className="public-table">
                  <table>
                    <caption>Ranked transaction candidates</caption>
                    <thead>
                      <tr>
                        <th>Rank</th>
                        <th>Transaction</th>
                        <th>Agency</th>
                        <th>Amount</th>
                        <th>Score</th>
                        <th>Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.alerts.map((alert) => (
                        <tr key={alert.transaction_id}>
                          <td>{alert.rank}</td>
                          <td>{alert.transaction_id}</td>
                          <td>{alert.agency}</td>
                          <td>
                            {new Intl.NumberFormat('en-IN', {
                              style: 'currency',
                              currency: 'INR',
                              maximumFractionDigits: 0,
                            }).format(alert.amount_paise / 100)}
                          </td>
                          <td>{alert.score.toFixed(3)}</td>
                          <td>{alert.risk}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {result.issues.length > 0 && (
                  <details>
                    <summary>View excluded-row issues</summary>
                    <ul>
                      {result.issues.map((issue) => (
                        <li key={issue.row}>
                          Row {issue.row}: {issue.reason}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
                <p className="muted">
                  Expires {new Date(result.expires_at).toLocaleString()}. Download a copy before
                  expiry. Clearing browser cookies removes access.
                </p>
              </>
            )}
          </section>
        </div>
      </main>
      <footer className="public-footer">
        P.A.T.H. · Evidence for review, never an automatic accusation.
      </footer>
    </div>
  );
}
