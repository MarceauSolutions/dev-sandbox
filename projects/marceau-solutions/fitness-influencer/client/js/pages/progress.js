/* ============================================================
   Progress Page — Client Portal
   Full progress view: XP, streak, achievements, stats, rewards
   ============================================================ */

const ProgressPage = {
  title: 'My Progress',
  data: null,

  async init() {
    try {
      this.data = await API.get('/api/client/progress');
    } catch (err) {
      console.warn('Progress init:', err.message);
      this.data = null;
    }
  },

  render(container) {
    const d = this.data || {};
    const player = d.player || {};
    const achievements = d.achievements || [];
    const stats = d.stats || {};
    const rewards = d.rewards || [];
    const streakDays = d.streak_calendar || [];

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
      <div class="page-header">
        <h1>My Progress</h1>
        <p>Track your fitness journey and unlock achievements</p>
      </div>

      <!-- Level & XP -->
      <div class="card" style="margin-bottom:24px">
        <div style="display:flex;align-items:center;gap:20px;margin-bottom:16px">
          <div style="width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,var(--accent-primary),var(--accent-secondary));display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;color:#0a1128;flex-shrink:0">
            ${lvl}
          </div>
          <div style="flex:1">
            <div style="font-size:20px;font-weight:800;color:var(--text-primary)">${levelTitle}</div>
            <div style="font-size:13px;color:var(--text-secondary)">Level ${lvl} &middot; ${xp} total XP &middot; ${player.coins || 0} coins</div>
          </div>
        </div>
        <div class="xp-bar-lg">
          <div class="progress-bar-container">
            <div class="progress-bar" style="width:${Math.round(xpPct)}%"></div>
          </div>
          <div class="xp-labels">
            <span class="xp-current">${xp - curThreshold} / ${nextThreshold - curThreshold} XP</span>
            <span>Level ${lvl + 1}</span>
          </div>
        </div>
      </div>

      <!-- Streak Section -->
      <div class="section-divider"><span>Streak</span></div>
      <div class="grid-2" style="margin-bottom:24px">
        <div class="card">
          <div style="display:flex;gap:24px;justify-content:center;text-align:center">
            <div>
              <div class="stat-value" style="color:var(--accent-primary)">${player.current_streak || 0}</div>
              <div class="stat-label">Current Streak</div>
            </div>
            <div style="width:1px;background:var(--border-default)"></div>
            <div>
              <div class="stat-value">${player.best_streak || 0}</div>
              <div class="stat-label">Best Streak</div>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:12px">Last 30 Days</div>
          ${this._renderStreakCalendar(streakDays)}
        </div>
      </div>

      <!-- Stats Summary -->
      <div class="section-divider"><span>All-Time Stats</span></div>
      <div class="grid-4" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value">${stats.workouts_completed || 0}</div>
          <div class="stat-label">Workouts</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.form_checks || 0}</div>
          <div class="stat-label">Form Checks</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.meals_logged || 0}</div>
          <div class="stat-label">Meals Logged</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.personal_records || 0}</div>
          <div class="stat-label">Personal Records</div>
        </div>
      </div>

      <!-- Achievement Gallery -->
      <div class="section-divider"><span>Achievements (${achievements.filter(a => a.unlocked).length}/${achievements.length})</span></div>
      <div class="achievement-grid" style="margin-bottom:32px">
        ${achievements.length ? achievements.map(a => `
          <div class="achievement-card ${a.unlocked ? 'unlocked' : 'locked'}">
            <div class="achievement-icon">${a.icon || '&#127942;'}</div>
            <div class="achievement-name">${this._esc(a.name)}</div>
            <div class="achievement-desc">${this._esc(a.description || '')}</div>
            ${a.unlocked ? `<div style="font-size:10px;color:var(--accent-primary);font-weight:700;margin-top:6px">+${a.xp || 0} XP</div>` : ''}
          </div>
        `).join('') : `
          <div style="grid-column:1/-1;text-align:center;padding:32px;color:var(--text-muted)">
            <p>Achievements will appear here as you progress. Keep training!</p>
          </div>
        `}
      </div>

      <!-- Rewards -->
      ${rewards.length ? `
      <div class="section-divider"><span>Rewards (${player.coins || 0} coins available)</span></div>
      <div style="display:flex;flex-direction:column;gap:12px">
        ${rewards.map(r => `
          <div class="reward-card">
            <div class="reward-icon">${r.icon || '&#127873;'}</div>
            <div class="reward-info">
              <div class="reward-name">${this._esc(r.name)}</div>
              <div class="reward-cost">${r.cost} coins</div>
            </div>
            <button class="btn btn-sm ${(player.coins || 0) >= r.cost ? 'btn-primary' : 'btn-secondary'}"
              ${(player.coins || 0) < r.cost ? 'disabled' : ''}
              onclick="ProgressPage.redeemReward('${r.id}')">
              Redeem
            </button>
          </div>
        `).join('')}
      </div>
      ` : ''}
    `;
  },

  _renderStreakCalendar(streakDays) {
    const today = new Date();
    const dayHeaders = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

    // Build a 30-day grid
    const days = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      const isActive = streakDays.includes(dateStr);
      const isToday = i === 0;
      days.push({ date: d, dateStr, isActive, isToday, day: d.getDate() });
    }

    // Determine the starting day of week for the first date
    const firstDay = days[0].date.getDay();
    const startOffset = firstDay === 0 ? 6 : firstDay - 1; // Mon = 0

    // Pad beginning
    const paddedDays = [];
    for (let i = 0; i < startOffset; i++) {
      paddedDays.push(null);
    }
    paddedDays.push(...days);

    return `
      <div class="streak-calendar">
        ${dayHeaders.map(d => `<div class="streak-day-header">${d}</div>`).join('')}
        ${paddedDays.map(d => {
          if (!d) return '<div class="streak-day" style="opacity:0"></div>';
          let cls = 'streak-day';
          if (d.isActive) cls += ' active';
          if (d.isToday) cls += ' today';
          return `<div class="${cls}" title="${d.dateStr}">${d.day}</div>`;
        }).join('')}
      </div>
    `;
  },

  async redeemReward(rewardId) {
    try {
      const result = await API.post('/api/client/rewards/redeem', { reward_id: rewardId });
      Toast.success(result.message || 'Reward redeemed!');
      // Refresh data
      this.data = await API.get('/api/client/progress');
      this.render(document.getElementById('main-content'));
      App.loadUserInfo();
    } catch (err) {
      Toast.error(err.message);
    }
  },

  _esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
