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
      <header className="page-heading">
        <div>
          <p className="eyebrow">Model orchestration</p>
          <h1>ML Anomaly Control Center</h1>
          <p>
            One run executes at a time. Results activate only after the new run is written
            successfully.
          </p>
        </div>
      </header>
      <section className="panel">
        <form className="control-grid" onSubmit={run}>
          <label>
            Model
            <select value={model} onChange={(event) => setModel(event.target.value)}>
              {MODEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Alert budget (Top-K)
            <input
              type="number"
              min="1"
              max="5000"
              value={topK}
              onChange={(event) => setTopK(event.target.value)}
            />
          </label>
          <label>
            Trees
            <input
              type="number"
              min="50"
              max="1000"
              value={trees}
              onChange={(event) => setTrees(event.target.value)}
            />
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
        {job ? (
          <div className="job-progress" aria-live="polite">
            <div>
              <strong>{job.status}</strong>
              <span>{job.message}</span>
            </div>
            <progress value={job.progress} max="100">
              {job.progress}%
            </progress>
            <span>{job.progress}%</span>
          </div>
        ) : null}
      </section>
    </>
  );
}
