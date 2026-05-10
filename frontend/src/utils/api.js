const BASE_URL = '/api/v1';

function authHeaders(extra = {}) {
  const token = localStorage.getItem('authToken');
  return token
    ? { Authorization: `Bearer ${token}`, ...extra }
    : { ...extra };
}

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = authHeaders(isFormData ? {} : { 'Content-Type': 'application/json' });

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  get: (path) => request(path, { method: 'GET' }),
  post: (path, body) =>
    request(path, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: (path, body) =>
    request(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
};
