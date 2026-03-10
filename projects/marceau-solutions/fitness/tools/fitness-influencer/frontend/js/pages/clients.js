/* ============================================================
   Client Management Page — Admin view for managing coaching clients
   ============================================================ */

const ClientsPage = {
  title: 'Clients',
  data: { clients: [], templates: [], selectedClient: null },

  async init() {
    try {
      const [clients, templates] = await Promise.allSettled([
        API.get('/api/admin/clients'),
        API.get('/api/admin/workouts/templates')
      ]);
      this.data.clients = clients.status === 'fulfilled' ? (clients.value.clients || clients.value || []) : [];
      const tpl = templates.status === 'fulfilled' ? templates.value : {};
      this.data.templates = tpl.templates || [];
    } catch { this.data.clients = []; this.data.templates = []; }
  },

  render(container) {
    const clients = this.data.clients;
    container.innerHTML = `
      <div class="page-header" style="display:flex;align-items:center;justify-content:space-between">
        <div>
          <h1>Client Management</h1>
          <p>${clients.length} active client${clients.length !== 1 ? 's' : ''}</p>
        </div>
        <button class="btn btn-primary" onclick="ClientsPage.showAddModal()">+ Add Client</button>
      </div>

      ${clients.length === 0 ? `
        <div class="card">
          <div class="empty-state">
            <p>No clients yet. When you sign your first coaching client, add them here to give them access to their client portal.</p>
            <button class="btn btn-primary" style="margin-top:16px" onclick="ClientsPage.showAddModal()">Add Your First Client</button>
          </div>
        </div>
      ` : `
        <div class="grid-auto" id="clients-grid">
          ${clients.map(c => this._clientCard(c)).join('')}
        </div>
      `}

      <!-- Add Client Modal -->
      <div id="add-client-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);z-index:200;align-items:center;justify-content:center">
        <div style="background:var(--bg-base);border:1px solid var(--border-default);border-radius:var(--radius-xl);max-width:500px;width:90vw;padding:28px" onclick="event.stopPropagation()">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
            <h2 style="font-size:18px;font-weight:700">Add New Client</h2>
            <button style="background:none;border:none;color:var(--text-secondary);font-size:24px;cursor:pointer" onclick="ClientsPage.hideAddModal()">&times;</button>
          </div>
          <form id="add-client-form">
            <div class="form-group">
              <label class="form-label">Name *</label>
              <input type="text" id="client-name" class="form-input" placeholder="John Smith" required>
            </div>
            <div class="form-group">
              <label class="form-label">Email *</label>
              <input type="email" id="client-email" class="form-input" placeholder="john@example.com" required>
            </div>
            <div class="form-group">
              <label class="form-label">Phone</label>
              <input type="tel" id="client-phone" class="form-input" placeholder="+1 (555) 123-4567">
            </div>
            <div class="form-group">
              <label class="form-label">Goals</label>
              <textarea id="client-goals" class="form-textarea" rows="3" placeholder="What are their fitness goals?"></textarea>
            </div>
            <button type="submit" class="btn btn-primary btn-lg" style="width:100%" id="add-client-btn">Create Client Account</button>
          </form>
        </div>
      </div>

      <!-- Client Detail Modal -->
      <div id="client-detail-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);z-index:200;align-items:center;justify-content:center;overflow-y:auto">
        <div style="background:var(--bg-base);border:1px solid var(--border-default);border-radius:var(--radius-xl);max-width:700px;width:90vw;padding:28px;margin:40px auto" onclick="event.stopPropagation()">
          <div id="client-detail-content"></div>
        </div>
      </div>

      <!-- Magic Link Result Modal -->
      <div id="magic-link-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);z-index:210;align-items:center;justify-content:center">
        <div style="background:var(--bg-base);border:1px solid var(--border-default);border-radius:var(--radius-xl);max-width:500px;width:90vw;padding:28px;text-align:center" onclick="event.stopPropagation()">
          <div style="font-size:48px;margin-bottom:16px">&#x2705;</div>
          <h2 style="font-size:18px;font-weight:700;margin-bottom:8px">Client Created!</h2>
          <p style="color:var(--text-secondary);margin-bottom:20px">Send this link to your client so they can access their portal:</p>
          <div style="background:var(--surface-2);padding:14px;border-radius:var(--radius-md);border:1px solid var(--border-default);word-break:break-all;font-family:monospace;font-size:13px;margin-bottom:16px" id="magic-link-url"></div>
          <div style="display:flex;gap:10px;justify-content:center">
            <button class="btn btn-primary" onclick="ClientsPage.copyMagicLink()">Copy Link</button>
            <button class="btn btn-secondary" onclick="ClientsPage.hideMagicLink()">Done</button>
          </div>
        </div>
      </div>
    `;

    // Bind form
    const form = document.getElementById('add-client-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        ClientsPage.createClient();
      });
    }
  },

  _clientCard(c) {
    const streakFire = c.streak > 0 ? '&#x1F525; ' + c.streak + 'd' : 'No streak';
    const lastLogin = c.last_login ? new Date(c.last_login).toLocaleDateString() : 'Never';
    return `
      <div class="card" style="cursor:pointer" onclick="ClientsPage.showDetail('${c.client_id}')">
        <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px">
          <div style="width:44px;height:44px;border-radius:50%;background:var(--accent-primary-dim);border:2px solid var(--accent-primary);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:var(--accent-primary)">
            ${(c.name || '?')[0].toUpperCase()}
          </div>
          <div style="flex:1">
            <div style="font-weight:700;font-size:15px">${c.name || 'Unknown'}</div>
            <div style="font-size:12px;color:var(--text-secondary)">${c.email || ''}</div>
          </div>
          <span class="badge badge-success">Lv ${c.level || 1}</span>
        </div>
        <div style="display:flex;gap:16px;font-size:12px;color:var(--text-secondary)">
          <span>${streakFire}</span>
          <span>${c.workouts_completed || 0} workouts</span>
          <span>Last: ${lastLogin}</span>
        </div>
      </div>
    `;
  },

  showAddModal() {
    const modal = document.getElementById('add-client-modal');
    modal.style.display = 'flex';
    modal.onclick = (e) => { if (e.target === modal) ClientsPage.hideAddModal(); };
  },

  hideAddModal() {
    document.getElementById('add-client-modal').style.display = 'none';
    document.getElementById('add-client-form').reset();
  },

  async createClient() {
    const btn = document.getElementById('add-client-btn');
    const origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Creating...';

    try {
      const result = await API.post('/api/admin/clients', {
        name: document.getElementById('client-name').value.trim(),
        email: document.getElementById('client-email').value.trim(),
        phone: document.getElementById('client-phone').value.trim() || null,
        goals: document.getElementById('client-goals').value.trim() || null
      });

      this.hideAddModal();

      // Show magic link
      const fullUrl = window.location.origin + (result.login_url || '/client/#login?token=' + result.token);
      document.getElementById('magic-link-url').textContent = fullUrl;
      this._lastMagicLink = fullUrl;
      document.getElementById('magic-link-modal').style.display = 'flex';

      // Refresh list
      await this.init();
      this.render(document.getElementById('main-content'));
      // Re-show magic link after re-render
      document.getElementById('magic-link-url').textContent = fullUrl;
      document.getElementById('magic-link-modal').style.display = 'flex';

      Toast.success('Client account created!');
    } catch (err) {
      Toast.error('Failed to create client: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = origText;
    }
  },

  copyMagicLink() {
    const url = this._lastMagicLink || document.getElementById('magic-link-url').textContent;
    navigator.clipboard.writeText(url).then(() => {
      Toast.success('Link copied to clipboard!');
    }).catch(() => {
      Toast.warning('Could not copy — please select and copy manually');
    });
  },

  hideMagicLink() {
    document.getElementById('magic-link-modal').style.display = 'none';
  },

  async showDetail(clientId) {
    const modal = document.getElementById('client-detail-modal');
    const content = document.getElementById('client-detail-content');
    modal.style.display = 'flex';
    modal.onclick = (e) => { if (e.target === modal) ClientsPage.hideDetail(); };
    content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div> Loading...</div>';

    try {
      const detail = await API.get('/api/admin/clients/' + clientId);
      const c = detail.profile || detail;
      const gam = detail.gamification || {};
      const player = gam.player || {};
      const stats = gam.stats || {};
      const achievements = (gam.achievements || []).filter(a => a.unlocked);
      const workouts = detail.workouts || {};
      const wkStats = workouts.stats || {};

      content.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
          <div style="display:flex;align-items:center;gap:14px">
            <div style="width:52px;height:52px;border-radius:50%;background:var(--accent-primary-dim);border:2px solid var(--accent-primary);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:var(--accent-primary)">
              ${(c.name || '?')[0].toUpperCase()}
            </div>
            <div>
              <h2 style="font-size:20px;font-weight:700;margin-bottom:2px">${c.name || 'Unknown'}</h2>
              <div style="font-size:13px;color:var(--text-secondary)">${c.email || ''} ${c.phone ? '&bull; ' + c.phone : ''}</div>
            </div>
          </div>
          <button style="background:none;border:none;color:var(--text-secondary);font-size:24px;cursor:pointer" onclick="ClientsPage.hideDetail()">&times;</button>
        </div>

        <!-- Stats -->
        <div class="grid-4" style="margin-bottom:20px">
          <div class="stat-card"><div class="stat-value" style="font-size:22px">Lv ${player.level || 1}</div><div class="stat-label">${player.title || 'New Member'}</div></div>
          <div class="stat-card"><div class="stat-value" style="font-size:22px">${player.current_streak || 0}d</div><div class="stat-label">Streak</div></div>
          <div class="stat-card"><div class="stat-value" style="font-size:22px">${player.xp_total || 0}</div><div class="stat-label">Total XP</div></div>
          <div class="stat-card"><div class="stat-value" style="font-size:22px">${wkStats.total_completed || 0}</div><div class="stat-label">Workouts Done</div></div>
        </div>

        <!-- Goals -->
        ${c.goals ? `<div class="card" style="margin-bottom:16px"><div class="card-title" style="margin-bottom:8px">Goals</div><p style="font-size:13px;color:var(--text-secondary)">${c.goals}</p></div>` : ''}

        <!-- Achievements -->
        ${achievements.length > 0 ? `
          <div class="card" style="margin-bottom:16px">
            <div class="card-title" style="margin-bottom:12px">Achievements Unlocked (${achievements.length})</div>
            <div style="display:flex;flex-wrap:wrap;gap:8px">
              ${achievements.map(a => `<span class="badge badge-success">${a.name}</span>`).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Actions -->
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">
          <button class="btn btn-primary btn-sm" onclick="ClientsPage.assignWorkout('${clientId}')">Assign Workout</button>
          <button class="btn btn-secondary btn-sm" onclick="ClientsPage.regenToken('${clientId}')">Regenerate Link</button>
          <button class="btn btn-ghost btn-sm" onclick="ClientsPage.copyPortalLink('${clientId}')">Copy Portal Link</button>
        </div>

        <!-- Assign Workout Section -->
        <div id="assign-workout-section" style="display:none;margin-top:20px">
          <div class="card">
            <div class="card-title" style="margin-bottom:12px">Assign Workout Template</div>
            <div class="form-group">
              <label class="form-label">Template</label>
              <select id="assign-template" class="form-select">
                <option value="">Select a template...</option>
                ${this.data.templates.map(t => `<option value="${t.id}">${t.name} (${t.days_per_week || '?'}x/week)</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Week Starting (Monday)</label>
              <input type="date" id="assign-week" class="form-input" value="${this._nextMonday()}">
            </div>
            <button class="btn btn-primary btn-sm" onclick="ClientsPage.doAssign('${clientId}')">Assign</button>
          </div>
        </div>
      `;
    } catch (err) {
      content.innerHTML = '<div class="empty-state"><p>Failed to load client details: ' + err.message + '</p></div>';
    }
  },

  hideDetail() {
    document.getElementById('client-detail-modal').style.display = 'none';
  },

  assignWorkout(clientId) {
    const section = document.getElementById('assign-workout-section');
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
  },

  async doAssign(clientId) {
    const templateId = document.getElementById('assign-template').value;
    const weekStart = document.getElementById('assign-week').value;
    if (!templateId) { Toast.warning('Select a template first'); return; }
    if (!weekStart) { Toast.warning('Select a week start date'); return; }
    try {
      await API.post('/api/admin/clients/' + clientId + '/assign-workout', {
        template_id: templateId, week_start: weekStart
      });
      Toast.success('Workout assigned!');
      document.getElementById('assign-workout-section').style.display = 'none';
    } catch (err) {
      Toast.error('Failed: ' + err.message);
    }
  },

  async regenToken(clientId) {
    try {
      const result = await API.post('/api/admin/clients/' + clientId + '/regenerate-token', {});
      const fullUrl = window.location.origin + '/client/#login?token=' + result.token;
      this._lastMagicLink = fullUrl;
      document.getElementById('magic-link-url').textContent = fullUrl;
      document.getElementById('magic-link-modal').style.display = 'flex';
      Toast.success('New access link generated');
    } catch (err) {
      Toast.error('Failed: ' + err.message);
    }
  },

  copyPortalLink(clientId) {
    const index = this.data.clients.find(c => c.client_id === clientId);
    if (index) {
      const url = window.location.origin + '/client/';
      navigator.clipboard.writeText(url).then(() => Toast.success('Portal URL copied'));
    }
  },

  _nextMonday() {
    const d = new Date();
    const day = d.getDay();
    const diff = day === 0 ? 1 : 8 - day;
    d.setDate(d.getDate() + diff);
    return d.toISOString().split('T')[0];
  }
};
