/* ============================================================
   App — Client Portal Main Entry Point
   ============================================================ */

const App = {
  init() {
    const token = localStorage.getItem('client_token');
    const hash = location.hash.slice(1) || '';

    // Redirect to login if no token (unless already on login page)
    if (!token && !hash.startsWith('login')) {
      location.hash = 'login';
    }

    // Register all pages
    Router.register('login', LoginPage);
    Router.register('', DashboardPage);
    Router.register('workouts', WorkoutsPage);
    Router.register('form-check', FormCheckPage);
    Router.register('ask-coach', AskCoachPage);
    Router.register('progress', ProgressPage);
    Router.register('profile', ProfilePage);

    // Initialize router
    Router.init('main-content');

    // Initialize toast
    Toast.init();

    // Load user info if authenticated
    if (token) this.loadUserInfo();
  },

  async loadUserInfo() {
    try {
      const me = await API.get('/api/client/me');
      const nameEl = document.getElementById('client-name');
      if (nameEl) nameEl.textContent = me.name || '';

      // Update level and streak in topbar
      try {
        const stats = await API.get('/api/client/progress');
        const p = stats.player || {};
        const levelEl = document.getElementById('client-level');
        const streakEl = document.getElementById('client-streak');
        if (levelEl) levelEl.textContent = 'Lv ' + (p.level || 1);
        if (streakEl) streakEl.textContent = (p.current_streak || 0) + ' day streak';
      } catch {}
    } catch {
      localStorage.removeItem('client_token');
      location.hash = 'login';
    }
  },

  toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
  },

  logout() {
    localStorage.removeItem('client_token');
    location.hash = 'login';
    location.reload();
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
