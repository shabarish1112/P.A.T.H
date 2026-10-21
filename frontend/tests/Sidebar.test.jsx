import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Sidebar } from '../src/components/Sidebar';

vi.mock('../src/contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } }),
}));

afterEach(cleanup);

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

describe('automatic sidebar', () => {
  it('expands on pointer entry and collapses when the pointer leaves', () => {
    const { sidebar } = mount();
    expect(sidebar).toHaveClass('collapsed');
    expect(screen.getByRole('link', { name: 'Datasets' })).toBeInTheDocument();
    fireEvent.pointerEnter(sidebar, { pointerType: 'mouse' });
    expect(sidebar).not.toHaveClass('collapsed');
    fireEvent.pointerLeave(sidebar);
    expect(sidebar).toHaveClass('collapsed');
  });

  it('keeps navigation expanded while keyboard focus stays inside', () => {
    const { sidebar } = mount();
    const link = screen.getByRole('link', { name: 'Overview' });
    const nextLink = screen.getByRole('link', { name: 'Datasets' });
    fireEvent.focus(link);
    fireEvent.pointerLeave(sidebar);
    expect(sidebar).not.toHaveClass('collapsed');
    fireEvent.blur(link, { relatedTarget: nextLink });
    expect(sidebar).not.toHaveClass('collapsed');
    fireEvent.blur(nextLink, { relatedTarget: screen.getByText('Page action') });
    expect(sidebar).toHaveClass('collapsed');
  });

  it('collapses after clicking a navigation link and moving the pointer away', () => {
    const { sidebar } = mount();
    const link = screen.getByRole('link', { name: 'Datasets' });
    fireEvent.pointerEnter(sidebar, { pointerType: 'mouse' });
    fireEvent.pointerDown(link, { pointerType: 'mouse' });
    fireEvent.focus(link);
    fireEvent.click(link);
    fireEvent.pointerLeave(sidebar);
    expect(sidebar).toHaveClass('collapsed');
    fireEvent.keyDown(link, { key: 'Tab' });
    expect(sidebar).not.toHaveClass('collapsed');
  });

  it('shows full labels in the mobile drawer and closes it after navigation', () => {
    const { sidebar, onMobileClose } = mount(true);
    expect(sidebar).not.toHaveClass('collapsed');
    expect(screen.getByText('Datasets')).toBeVisible();
    fireEvent.click(screen.getByRole('link', { name: 'Datasets' }));
    expect(onMobileClose).toHaveBeenCalledOnce();
  });
});
