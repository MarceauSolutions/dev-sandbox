const TasksPage = {
  title: 'Task Manager',
  _tasks: [],
  _stats: null,

  async init() {
    try {
      const [tasksRes, statsRes] = await Promise.allSettled([
        API.get('/api/tasks/'),
        API.get('/api/tasks/stats/summary')
      ]);
      this._tasks = tasksRes.status === 'fulfilled' ? (tasksRes.value.tasks || tasksRes.value || []) : [];
      this._stats = statsRes.status === 'fulfilled' ? statsRes.value : null;
    } catch {
      this._tasks = [];
      this._stats = null;
    }
  },

  render(container) {
    const stats = this._stats || {};
    const total = stats.total || this._tasks.length;
    const completed = stats.completed || this._tasks.filter(t => t.section === 'completed' || t.completed).length;
    const pending = stats.pending || (total - completed);

    const sections = ['today', 'this_week', 'circle_back', 'completed'];
    const sectionLabels = {
      today: 'Today',
      this_week: 'This Week',
      circle_back: 'Circle Back',
      completed: 'Completed'
    };

    container.innerHTML = `
      <div class="page-header">
        <h1>Task Manager</h1>
        <p>Stay on top of your content workflow</p>
      </div>

      <div class="grid-3" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">${total}</div>
          <div class="stat-label">Total Tasks</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-processing)">${pending}</div>
          <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-completed)">${completed}</div>
          <div class="stat-label">Completed</div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px">
        <div class="card-header">
          <h2 class="card-title">Add Task</h2>
        </div>
        <form id="task-add-form">
          <div class="grid-3">
            <div class="form-group" style="grid-column:span 1">
              <label class="form-label" for="task-content">Task</label>
              <input class="form-input" type="text" id="task-content" name="content" placeholder="What needs to be done?" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="task-section">Section</label>
              <select class="form-select" id="task-section" name="section">
                <option value="today">Today</option>
                <option value="this_week">This Week</option>
                <option value="circle_back">Circle Back</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" for="task-priority">Priority</label>
              <select class="form-select" id="task-priority" name="priority">
                <option value="low">Low</option>
                <option value="medium" selected>Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
          <button type="submit" class="btn btn-primary" id="task-add-btn">Add Task</button>
        </form>
      </div>

      <div id="task-sections">
        ${sections.map(section => this._renderSection(section, sectionLabels[section])).join('')}
      </div>
    `;

    this._bindEvents(container);
  },

  _renderSection(section, label) {
    const tasks = this._tasks.filter(t => {
      if (section === 'completed') return t.section === 'completed' || t.completed;
      return t.section === section && !t.completed;
    });

    return `
      <div class="card" style="margin-bottom:16px">
        <div class="card-header">
          <h2 class="card-title">${label}</h2>
          <span style="font-size:12px;color:var(--text-muted)">${tasks.length} task${tasks.length !== 1 ? 's' : ''}</span>
        </div>
        <div class="task-list" data-section="${section}">
          ${tasks.length ? tasks.map(t => `
            <div class="job-item" data-id="${t.id}" style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border)">
              <span style="flex:1;${section === 'completed' ? 'text-decoration:line-through;opacity:0.6' : ''}">${t.content || t.title || t.text}</span>
              ${t.priority ? `<span class="tag${t.priority === 'high' ? ' active' : ''}" style="font-size:11px">${t.priority}</span>` : ''}
              ${section !== 'completed' ? `
                <button class="btn btn-sm btn-ghost task-complete-btn" data-id="${t.id}" title="Complete">&#10003;</button>
              ` : ''}
              <button class="btn btn-sm btn-ghost task-delete-btn" data-id="${t.id}" title="Delete">&#10005;</button>
            </div>
          `).join('') : `
            <div style="padding:12px 0;color:var(--text-muted);font-size:13px">No tasks in this section</div>
          `}
        </div>
      </div>
    `;
  },

  _bindEvents(container) {
    App.formHandler('task-add-form', 'task-add-btn', async () => {
      const content = container.querySelector('#task-content').value.trim();
      const section = container.querySelector('#task-section').value;
      const priority = container.querySelector('#task-priority').value;

      if (!content) { Toast.error('Please enter a task'); return; }

      const res = await API.post('/api/tasks/', { content, section, priority });
      Toast.success('Task added');
      this._tasks.unshift(res.task || res);
      container.querySelector('#task-content').value = '';
      this._refreshSections(container);
    });

    container.querySelector('#task-sections').addEventListener('click', async (e) => {
      const completeBtn = e.target.closest('.task-complete-btn');
      if (completeBtn) {
        const id = completeBtn.dataset.id;
        try {
          await API.post('/api/tasks/' + id + '/complete');
          Toast.success('Task completed');
          const task = this._tasks.find(t => String(t.id) === String(id));
          if (task) { task.section = 'completed'; task.completed = true; }
          this._refreshSections(container);
        } catch (err) {
          Toast.error('Failed to complete task: ' + err.message);
        }
        return;
      }

      const deleteBtn = e.target.closest('.task-delete-btn');
      if (deleteBtn) {
        const id = deleteBtn.dataset.id;
        try {
          await API.delete('/api/tasks/' + id);
          Toast.success('Task deleted');
          this._tasks = this._tasks.filter(t => String(t.id) !== String(id));
          this._refreshSections(container);
        } catch (err) {
          Toast.error('Failed to delete task: ' + err.message);
        }
      }
    });
  },

  _refreshSections(container) {
    const sectionsEl = container.querySelector('#task-sections');
    if (!sectionsEl) return;

    const sections = ['today', 'this_week', 'circle_back', 'completed'];
    const sectionLabels = {
      today: 'Today',
      this_week: 'This Week',
      circle_back: 'Circle Back',
      completed: 'Completed'
    };

    sectionsEl.innerHTML = sections.map(s => this._renderSection(s, sectionLabels[s])).join('');
  },

  destroy() {
    this._tasks = [];
    this._stats = null;
  }
};
