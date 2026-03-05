/* ============================================================
   Workouts Page — Client Portal
   Weekly workout view with exercise details
   ============================================================ */

const WorkoutsPage = {
  title: 'My Workouts',
  weekData: null,
  activeTab: 'current',
  expandedDay: null,

  async init() {
    try {
      this.weekData = await API.get('/api/client/workouts/current-week');
    } catch (err) {
      console.warn('Workouts init:', err.message);
      this.weekData = null;
    }
  },

  render(container) {
    const week = this.weekData || {};
    const days = week.days || [];
    const todayIndex = new Date().getDay(); // 0=Sun
    // Map to Mon=0 ... Sun=6
    const todayMapped = todayIndex === 0 ? 6 : todayIndex - 1;
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    container.innerHTML = `
      <div class="page-header">
        <h1>My Workouts</h1>
        <p>${week.week_label || 'This Week'}</p>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button class="tab ${this.activeTab === 'current' ? 'active' : ''}" onclick="WorkoutsPage.switchTab('current')">This Week</button>
        <button class="tab ${this.activeTab === 'history' ? 'active' : ''}" onclick="WorkoutsPage.switchTab('history')">History</button>
      </div>

      <div id="workouts-content">
        ${this.activeTab === 'current' ? this._renderCurrentWeek(days, dayNames, todayMapped) : ''}
      </div>
    `;

    if (this.activeTab === 'history') {
      this._loadHistory();
    }
  },

  _renderCurrentWeek(days, dayNames, todayMapped) {
    if (!days.length) {
      // Generate placeholder cards for the week
      return `
        <div style="display:flex;flex-direction:column;gap:12px">
          ${dayNames.map((name, i) => `
            <div class="workout-card ${i === todayMapped ? 'today' : ''}">
              <div class="workout-day-label">${name}</div>
              <div class="workout-name" style="color:var(--text-muted)">Rest Day</div>
              <div class="workout-meta">
                <span>No workout scheduled</span>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    return `
      <div style="display:flex;flex-direction:column;gap:12px">
        ${days.map((day, i) => {
          const isToday = i === todayMapped;
          const isCompleted = day.completed;
          const isRest = !day.workout;
          const isExpanded = this.expandedDay === i;

          if (isRest) {
            return `
              <div class="workout-card ${isToday ? 'today' : ''}">
                <div class="workout-day-label">${dayNames[i] || 'Day ' + (i + 1)}</div>
                <div class="workout-name" style="color:var(--text-muted)">Rest Day</div>
                <div class="workout-meta">
                  <span>Recovery & flexibility</span>
                </div>
              </div>
            `;
          }

          const w = day.workout;
          return `
            <div class="workout-card ${isToday ? 'today' : ''} ${isCompleted ? 'completed' : ''}"
                 onclick="WorkoutsPage.toggleExpand(${i})">
              <div class="workout-day-label">${dayNames[i] || 'Day ' + (i + 1)} ${isCompleted ? '&#9989;' : ''}</div>
              <div class="workout-name">${this._esc(w.name || 'Workout')}</div>
              <div class="workout-meta">
                <span>${w.exercise_count || (w.exercises || []).length} exercises</span>
                <span>~${w.est_duration || 45} min</span>
                <span class="workout-xp">+${w.xp_reward || 50} XP</span>
              </div>

              ${isExpanded ? `
              <div class="exercise-list">
                ${(w.exercises || []).map(ex => `
                  <div class="exercise-item">
                    <div>
                      <div class="exercise-name">${this._esc(ex.name)}</div>
                      ${ex.form_cue ? `<div class="exercise-cue">${this._esc(ex.form_cue)}</div>` : ''}
                    </div>
                    <div class="exercise-detail">
                      ${ex.sets ? ex.sets + ' x ' : ''}${ex.reps || ex.duration || ''}${ex.rest ? ' &middot; ' + ex.rest + 's rest' : ''}
                    </div>
                  </div>
                `).join('')}
              </div>
              ${!isCompleted ? `
              <div style="margin-top:16px;text-align:center">
                <button class="btn btn-primary" onclick="event.stopPropagation(); WorkoutsPage.completeWorkout('${w.id || i}', ${i})">
                  Mark Complete
                </button>
              </div>
              ` : ''}
              ` : `
              <div style="margin-top:8px;font-size:11px;color:var(--text-muted)">Click to expand</div>
              `}
            </div>
          `;
        }).join('')}
      </div>
    `;
  },

  toggleExpand(index) {
    this.expandedDay = this.expandedDay === index ? null : index;
    // Re-render content area only
    const content = document.getElementById('workouts-content');
    if (content && this.activeTab === 'current') {
      const week = this.weekData || {};
      const days = week.days || [];
      const todayIndex = new Date().getDay();
      const todayMapped = todayIndex === 0 ? 6 : todayIndex - 1;
      const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      content.innerHTML = this._renderCurrentWeek(days, dayNames, todayMapped);
    }
  },

  async completeWorkout(workoutId, dayIndex) {
    try {
      const result = await API.post('/api/client/workouts/' + workoutId + '/complete');
      const xp = result.xp_earned || 50;

      // Show undo toast
      Toast.showWithUndo(
        `Workout complete! +${xp} XP`,
        workoutId,
        async (id) => {
          await API.post('/api/client/workouts/' + id + '/uncomplete');
        }
      );

      // Update local state
      if (this.weekData && this.weekData.days && this.weekData.days[dayIndex]) {
        this.weekData.days[dayIndex].completed = true;
      }

      App.loadUserInfo();

      // Re-render
      const content = document.getElementById('workouts-content');
      if (content && this.activeTab === 'current') {
        const days = (this.weekData || {}).days || [];
        const todayIndex = new Date().getDay();
        const todayMapped = todayIndex === 0 ? 6 : todayIndex - 1;
        const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        content.innerHTML = this._renderCurrentWeek(days, dayNames, todayMapped);
      }
    } catch (err) {
      Toast.error(err.message);
    }
  },

  switchTab(tab) {
    this.activeTab = tab;
    this.render(document.getElementById('main-content'));
  },

  async _loadHistory() {
    const content = document.getElementById('workouts-content');
    content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div> Loading history...</div>';

    try {
      const history = await API.get('/api/client/workouts/history');
      const weeks = history.weeks || [];

      if (!weeks.length) {
        content.innerHTML = `
          <div class="empty-state">
            <p>No workout history yet. Complete your first workout to see it here!</p>
          </div>
        `;
        return;
      }

      content.innerHTML = weeks.map(week => `
        <div class="card" style="margin-bottom:12px">
          <div class="card-header">
            <div class="card-title">${this._esc(week.label || 'Week')}</div>
            <span class="badge badge-gold">${week.completed || 0}/${week.total || 0} completed</span>
          </div>
          <div class="progress-bar-container" style="margin-bottom:12px">
            <div class="progress-bar" style="width:${week.total ? Math.round((week.completed / week.total) * 100) : 0}%"></div>
          </div>
          <div style="font-size:12px;color:var(--text-secondary)">
            ${week.xp_earned || 0} XP earned
          </div>
        </div>
      `).join('');
    } catch (err) {
      content.innerHTML = `<div class="empty-state"><p>Unable to load history: ${this._esc(err.message)}</p></div>`;
    }
  },

  _esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};
