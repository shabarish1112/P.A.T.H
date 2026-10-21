import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import Login from '../src/pages/Login';

vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({ authenticated: false, loading: false, login: vi.fn().mockRejectedValue(new Error('Invalid email or password')) }),
}));

describe('Login', () => {
  it('does not prefill credentials and shows login failures', async () => {
    render(<MemoryRouter><Login /></MemoryRouter>);
    const email = screen.getByLabelText('Email');
    const password = screen.getByLabelText('Password');
    expect(email).toHaveValue('');
    expect(password).toHaveValue('');
    fireEvent.change(email, { target: { value: 'x@example.com' } });
    fireEvent.change(password, { target: { value: 'badpassword' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password');
  });
});
