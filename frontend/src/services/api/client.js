import { clearAccessToken, getAccessToken, setAccessToken } from './tokenStore';

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const DEFAULT_GET_TIMEOUT = 8000;
const DEFAULT_MUTATION_TIMEOUT = 30000;
let refreshPromise = null;
let authFailureHandler = null;

export class ApiError extends Error {
  constructor(message, status = 0, code = 'NETWORK_ERROR', requestId = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

export function setAuthFailureHandler(handler) {
  authFailureHandler = handler;
}

function createLinkedController(externalSignal, timeoutMs) {
  const controller = new AbortController();
  const onAbort = () => controller.abort(externalSignal?.reason);
  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort(externalSignal.reason);
    } else {
      externalSignal.addEventListener('abort', onAbort, { once: true });
    }
  }
  const timer = setTimeout(
    () => controller.abort(new DOMException('Request timed out', 'TimeoutError')),
    timeoutMs,
  );
  return {
    signal: controller.signal,
    cleanup() {
      clearTimeout(timer);
      externalSignal?.removeEventListener('abort', onAbort);
    },
  };
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return response.json();
  return response.text();
}

async function performFetch(path, options, token, timeoutMs) {
  const linked = createLinkedController(options.signal, timeoutMs);
  const headers = new Headers(options.headers || {});
  if (
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams) &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) headers.set('Authorization', `Bearer ${token}`);
  try {
    return await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      signal: linked.signal,
      credentials: 'include',
    });
  } finally {
    linked.cleanup();
  }
}

export async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = performFetch('/api/auth/refresh', { method: 'POST' }, null, 8000)
      .then(async (response) => {
        if (!response.ok) throw new ApiError('Session expired', response.status, 'SESSION_EXPIRED');
        const data = await parseResponse(response);
        setAccessToken(data.access_token);
        return data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export async function apiRequest(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const isGet = method === 'GET';
  const timeoutMs = options.timeoutMs ?? (isGet ? DEFAULT_GET_TIMEOUT : DEFAULT_MUTATION_TIMEOUT);
  const retryCount = isGet ? 1 : 0;
  let attempt = 0;
  let hasRefreshed = false;

  while (true) {
    try {
      const response = await performFetch(path, options, getAccessToken(), timeoutMs);
      if (
        response.status === 401 &&
        !hasRefreshed &&
        path !== '/api/auth/refresh' &&
        path !== '/api/auth/login'
      ) {
        hasRefreshed = true;
        try {
          await refreshAccessToken();
        } catch (error) {
          clearAccessToken();
          authFailureHandler?.();
          throw error;
        }
        if (!isGet) {
          throw new ApiError('Session refreshed. Retry the action.', 401, 'SESSION_REFRESHED');
        }
        continue;
      }
      const data = await parseResponse(response);
      if (!response.ok) {
        const error = data?.error;
        const message = error?.message || data?.detail || `Request failed (${response.status})`;
        throw new ApiError(
          message,
          response.status,
          error?.code || `HTTP_${response.status}`,
          error?.request_id || null,
        );
      }
      return data;
    } catch (error) {
      if (error?.name === 'AbortError' || error?.name === 'TimeoutError') throw error;
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) throw error;
      if (attempt >= retryCount) {
        if (error instanceof ApiError) throw error;
        throw new ApiError('Unable to reach P.A.T.H. services. Check connectivity and retry.');
      }
      attempt += 1;
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
}

export const api = {
  get(path, options = {}) {
    return apiRequest(path, { ...options, method: 'GET' });
  },
  post(path, body, options = {}) {
    return apiRequest(path, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
  },
  put(path, body, options = {}) {
    return apiRequest(path, { ...options, method: 'PUT', body: JSON.stringify(body) });
  },
  patch(path, body, options = {}) {
    return apiRequest(path, { ...options, method: 'PATCH', body: JSON.stringify(body) });
  },
  delete(path, options = {}) {
    return apiRequest(path, { ...options, method: 'DELETE' });
  },
};
