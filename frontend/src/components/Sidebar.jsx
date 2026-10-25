import { memo, useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';

import { NAV_ITEMS } from '../constants';
import { Icon } from './Icon';
import { useAuth } from '../contexts/AuthContext';

export const Sidebar = memo(function Sidebar({ mobileOpen, onMobileClose }) {
  const { user } = useAuth();
  const collapsed = !mobileOpen;
  const visible = NAV_ITEMS.filter((item) => !item.admin || user?.role === 'admin');
  return (
    <>
      {!mobileOpen ? <ThemeSwitch /> : null}
      <aside
        className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}
        aria-label="Primary navigation"
        role={mobileOpen ? 'dialog' : undefined}
        aria-modal={mobileOpen ? true : undefined}
      >
        {mobileOpen ? (
          <div className="brand-row">
            <button
              type="button"
              className="icon-button sidebar-close"
              aria-label="Close sidebar"
              title="Close sidebar"
              onClick={onMobileClose}
            >
              ×
            </button>
          </div>
        ) : null}
        <nav>
          {visible.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              aria-label={item.label}
              title={collapsed ? item.label : undefined}
              onClick={onMobileClose}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon" aria-hidden="true">
                <Icon name={item.icon} />
              </span>
              {!collapsed ? <span>{item.label}</span> : null}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
});

function ThemeSwitch() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('path-theme') === 'dark' ? 'dark' : 'light';
    } catch {
      return 'light';
    }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem('path-theme', theme);
    } catch {
      /* Storage may be unavailable. */
    }
  }, [theme]);
  return (
    <div className="theme-card theme-floating">
      <button
        type="button"
        role="switch"
        aria-label="Dark mode"
        title="Toggle dark mode"
        aria-checked={theme === 'dark'}
        onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      >
        <Icon name="sun" size={14} />
        <span className={`switch-track ${theme === 'dark' ? 'on' : ''}`}>
          <i />
        </span>
        <Icon name="moon" size={14} />
      </button>
    </div>
  );
}
