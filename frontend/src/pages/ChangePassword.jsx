import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { PageHeader } from '../components/PageHeader';

export default function ChangePassword() {
  const { clearSession } = useAuth();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    if (data.get('new_password') !== data.get('confirm_password')) {
      setError('New passwords must match.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await api.post('/api/auth/change-password', {
        current_password: data.get('current_password'),
        new_password: data.get('new_password'),
      });
      clearSession();
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeader
        title="Change password"
        description="Use at least 12 characters. You will sign in again after changing your password."
      />
      <section className="panel password-panel">
        <form className="review-form" onSubmit={submit}>
          <label>
            Current password
            <input
              name="current_password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <label>
            New password
            <input
              name="new_password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              required
            />
          </label>
          <label>
            Confirm new password
            <input
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              required
            />
          </label>
          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}
          <button className="button primary" disabled={busy}>
            {busy ? 'Changing…' : 'Change password'}
          </button>
        </form>
      </section>
    </>
  );
}
