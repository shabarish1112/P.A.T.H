import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

export const handlers = [
  http.post('/api/auth/refresh', () => HttpResponse.json({
    access_token: 'access-refreshed',
    token_type: 'bearer',
    expires_at: new Date(Date.now() + 60000).toISOString(),
    user: { id: '1', email: 'analyst@example.com', role: 'analyst', is_active: true },
  })),
  http.get('/api/auth/me', () => HttpResponse.json({ user: { id: '1', email: 'analyst@example.com', role: 'analyst', is_active: true } })),
];

export const server = setupServer(...handlers);
