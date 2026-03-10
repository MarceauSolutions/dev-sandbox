/* ============================================================
   Command Center Dashboard — Unified business operations view
   ============================================================ */

const DashboardPage = {
  title: 'Dashboard',
  data: { stats: null, tasks: [], calendar: null },

  async init() {
    try {
      const [stats, tasks, calendar] = await Promise.allSettled([
        API.get('/api/gamification/player/stats'),
        API.get('/api/tasks/'),
        API.get('/api/content/calendar/today')
      ]);
      this.data.stats = stats.status === 'fulfilled' ? stats.value : null;
      const taskData = tasks.status === 'fulfilled' ? tasks.value : { tasks: [] };
      this.data.tasks = Array.isArray(taskData) ? taskData : (taskData && taskData.tasks ? taskData.tasks : []);
      this.data.calendar = calendar.status === 'fulfilled' ? calendar.value : null;
    } catch {}
  },

  render(container) {
    const s = this.data.stats || {};
    const st = s.stats || {};
    const allTasks = this.data.tasks;
    const propaneTasks = allTasks.filter(t => t.tags && t.tags.includes('propane') && t.section !== 'RECENTLY_DONE');
    const todayTasks = allTasks.filter(t => (t.section === 'TODAY' || t.section === 'THIS_WEEK') && !(t.tags && t.tags.includes('propane')));
    container.innerHTML = `
      <div class="page-header">
        <h1>Command Center</h1>
        <p>Your daily business operations at a glance</p>
      </div>

      <!-- Quick Stats -->
      <div class="grid-5" style="margin-bottom:24px">
        ${this._stat('&#x1F91D;', st.totalClients || 0, 'Clients')}
        ${this._stat('&#x1F4B0;', '$' + (st.totalRevenue || 0), 'Revenue')}
        ${this._stat('&#x1F3AF;', st.totalLeads || 0, 'Leads')}
        ${this._stat('&#x1F525;', (s.day_streak || 0) + 'd', 'Streak')}
        ${this._stat('&#11088;', 'Lv ' + (s.level || 1), s.title || 'Rookie')}
      </div>

      <div class="grid-2" style="margin-bottom:24px">
        <!-- Today's Mission -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">&#x1F525; Today's Mission</div>
            <span class="badge">${propaneTasks.length} Propane tasks</span>
          </div>
          ${this._renderMissionTasks(propaneTasks, todayTasks)}
          <div style="margin-top:14px;display:flex;gap:8px">
            <button class="btn btn-sm btn-primary" onclick="Router.go('propane')">Propane Program</button>
            <button class="btn btn-sm btn-ghost" onclick="Router.go('tasks')">All Tasks</button>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">&#9889; Quick Actions</div>
          </div>
          <div class="grid-2" style="gap:10px">
            ${this._action('content_created', '&#x1F4F1;', 'Content Created', 15)}
            ${this._action('outreach', '&#x1F4E8;', 'Outreach', 15)}
            ${this._action('community_engage', '&#x1F4AC;', 'Community', 10)}
            ${this._action('lead_generated', '&#x1F3AF;', 'Lead Generated', 50)}
            ${this._action('call_booked', '&#x1F4DE;', 'Call Booked', 100)}
            ${this._action('client_signed', '&#x1F91D;', 'Client Signed', 500)}
          </div>
        </div>
      </div>

      <div class="grid-2">
        <!-- Tool Launcher -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">&#x1F6E0; Tools</div>
          </div>
          <div class="grid-auto-sm" style="gap:10px">
            ${this._tool('editor', '&#x1F3AC;', 'Video Editor')}
            ${this._tool('caption', '&#x1F4DD;', 'Captions')}
            ${this._tool('images', '&#x1F5BC;', 'Image Gen')}
            ${this._tool('chat', '&#x1F916;', 'AI Assistant')}
            ${this._tool('calendar', '&#x1F4C5;', 'Calendar')}
            ${this._tool('analytics', '&#x1F4CA;', 'Analytics')}
            ${this._tool('ads', '&#x1F4E2;', 'Ad Builder')}
            ${this._tool('leads', '&#x1F465;', 'Leads')}
          </div>
        </div>

        <!-- Documents -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">&#x1F4C4; Documents</div>
          </div>
          <div style="display:flex;flex-direction:column;gap:4px">
            ${this._doc('legal/cancellation-refund-policy.pdf', 'Cancellation Policy', 'pdf')}
            ${this._doc('legal/privacy-policy.md', 'Privacy Policy', 'md')}
            ${this._doc('ops/runbook.md', 'Operations Runbook', 'md')}
            ${this._doc('ops/coaching-onboarding-runbook.md', 'Onboarding Runbook', 'md')}
            ${this._doc('research/peptides/tesamorelin-deep-dive.md', 'Tesamorelin Research', 'md')}
            ${this._doc('business-planning/propane-fitness-tracker.md', 'Propane Tracker', 'md')}
          </div>
        </div>
      </div>
    `;
  },

  _stat(icon, value, label) {
    return `<div class="stat-card">
      <div style="font-size:18px;margin-bottom:4px">${icon}</div>
      <div class="stat-value" style="font-size:22px">${value}</div>
      <div class="stat-label">${label}</div>
    </div>`;
  },

  _renderMissionTasks(propane, other) {
    const tasks = [...propane.slice(0, 5), ...other.slice(0, 3)];
    if (!tasks.length) return '<div class="empty-state" style="padding:24px"><p>No tasks today. Start your Propane Program!</p></div>';
    return '<div>' + tasks.map(t => {
      const title = (t.title || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const isPropane = t.tags && t.tags.includes('propane');
      return `<div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border-muted)">
        <input type="checkbox" onchange="DashboardPage.completeTask('${t.id}', ${t.xp_value || 20}, '${title}')"
          style="accent-color:var(--accent-primary);width:16px;height:16px;cursor:pointer;flex-shrink:0">
        <span style="flex:1;font-size:13px;font-weight:500">${t.title}</span>
        ${t.xp_value ? '<span class="badge">' + t.xp_value + ' XP</span>' : ''}
        ${isPropane ? '<span style="font-size:9px;color:var(--accent-primary);font-weight:700;letter-spacing:0.05em">PROPANE</span>' : ''}
      </div>`;
    }).join('') + '</div>';
  },

  _action(action, icon, label, xp) {
    return `<button class="quick-action" style="padding:14px" onclick="DashboardPage.logAction('${action}', ${xp})">
      <div class="qa-icon">${icon}</div>
      <div class="qa-label">${label}</div>
      <div style="font-size:10px;color:var(--accent-primary);font-weight:700">+${xp} XP</div>
    </button>`;
  },

  _tool(page, icon, label) {
    return `<div class="quick-action" style="padding:12px" onclick="Router.go('${page}')">
      <div style="font-size:20px">${icon}</div>
      <div style="font-size:11px;font-weight:600">${label}</div>
    </div>`;
  },

  _doc(path, label, ext) {
    const url = ext === 'md' ? '/api/docs/' + path + '?format=html' : '/api/docs/' + path;
    return `<div style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:var(--radius-sm);cursor:pointer;transition:background 0.2s"
      onmouseover="this.style.background='var(--surface-2)'" onmouseout="this.style.background=''"
      onclick="DocViewer.open('${url}', '${label}')">
      <span style="font-size:16px">${ext === 'pdf' ? '&#x1F4D1;' : '&#x1F4C3;'}</span>
      <span style="font-size:13px;font-weight:500">${label}</span>
      <span style="margin-left:auto;font-size:10px;color:var(--text-muted);text-transform:uppercase">${ext}</span>
    </div>`;
  },

  async logAction(action, xp) {
    try {
      const result = await API.post('/api/gamification/player/action', {
        action: action,
        tenant_id: 'wmarceau'
      });
      const actionId = result && result.action_id;
      Toast.showWithUndo(
        '+' + xp + ' XP \u2014 ' + action.replace(/_/g, ' '),
        actionId,
        async (aid) => {
          await API.post('/api/gamification/player/undo', { action_id: aid, tenant_id: 'wmarceau' });
          App.loadXpBar();
        }
      );
      App.loadXpBar();
    } catch (err) {
      Toast.error('Action failed: ' + err.message);
    }
  },

  async completeTask(taskId, xpValue, title) {
    try {
      await API.put('/api/tasks/' + taskId, { section: 'RECENTLY_DONE' });
      const result = await API.post('/api/gamification/player/action', {
        action: 'task_completed',
        tenant_id: 'wmarceau',
        metadata: { xp_override: xpValue, task_title: title }
      });
      const actionId = result && result.action_id;
      Toast.showWithUndo(
        '+' + xpValue + ' XP \u2014 ' + title,
        actionId,
        async (aid) => {
          await API.put('/api/tasks/' + taskId, { section: 'THIS_WEEK' });
          await API.post('/api/gamification/player/undo', { action_id: aid, tenant_id: 'wmarceau' });
          await DashboardPage.init();
          DashboardPage.render(document.getElementById('main-content'));
          App.loadXpBar();
        }
      );
      // Re-render
      await this.init();
      this.render(document.getElementById('main-content'));
      App.loadXpBar();
    } catch (err) {
      Toast.error('Failed: ' + err.message);
    }
  }
};
