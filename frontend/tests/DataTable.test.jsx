import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DataTable } from '../src/components/DataTable';

describe('DataTable', () => {
  it('renders explicit empty state', () => {
    render(<DataTable columns={[]} rows={[]} rowKey={() => ''} />);
    expect(screen.getByText('No records found.')).toBeInTheDocument();
  });
});
