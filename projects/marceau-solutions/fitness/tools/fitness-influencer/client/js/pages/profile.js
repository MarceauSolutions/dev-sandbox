/* ============================================================
   Profile Page — Client Portal
   Simple profile view with client details
   ============================================================ */

const ProfilePage = {
  title: 'My Profile',
  profileData: null,

  async init() {
    try {
      this.profileData = await API.get('/api/client/me');
    } catch (err) {
      console.warn('Profile init:', err.message);
      this.profileData = null;
    }
  },

  render(container) {
    const p = this.profileData || {};

    container.innerHTML = `
      <div class="page-header">
        <h1>My Profile</h1>
        <p>Your account details and coaching information</p>
      </div>

      <!-- Profile Card -->
      <div class="card" style="margin-bottom:24px">
        <div style="display:flex;align-items:center;gap:20px;margin-bottom:24px">
          <div style="width:72px;height:72px;border-radius:50%;background:linear-gradient(135deg,var(--accent-primary),var(--accent-secondary));display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:800;color:#0a1128;flex-shrink:0">
            ${p.name ? p.name.charAt(0).toUpperCase() : '?'}
          </div>
          <div>
            <div style="font-size:22px;font-weight:800;color:var(--text-primary)">${this._esc(p.name || 'Client')}</div>
            <div style="font-size:13px;color:var(--text-secondary)">${this._esc(p.email || '')}</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          <div>
            <div class="form-label" style="margin-bottom:4px">Program</div>
            <div style="font-size:14px;font-weight:600;color:var(--text-primary)">${this._esc(p.program || 'General Fitness')}</div>
          </div>
          <div>
            <div class="form-label" style="margin-bottom:4px">Start Date</div>
            <div style="font-size:14px;font-weight:600;color:var(--text-primary)">${p.start_date || '--'}</div>
          </div>
          <div>
            <div class="form-label" style="margin-bottom:4px">Coach</div>
            <div style="font-size:14px;font-weight:600;color:var(--text-primary)">${this._esc(p.coach_name || 'William Marceau')}</div>
          </div>
          <div>
            <div class="form-label" style="margin-bottom:4px">Status</div>
            <div><span class="badge badge-success">Active</span></div>
          </div>
        </div>
      </div>

      <!-- Goals -->
      ${p.goals ? `
      <div class="card" style="margin-bottom:24px">
        <div class="card-title" style="margin-bottom:14px">My Goals</div>
        <div style="display:flex;flex-direction:column;gap:10px">
          ${(Array.isArray(p.goals) ? p.goals : [p.goals]).map(goal => `
            <div style="display:flex;align-items:center;gap:10px;font-size:13px">
              <div style="width:8px;height:8px;border-radius:50%;background:var(--accent-primary);flex-shrink:0"></div>
              <span>${this._esc(typeof goal === 'string' ? goal : goal.text || JSON.stringify(goal))}</span>
            </div>
          `).join('')}
        </div>
      </div>
      ` : ''}

      <!-- Contact Coach -->
      <div class="card" style="margin-bottom:24px">
        <div class="card-title" style="margin-bottom:14px">Need Help?</div>
        <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px;line-height:1.6">
          Have questions about your program, billing, or anything else? Reach out to your coach directly.
        </p>
        <div style="display:flex;gap:12px;flex-wrap:wrap">
          <a href="#ask-coach" class="btn btn-primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3c-4.97 0-9 3.13-9 7s4.03 7 9 7c.7 0 1.38-.07 2.04-.2L19 19l-1.22-3.04C19.18 14.56 21 12.9 21 10c0-3.87-4.03-7-9-7z"/></svg>
            Ask AI Coach
          </a>
          ${p.coach_email ? `
          <a href="mailto:${this._esc(p.coach_email)}" class="btn btn-secondary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 7L2 7"/></svg>
            Email Coach
          </a>
          ` : ''}
          ${p.coach_phone ? `
          <a href="tel:${this._esc(p.coach_phone)}" class="btn btn-secondary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>
            Call Coach
          </a>
          ` : ''}
        </div>
      </div>

      <!-- Account Actions -->
      <div class="card">
        <div class="card-title" style="margin-bottom:14px">Account</div>
        <div style="display:flex;gap:12px">
          <button class="btn btn-secondary" onclick="App.logout()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>
            Logout
          </button>
        </div>
      </div>
    `;
  },

  _esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
