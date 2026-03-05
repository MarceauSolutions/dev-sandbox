/* ============================================================
   Form Check Page — Client Portal
   Upload video for form analysis
   ============================================================ */

const FormCheckPage = {
  title: 'Form Check',
  history: [],
  activeTab: 'upload',

  async init() {
    try {
      const data = await API.get('/api/client/form-check/history');
      this.history = data.checks || [];
    } catch (err) {
      console.warn('Form check init:', err.message);
      this.history = [];
    }
  },

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Form Check</h1>
        <p>Upload a video of your exercise and get AI-powered form analysis</p>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button class="tab ${this.activeTab === 'upload' ? 'active' : ''}" onclick="FormCheckPage.switchTab('upload')">New Check</button>
        <button class="tab ${this.activeTab === 'history' ? 'active' : ''}" onclick="FormCheckPage.switchTab('history')">History (${this.history.length})</button>
      </div>

      <div id="form-check-content">
        ${this.activeTab === 'upload' ? this._renderUpload() : this._renderHistory()}
      </div>
    `;
  },

  _renderUpload() {
    return `
      <div class="card">
        <form id="form-check-form">
          <!-- Exercise Selector -->
          <div class="form-group">
            <label class="form-label">Exercise</label>
            <select id="fc-exercise" class="form-select" required>
              <option value="">Select exercise...</option>
              <option value="squat">Barbell Squat</option>
              <option value="deadlift">Deadlift</option>
              <option value="bench_press">Bench Press</option>
              <option value="overhead_press">Overhead Press</option>
              <option value="barbell_row">Barbell Row</option>
              <option value="pull_up">Pull-up</option>
              <option value="push_up">Push-up</option>
              <option value="lunge">Lunge</option>
              <option value="romanian_deadlift">Romanian Deadlift</option>
              <option value="hip_thrust">Hip Thrust</option>
              <option value="bicep_curl">Bicep Curl</option>
              <option value="lateral_raise">Lateral Raise</option>
              <option value="plank">Plank</option>
              <option value="other">Other</option>
            </select>
          </div>

          <!-- Video Upload -->
          <div class="form-group">
            <label class="form-label">Video</label>
            <div class="upload-zone" id="fc-upload-zone" onclick="document.getElementById('fc-video-input').click()">
              <div style="font-size:32px;margin-bottom:12px">&#127909;</div>
              <div class="upload-text">
                <span class="upload-browse">Click to upload</span> or drag and drop
              </div>
              <div class="upload-hint">MP4, MOV up to 100MB &middot; 10-60 seconds recommended</div>
            </div>
            <input type="file" id="fc-video-input" accept="video/*" style="display:none" onchange="FormCheckPage.onFileSelect(this)">
            <div id="fc-file-name" style="margin-top:8px;font-size:12px;color:var(--text-secondary);display:none"></div>
          </div>

          <!-- Notes -->
          <div class="form-group">
            <label class="form-label">Notes (optional)</label>
            <textarea id="fc-notes" class="form-textarea" placeholder="Any specific concerns? e.g., knee caving, lower back rounding..." rows="2"></textarea>
          </div>

          <button type="submit" id="fc-submit" class="btn btn-primary btn-lg" style="width:100%">
            Analyze My Form
          </button>
        </form>
      </div>

      <!-- Results Area -->
      <div id="fc-results" style="display:none"></div>
    `;

    // Re-attach event listeners after render
    setTimeout(() => {
      this._attachListeners();
    }, 0);
  },

  _renderHistory() {
    if (!this.history.length) {
      return `
        <div class="empty-state">
          <p>No form checks yet. Upload your first video to get started!</p>
        </div>
      `;
    }

    return this.history.map(check => `
      <div class="card" style="margin-bottom:12px">
        <div class="card-header">
          <div>
            <div class="card-title">${this._esc(check.exercise || 'Exercise')}</div>
            <div class="card-subtitle">${check.date || ''}</div>
          </div>
          <div style="text-align:right">
            <div class="form-score-number" style="font-size:36px">${check.score || '--'}</div>
            <div style="font-size:10px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.06em">Form Score</div>
          </div>
        </div>
        ${check.rep_count ? `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px">${check.rep_count} reps detected</div>` : ''}
        ${check.cues && check.cues.length ? `
          <ul class="form-cue-list">
            ${check.cues.slice(0, 3).map(cue => `
              <li class="form-cue-item">
                <div class="form-cue-icon ${cue.type === 'good' ? 'good' : 'fix'}">${cue.type === 'good' ? '&#10003;' : '&#9888;'}</div>
                <span>${this._esc(cue.text)}</span>
              </li>
            `).join('')}
          </ul>
        ` : ''}
      </div>
    `).join('');
  },

  _attachListeners() {
    const form = document.getElementById('form-check-form');
    if (!form) return;

    // Drag and drop
    const zone = document.getElementById('fc-upload-zone');
    if (zone) {
      zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
      zone.addEventListener('dragleave', () => { zone.classList.remove('dragover'); });
      zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('video/')) {
          document.getElementById('fc-video-input').files = e.dataTransfer.files;
          this.onFileSelect(document.getElementById('fc-video-input'));
        }
      });
    }

    // Form submit
    App.formHandler('form-check-form', 'fc-submit', async () => {
      const exercise = document.getElementById('fc-exercise').value;
      const fileInput = document.getElementById('fc-video-input');
      const notes = document.getElementById('fc-notes').value;

      if (!exercise) {
        Toast.warning('Please select an exercise');
        return;
      }
      if (!fileInput.files.length) {
        Toast.warning('Please upload a video');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('exercise', exercise);
      if (notes) formData.append('notes', notes);

      const result = await API.upload('/api/client/form-check', formData);
      this._showResults(result);
      Toast.success(`Form check complete! +${result.xp_earned || 25} XP`);
      App.loadUserInfo();
    });
  },

  onFileSelect(input) {
    const fileNameEl = document.getElementById('fc-file-name');
    if (input.files.length) {
      const file = input.files[0];
      const sizeMB = (file.size / 1024 / 1024).toFixed(1);
      fileNameEl.textContent = `${file.name} (${sizeMB} MB)`;
      fileNameEl.style.display = 'block';
    } else {
      fileNameEl.style.display = 'none';
    }
  },

  _showResults(result) {
    const el = document.getElementById('fc-results');
    if (!el) return;

    const cues = result.cues || result.form_cues || [];
    el.style.display = 'block';
    el.innerHTML = `
      <div class="section-divider"><span>Analysis Results</span></div>
      <div class="grid-2">
        <div class="card">
          <div class="form-score-display">
            <div class="form-score-number">${result.score || result.form_score || '--'}</div>
            <div class="form-score-label">Form Score</div>
          </div>
          ${result.rep_count ? `
          <div style="text-align:center;font-size:14px;color:var(--text-secondary);margin-top:8px">
            <strong>${result.rep_count}</strong> reps counted
          </div>
          ` : ''}
        </div>
        <div class="card">
          <div class="card-title" style="margin-bottom:14px">Form Cues</div>
          ${cues.length ? `
          <ul class="form-cue-list">
            ${cues.map(cue => `
              <li class="form-cue-item">
                <div class="form-cue-icon ${cue.type === 'good' ? 'good' : 'fix'}">${cue.type === 'good' ? '&#10003;' : '&#9888;'}</div>
                <span>${this._esc(cue.text || cue.message || cue)}</span>
              </li>
            `).join('')}
          </ul>
          ` : '<p style="color:var(--text-muted)">No specific cues detected</p>'}
        </div>
      </div>
    `;

    // Scroll to results
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  },

  switchTab(tab) {
    this.activeTab = tab;
    this.render(document.getElementById('main-content'));
    // Re-attach listeners if on upload tab
    if (tab === 'upload') {
      setTimeout(() => this._attachListeners(), 0);
    }
  },

  _esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = typeof str === 'string' ? str : JSON.stringify(str);
    return div.innerHTML;
  }
};
