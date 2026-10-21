import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';
import { Sidebar } from './Sidebar';

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState('');

  function submitSearch(event) {
    event.preventDefault();
    const value = search.trim();
    if (!value) return;
    navigate(`/investigation/${encodeURIComponent(value)}`);
  }

  return (
    <div className="app-shell">
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
      <div className="app-content">
        <header className="topbar">
          <button
            className="icon-button mobile-only"
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            ☰
          </button>
          <div className="breadcrumb">Public Anomaly Tracking Hub</div>
          <form className="global-search" onSubmit={submitSearch} role="search">
            <label className="sr-only" htmlFor="global-search">
              Search transaction ID
            </label>
            <input
              id="global-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search transaction"
              maxLength={64}
            />
          </form>
          <div className="user-menu">
            <div>
              <strong>{user?.email}</strong>
              <span>{user?.role}</span>
            </div>
            <button type="button" className="button subtle" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
      {mobileOpen ? (
        <button
          className="mobile-backdrop"
          type="button"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}
    </div>
  );
}
