import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Sidebar } from '../src/components/Sidebar';

vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } }),
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});

function mount(mobileOpen = false) {
  const onMobileClose = vi.fn();
  render(
    <MemoryRouter>
      <Sidebar mobileOpen={mobileOpen} onMobileClose={onMobileClose} />
      <button>Page action</button>
    </MemoryRouter>,
  );
  return { sidebar: screen.getByLabelText('Primary navigation'), onMobileClose };
}

describe('fixed navigation rail', () => {
  it('switches the document theme and persists the preference', () => {
    const { sidebar } = mount();
    const toggle = screen.getByRole('switch', { name: 'Dark mode' });
    expect(sidebar).not.toContainElement(toggle);
    expect(toggle).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(toggle);
    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(localStorage.getItem('path-theme')).toBe('dark');
    expect(toggle).toHaveAttribute('aria-checked', 'true');
  });

  it('keeps a fixed icon rail on pointer and keyboard activity', () => {
    const { sidebar } = mount();
    expect(sidebar).toHaveClass('collapsed');
    expect(screen.queryByText('Workspace')).not.toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Datasets' });
    expect(link).toHaveAttribute('title', 'Datasets');
    fireEvent.pointerEnter(sidebar, { pointerType: 'mouse' });
    fireEvent.focus(link);
    fireEvent.keyDown(link, { key: 'Tab' });
    expect(sidebar).toHaveClass('collapsed');
    fireEvent.pointerLeave(sidebar);
    expect(sidebar).toHaveClass('collapsed');
  });

  it('shows full labels in the mobile drawer and closes it after navigation', () => {
    const { sidebar, onMobileClose } = mount(true);
    expect(sidebar).not.toHaveClass('collapsed');
    expect(screen.getByText('Datasets')).toBeVisible();
    fireEvent.click(screen.getByRole('link', { name: 'Datasets' }));
    expect(onMobileClose).toHaveBeenCalledOnce();
  });
});
