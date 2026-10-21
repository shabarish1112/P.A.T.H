import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it } from 'vitest';

import { api, apiRequest, clearAccessToken, setAccessToken } from '../src/services/api';
import { server } from './testServer';

beforeEach(() => {
  clearAccessToken();
});

describe('API client', () => {
  it('retries a failed GET once', async () => {
    let calls = 0;
    server.use(
      http.get('/api/example', () => {
        calls += 1;
        if (calls === 1) return HttpResponse.error();
        return HttpResponse.json({ ok: true });
      }),
    );
    await expect(api.get('/api/example')).resolves.toEqual({ ok: true });
    expect(calls).toBe(2);
  });

  it('never retries POST', async () => {
    let calls = 0;
    server.use(
      http.post('/api/example', () => {
        calls += 1;
        return HttpResponse.error();
      }),
    );
    await expect(api.post('/api/example', { x: 1 })).rejects.toThrow();
    expect(calls).toBe(1);
  });

  it('refreshes once after a 401 and replays only the original GET', async () => {
    setAccessToken('expired');
    let calls = 0;
    server.use(
      http.get('/api/secure', ({ request }) => {
        calls += 1;
        if (request.headers.get('authorization') === 'Bearer access-refreshed') {
          return HttpResponse.json({ ok: true });
        }
        return new HttpResponse(null, { status: 401 });
      }),
    );
    await expect(api.get('/api/secure')).resolves.toEqual({ ok: true });
    expect(calls).toBe(2);
  });

  it('does not duplicate an aborted request', async () => {
    const controller = new AbortController();
    controller.abort();
    await expect(
      apiRequest('/api/example', { method: 'GET', signal: controller.signal }),
    ).rejects.toBeTruthy();
  });
});
