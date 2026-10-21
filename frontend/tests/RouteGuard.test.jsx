import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import App from '../src/App';

vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({ authenticated: false, loading: false, user: null, login: vi.fn(), logout: vi.fn() }),
}));

describe('Route guard', () => {
  it('redirects unauthenticated users to validated login flow', () => {
    render(<MemoryRouter initialEntries={['/transactions']}><App /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
  });
});
