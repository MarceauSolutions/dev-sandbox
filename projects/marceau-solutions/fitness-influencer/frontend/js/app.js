/* ============================================================
   App - Main entry point & global utilities
   ============================================================ */

const App = {
  init() {
    // Register all pages
    Router.register('', DashboardPage);
    Router.register('editor', EditorPage);
    Router.register('calendar', CalendarPage);
    Router.register('chat', ChatPage);
    Router.register('caption', CaptionPage);
    Router.register('reframe', ReframePage);
    Router.register('filler', FillerPage);
    Router.register('export', ExportPage);
    Router.register('overlay', OverlayPage);
    Router.register('annotations', AnnotationsPage);
    Router.register('exercise', ExercisePage);
    Router.register('transcription', TranscriptionPage);
    Router.register('analyze', AnalyzePage);
    Router.register('viral', ViralPage);
    Router.register('hook', HookPage);
    Router.register('retention', RetentionPage);
    Router.register('images', ImagesPage);
    Router.register('graphics', GraphicsPage);
    Router.register('ads', AdsPage);
    Router.register('brand', BrandPage);
    Router.register('analytics', AnalyticsPage);
    Router.register('leads', LeadsPage);
    Router.register('tasks', TasksPage);
    Router.register('clients', ClientsPage);
    Router.register('propane', PropanePage);
    Router.register('gamification', GamificationPage);
    Router.register('quota', QuotaPage);
    Router.register('oauth', OAuthPage);
    Router.register('jobs', JobsPage);

    // Initialize router
    Router.init('main-content');

    // Initialize toast
    Toast.init();

    // Setup job bar updates
    JobPoller.onUpdate((counts) => {
      document.getElementById('jb-processing').textContent = counts.processing + ' processing';
      document.getElementById('jb-queued').textContent = counts.queued + ' queued';
      document.getElementById('jb-completed').textContent = counts.completed + ' completed';
      this.renderJobBarItems();
    });

    // Check API health
    this.checkHealth();

    // Load XP bar
    this.loadXpBar();
  },

  async checkHealth() {
    try {
      const data = await API.get('/');
      const dot = document.getElementById('api-status-dot');
      const text = document.getElementById('api-status-text');
      if (data && data.status === 'active') {
        dot.className = 'status-dot';
        text.textContent = 'v' + (data.version || '2.0');
      }
    } catch {
      document.getElementById('api-status-dot').classList.add('offline');
      document.getElementById('api-status-text').textContent = 'Offline';
    }
  },

  toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth <= 768) {
      sidebar.classList.toggle('open');
    } else {
      document.getElementById('app-shell').classList.toggle('sidebar-collapsed');
    }
  },

  toggleNavGroup(labelEl) {
    const group = labelEl.closest('.nav-group');
    if (!group) return;
    const isCollapsed = group.dataset.collapsed === 'true';
    group.dataset.collapsed = isCollapsed ? 'false' : 'true';
  },

  async loadXpBar() {
    try {
      const p = await API.get('/api/gamification/player/stats');
      if (!p) return;
      const LEVEL_XP = [0, 100, 250, 500, 1000, 2000, 4000, 7500, 12000, 20000, 35000];
      const lvl = p.level || 1;
      const cur = LEVEL_XP[lvl - 1] || 0;
      const nxt = LEVEL_XP[lvl] || (cur + 1000);
      const pct = Math.min(100, Math.max(0, ((p.xp - cur) / (nxt - cur)) * 100));
      document.getElementById('xp-level').textContent = 'Lv ' + lvl;
      document.getElementById('xp-fill').style.width = Math.round(pct) + '%';
      document.getElementById('xp-coins').innerHTML = (p.coins || 0) + ' &#x1FA99;';
      document.getElementById('xp-streak').innerHTML = (p.day_streak || 0) + '&#x1F525;';
    } catch {}
  },

  toggleJobBar() {
    const bar = document.getElementById('job-bar');
    bar.classList.toggle('expanded');
    const hint = document.getElementById('jb-expand-hint');
    hint.textContent = bar.classList.contains('expanded') ? 'Click to collapse' : 'Click to expand';
  },

  renderJobBarItems() {
    const container = document.getElementById('job-bar-items');
    const jobs = JobPoller.getActiveJobs();
    if (!jobs.length) {
      container.innerHTML = '<div style="padding:8px 0;font-size:12px;color:var(--text-muted)">No active jobs</div>';
      return;
    }
    container.innerHTML = jobs.map(j => {
      const pct = j.progress || 0;
      const statusColor = (j.status === 'complete' || j.status === 'completed') ? 'complete' : '';
      return `<div class="job-item">
        <span style="font-weight:500;min-width:120px">${j.type || 'Job'}</span>
        <div class="job-progress"><div class="job-progress-fill ${statusColor}" style="width:${pct}%"></div></div>
        <span style="min-width:40px;text-align:right">${pct}%</span>
        <span style="min-width:70px;text-align:right;color:var(--text-muted)">${j.status}</span>
      </div>`;
    }).join('');
  },

  // Utility: render a video URL input field used by many pages
  videoUrlField(id = 'video-url') {
    return `<div class="form-group">
      <label class="form-label">Video URL</label>
      <input type="text" id="${id}" class="form-input" placeholder="https://example.com/video.mp4 or local path">
      <div class="form-hint">Paste a direct video URL or file path</div>
    </div>`;
  },

  // Utility: create a form submit handler that shows loading state
  formHandler(formId, buttonId, handler) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById(buttonId);
      const origText = btn.textContent;
      btn.disabled = true;
      btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;display:inline-block"></div> Processing...';
      try {
        await handler(e);
      } catch (err) {
        Toast.error(err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = origText;
      }
    });
  }
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
