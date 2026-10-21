import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { useReviews } from '../hooks/data';

export default function Queue() {
  const state = useReviews(250);
  const columns = [
    { key: 'transaction_id', label: 'Transaction' },
    { key: 'status', label: 'Status' },
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
      <header className="page-heading">
        <div>
          <p className="eyebrow">Human validation</p>
          <h1>Investigation Queue</h1>
          <p>
            Review decisions are append-only events; sensitive changes require separation of duties.
          </p>
        </div>
      </header>
      <section className="panel">
        <AsyncState
          loading={state.loading}
          error={state.error}
          empty={!state.data?.items?.length}
          onRetry={state.retry}
        >
          <DataTable columns={columns} rows={state.data?.items || []} rowKey={(row) => row.id} />
        </AsyncState>
      </section>
    </>
  );
}
