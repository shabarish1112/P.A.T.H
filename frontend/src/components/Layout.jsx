import { useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { NAV_ITEMS } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { Icon } from './Icon';
import { Sidebar } from './Sidebar';
import { ProjectContext } from './ProjectContext';

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const menuButton = useRef(null);

  useEffect(() => {
    if (!mobileOpen) return undefined;
    const trigger = menuButton.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const sidebar = document.querySelector('.sidebar');
    const controls = () =>
      Array.from(sidebar.querySelectorAll('a,button')).filter((element) => !element.disabled);
    controls()[0]?.focus();
    function handleKey(event) {
      if (event.key === 'Escape') {
        setMobileOpen(false);
      }
      if (event.key === 'Tab') {
        const items = controls();
        const first = items[0];
        const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = previousOverflow;
      trigger?.focus();
    };
  }, [mobileOpen]);

  return (
    <div className="app-shell">
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
      <div className="app-content" inert={mobileOpen}>
        <header className="topbar top-shell">
          <button
            className="icon-button mobile-only"
            ref={menuButton}
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
            aria-expanded={mobileOpen}
            title="Open navigation"
          >
            ☰
          </button>
          <button type="button" className="top-card logo-card" onClick={() => navigate('/')}>
            <span className="path-mark">P</span>
            <span className="logo-copy">
              <b>P.A.T.H.</b>
              <small>Public Anomaly Tracking Hub</small>
            </span>
          </button>
          <nav className="page-navigation top-card" aria-label="Page navigation">
            {NAV_ITEMS.filter((item) => !item.admin || user?.role === 'admin').map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `page-link ${isActive ? 'active' : ''}`}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="user-menu top-card profile-card">
            <span className="profile-icon">
              <Icon name="user" size={15} />
            </span>
            <div className="profile-copy">
              <strong>{user?.email}</strong>
              <span>{user?.role}</span>
            </div>
            <button type="button" className="button ghost" onClick={logout}>
              Logout
            </button>
          </div>
        </header>
        <main className="page">
          <ProjectContext />
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
