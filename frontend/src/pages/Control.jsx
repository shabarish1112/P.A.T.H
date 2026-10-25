import { PageHeader } from '../components/PageHeader';
import { useEffect, useState } from 'react';

import { MODEL_OPTIONS } from '../constants';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/api';

export default function Control() {
  const { push } = useToast();
  const [model, setModel] = useState('if');
  const [topK, setTopK] = useState(50);
  const [trees, setTrees] = useState(200);
  const [includeUmap, setIncludeUmap] = useState(false);
  const [job, setJob] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!job?.job_id || ['completed', 'failed'].includes(job.status)) return undefined;
    const controller = new AbortController();
    const timer = window.setInterval(async () => {
      try {
        const next = await api.get(`/api/models/jobs/${encodeURIComponent(job.job_id)}`, {
          signal: controller.signal,
        });
        setJob(next);
        if (next.status === 'completed') {
          setRunning(false);
          push('Model run completed.', 'success');
        }
        if (next.status === 'failed') {
          setRunning(false);
          push(next.message || 'Model run failed.', 'error');
        }
      } catch (error) {
        if (error?.name !== 'AbortError') push(error.message, 'error');
      }
    }, 1200);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [job?.job_id, job?.status, push]);

  async function run(event) {
    event.preventDefault();
    setRunning(true);
    try {
      const next = await api.post(
        '/api/models/run',
        {
          model,
          top_k: Number(topK),
          n_estimators: Number(trees),
          random_state: 42,
          include_umap: includeUmap,
        },
        { timeoutMs: 120000 },
      );
      setJob(next);
    } catch (error) {
      setRunning(false);
      push(error.message, 'error');
    }
  }

  return (
    <>
      <PageHeader
        title="ML Anomaly Control Center"
        description="One run executes at a time. Results activate only after the new run is written successfully."
        eyebrow="Model orchestration"
      />
      <div className="dashboard-grid">
        <section className="panel">
          <h2>Run configuration</h2>
          <p className="panel-description">Choose the screening model and alert budget.</p>
          <form className="control-grid" onSubmit={run}>
            <label>
              Model
              <select
                aria-label="Model"
                aria-describedby="model-help"
                value={model}
                onChange={(event) => setModel(event.target.value)}
              >
                {MODEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <span id="model-help" className="field-help">
                Algorithm used to rank unusual transactions.
              </span>
            </label>
            <label>
              Alert budget (Top-K)
              <input
                type="number"
                min="1"
                max="5000"
                aria-label="Alert budget (Top-K)"
                aria-describedby="budget-help"
                value={topK}
                onChange={(event) => setTopK(event.target.value)}
              />
              <span id="budget-help" className="field-help">
                Maximum number of alerts returned for review.
              </span>
            </label>
            <label>
              Trees
              <input
                type="number"
                min="50"
                max="1000"
                aria-label="Trees"
                aria-describedby="trees-help"
                value={trees}
                onChange={(event) => setTrees(event.target.value)}
              />
              <span id="trees-help" className="field-help">
                Model complexity: 50–1,000 trees.
              </span>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={includeUmap}
                onChange={(event) => setIncludeUmap(event.target.checked)}
              />{' '}
              Generate optional UMAP sample
            </label>
            <button type="submit" className="button primary" disabled={running}>
              {running ? 'Run in progress…' : 'Run model'}
            </button>
          </form>
        </section>
        <section className="panel">
          <h2>Run status</h2>
          {job ? (
            <div className="job-progress" aria-live="polite">
              <div>
                <strong>{job.status}</strong>
                <span>{job.message}</span>
              </div>
              <progress aria-label="Model run progress" value={job.progress} max="100">
                {job.progress}%
              </progress>
              <span>{job.progress}%</span>
            </div>
          ) : (
            <div className="async-state">No run has been started in this session.</div>
          )}
        </section>
      </div>
    </>
  );
}
