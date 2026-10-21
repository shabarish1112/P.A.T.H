import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import Datasets from '../src/pages/Datasets';

vi.mock('../src/contexts/AuthContext', () => ({ useAuth: () => ({ user: { role: 'admin' } }) }));
vi.mock('../src/contexts/ToastContext', () => ({ useToast: () => ({ push: vi.fn() }) }));
vi.mock('../src/hooks/data', () => ({
  useDatasets: () => ({ data: { items: [] }, loading: false, error: null, retry: vi.fn() }),
}));
vi.mock('../src/services/api', () => ({
  apiRequest: vi.fn().mockResolvedValue({
    rows_accepted: 1,
    rows_received: 2,
    issues: [{ row: 3, reason: 'bad date' }],
  }),
}));

describe('Datasets', () => {
  it('renders validation issues returned by upload', async () => {
    const user = userEvent.setup();
    render(<Datasets />);
    const file = new File(['x'], 'data.csv', { type: 'text/csv' });
    await user.upload(screen.getByLabelText('CSV file'), file);
    fireEvent.submit(screen.getByRole('button', { name: 'Upload and validate' }).closest('form'));
    expect(await screen.findByText(/Row 3: bad date/)).toBeInTheDocument();
  });
});
