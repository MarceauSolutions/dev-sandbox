/* ============================================================
   API Client - Fetch wrapper with error handling
   ============================================================ */

const API = {
  baseUrl: window.location.origin,

  async get(path, params = {}) {
    const url = new URL(this.baseUrl + path);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, v);
    });
    try {
      const res = await fetch(url);
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
        headers: { 'Content-Type': 'application/json' },
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
      const res = await fetch(this.baseUrl + path, { method: 'DELETE' });
      if (!res.ok) return this._handleError(res);
      return await res.json();
    } catch (err) {
      if (err instanceof APIError) throw err;
      throw new APIError(0, 'Network error: ' + err.message);
    }
  },

  async upload(path, file, additionalData = {}) {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(additionalData).forEach(([k, v]) => formData.append(k, String(v)));
    try {
      const res = await fetch(this.baseUrl + path, {
        method: 'POST',
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
