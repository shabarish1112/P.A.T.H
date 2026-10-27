import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';

export default function Login({ signup = false }) {
  const { user, authenticated, loading, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [confirmation, setConfirmation] = useState('');

  if (!loading && authenticated)
    return (
      <Navigate
        to={
          user?.must_change_password
            ? '/change-password'
            : ['admin', 'analyst', 'reviewer'].includes(user?.role)
              ? '/workspace'
              : '/'
        }
        replace
      />
    );

  async function submit(event) {
    event.preventDefault();
    if (signup && password !== confirmation) {
      setError('Passwords must match.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const account = signup ? await register(email, password) : await login(email, password);
      const target = location.state?.from;
      navigate(
        typeof target === 'string' && target.startsWith('/') && !target.startsWith('//')
          ? target
          : ['admin', 'analyst', 'reviewer'].includes(account?.role)
            ? '/workspace'
            : '/',
        { replace: true },
      );
    } catch (requestError) {
      setError(requestError.message || 'Sign in failed.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-story" aria-label="P.A.T.H. product principle">
        <div className="login-brand">
          <span className="brand-mark" /> P.A.T.H.
        </div>
        <div>
          <p className="eyebrow">Public anomaly surveillance</p>
          <h1>Screen unusual fund activity without turning a score into an accusation.</h1>
          <p className="lead">
            P.A.T.H. prioritizes statistically unusual disbursals for authorized human review above
            the system of record.
          </p>
        </div>
        <div className="principle-card">
          <span className="principle-dot" /> Unusual ≠ Fraudulent
        </div>
      </section>
      <section className="login-panel">
        <div className="login-brand-heading">
          <span className="path-mark large">P</span>
          <span>P.A.T.H.</span>
        </div>
        <form className="login-form" onSubmit={submit}>
          <p className="eyebrow">Secure workspace</p>
          <h2>{signup ? 'Create account' : 'Sign in'}</h2>
          <p className="muted">An account is optional. You can analyze a CSV without signing in.</p>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete={signup ? 'new-password' : 'current-password'}
            required
            minLength={signup ? 12 : 8}
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {signup && (
            <>
              <label htmlFor="confirmation">Confirm password</label>
              <input
                id="confirmation"
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={128}
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
              />
              <p className="muted">Use 12–128 characters. Your email is not verified yet.</p>
            </>
          )}
          {error ? (
            <div className="inline-error" role="alert" aria-live="assertive">
              {error}
            </div>
          ) : null}
          <button type="submit" className="button primary wide" disabled={submitting}>
            {submitting ? 'Please wait…' : signup ? 'Create account' : 'Sign in'}
          </button>
          <Link to={signup ? '/login' : '/signup'}>
            {signup ? 'Already have an account? Sign in' : 'Create an account'}
          </Link>
          <Link to="/">Continue without an account</Link>
        </form>
      </section>
    </main>
  );
}
