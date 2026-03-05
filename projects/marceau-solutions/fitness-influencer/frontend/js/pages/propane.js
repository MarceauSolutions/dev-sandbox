/* ============================================================
   Propane Program Page — 12-week business build tracker
   ============================================================ */

const PropanePage = {
  STAGES: [
    { name: 'Foundation', weeks: '1-3', desc: 'Build your base' },
    { name: 'Brand & Content', weeks: '4-6', desc: 'Create your identity' },
    { name: 'Systems & Delivery', weeks: '7-9', desc: 'Build your machine' },
    { name: 'Launch', weeks: '10-12', desc: 'Go live' }
  ],

  SEED_TASKS: [
    { title: 'Complete onboarding call', week: 1, xp: 25, tags: ['propane', 'week-1'] },
    { title: 'Define ideal client avatar', week: 1, xp: 30, tags: ['propane', 'week-1'] },
    { title: 'Review existing assets & content', week: 1, xp: 15, tags: ['propane', 'week-1'] },
    { title: 'Complete niche workshop', week: 2, xp: 25, tags: ['propane', 'week-2'] },
    { title: 'Decide gym/online/hybrid model', week: 2, xp: 10, tags: ['propane', 'week-2'] },
    { title: 'Set up social media profiles', week: 3, xp: 20, tags: ['propane', 'week-3'] },
    { title: 'Finalize niche positioning statement', week: 4, xp: 25, tags: ['propane', 'week-4'] },
    { title: 'Create first ad creative', week: 4, xp: 40, tags: ['propane', 'week-4'] },
    { title: 'Determine primary content format', week: 5, xp: 15, tags: ['propane', 'week-5'] },
    { title: 'Outline selling system', week: 5, xp: 30, tags: ['propane', 'week-5'] },
    { title: 'First social media posts live', week: 6, xp: 20, tags: ['propane', 'week-6'] },
    { title: 'Build selling system end-to-end', week: 7, xp: 50, tags: ['propane', 'week-7'] },
    { title: 'Define pricing tier structure', week: 8, xp: 30, tags: ['propane', 'week-8'] },
    { title: 'Set up delivery platform', week: 8, xp: 40, tags: ['propane', 'week-8'] },
    { title: 'Build follow-up sequences', week: 9, xp: 35, tags: ['propane', 'week-9'] },
    { title: 'Complete full system build', week: 10, xp: 50, tags: ['propane', 'week-10'] },
    { title: 'Test everything end-to-end', week: 11, xp: 25, tags: ['propane', 'week-11'] },
    { title: 'Launch Meta ads', week: 11, xp: 75, tags: ['propane', 'week-11'] },
    { title: 'Get first leads', week: 12, xp: 50, tags: ['propane', 'week-12'] }
  ],

  allTasks: [],
  currentWeek: 1,

  async init() {
    // Load all tasks, check for propane tasks
    try {
      const data = await API.get('/api/tasks/');
      const tasks = Array.isArray(data) ? data : (data && data.tasks ? data.tasks : []);
      const propaneTasks = tasks.filter(t => t.tags && t.tags.includes('propane'));

      if (propaneTasks.length === 0) {
        await this._seedTasks();
        // Reload after seeding
        const refreshed = await API.get('/api/tasks/');
        this.allTasks = Array.isArray(refreshed) ? refreshed : (refreshed && refreshed.tasks ? refreshed.tasks : []);
      } else {
        this.allTasks = tasks;
      }
    } catch {
      this.allTasks = [];
    }
  },

  async _seedTasks() {
    for (const t of this.SEED_TASKS) {
      try {
        await API.post('/api/tasks/', {
          title: t.title,
          priority: 'medium',
          section: 'THIS_WEEK',
          tags: t.tags,
          xp_value: t.xp
        });
      } catch {}
    }
    Toast.success('Propane Program tasks created!');
  },

  render(container) {
    const propaneTasks = this.allTasks.filter(t => t.tags && t.tags.includes('propane'));
    const weekTasks = propaneTasks.filter(t => t.tags.includes('week-' + this.currentWeek));
    const completedAll = propaneTasks.filter(t => t.section === 'RECENTLY_DONE');
    const completedWeek = weekTasks.filter(t => t.section === 'RECENTLY_DONE');
    const totalXP = this.SEED_TASKS.reduce((s, t) => s + t.xp, 0);
    const earnedXP = completedAll.reduce((s, t) => s + (t.xp_value || 0), 0);

    const currentStage = this.currentWeek <= 3 ? 0 : this.currentWeek <= 6 ? 1 : this.currentWeek <= 9 ? 2 : 3;

    container.innerHTML = `
      <div class="page-header">
        <h1>&#x1F525; Propane Fitness Program</h1>
        <p>12-week business build &mdash; Stage ${currentStage + 1}: ${this.STAGES[currentStage].name}</p>
      </div>

      <!-- Stage Progress -->
      <div class="card" style="margin-bottom:24px">
        <div style="display:flex;gap:8px;margin-bottom:16px">
          ${this.STAGES.map((s, i) => `
            <div style="flex:1;text-align:center;padding:12px 8px;border-radius:var(--radius-md);
              background:${i === currentStage ? 'var(--accent-primary-dim)' : 'var(--surface-2)'};
              border:1px solid ${i === currentStage ? 'var(--accent-primary)' : 'var(--border-default)'};
              ${i < currentStage ? 'opacity:0.6' : ''}">
              <div style="font-size:10px;color:${i === currentStage ? 'var(--accent-primary)' : 'var(--text-muted)'};text-transform:uppercase;letter-spacing:0.08em;font-weight:700">Stage ${i + 1}</div>
              <div style="font-weight:700;font-size:13px;margin:4px 0">${s.name}</div>
              <div style="font-size:10px;color:var(--text-secondary)">Weeks ${s.weeks}</div>
            </div>
          `).join('')}
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" style="width:${totalXP > 0 ? Math.round(earnedXP / totalXP * 100) : 0}%"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:12px;color:var(--text-secondary)">
          <span>${earnedXP} / ${totalXP} XP earned</span>
          <span>${completedAll.length} / ${propaneTasks.length} tasks done</span>
        </div>
      </div>

      <!-- Week Tabs -->
      <div class="tabs" style="margin-bottom:20px;flex-wrap:wrap">
        ${[1,2,3,4,5,6,7,8,9,10,11,12].map(w => `
          <div class="tab ${w === this.currentWeek ? 'active' : ''}" onclick="PropanePage.switchWeek(${w})">W${w}</div>
        `).join('')}
      </div>

      <!-- Tasks for Current Week -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Week ${this.currentWeek} Tasks</div>
          <span class="badge">${completedWeek.length}/${weekTasks.length} done</span>
        </div>
        <div id="propane-tasks">
          ${weekTasks.length === 0 ?
            '<div class="empty-state"><p>No tasks for this week yet</p></div>' :
            weekTasks.map(t => this._renderTask(t)).join('')}
        </div>
      </div>
    `;
  },

  _renderTask(t) {
    const done = t.section === 'RECENTLY_DONE';
    const title = (t.title || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    return `
      <div style="display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border-muted)">
        <input type="checkbox" ${done ? 'checked disabled' : ''}
          onchange="PropanePage.completeTask('${t.id}', ${t.xp_value || 0}, '${title}')"
          style="accent-color:var(--accent-primary);width:18px;height:18px;cursor:pointer;flex-shrink:0">
        <div style="flex:1;${done ? 'text-decoration:line-through;opacity:0.5' : ''}">
          <div style="font-weight:600;font-size:14px">${t.title}</div>
        </div>
        <span class="badge ${done ? 'badge-success' : ''}">${t.xp_value || 0} XP</span>
      </div>
    `;
  },

  async switchWeek(week) {
    this.currentWeek = week;
    this.render(document.getElementById('main-content'));
  },

  async completeTask(taskId, xpValue, title) {
    try {
      // Move task to RECENTLY_DONE
      await API.put('/api/tasks/' + taskId, { section: 'RECENTLY_DONE' });

      // Log gamification action with XP override
      const result = await API.post('/api/gamification/player/action', {
        action: 'task_completed',
        tenant_id: 'wmarceau',
        metadata: { xp_override: xpValue, task_title: title }
      });

      const actionId = result && result.action_id;

      // Show undo toast
      Toast.showWithUndo(
        '+' + xpValue + ' XP \u2014 ' + title,
        actionId,
        async (aid) => {
          await API.put('/api/tasks/' + taskId, { section: 'THIS_WEEK' });
          await API.post('/api/gamification/player/undo', { action_id: aid, tenant_id: 'wmarceau' });
          // Update local state
          const task = this.allTasks.find(t => t.id === taskId);
          if (task) task.section = 'THIS_WEEK';
          this.render(document.getElementById('main-content'));
          App.loadXpBar();
        }
      );

      // Update local state
      const task = this.allTasks.find(t => t.id === taskId);
      if (task) task.section = 'RECENTLY_DONE';
      this.render(document.getElementById('main-content'));
      App.loadXpBar();
    } catch (err) {
      Toast.error('Failed to complete task: ' + err.message);
    }
  }
};
