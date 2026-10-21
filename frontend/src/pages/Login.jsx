import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const { authenticated, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!loading && authenticated) return <Navigate to="/" replace />;

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await login(email, password);
      navigate(location.state?.from || '/', { replace: true });
    } catch (requestError) {
      setError(requestError.message || 'Sign in failed.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-story" aria-label="P.A.T.H. product principle">
        <div className="login-brand"><span className="brand-mark" /> P.A.T.H.</div>
        <div>
          <p className="eyebrow">Public anomaly surveillance</p>
          <h1>Screen unusual fund activity without turning a score into an accusation.</h1>
          <p className="lead">P.A.T.H. prioritizes statistically unusual disbursals for authorized human review above the system of record.</p>
        </div>
        <div className="principle-card"><span className="principle-dot" /> Unusual ≠ Fraudulent</div>
      </section>
      <section className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <p className="eyebrow">Secure workspace</p>
          <h2>Sign in</h2>
          <p className="muted">Use an account provisioned by a P.A.T.H. administrator.</p>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} />
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} />
          {error ? <div className="inline-error" role="alert" aria-live="assertive">{error}</div> : null}
          <button type="submit" className="button primary wide" disabled={submitting}>{submitting ? 'Signing in…' : 'Sign in'}</button>
        </form>
      </section>
    </main>
  );
}
