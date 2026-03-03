const GamificationPage = {
  title: 'Gamification',
  _player: null,
  _quests: [],
  _achievements: [],
  _rewards: [],
  _stats: null,

  ACHIEVEMENT_ICONS: {
    first_steps: '&#x1F463;', week_warrior: '&#9876;&#65039;', consistency_king: '&#x1F451;',
    month_master: '&#x1F4C5;', quarter_champion: '&#x1F3C6;', yearly_legend: '&#11088;',
    first_sale: '&#x1F4B5;', '5k_goal': '&#x1F48E;', '10k_goal': '&#x1F4B0;',
    '50k_goal': '&#x1F3AF;', '100k_goal': '&#x1F680;',
    first_post: '&#x1F4F1;', week_streak: '&#x1F525;', month_streak: '&#x1F451;',
    first_client: '&#x1F91D;', level_5: '&#11088;', level_10: '&#x1F680;'
  },

  ACTIONS: [
    { id: 'post',           icon: '&#x1F4F1;', label: 'Posted Content',  xp: 15 },
    { id: 'comment',        icon: '&#x1F4AC;', label: 'Comments',        xp: 10 },
    { id: 'dm',             icon: '&#9993;&#65039;',  label: 'Checked DMs',     xp: 10 },
    { id: 'story',          icon: '&#x1F4F8;', label: 'Posted Story',    xp: 15 },
    { id: 'engage',         icon: '&#x1F44D;', label: 'Engaged 5 Posts', xp: 10 },
    { id: 'consultation',   icon: '&#x1F4DE;', label: 'Consultation',    xp: 100 },
    { id: 'client_signed',  icon: '&#x1F91D;', label: 'Client Signed',   xp: 500 },
    { id: 'revenue',        icon: '&#x1F4B0;', label: 'Revenue Goal',    xp: 200 }
  ],

  async init() {
    try {
      const [playerRes, questsRes, achievementsRes, rewardsRes, statsRes] = await Promise.allSettled([
        API.get('/api/gamification/player/stats?tenant_id=wmarceau'),
        API.get('/api/gamification/quests/daily'),
        API.get('/api/gamification/achievements'),
        API.get('/api/gamification/rewards'),
        API.get('/api/gamification/stats/summary?tenant_id=wmarceau')
      ]);
      this._player = playerRes.status === 'fulfilled' ? playerRes.value : null;
      this._quests = questsRes.status === 'fulfilled' ? (questsRes.value.quests || questsRes.value || []) : [];
      this._achievements = achievementsRes.status === 'fulfilled' ? (achievementsRes.value.achievements || achievementsRes.value || []) : [];
      this._rewards = rewardsRes.status === 'fulfilled' ? (rewardsRes.value.rewards || rewardsRes.value || []) : [];
      this._stats = statsRes.status === 'fulfilled' ? statsRes.value : null;
    } catch {
      this._player = null;
      this._quests = [];
      this._achievements = [];
      this._rewards = [];
      this._stats = null;
    }
  },

  render(container) {
    const p = this._player || {};
    const level = p.level || 1;
    const title = p.title || 'Aspiring Coach';
    const xp = p.xp || p.experience || 0;
    const xpNext = p.next_level_xp || p.xp_to_next || (level * 100);
    const xpPercent = Math.min(100, Math.round((xp / xpNext) * 100));
    const coins = p.coins || p.currency || 0;
    const streak = p.current_streak || p.streak || p.daily_streak || 0;
    const bestStreak = p.best_streak || streak;
    const multiplier = p.streak_multiplier || p.multiplier || '1.0';

    const stats = this._stats || p.stats || {};
    const totalPosts = stats.total_posts || 0;
    const totalClients = stats.total_clients || 0;
    const totalRevenue = stats.total_revenue || 0;

    container.innerHTML = `
      <div class="page-header">
        <h1>Gamification</h1>
        <p>Level up your fitness coaching career</p>
      </div>

      <!-- Player Profile Card -->
      <div class="card" style="margin-bottom:24px">
        <div class="card-header">
          <span class="card-title">Player Profile</span>
          <span class="tag active">Level ${level} - ${title}</span>
        </div>

        <div class="grid-4" style="margin-bottom:16px">
          <div class="stat-card">
            <div class="stat-value" style="color:var(--accent-primary)">${xp.toLocaleString()}</div>
            <div class="stat-label">XP</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color:var(--accent-secondary)">${coins.toLocaleString()}</div>
            <div class="stat-label">Coins</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color:var(--status-processing)">${streak} &#x1F525;</div>
            <div class="stat-label">Streak</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="color:var(--accent-primary)">${multiplier}x</div>
            <div class="stat-label">Multiplier</div>
          </div>
        </div>

        <div style="margin-top:12px">
          <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted);margin-bottom:4px">
            <span>Level ${level}</span>
            <span>${xp.toLocaleString()} / ${xpNext.toLocaleString()} XP (${xpPercent}%)</span>
            <span>Level ${level + 1}</span>
          </div>
          <div class="job-progress" style="height:12px;border-radius:6px">
            <div class="job-progress-fill" style="width:${xpPercent}%"></div>
          </div>
        </div>
      </div>

      <!-- Quick Actions (8 buttons) -->
      <div class="section-divider"><span>Log Action</span></div>

      <div class="card" style="margin-bottom:24px">
        <div class="grid-4" id="gamification-actions">
          ${this.ACTIONS.map(a => `
            <button class="btn ${a.xp >= 100 ? 'btn-primary' : 'btn-secondary'}" data-action="${a.id}" style="width:100%;display:flex;flex-direction:column;align-items:center;gap:4px;padding:12px 8px">
              <span style="font-size:20px">${a.icon}</span>
              <span style="font-size:12px;font-weight:500">${a.label}</span>
              <span style="font-size:11px;opacity:0.7">+${a.xp} XP</span>
            </button>
          `).join('')}
        </div>
      </div>

      <div class="grid-2">
        <!-- Daily Quests -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Daily Quests</h2>
            <span class="tag" id="gamification-quest-progress">${this._quests.filter(q => q.completed).length}/${this._quests.length}</span>
          </div>
          <div id="gamification-quest-list">
            ${this._renderQuests()}
          </div>
          <div style="text-align:center;margin-top:12px;padding:10px;background:rgba(255,215,0,0.08);border-radius:8px">
            <span style="color:var(--accent-secondary);font-size:13px">&#x1F3C6; Complete all for +50 XP bonus!</span>
          </div>
        </div>

        <!-- Streak & Stats -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Streak</h2>
          </div>
          <div style="text-align:center;padding:16px 0">
            <div style="font-size:40px">&#x1F525;</div>
            <div style="font-size:28px;font-weight:700;color:var(--status-processing)">${streak} Days</div>
            <div style="font-size:13px;color:var(--accent-secondary);margin-top:6px">${this._getStreakMessage(streak, bestStreak)}</div>
          </div>
          <div class="grid-3" style="gap:8px;margin-top:8px">
            <div class="stat-card" style="padding:10px">
              <div class="stat-value" style="font-size:18px;color:var(--accent-secondary)">${totalPosts}</div>
              <div class="stat-label" style="font-size:11px">Total Posts</div>
            </div>
            <div class="stat-card" style="padding:10px">
              <div class="stat-value" style="font-size:18px;color:var(--accent-secondary)">${totalClients}</div>
              <div class="stat-label" style="font-size:11px">Clients</div>
            </div>
            <div class="stat-card" style="padding:10px">
              <div class="stat-value" style="font-size:18px;color:var(--accent-secondary)">$${totalRevenue.toLocaleString()}</div>
              <div class="stat-label" style="font-size:11px">Revenue</div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid-2" style="margin-top:24px">
        <!-- Achievements -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Achievements</h2>
            <span class="tag" id="gamification-ach-count">${this._achievements.filter(a => a.unlocked).length}/${this._achievements.length}</span>
          </div>
          <div class="grid-3" style="gap:8px">
            ${this._renderAchievements()}
          </div>
        </div>

        <!-- Rewards Shop -->
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Rewards Shop</h2>
            <span class="tag active" id="gamification-coin-balance">&#x1F4B0; ${coins} coins</span>
          </div>
          <div id="gamification-rewards-list">
            ${this._renderRewards(coins)}
          </div>
        </div>
      </div>
    `;

    this._bindEvents(container);
  },

  _renderQuests() {
    if (!this._quests.length) {
      return '<div style="color:var(--text-muted);font-size:13px;padding:12px 0">No daily quests available</div>';
    }
    return this._quests.map(q => `
      <div class="job-item" style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-default);cursor:pointer;opacity:${q.completed ? '0.6' : '1'}" data-quest-id="${q.id}">
        <span style="font-size:20px;width:24px;height:24px;display:flex;align-items:center;justify-content:center;border-radius:50%;border:2px solid ${q.completed ? 'var(--accent-primary)' : 'var(--text-muted)'};background:${q.completed ? 'var(--accent-primary)' : 'transparent'};color:${q.completed ? '#fff' : 'transparent'};font-size:12px">${q.completed ? '&#10003;' : ''}</span>
        <div style="flex:1">
          <div style="font-weight:600">${q.title || q.name}</div>
          <div style="font-size:12px;color:var(--text-muted)">${q.description || ''}</div>
        </div>
        <span class="tag" style="color:var(--accent-secondary)">${q.xp_reward || q.reward || 0} XP</span>
      </div>
    `).join('');
  },

  _renderAchievements() {
    if (!this._achievements.length) {
      return '<div style="color:var(--text-muted);font-size:13px;grid-column:1/-1">No achievements yet</div>';
    }
    return this._achievements.map(a => {
      const icon = this.ACHIEVEMENT_ICONS[a.id] || a.icon || '&#x1F3C5;';
      return `
        <div class="stat-card" style="text-align:center;opacity:${a.unlocked ? '1' : '0.35'};${a.unlocked ? '' : 'filter:grayscale(1);'}cursor:default" title="${a.description || ''}">
          <div style="font-size:28px;margin-bottom:4px">${icon}</div>
          <div style="font-weight:600;font-size:12px">${a.title || a.name}</div>
        </div>`;
    }).join('');
  },

  _renderRewards(coins) {
    if (!this._rewards.length) {
      return '<div style="color:var(--text-muted);font-size:13px;padding:12px 0">No rewards available</div>';
    }
    return this._rewards.map(r => {
      const cost = r.cost || r.price || 0;
      const canAfford = coins >= cost;
      return `
        <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-default)">
          <span style="font-size:22px;width:36px;text-align:center">${r.icon || '&#x1F381;'}</span>
          <div style="flex:1">
            <div style="font-weight:600;font-size:13px">${r.name}</div>
            <div style="font-size:12px;color:var(--accent-secondary)">${cost} coins</div>
          </div>
          <button class="btn btn-primary" data-reward-id="${r.id}" style="padding:6px 14px;font-size:12px" ${canAfford ? '' : 'disabled'}>Buy</button>
        </div>`;
    }).join('');
  },

  _getStreakMessage(streak, bestStreak) {
    const best = bestStreak > streak ? ` Best: ${bestStreak} days` : '';
    if (streak >= 30) return `&#x1F525; 3x XP Multiplier Active!${best}`;
    if (streak >= 14) return `&#x1F525; 2x XP Multiplier Active!${best}`;
    if (streak >= 7) return `&#x1F525; 1.5x XP Multiplier Active!${best}`;
    if (streak >= 3) return `&#x1F525; 1.25x XP Multiplier Active!${best}`;
    return 'Keep a 3+ day streak for bonus XP!';
  },

  async _refreshAndRender(container) {
    try {
      const [playerRes, questsRes, rewardsRes, statsRes] = await Promise.allSettled([
        API.get('/api/gamification/player/stats?tenant_id=wmarceau'),
        API.get('/api/gamification/quests/daily'),
        API.get('/api/gamification/rewards'),
        API.get('/api/gamification/stats/summary?tenant_id=wmarceau')
      ]);
      if (playerRes.status === 'fulfilled') this._player = playerRes.value;
      if (questsRes.status === 'fulfilled') this._quests = questsRes.value.quests || questsRes.value || [];
      if (rewardsRes.status === 'fulfilled') this._rewards = rewardsRes.value.rewards || rewardsRes.value || [];
      if (statsRes.status === 'fulfilled') this._stats = statsRes.value;
    } catch {}
    const target = container.closest('#main-content') || container.parentElement || document.querySelector('#main-content');
    this.render(target);
  },

  _bindEvents(container) {
    // Action buttons
    const actionsEl = container.querySelector('#gamification-actions');
    if (actionsEl) {
      actionsEl.addEventListener('click', async (e) => {
        const btn = e.target.closest('[data-action]');
        if (!btn || btn.disabled) return;

        const action = btn.dataset.action;
        btn.disabled = true;
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;display:inline-block"></div>';

        try {
          const res = await API.post('/api/gamification/player/action', {
            action_type: action,
            action: action,
            tenant_id: 'wmarceau'
          });

          const xpGained = res.xp_earned || res.xp_gained || res.xp || 0;
          const coinsGained = res.coins_earned || res.coins_gained || res.coins || 0;
          Toast.success(`+${xpGained} XP${coinsGained ? `, +${coinsGained} coins` : ''}!`);

          if (res.level_up) {
            Toast.success('Level Up! You are now level ' + (res.new_level || res.level));
          }

          await this._refreshAndRender(container);
        } catch (err) {
          Toast.error('Failed to record action: ' + err.message);
          btn.disabled = false;
          btn.innerHTML = originalHTML;
        }
      });
    }

    // Quest completion
    const questList = container.querySelector('#gamification-quest-list');
    if (questList) {
      questList.addEventListener('click', async (e) => {
        const item = e.target.closest('[data-quest-id]');
        if (!item) return;

        const questId = item.dataset.questId;
        const quest = this._quests.find(q => q.id === questId);
        if (!quest || quest.completed) return;

        item.style.opacity = '0.5';
        item.style.pointerEvents = 'none';

        try {
          const res = await API.post(`/api/gamification/quests/${questId}/complete`, {
            tenant_id: 'wmarceau'
          });
          const xpEarned = res.xp_earned || res.xp || 0;
          Toast.success(`Quest complete! +${xpEarned} XP`);
          await this._refreshAndRender(container);
        } catch (err) {
          Toast.error(err.message || 'Failed to complete quest');
          item.style.opacity = '1';
          item.style.pointerEvents = '';
        }
      });
    }

    // Reward purchase
    const rewardsList = container.querySelector('#gamification-rewards-list');
    if (rewardsList) {
      rewardsList.addEventListener('click', async (e) => {
        const btn = e.target.closest('[data-reward-id]');
        if (!btn || btn.disabled) return;

        const rewardId = btn.dataset.rewardId;
        btn.disabled = true;
        const origText = btn.textContent;
        btn.textContent = '...';

        try {
          const res = await API.post('/api/gamification/rewards/purchase', {
            reward_id: rewardId,
            tenant_id: 'wmarceau'
          });
          Toast.success(`&#x1F389; ${res.reward_name || 'Reward'} purchased!`);
          await this._refreshAndRender(container);
        } catch (err) {
          Toast.error(err.message || 'Failed to purchase reward');
          btn.disabled = false;
          btn.textContent = origText;
        }
      });
    }
  },

  destroy() {
    this._player = null;
    this._quests = [];
    this._achievements = [];
    this._rewards = [];
    this._stats = null;
  }
};
