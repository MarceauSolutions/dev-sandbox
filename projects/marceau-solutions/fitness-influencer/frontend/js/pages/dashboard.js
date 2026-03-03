const DashboardPage = {
  title: 'Home',
  data: {},

  async init() {
    try {
      const [calendar, quota] = await Promise.allSettled([
        API.get('/api/content/calendar/today'),
        API.get('/api/quota/status')
      ]);
      this.data.calendar = calendar.status === 'fulfilled' ? calendar.value : null;
      this.data.quota = quota.status === 'fulfilled' ? quota.value : null;
    } catch {}
  },

  render(container) {
    const cal = this.data.calendar;
    const todayTheme = cal?.theme || cal?.day_theme || 'No plan set';
    const todayTopic = cal?.topic || cal?.hook_idea || '';
    const todayFormat = cal?.format || cal?.content_format || '';

    container.innerHTML = `
      <div class="page-header">
        <h1>Welcome back, Coach</h1>
        <p>Your fitness content command center</p>
      </div>

      <div class="grid-2" style="margin-bottom:28px">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Today's Content Plan</span>
            <button class="btn btn-sm btn-ghost" onclick="Router.go('calendar')">View Week &rarr;</button>
          </div>
          <div style="font-size:20px;font-weight:800;margin-bottom:10px;color:var(--accent-primary);letter-spacing:-0.01em">${todayTheme}</div>
          ${todayTopic ? `<p style="font-size:13px;color:var(--text-secondary);margin-bottom:4px;line-height:1.5">${todayTopic}</p>` : ''}
          ${todayFormat ? `<div class="badge" style="margin-top:8px">${todayFormat}</div>` : ''}
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">Active Jobs</span>
            <button class="btn btn-sm btn-ghost" onclick="Router.go('jobs')">View All &rarr;</button>
          </div>
          <div id="dash-active-jobs">
            <div style="color:var(--text-muted);font-size:13px">No active jobs</div>
          </div>
        </div>
      </div>

      <div class="section-divider"><span>Quick Actions</span></div>

      <div class="grid-4" style="margin-bottom:28px">
        <div class="quick-action" onclick="Router.go('editor')">
          <div class="qa-icon" style="background:var(--accent-secondary-dim);color:var(--accent-secondary)">&#127909;</div>
          <span class="qa-label">Video Editor</span>
        </div>
        <div class="quick-action" onclick="Router.go('caption')">
          <div class="qa-icon" style="background:var(--accent-primary-dim);color:var(--accent-primary)">&#9998;</div>
          <span class="qa-label">Add Captions</span>
        </div>
        <div class="quick-action" onclick="Router.go('images')">
          <div class="qa-icon" style="background:var(--accent-tertiary-dim);color:var(--accent-tertiary)">&#127912;</div>
          <span class="qa-label">Generate Images</span>
        </div>
        <div class="quick-action" onclick="Router.go('chat')">
          <div class="qa-icon" style="background:var(--accent-secondary-dim);color:var(--accent-secondary)">&#10024;</div>
          <span class="qa-label">AI Assistant</span>
        </div>
        <div class="quick-action" onclick="Router.go('viral')">
          <div class="qa-icon" style="background:rgba(255,82,82,0.12);color:#FF5252">&#128293;</div>
          <span class="qa-label">Find Viral Clips</span>
        </div>
        <div class="quick-action" onclick="Router.go('export')">
          <div class="qa-icon" style="background:rgba(255,215,64,0.12);color:#FFD740">&#128640;</div>
          <span class="qa-label">Export Video</span>
        </div>
        <div class="quick-action" onclick="Router.go('graphics')">
          <div class="qa-icon" style="background:rgba(0,176,255,0.12);color:#00B0FF">&#127752;</div>
          <span class="qa-label">Create Graphic</span>
        </div>
        <div class="quick-action" onclick="Router.go('analyze')">
          <div class="qa-icon" style="background:var(--accent-primary-dim);color:var(--accent-primary)">&#128202;</div>
          <span class="qa-label">Analyze Video</span>
        </div>
      </div>

      <div class="section-divider"><span>System Status</span></div>

      <div class="grid-3">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)" id="dash-quota-used">--</div>
          <div class="stat-label">Jobs Used Today</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-secondary)" id="dash-tier">--</div>
          <div class="stat-label">Current Tier</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-tertiary)" id="dash-api-version">v2.0</div>
          <div class="stat-label">API Version</div>
        </div>
      </div>
    `;

    // Fill quota data
    if (this.data.quota) {
      const q = this.data.quota;
      document.getElementById('dash-quota-used').textContent = q.used_today ?? q.video_jobs_used ?? '--';
      document.getElementById('dash-tier').textContent = q.tier || q.plan || '--';
    }

    // Load active jobs
    this.loadActiveJobs();
  },

  async loadActiveJobs() {
    try {
      const jobs = await API.get('/api/jobs');
      const list = (jobs.jobs || jobs || []).filter(j => j.status === 'processing' || j.status === 'queued').slice(0, 3);
      const el = document.getElementById('dash-active-jobs');
      if (!el) return;
      if (!list.length) return;
      el.innerHTML = list.map(j => `
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;font-size:13px">
          <div class="spinner" style="width:14px;height:14px"></div>
          <span style="font-weight:500">${j.job_type || j.type || 'Job'}</span>
          <span style="margin-left:auto;color:var(--text-muted);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.04em">${j.status}</span>
        </div>
      `).join('');
    } catch {}
  }
};
