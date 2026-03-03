/* ============================================================
   Editor Page — Video Pipeline with Presets (Ryan Humiston Style)
   ============================================================ */

const EditorPage = {
  title: 'Video Editor',
  _pollInterval: null,
  _presets: [],

  async init() {
    try {
      const data = await API.get('/api/video/pipeline/presets');
      this._presets = data.presets || [];
    } catch {
      this._presets = [];
    }
  },

  render(container) {
    const presetCards = this._presets.map(p => `
      <label class="preset-card" data-preset="${p.id}">
        <input type="radio" name="preset" value="${p.id}" ${p.id === 'humiston_style' ? 'checked' : ''}>
        <div class="preset-card-inner">
          <div class="preset-name">${p.name}</div>
          <div class="preset-desc">${p.description}</div>
          <div class="preset-steps">${p.step_count} steps</div>
        </div>
      </label>
    `).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Video Editor</h1>
        <p>Upload raw gym footage and transform it with automated editing pipelines</p>
      </div>

      <!-- Upload Section -->
      <div class="card" id="editor-upload-card">
        <div class="card-header">
          <h2 class="card-title">Upload Video</h2>
        </div>
        <div class="upload-zone" id="editor-drop-zone">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width:48px;height:48px;opacity:0.4;margin-bottom:12px">
            <path d="M4 14.899A7 7 0 1115.71 8h1.79a4.5 4.5 0 012.5 8.242"/>
            <path d="M12 12v9"/>
            <path d="M8 17l4-5 4 5"/>
          </svg>
          <div class="upload-text">Drag & drop video here or <span class="upload-browse">browse</span></div>
          <div class="upload-hint">MP4, MOV, AVI, MKV, WebM</div>
          <input type="file" id="editor-file-input" accept="video/*" style="display:none">
        </div>
        <div id="editor-file-info" style="display:none;margin-top:12px;">
          <div class="badge badge-success" id="editor-file-name"></div>
          <button class="btn btn-sm" onclick="EditorPage._clearFile()" style="margin-left:8px">Remove</button>
        </div>
      </div>

      <!-- Preset Selection -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Select Preset</h2>
        </div>
        <div class="preset-grid">
          ${presetCards || '<p style="opacity:0.5">Could not load presets. Check API.</p>'}
        </div>
      </div>

      <!-- Step Toggles -->
      <div class="card" id="editor-steps-card">
        <div class="card-header">
          <h2 class="card-title">Pipeline Steps</h2>
          <span class="form-hint">Toggle individual steps on/off</span>
        </div>
        <div id="editor-step-toggles"></div>
      </div>

      <!-- Run Button -->
      <button class="btn btn-primary btn-lg" id="editor-run-btn" style="width:100%;margin-top:8px;" disabled>
        Run Pipeline
      </button>

      <!-- Progress Section (hidden until running) -->
      <div class="card" id="editor-progress-card" style="display:none;margin-top:16px;">
        <div class="card-header">
          <h2 class="card-title">Processing</h2>
          <span class="badge" id="editor-status-badge">Running</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" id="editor-progress-bar" style="width:0%"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:0.85rem;opacity:0.7">
          <span id="editor-step-label">Initializing...</span>
          <span id="editor-progress-pct">0%</span>
        </div>
        <div id="editor-steps-log" style="margin-top:12px;font-size:0.82rem;max-height:200px;overflow-y:auto;"></div>
      </div>

      <!-- Viral Score Section (hidden until pipeline has viral data) -->
      <div class="card" id="editor-viral-card" style="display:none;margin-top:16px;">
        <div class="card-header">
          <h2 class="card-title">Viral Intelligence</h2>
          <span class="badge" id="viral-grade-badge">--</span>
        </div>
        <div class="viral-score-row">
          <div class="viral-gauge-container">
            <div class="viral-gauge-label">Before</div>
            <div class="viral-gauge">
              <svg viewBox="0 0 120 60" class="viral-gauge-svg">
                <path d="M10 55 A50 50 0 0 1 110 55" fill="none" stroke="var(--border-default)" stroke-width="8" stroke-linecap="round"/>
                <path d="M10 55 A50 50 0 0 1 110 55" fill="none" stroke="var(--status-error)" stroke-width="8" stroke-linecap="round"
                  id="viral-gauge-before-arc" stroke-dasharray="0 157" style="transition:stroke-dasharray 1.2s ease"/>
              </svg>
              <div class="viral-gauge-value" id="viral-score-before">--</div>
            </div>
          </div>
          <div class="viral-delta-arrow" id="viral-delta-container" style="display:none;">
            <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="2" style="width:32px;height:32px">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
            <div class="viral-delta-value" id="viral-delta-value">+0</div>
          </div>
          <div class="viral-gauge-container">
            <div class="viral-gauge-label">After</div>
            <div class="viral-gauge">
              <svg viewBox="0 0 120 60" class="viral-gauge-svg">
                <path d="M10 55 A50 50 0 0 1 110 55" fill="none" stroke="var(--border-default)" stroke-width="8" stroke-linecap="round"/>
                <path d="M10 55 A50 50 0 0 1 110 55" fill="none" stroke="var(--accent-primary)" stroke-width="8" stroke-linecap="round"
                  id="viral-gauge-after-arc" stroke-dasharray="0 157" style="transition:stroke-dasharray 1.2s ease"/>
              </svg>
              <div class="viral-gauge-value" id="viral-score-after">--</div>
            </div>
          </div>
        </div>
        <!-- Improvement breakdown -->
        <div id="viral-improvements" style="margin-top:16px;"></div>
      </div>

      <!-- Result Section (hidden until complete) -->
      <div class="card" id="editor-result-card" style="display:none;margin-top:16px;">
        <div class="card-header">
          <h2 class="card-title">Result</h2>
          <span class="badge badge-success">Complete</span>
        </div>
        <video id="editor-result-video" controls style="width:100%;max-height:400px;border-radius:8px;background:#000;"></video>
        <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">
          <a class="btn btn-primary" id="editor-download-btn" download>Download Video</a>
          <button class="btn" id="editor-package-btn" onclick="EditorPage._createPackage()">Export Package</button>
          <button class="btn" onclick="EditorPage._reset()">Edit Another</button>
        </div>
        <!-- Export package details (hidden until requested) -->
        <div id="editor-package-card" style="display:none;margin-top:12px;padding:12px;border-radius:8px;background:var(--surface-2);">
          <div style="font-weight:600;margin-bottom:8px;">Export Package</div>
          <div id="editor-package-list"></div>
        </div>
      </div>
    `;

    this._bindEvents(container);
    this._updateStepToggles();
  },

  _bindEvents(container) {
    const dropZone = container.querySelector('#editor-drop-zone');
    const fileInput = container.querySelector('#editor-file-input');
    const runBtn = container.querySelector('#editor-run-btn');

    // Drag & drop
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('drag-over');
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      if (e.dataTransfer.files.length) {
        this._selectedFile = e.dataTransfer.files[0];
        this._showFileInfo();
      }
    });

    // Click to browse
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        this._selectedFile = e.target.files[0];
        this._showFileInfo();
      }
    });

    // Preset selection updates step toggles
    container.querySelectorAll('input[name="preset"]').forEach(radio => {
      radio.addEventListener('change', () => this._updateStepToggles());
    });

    // Run button
    runBtn.addEventListener('click', () => this._runPipeline());
  },

  _showFileInfo() {
    const info = document.getElementById('editor-file-info');
    const name = document.getElementById('editor-file-name');
    const runBtn = document.getElementById('editor-run-btn');
    if (this._selectedFile) {
      const sizeMB = (this._selectedFile.size / 1024 / 1024).toFixed(1);
      name.textContent = `${this._selectedFile.name} (${sizeMB} MB)`;
      info.style.display = 'block';
      runBtn.disabled = false;
    }
  },

  _clearFile() {
    this._selectedFile = null;
    document.getElementById('editor-file-info').style.display = 'none';
    document.getElementById('editor-file-input').value = '';
    document.getElementById('editor-run-btn').disabled = true;
  },

  _updateStepToggles() {
    const selected = document.querySelector('input[name="preset"]:checked');
    if (!selected) return;
    const preset = this._presets.find(p => p.id === selected.value);
    if (!preset) return;

    const togglesEl = document.getElementById('editor-step-toggles');
    const steps = preset.steps || [];
    togglesEl.innerHTML = steps.map(s => {
      const name = typeof s === 'string' ? s : s.name;
      const enabled = typeof s === 'object' ? s.enabled !== false : true;
      return `
        <label class="step-toggle">
          <input type="checkbox" ${enabled ? 'checked' : ''} data-step="${name}">
          <span class="step-toggle-label">${name.replace(/_/g, ' ')}</span>
        </label>
      `;
    }).join('');
  },

  async _runPipeline() {
    if (!this._selectedFile) return;

    const preset = document.querySelector('input[name="preset"]:checked')?.value || 'humiston_style';

    // Collect step overrides
    const overrides = {};
    document.querySelectorAll('#editor-step-toggles input[type="checkbox"]').forEach(cb => {
      overrides[cb.dataset.step] = cb.checked;
    });

    // Build form data
    const formData = new FormData();
    formData.append('video', this._selectedFile);
    formData.append('preset', preset);
    formData.append('step_overrides', JSON.stringify(overrides));

    // Show progress
    document.getElementById('editor-progress-card').style.display = 'block';
    document.getElementById('editor-result-card').style.display = 'none';
    document.getElementById('editor-run-btn').disabled = true;
    document.getElementById('editor-run-btn').textContent = 'Processing...';
    document.getElementById('editor-steps-log').innerHTML = '';

    try {
      const res = await fetch('/api/video/pipeline/run', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        Toast.error(data.detail || 'Failed to start pipeline');
        this._resetRunBtn();
        return;
      }

      // Start polling
      this._jobId = data.job_id;
      this._startPolling();
    } catch (err) {
      Toast.error('Network error: ' + err.message);
      this._resetRunBtn();
    }
  },

  _startPolling() {
    if (this._pollInterval) clearInterval(this._pollInterval);
    this._pollInterval = setInterval(() => this._pollStatus(), 2000);
    this._pollStatus(); // immediate first check
  },

  async _pollStatus() {
    if (!this._jobId) return;
    try {
      const data = await API.get(`/api/video/pipeline/status/${this._jobId}`);
      const pct = Math.round((data.progress || 0) * 100);
      document.getElementById('editor-progress-bar').style.width = pct + '%';
      document.getElementById('editor-progress-pct').textContent = pct + '%';
      document.getElementById('editor-step-label').textContent =
        data.current_step ? `Step: ${data.current_step}` : 'Initializing...';

      const badge = document.getElementById('editor-status-badge');
      badge.textContent = data.status;
      badge.className = 'badge' + (data.status === 'complete' ? ' badge-success' : data.status === 'failed' ? ' badge-error' : '');

      // Log completed steps
      if (data.steps_completed) {
        const log = document.getElementById('editor-steps-log');
        log.innerHTML = data.steps_completed.map(s =>
          `<div style="color:var(--accent-primary)">&#10003; ${s}</div>`
        ).join('');
        if (data.steps_failed) {
          log.innerHTML += data.steps_failed.map(s =>
            `<div style="color:var(--status-error)">&#10007; ${s}</div>`
          ).join('');
        }
      }

      if (data.status === 'complete') {
        clearInterval(this._pollInterval);
        this._showResult(data);
      } else if (data.status === 'failed') {
        clearInterval(this._pollInterval);
        Toast.error(data.error || 'Pipeline failed');
        this._resetRunBtn();
      }
    } catch {
      // Keep polling on network errors
    }
  },

  _showResult(data) {
    document.getElementById('editor-result-card').style.display = 'block';
    const video = document.getElementById('editor-result-video');
    const dlBtn = document.getElementById('editor-download-btn');

    if (data.output_url) {
      video.src = data.output_url;
      dlBtn.href = data.output_url;
    }

    // Show viral score gauges if data available
    this._updateViralDisplay(data);

    this._resetRunBtn();
    Toast.success('Pipeline complete!');
  },

  _updateViralDisplay(data) {
    const before = data.viral_score_before;
    const after = data.viral_score_after;
    const stepResults = data.step_results || {};

    if (before == null && after == null && !stepResults.viral_optimize) return;

    const card = document.getElementById('editor-viral-card');
    card.style.display = 'block';

    // Gauge arc length: 157 is full arc (pi * 50)
    const maxArc = 157;

    if (before != null) {
      const pct = Math.min(before / 100, 1);
      document.getElementById('viral-score-before').textContent = Math.round(before);
      document.getElementById('viral-gauge-before-arc').setAttribute(
        'stroke-dasharray', `${pct * maxArc} ${maxArc}`
      );
    }

    if (after != null) {
      const pct = Math.min(after / 100, 1);
      document.getElementById('viral-score-after').textContent = Math.round(after);
      document.getElementById('viral-gauge-after-arc').setAttribute(
        'stroke-dasharray', `${pct * maxArc} ${maxArc}`
      );
    }

    if (before != null && after != null) {
      const delta = after - before;
      const deltaEl = document.getElementById('viral-delta-container');
      deltaEl.style.display = 'flex';
      const valEl = document.getElementById('viral-delta-value');
      valEl.textContent = (delta >= 0 ? '+' : '') + Math.round(delta);
      valEl.style.color = delta >= 0 ? 'var(--accent-primary)' : 'var(--status-error)';

      // Grade badge
      const badge = document.getElementById('viral-grade-badge');
      if (after >= 80) { badge.textContent = 'A'; badge.className = 'badge badge-success'; }
      else if (after >= 60) { badge.textContent = 'B'; badge.className = 'badge badge-success'; }
      else if (after >= 40) { badge.textContent = 'C'; badge.className = 'badge'; }
      else { badge.textContent = 'D'; badge.className = 'badge badge-error'; }
    }

    // Improvement breakdown from viral_optimize step
    const viralOpt = stepResults.viral_optimize;
    if (viralOpt && viralOpt.fix_steps) {
      const impEl = document.getElementById('viral-improvements');
      impEl.innerHTML = `
        <div style="font-weight:600;margin-bottom:8px;font-size:0.9rem">
          Optimization Applied (${viralOpt.weaknesses || 0} weaknesses detected)
        </div>
        ${viralOpt.fix_steps.map(f => `
          <div class="viral-fix-row">
            <span class="viral-fix-step">${(f.step || '').replace(/_/g, ' ')}</span>
            <span class="viral-fix-impact" style="color:var(--accent-primary)">
              +${Math.round((f.impact || 0) * 100)}%
            </span>
          </div>
        `).join('')}
      `;
    }

    // Show step result summaries
    const summaryParts = [];
    if (stepResults.transition_effects && !stepResults.transition_effects.skipped) {
      summaryParts.push(`${stepResults.transition_effects.applied} transitions`);
    }
    if (stepResults.color_grade && !stepResults.color_grade.skipped) {
      summaryParts.push(`Color: ${stepResults.color_grade.preset}`);
    }
    if (stepResults.background_music && !stepResults.background_music.skipped) {
      const m = stepResults.background_music;
      let label = `Music: ${m.track || 'added'}`;
      if (m.bpm) label += ` (${m.bpm} BPM)`;
      summaryParts.push(label);
    }
    if (stepResults.broll_insert && !stepResults.broll_insert.skipped) {
      summaryParts.push(`${stepResults.broll_insert.filled}/${stepResults.broll_insert.detected} B-roll inserts`);
    }
    if (summaryParts.length > 0) {
      const impEl = document.getElementById('viral-improvements');
      impEl.innerHTML += `
        <div style="margin-top:12px;font-size:0.82rem;opacity:0.7">
          ${summaryParts.join(' &middot; ')}
        </div>
      `;
    }
  },

  async _createPackage() {
    if (!this._jobId) return;
    const btn = document.getElementById('editor-package-btn');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
      const formData = new FormData();
      formData.append('platforms', 'tiktok,youtube_shorts,instagram_reels');
      const res = await fetch(`/api/video/pipeline/package/${this._jobId}`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.packages && data.packages.length > 0) {
        const listEl = document.getElementById('editor-package-list');
        listEl.innerHTML = data.packages.map(pkg => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border-default);">
            <div>
              <span style="font-weight:500;text-transform:capitalize;">${pkg.platform.replace(/_/g, ' ')}</span>
              ${pkg.thumbnail_path ? '<span class="badge" style="margin-left:6px;font-size:0.7rem">Thumbnail</span>' : ''}
            </div>
            <div style="font-size:0.8rem;opacity:0.7;max-width:60%;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
              ${pkg.hashtags.slice(0, 5).join(' ')}
            </div>
          </div>
        `).join('');
        document.getElementById('editor-package-card').style.display = 'block';
      }
    } catch (err) {
      Toast.error('Failed to create package: ' + err.message);
    }
    btn.disabled = false;
    btn.textContent = 'Export Package';
  },

  _resetRunBtn() {
    const btn = document.getElementById('editor-run-btn');
    if (btn) {
      btn.disabled = !this._selectedFile;
      btn.textContent = 'Run Pipeline';
    }
  },

  _reset() {
    this._clearFile();
    document.getElementById('editor-progress-card').style.display = 'none';
    document.getElementById('editor-result-card').style.display = 'none';
    document.getElementById('editor-viral-card').style.display = 'none';
    document.getElementById('editor-package-card').style.display = 'none';
    document.getElementById('editor-progress-bar').style.width = '0%';
    document.getElementById('editor-progress-pct').textContent = '0%';
    document.getElementById('editor-steps-log').innerHTML = '';
    this._jobId = null;
  },

  destroy() {
    if (this._pollInterval) clearInterval(this._pollInterval);
  }
};
