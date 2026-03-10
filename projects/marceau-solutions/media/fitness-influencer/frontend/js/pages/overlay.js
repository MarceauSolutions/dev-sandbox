const OverlayPage = {
  title: 'Workout Overlays',
  _presets: [],
  _styles: [],
  _timerTypes: [],
  _selectedPreset: null,
  _selectedStyle: null,
  _selectedTimerType: null,

  async init() {
    try {
      const [presetsRes, stylesRes, timerRes] = await Promise.all([
        API.get('/api/video/add-workout-overlay/presets'),
        API.get('/api/video/add-workout-overlay/styles'),
        API.get('/api/video/add-workout-overlay/timer-types')
      ]);
      this._presets = presetsRes.presets || presetsRes || [];
      this._styles = stylesRes.styles || stylesRes || [];
      this._timerTypes = timerRes.timer_types || timerRes.types || timerRes || [];
    } catch (err) {
      Toast.error('Failed to load overlay options: ' + err.message);
      this._presets = [];
      this._styles = [];
      this._timerTypes = [];
    }
  },

  render(container) {
    const presetTags = this._presets.map(p => {
      const id = typeof p === 'string' ? p : p.id || p.name;
      const label = typeof p === 'string' ? p : p.name || p.label || p.id;
      return `<span class="tag" data-preset="${id}">${label}</span>`;
    }).join('');

    const timerTags = this._timerTypes.map(t => {
      const id = typeof t === 'string' ? t : t.id || t.name;
      const label = typeof t === 'string' ? t : t.name || t.label || t.id;
      return `<span class="tag" data-timer="${id}">${label}</span>`;
    }).join('');

    const styleTags = this._styles.map(s => {
      const id = typeof s === 'string' ? s : s.id || s.name;
      const label = typeof s === 'string' ? s : s.name || s.label || s.id;
      return `<span class="tag" data-style="${id}">${label}</span>`;
    }).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Workout Overlays</h1>
        <p>Add timer overlays and workout info to your videos</p>
      </div>

      <form id="overlay-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('overlay-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Workout Preset</h2>
          </div>
          <div class="form-group">
            <label class="form-label">Select Preset</label>
            <div class="grid-auto" id="overlay-preset-tags">
              ${presetTags || '<p style="color:var(--text-muted)">No presets available</p>'}
            </div>
            <span class="form-hint">Choose a workout structure for the overlay</span>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Timer & Style</h2>
          </div>

          <div class="form-group">
            <label class="form-label">Timer Type</label>
            <div class="grid-auto" id="overlay-timer-tags">
              ${timerTags || '<p style="color:var(--text-muted)">No timer types available</p>'}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Overlay Style</label>
            <div class="grid-auto" id="overlay-style-tags">
              ${styleTags || '<p style="color:var(--text-muted)">No styles available</p>'}
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="overlay-duration">Custom Duration (seconds)</label>
            <input class="form-input" type="number" id="overlay-duration" name="custom_duration"
              placeholder="Leave blank to use preset default" min="1" max="3600">
            <span class="form-hint">Override the default duration from the preset</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="overlay-submit-btn">Add Overlay</button>
      </form>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Preset tag selection
    const presetTags = container.querySelector('#overlay-preset-tags');
    if (presetTags) {
      presetTags.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag) return;
        presetTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        this._selectedPreset = tag.dataset.preset;
      });
    }

    // Timer type tag selection
    const timerTags = container.querySelector('#overlay-timer-tags');
    if (timerTags) {
      timerTags.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag) return;
        timerTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        this._selectedTimerType = tag.dataset.timer;
      });
    }

    // Style tag selection
    const styleTags = container.querySelector('#overlay-style-tags');
    if (styleTags) {
      styleTags.addEventListener('click', (e) => {
        const tag = e.target.closest('.tag');
        if (!tag) return;
        styleTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        this._selectedStyle = tag.dataset.style;
      });
    }

    App.formHandler('overlay-form', 'overlay-submit-btn', async () => {
      const videoUrl = container.querySelector('#overlay-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }
      if (!this._selectedPreset) { Toast.error('Please select a workout preset'); return; }

      const payload = {
        video_url: videoUrl,
        preset: this._selectedPreset
      };

      if (this._selectedTimerType) payload.timer_type = this._selectedTimerType;
      if (this._selectedStyle) payload.style = this._selectedStyle;

      const duration = container.querySelector('#overlay-duration').value;
      if (duration) payload.custom_duration = parseInt(duration, 10);

      const res = await API.post('/api/video/add-workout-overlay', payload);

      if (res.job_id) {
        JobPoller.startPolling(res.job_id);
        Toast.success('Overlay job started! You will be notified when it completes.');
      } else {
        Toast.success('Overlay added successfully.');
      }
    });
  },

  destroy() {
    this._presets = [];
    this._styles = [];
    this._timerTypes = [];
    this._selectedPreset = null;
    this._selectedStyle = null;
    this._selectedTimerType = null;
  }
};
