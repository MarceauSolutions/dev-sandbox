/* ============================================================
   API Client — Client Portal
   Fetch wrapper with Bearer token auth and 401 redirect
   ============================================================ */

const API = {
  baseUrl: window.location.origin,

  _headers() {
    const h = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('client_token');
    if (token) h['Authorization'] = 'Bearer ' + token;
    return h;
  },

  _authOnly() {
    const h = {};
    const token = localStorage.getItem('client_token');
    if (token) h['Authorization'] = 'Bearer ' + token;
    return h;
  },

  async get(path, params = {}) {
    const url = new URL(this.baseUrl + path);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, v);
    });
    try {
      const res = await fetch(url, { headers: this._headers() });
      if (!res.ok) return this._handleError(res);
      return await res.json();
    } catch (err) {
      if (err instanceof APIError) throw err;
      throw new APIError(0, 'Network error: ' + err.message);
    }
  },

  async post(path, body = {}) {
    try {
      const res = await fetch(this.baseUrl + path, {
        method: 'POST',
        headers: this._headers(),
        body: JSON.stringify(body)
      });
      if (!res.ok) return this._handleError(res);
      return await res.json();
    } catch (err) {
      if (err instanceof APIError) throw err;
      throw new APIError(0, 'Network error: ' + err.message);
    }
  },

  async put(path, body = {}) {
    try {
      const res = await fetch(this.baseUrl + path, {
        method: 'PUT',
        headers: this._headers(),
        body: JSON.stringify(body)
      });
      if (!res.ok) return this._handleError(res);
      return await res.json();
    } catch (err) {
      if (err instanceof APIError) throw err;
      throw new APIError(0, 'Network error: ' + err.message);
    }
  },

  async delete(path) {
    try {
      const res = await fetch(this.baseUrl + path, {
        method: 'DELETE',
        headers: this._headers()
      });
      if (!res.ok) return this._handleError(res);
      return await res.json();
    } catch (err) {
      if (err instanceof APIError) throw err;
      throw new APIError(0, 'Network error: ' + err.message);
    }
  },

  async upload(path, formData) {
    // FormData upload — add auth header but NOT content-type (browser sets boundary)
    try {
      const res = await fetch(this.baseUrl + path, {
        method: 'POST',
        headers: this._authOnly(),
        body: formData
      });
      if (!res.ok) return this._handleError(res);
      return await res.json();
    } catch (err) {
      if (err instanceof APIError) throw err;
      throw new APIError(0, 'Network error: ' + err.message);
    }
  },

  async _handleError(res) {
    let detail = 'Request failed';
    try {
      const body = await res.json();
      detail = body.detail || body.message || body.error || detail;
    } catch {}

    // On 401: clear token and redirect to login
    if (res.status === 401) {
      localStorage.removeItem('client_token');
      location.hash = 'login';
      throw new APIError(401, 'Session expired. Please log in again.');
    }

    if (res.status === 429) {
      Toast.show('Rate limit exceeded. Please wait a moment.', 'warning');
    }

    throw new APIError(res.status, detail);
  }
};

class APIError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = 'APIError';
  }
}
