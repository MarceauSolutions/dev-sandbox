const OAuthPage = {
  title: 'OAuth Settings',
  _users: [],

  async init() {
    try {
      const res = await API.get('/api/oauth/users');
      this._users = res.users || res || [];
    } catch {
      this._users = [];
    }
  },

  render(container) {
    const userCards = this._users.length
      ? this._users.map(u => `
        <div class="card" style="display:flex;align-items:center;gap:16px;padding:16px">
          <div style="width:40px;height:40px;border-radius:50%;background:var(--accent-primary-dim);display:flex;align-items:center;justify-content:center;font-size:18px;color:var(--accent-primary)">
            ${u.provider === 'google' ? 'G' : u.provider?.[0]?.toUpperCase() || '?'}
          </div>
          <div style="flex:1">
            <div style="font-weight:600">${u.email || u.name || 'Connected Account'}</div>
            <div style="font-size:12px;color:var(--text-muted)">
              ${u.provider ? u.provider.charAt(0).toUpperCase() + u.provider.slice(1) : 'OAuth'}
              ${u.connected_at ? ' &middot; Connected ' + new Date(u.connected_at).toLocaleDateString() : ''}
            </div>
          </div>
          <span class="tag ${u.status === 'active' || u.connected ? 'active' : ''}" style="font-size:11px">
            ${u.status || (u.connected ? 'Active' : 'Inactive')}
          </span>
          <button class="btn btn-sm btn-ghost oauth-disconnect-btn" data-user-id="${u.user_id || u.id}" data-name="${u.email || u.name || 'this account'}">
            Disconnect
          </button>
        </div>
      `).join('')
      : '<div class="empty-state">No accounts connected yet. Connect your Google account to get started.</div>';

    container.innerHTML = `
      <div class="page-header">
        <h1>OAuth Settings</h1>
        <p>Manage connected accounts and permissions</p>
      </div>

      <div class="card" style="margin-bottom:24px">
        <div class="card-header">
          <h2 class="card-title">Connect New Account</h2>
        </div>
        <p style="color:var(--text-secondary);margin-bottom:16px">
          Connect your Google account to enable Gmail integration, Google Sheets access, and Calendar sync.
        </p>
        <button class="btn btn-primary" id="oauth-connect-google-btn">Connect Google Account</button>
      </div>

      <div class="section-divider"><span>Connected Accounts</span></div>

      <div id="oauth-accounts-list" style="display:flex;flex-direction:column;gap:12px">
        ${userCards}
      </div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    container.querySelector('#oauth-connect-google-btn').addEventListener('click', async () => {
      const btn = container.querySelector('#oauth-connect-google-btn');
      btn.disabled = true;
      btn.textContent = 'Connecting...';

      try {
        const res = await API.post('/api/oauth/start');
        if (res.auth_url || res.url) {
          window.open(res.auth_url || res.url, '_blank', 'width=600,height=700');
          Toast.success('Authorization window opened. Complete the flow to connect.');
        } else {
          Toast.success('OAuth connection initiated');
        }
      } catch (err) {
        Toast.error('Failed to start OAuth: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Connect Google Account';
      }
    });

    container.querySelector('#oauth-accounts-list').addEventListener('click', async (e) => {
      const btn = e.target.closest('.oauth-disconnect-btn');
      if (!btn) return;

      const userId = btn.dataset.userId;
      const name = btn.dataset.name;
      if (!confirm('Disconnect ' + name + '? This will revoke access.')) return;

      btn.disabled = true;
      btn.textContent = 'Removing...';

      try {
        await API.delete('/api/oauth/disconnect/' + encodeURIComponent(userId));
        Toast.success('Account disconnected');
        this._users = this._users.filter(u => String(u.user_id || u.id) !== String(userId));
        this._refreshList(container);
      } catch (err) {
        Toast.error('Failed to disconnect: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Disconnect';
      }
    });
  },

  _refreshList(container) {
    const listEl = container.querySelector('#oauth-accounts-list');
    if (!listEl) return;

    if (!this._users.length) {
      listEl.innerHTML = '<div class="empty-state">No accounts connected yet. Connect your Google account to get started.</div>';
      return;
    }

    listEl.innerHTML = this._users.map(u => `
      <div class="card" style="display:flex;align-items:center;gap:16px;padding:16px">
        <div style="width:40px;height:40px;border-radius:50%;background:var(--accent-primary-dim);display:flex;align-items:center;justify-content:center;font-size:18px;color:var(--accent-primary)">
          ${u.provider === 'google' ? 'G' : u.provider?.[0]?.toUpperCase() || '?'}
        </div>
        <div style="flex:1">
          <div style="font-weight:600">${u.email || u.name || 'Connected Account'}</div>
          <div style="font-size:12px;color:var(--text-muted)">
            ${u.provider ? u.provider.charAt(0).toUpperCase() + u.provider.slice(1) : 'OAuth'}
            ${u.connected_at ? ' &middot; Connected ' + new Date(u.connected_at).toLocaleDateString() : ''}
          </div>
        </div>
        <span class="tag ${u.status === 'active' || u.connected ? 'active' : ''}" style="font-size:11px">
          ${u.status || (u.connected ? 'Active' : 'Inactive')}
        </span>
        <button class="btn btn-sm btn-ghost oauth-disconnect-btn" data-user-id="${u.user_id || u.id}" data-name="${u.email || u.name || 'this account'}">
          Disconnect
        </button>
      </div>
    `).join('');
  },

  destroy() {
    this._users = [];
  }
};
