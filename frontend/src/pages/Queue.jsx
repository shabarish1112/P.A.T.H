import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { ReviewBadge } from '../components/Badge';
import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { useReviews } from '../hooks/data';

export default function Queue() {
  const state = useReviews(250);
  const columns = [
    {
      key: 'transaction_id',
      label: 'Transaction',
      render: (row) => (
        <Link
          className="record-link"
          to={`/investigation/${encodeURIComponent(row.transaction_id)}`}
        >
          {row.transaction_id}
        </Link>
      ),
    },
    { key: 'status', label: 'Status', render: (row) => <ReviewBadge status={row.status} /> },
    { key: 'actor_email', label: 'Reviewer' },
    {
      key: 'created_at',
      label: 'Recorded',
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    { key: 'note', label: 'Note' },
  ];
  return (
    <>
      <PageHeader
        title="Review history"
        description="The latest 250 recorded decisions for the active model run. Each decision is retained as an event."
        eyebrow="Human validation"
        actions={
          <button
            type="button"
            className="button subtle"
            onClick={state.retry}
            disabled={state.loading}
          >
            Refresh history
          </button>
        }
      />
      <section className="panel">
        <p className="history-context">
          Pending Review means more checking is needed. False Alert records a reviewer’s clearance
          of the screening signal. Confirmed Finding and Escalated are human review outcomes, not
          automatic fraud determinations.
        </p>
        <AsyncState
          loading={state.loading}
          error={state.error}
          empty={!state.data?.items?.length}
          emptyMessage={
            <div className="review-empty">
              <h2>No review decisions have been recorded.</h2>
              <p>
                Model alerts are not human review decisions. Open a transaction in Investigation; a
                reviewer or administrator can record a status and note.
              </p>
              <ol>
                <li>Choose a transaction from the dashboard or Anomaly Explorer.</li>
                <li>Check its context and supporting records.</li>
                <li>
                  Record Pending Review, Confirmed Finding, False Alert, or Escalated, with a note.
                </li>
              </ol>
              <p>
                The transaction ID, reviewer, status, note, and time will appear in this table. This
                view follows the active run; it is not an assigned-task queue.
              </p>
              <Link className="button subtle" to="/anomalies">
                Find a transaction to review
              </Link>
            </div>
          }
          onRetry={state.retry}
        >
          <DataTable
            label="Recorded review decisions"
            columns={columns}
            rows={state.data?.items || []}
            rowKey={(row) => row.id}
          />
        </AsyncState>
      </section>
    </>
  );
}
