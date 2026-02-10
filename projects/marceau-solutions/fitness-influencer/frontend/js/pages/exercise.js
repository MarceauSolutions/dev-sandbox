const ExercisePage = {
  title: 'Exercise Detection',
  _exercises: [],
  _categories: [],
  _activeCategory: null,
  _selectedExercises: new Set(),

  async init() {
    try {
      const [exercisesRes, categoriesRes] = await Promise.all([
        API.get('/api/video/detect-exercise/exercises'),
        API.get('/api/video/detect-exercise/categories')
      ]);
      this._exercises = exercisesRes.exercises || exercisesRes || [];
      this._categories = categoriesRes.categories || categoriesRes || [];
    } catch (err) {
      Toast.error('Failed to load exercise data: ' + err.message);
      this._exercises = [];
      this._categories = [];
    }
  },

  render(container) {
    const categoryTags = [
      '<span class="tag active" data-category="">All</span>',
      ...this._categories.map(c => {
        const id = typeof c === 'string' ? c : c.id || c.name;
        const label = typeof c === 'string' ? c : c.name || c.label || c.id;
        return `<span class="tag" data-category="${id}">${label}</span>`;
      })
    ].join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Exercise Detection</h1>
        <p>Detect and analyze exercises performed in your videos</p>
      </div>

      <form id="exercise-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('exercise-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Filter by Category</h2>
          </div>
          <div class="form-group">
            <div class="grid-auto" id="exercise-category-tags">
              ${categoryTags}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Select Exercises to Detect</h2>
            <span style="font-size:12px;color:var(--text-muted)" id="exercise-selected-count">0 selected</span>
          </div>
          <div class="form-hint" style="margin-bottom:12px">Click exercises to select which ones to look for. Leave empty to detect all.</div>
          <div class="grid-3" id="exercise-list">
            ${this._renderExerciseList()}
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="exercise-submit-btn">Detect Exercises</button>
      </form>

      <div id="exercise-results"></div>
    `;

    this._bindEvents(container);
  },

  _renderExerciseList(filter) {
    const filtered = filter
      ? this._exercises.filter(ex => {
          const cat = typeof ex === 'string' ? '' : ex.category || ex.group || '';
          return cat.toLowerCase() === filter.toLowerCase();
        })
      : this._exercises;

    if (!filtered.length) {
      return '<p style="color:var(--text-muted);grid-column:1/-1">No exercises found</p>';
    }

    return filtered.map(ex => {
      const id = typeof ex === 'string' ? ex : ex.id || ex.name;
      const name = typeof ex === 'string' ? ex : ex.name || ex.label || ex.id;
      const cat = typeof ex === 'string' ? '' : ex.category || ex.group || '';
      const isSelected = this._selectedExercises.has(id);
      return `
        <div class="tag${isSelected ? ' active' : ''}" data-exercise="${id}" style="cursor:pointer;text-align:center;padding:8px 12px">
          <div style="font-weight:500">${name}</div>
          ${cat ? `<div style="font-size:11px;opacity:0.7;margin-top:2px">${cat}</div>` : ''}
        </div>`;
    }).join('');
  },

  _updateSelectedCount(container) {
    const countEl = container.querySelector('#exercise-selected-count');
    if (countEl) {
      const count = this._selectedExercises.size;
      countEl.textContent = count ? `${count} selected` : '0 selected';
    }
  },

  _bindEvents(container) {
    // Category filter
    const categoryTags = container.querySelector('#exercise-category-tags');
    if (categoryTags) {
      categoryTags.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag) return;
        categoryTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        this._activeCategory = tag.dataset.category || null;

        const listEl = container.querySelector('#exercise-list');
        if (listEl) {
          listEl.innerHTML = this._renderExerciseList(this._activeCategory);
        }
      });
    }

    // Exercise selection (toggle)
    const exerciseList = container.querySelector('#exercise-list');
    if (exerciseList) {
      exerciseList.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag || !tag.dataset.exercise) return;

        const id = tag.dataset.exercise;
        if (this._selectedExercises.has(id)) {
          this._selectedExercises.delete(id);
          tag.classList.remove('active');
        } else {
          this._selectedExercises.add(id);
          tag.classList.add('active');
        }
        this._updateSelectedCount(container);
      });
    }

    App.formHandler('exercise-form', 'exercise-submit-btn', async () => {
      const videoUrl = container.querySelector('#exercise-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl
      };

      if (this._selectedExercises.size > 0) {
        payload.target_exercises = Array.from(this._selectedExercises);
      }

      const res = await API.post('/api/video/detect-exercise', payload);

      if (res.job_id) {
        JobPoller.startPolling(res.job_id, {
          onComplete: (data) => this._renderResults(container, data.result)
        });
        Toast.success('Exercise detection started!');
      } else {
        this._renderResults(container, res);
        Toast.success('Detection complete.');
      }
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#exercise-results');
    if (!resultsEl) return;

    const detections = data?.detections || data?.exercises || data?.results || [];

    if (!detections.length) {
      resultsEl.innerHTML = `
        <div class="card" style="margin-top:24px">
          <p style="color:var(--text-muted)">No exercises detected in the video.</p>
        </div>`;
      return;
    }

    resultsEl.innerHTML = `
      <div class="section-divider" style="margin-top:24px"><span>Detection Results</span></div>

      <div class="grid-3" style="margin-bottom:16px">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">${detections.length}</div>
          <div class="stat-label">Exercises Found</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-secondary)">${detections.reduce((sum, d) => sum + (d.rep_count || 0), 0)}</div>
          <div class="stat-label">Total Reps</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-processing)">${Math.round(detections.reduce((sum, d) => sum + (d.confidence || 0), 0) / detections.length * 100)}%</div>
          <div class="stat-label">Avg Confidence</div>
        </div>
      </div>

      <div class="card" style="padding:0">
        <div class="table-wrap">
          <table style="width:100%;border-collapse:collapse">
            <thead>
              <tr style="border-bottom:1px solid var(--border-subtle);text-align:left">
                <th style="padding:12px 16px;font-weight:600">Exercise</th>
                <th style="padding:12px 16px;font-weight:600">Confidence</th>
                <th style="padding:12px 16px;font-weight:600">Timestamps</th>
                <th style="padding:12px 16px;font-weight:600;text-align:right">Reps</th>
              </tr>
            </thead>
            <tbody>
              ${detections.map(d => {
                const name = d.name || d.exercise || d.label || 'Unknown';
                const confidence = d.confidence != null ? (d.confidence * 100).toFixed(1) + '%' : '--';
                const timestamps = d.timestamps || d.time_range || '';
                const tsDisplay = Array.isArray(timestamps)
                  ? timestamps.map(t => typeof t === 'object' ? `${t.start || ''}–${t.end || ''}` : t).join(', ')
                  : timestamps;
                const reps = d.rep_count != null ? d.rep_count : d.reps != null ? d.reps : '--';
                const confVal = d.confidence || 0;
                const confColor = confVal >= 0.9 ? 'var(--accent-primary)' : confVal >= 0.7 ? 'var(--status-processing)' : 'var(--status-failed)';
                return `
                  <tr style="border-bottom:1px solid var(--border-subtle)">
                    <td style="padding:10px 16px;font-weight:500">${name}</td>
                    <td style="padding:10px 16px;color:${confColor}">${confidence}</td>
                    <td style="padding:10px 16px;color:var(--text-secondary);font-size:13px">${tsDisplay || '--'}</td>
                    <td style="padding:10px 16px;text-align:right;font-weight:600">${reps}</td>
                  </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  destroy() {
    this._exercises = [];
    this._categories = [];
    this._activeCategory = null;
    this._selectedExercises = new Set();
  }
};
