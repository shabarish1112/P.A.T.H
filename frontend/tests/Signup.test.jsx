import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import Login from '../src/pages/Login';

const { register } = vi.hoisted(() => ({ register: vi.fn() }));
vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({ authenticated: false, loading: false, register }),
}));
afterEach(cleanup);
beforeEach(() => {
  register.mockReset();
});

function mount() {
  render(
    <MemoryRouter>
      <Login signup />
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'member@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'VeryStrongPassword!123' },
  });
}

describe('optional account creation', () => {
  it('rejects mismatched passwords without a request', () => {
    mount();
    fireEvent.change(screen.getByLabelText('Confirm password'), {
      target: { value: 'DifferentPassword!123' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Create account' }).closest('form'));
    expect(screen.getByRole('alert')).toHaveTextContent('Passwords must match');
    expect(register).not.toHaveBeenCalled();
    expect(screen.getByRole('link', { name: 'Continue without an account' })).toHaveAttribute(
      'href',
      '/',
    );
  });

  it('submits only email and password and shows account errors', async () => {
    register.mockRejectedValue(new Error('Unable to create account. Try signing in instead.'));
    mount();
    fireEvent.change(screen.getByLabelText('Confirm password'), {
      target: { value: 'VeryStrongPassword!123' },
    });
    fireEvent.submit(screen.getByRole('button', { name: 'Create account' }).closest('form'));
    await waitFor(() =>
      expect(register).toHaveBeenCalledWith('member@example.com', 'VeryStrongPassword!123'),
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('Try signing in instead');
  });
});
