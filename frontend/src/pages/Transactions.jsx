import { PageHeader } from '../components/PageHeader';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AsyncState } from '../components/AsyncState';
import { DataTable } from '../components/DataTable';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { useTransactions } from '../hooks/data';
import { formatMoney } from '../lib';

export default function Transactions() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [cursor, setCursor] = useState('');
  const query = useDebouncedValue(search, 300);
  const state = useTransactions({ query, cursor, limit: 50 });
  const columns = [
    { key: 'transaction_id', label: 'Transaction' },
    { key: 'date', label: 'Date', render: (row) => new Date(row.date).toLocaleDateString() },
    { key: 'agency', label: 'Agency' },
    { key: 'scheme', label: 'Scheme' },
    { key: 'vendor', label: 'Vendor' },
    {
      key: 'amount',
      align: 'right',
      label: 'Amount',
      render: (row) => formatMoney(row.amount_paise),
    },
  ];
  return (
    <>
      <PageHeader
        title="Master Transactions"
        description="Authorized disbursal records from the active dataset."
        eyebrow="System of record view"
      />
      <section className="panel">
        <div className="toolbar">
          <label className="search-field">
            Search
            <input
              value={search}
              maxLength={64}
              placeholder="Transaction ID prefix"
              onChange={(event) => {
                setSearch(event.target.value);
                setCursor('');
              }}
            />
          </label>
          <span className="muted">Estimated rows: {state.data?.estimated_total ?? '—'}</span>
        </div>
        <AsyncState
          loading={state.loading}
          error={state.error}
          empty={!state.data?.items?.length}
          emptyMessage={
            query ? 'No transactions match this search.' : 'No active dataset is available.'
          }
          onRetry={state.retry}
        >
          <DataTable
            label="Transactions"
            columns={columns}
            rows={state.data?.items || []}
            rowKey={(row) => row.id}
            onRowClick={(row) =>
              navigate(`/investigation/${encodeURIComponent(row.transaction_id)}`)
            }
          />
        </AsyncState>
        <div className="pagination-actions">
          <button
            className="button subtle"
            type="button"
            disabled={!state.data?.next_cursor}
            onClick={() => setCursor(state.data.next_cursor)}
          >
            Next page
          </button>
        </div>
      </section>
    </>
  );
}
