/* ============================================================
   Dashboard Page — Client Portal
   Welcome banner, today's workout, quick actions, achievements
   ============================================================ */

const DashboardPage = {
  title: 'Dashboard',
  data: null,

  async init() {
    try {
      this.data = await API.get('/api/client/dashboard');
    } catch (err) {
      console.warn('Dashboard init:', err.message);
      this.data = null;
    }
  },

  render(container) {
    const d = this.data || {};
    const player = d.player || {};
    const workout = d.today_workout || null;
    const achievements = d.recent_achievements || [];
    const coachNote = d.coach_note || '';
    const weekSummary = d.week_summary || {};

    // XP calculation
    const LEVEL_XP = [0, 100, 250, 500, 1000, 2000, 4000, 7500, 12000, 20000, 35000];
    const lvl = player.level || 1;
    const xp = player.xp || 0;
    const curThreshold = LEVEL_XP[lvl - 1] || 0;
    const nextThreshold = LEVEL_XP[lvl] || (curThreshold + 1000);
    const xpPct = Math.min(100, Math.max(0, ((xp - curThreshold) / (nextThreshold - curThreshold)) * 100));

    const levelTitles = ['Beginner', 'Novice', 'Apprentice', 'Warrior', 'Champion', 'Elite', 'Master', 'Legend', 'Titan', 'Immortal'];
    const levelTitle = levelTitles[lvl - 1] || 'Warrior';

    container.innerHTML = `
      <!-- Welcome Banner -->
      <div class="welcome-banner">
        <div class="welcome-name">Welcome back${d.client_name ? ', ' + d.client_name : ''}</div>
        <div class="welcome-subtitle">${levelTitle} &middot; Level ${lvl} &middot; ${player.current_streak || 0} day streak</div>
        <div style="margin-top:16px;max-width:300px">
          <div class="progress-bar-container" style="height:10px;border-radius:5px">
            <div class="progress-bar" style="width:${Math.round(xpPct)}%;border-radius:5px"></div>
          </div>
          <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:11px;color:var(--text-secondary)">
            <span>${xp} XP</span>
            <span>${nextThreshold} XP to Level ${lvl + 1}</span>
          </div>
        </div>
      </div>

      ${coachNote ? `
      <div class="coach-note" style="margin-bottom:24px">
        <strong style="color:var(--accent-primary)">Coach's Note:</strong> ${this._escHtml(coachNote)}
      </div>
      ` : ''}

      <!-- Today's Workout -->
      <div class="section-divider"><span>Today's Workout</span></div>
      ${workout ? `
      <div class="card" style="cursor:pointer" onclick="Router.go('workouts')">
        <div class="card-header">
          <div>
            <div class="card-title">${this._escHtml(workout.name || 'Workout')}</div>
            <div class="card-subtitle">${workout.exercise_count || 0} exercises &middot; ~${workout.est_duration || 45} min</div>
          </div>
          <span class="badge badge-gold">+${workout.xp_reward || 50} XP</span>
        </div>
        ${workout.exercises ? `
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">
          ${(workout.exercises || []).slice(0, 4).map(ex => `
            <span class="tag">${this._escHtml(ex.name || ex)}</span>
          `).join('')}
          ${(workout.exercises || []).length > 4 ? `<span class="tag">+${workout.exercises.length - 4} more</span>` : ''}
        </div>
        ` : ''}
        <button class="btn btn-primary" onclick="event.stopPropagation(); Router.go('workouts')">
          Start Workout
        </button>
      </div>
      ` : `
      <div class="card">
        <div class="empty-state" style="padding:32px">
          <p style="font-size:16px;margin-bottom:8px">&#127774;</p>
          <p>No workout scheduled for today. Enjoy your rest day!</p>
        </div>
      </div>
      `}

      <!-- Quick Actions -->
      <div class="section-divider"><span>Quick Actions</span></div>
      <div class="grid-3" style="margin-bottom:24px">
        <div class="quick-action" onclick="DashboardPage.logMeal()">
          <div class="qa-icon">&#127869;</div>
          <div class="qa-label">Log Meal</div>
          <div class="qa-xp">+15 XP</div>
        </div>
        <div class="quick-action" onclick="DashboardPage.dailyCheckIn()">
          <div class="qa-icon">&#9989;</div>
          <div class="qa-label">Daily Check-in</div>
          <div class="qa-xp">+10 XP</div>
        </div>
        <div class="quick-action" onclick="Router.go('form-check')">
          <div class="qa-icon">&#127909;</div>
          <div class="qa-label">Form Check</div>
          <div class="qa-xp">+25 XP</div>
        </div>
      </div>

      <!-- Week Summary -->
      <div class="section-divider"><span>This Week</span></div>
      <div class="grid-4" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value">${weekSummary.workouts_completed || 0}<span style="font-size:16px;color:var(--text-secondary)">/${weekSummary.workouts_total || 0}</span></div>
          <div class="stat-label">Workouts</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">${weekSummary.xp_earned || 0}</div>
          <div class="stat-label">XP Earned</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${weekSummary.meals_logged || 0}</div>
          <div class="stat-label">Meals Logged</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${weekSummary.form_checks || 0}</div>
          <div class="stat-label">Form Checks</div>
        </div>
      </div>

      <!-- Recent Achievements -->
      ${achievements.length > 0 ? `
      <div class="section-divider"><span>Recent Achievements</span></div>
      <div class="grid-3">
        ${achievements.slice(0, 3).map(a => `
          <div class="card" style="text-align:center;padding:24px">
            <div style="font-size:36px;margin-bottom:10px">${a.icon || '&#127942;'}</div>
            <div style="font-size:14px;font-weight:700;color:var(--text-primary);margin-bottom:4px">${this._escHtml(a.name || 'Achievement')}</div>
            <div style="font-size:12px;color:var(--text-secondary)">${this._escHtml(a.description || '')}</div>
            <div style="font-size:11px;color:var(--accent-primary);font-weight:700;margin-top:8px">+${a.xp || 0} XP</div>
          </div>
        `).join('')}
      </div>
      ` : ''}
    `;
  },

  async logMeal() {
    try {
      const result = await API.post('/api/client/actions/log-meal');
      Toast.success(`Meal logged! +${result.xp_earned || 15} XP`);
      App.loadUserInfo();
    } catch (err) {
      Toast.error(err.message);
    }
  },

  async dailyCheckIn() {
    try {
      const result = await API.post('/api/client/actions/check-in');
      Toast.success(`Daily check-in complete! +${result.xp_earned || 10} XP`);
      App.loadUserInfo();
    } catch (err) {
      Toast.error(err.message);
    }
  },

  _escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
