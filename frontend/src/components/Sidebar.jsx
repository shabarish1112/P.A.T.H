import { memo, useRef, useState } from 'react';
import { NavLink } from 'react-router-dom';

import { useAuth } from '../contexts/AuthContext';

const nav = [
  { to: '/', label: 'Overview', icon: '◫' },
  { to: '/datasets', label: 'Datasets', icon: '▤', admin: true },
  { to: '/transactions', label: 'Transactions', icon: '≡' },
  { to: '/control', label: 'ML Control', icon: '⌁' },
  { to: '/anomalies', label: 'Anomaly Explorer', icon: '◇' },
  { to: '/investigation', label: 'Investigation', icon: '◎' },
  { to: '/analytics', label: 'Visual Analytics', icon: '⌇' },
  { to: '/queue', label: 'Review Queue', icon: '✓' },
  { to: '/admin', label: 'Access & Audit', icon: '⚙', admin: true },
];

export const Sidebar = memo(function Sidebar({ mobileOpen, onMobileClose }) {
  const { user } = useAuth();
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const pointerFocus = useRef(false);
  const collapsed = !mobileOpen && !hovered && !focused;
  const visible = nav.filter((item) => !item.admin || user?.role === 'admin');
  return (
    <aside
      className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}
      aria-label="Primary navigation"
      onPointerEnter={(event) => {
        if (event.pointerType !== 'touch') setHovered(true);
      }}
      onPointerLeave={() => setHovered(false)}
      onPointerDownCapture={() => {
        pointerFocus.current = true;
        setFocused(false);
      }}
      onKeyDownCapture={() => {
        pointerFocus.current = false;
        setFocused(true);
      }}
      onFocusCapture={() => setFocused(!pointerFocus.current)}
      onBlurCapture={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          pointerFocus.current = false;
          setFocused(false);
        }
      }}
    >
      <div className="brand-row">
        <div className="brand-mark" aria-hidden="true" />
        {!collapsed ? <span>P.A.T.H.</span> : null}
      </div>
      <nav>
        <p className="nav-label">Workspace</p>
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
              {item.icon}
            </span>
            {!collapsed ? <span>{item.label}</span> : null}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-footer">
        {!collapsed ? (
          <>
            <span className="principle-dot" aria-hidden="true" />
            <span>Unusual ≠ Fraudulent</span>
          </>
        ) : (
          <span className="principle-dot" aria-label="Unusual is not fraudulent" />
        )}
      </div>
    </aside>
  );
});
