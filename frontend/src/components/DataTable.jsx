import { memo } from 'react';

export const DataTable = memo(function DataTable({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyMessage = 'No records found.',
  label = 'Records',
}) {
  if (!rows?.length) return <div className="table-empty">{emptyMessage}</div>;
  /* eslint-disable jsx-a11y/no-noninteractive-tabindex -- Keyboard users need access to the named horizontally scrollable table region. */
  return (
    <div
      className="table-scroll"
      tabIndex="0"
      role="region"
      aria-label={`${label}; scroll horizontally for more columns`}
    >
      <table className="data-table">
        <caption className="sr-only">{label}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={column.align === 'right' ? 'numeric-cell' : undefined}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              tabIndex={onRowClick ? 0 : undefined}
              className={onRowClick ? 'clickable-row' : undefined}
              onClick={() => onRowClick?.(row)}
              onKeyDown={(event) => {
                if (onRowClick && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault();
                  onRowClick(row);
                }
              }}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={
                    [
                      column.align === 'right' ? 'numeric-cell' : '',
                      column.key === 'transaction_id' || column.key === 'resource_id'
                        ? 'identifier'
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' ') || undefined
                  }
                >
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
  /* eslint-enable jsx-a11y/no-noninteractive-tabindex */
});
