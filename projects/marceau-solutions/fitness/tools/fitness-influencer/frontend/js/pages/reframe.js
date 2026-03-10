const ReframePage = {
  title: 'Reframe & Edit',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Reframe & Edit</h1>
        <p>Reframe videos for different aspect ratios and perform smart edits</p>
      </div>

      <div class="tabs" id="reframe-tabs">
        <button class="tab active" data-tab="reframe">Reframe</button>
        <button class="tab" data-tab="smart-edit">Smart Edit</button>
      </div>

      <div id="reframe-tab-content">
        <div id="tab-reframe">
          <form id="reframe-form">
            <div class="card">
              <div class="card-header">
                <h2 class="card-title">Video Source</h2>
              </div>
              <div class="form-group">
                <label class="form-label" for="reframe-video-url">Video URL</label>
                ${App.videoUrlField('reframe-video-url')}
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h2 class="card-title">Reframe Settings</h2>
              </div>

              <div class="grid-3">
                <div class="form-group">
                  <label class="form-label" for="reframe-aspect">Target Aspect Ratio</label>
                  <select class="form-select" id="reframe-aspect" name="target_aspect">
                    <option value="9:16">9:16 (Vertical / Reels)</option>
                    <option value="1:1">1:1 (Square)</option>
                    <option value="4:5">4:5 (Portrait)</option>
                    <option value="16:9">16:9 (Landscape)</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label" for="reframe-tracking">Tracking Mode</label>
                  <select class="form-select" id="reframe-tracking" name="tracking_mode">
                    <option value="face">Face Tracking</option>
                    <option value="body">Body Tracking</option>
                    <option value="center">Center Crop</option>
                  </select>
                  <span class="form-hint">How the frame follows the subject</span>
                </div>

                <div class="form-group">
                  <label class="form-label" for="reframe-smoothing">Smoothing</label>
                  <input class="form-input" type="range" id="reframe-smoothing" name="smoothing" min="0" max="1" step="0.05" value="0.5">
                  <div style="display: flex; justify-content: space-between; font-size: 0.8rem; opacity: 0.6;">
                    <span>Responsive</span>
                    <span id="reframe-smoothing-value">0.50</span>
                    <span>Smooth</span>
                  </div>
                </div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary" id="reframe-submit-btn">Reframe Video</button>
          </form>
        </div>

        <div id="tab-smart-edit" style="display: none;">
          <form id="smart-edit-form">
            <div class="card">
              <div class="card-header">
                <h2 class="card-title">Video Source</h2>
              </div>
              <div class="form-group">
                <label class="form-label" for="edit-video-url">Video URL</label>
                ${App.videoUrlField('edit-video-url')}
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h2 class="card-title">Smart Edit Settings</h2>
              </div>
              <p style="margin-bottom: 1rem; opacity: 0.7;">Automatically remove silences and dead air from your video.</p>

              <div class="grid-2">
                <div class="form-group">
                  <label class="form-label" for="edit-silence-threshold">Silence Threshold (dB)</label>
                  <input class="form-input" type="number" id="edit-silence-threshold" name="silence_threshold" value="-40" min="-80" max="0" step="1">
                  <span class="form-hint">Audio level below which is considered silence</span>
                </div>

                <div class="form-group">
                  <label class="form-label" for="edit-min-silence">Min Silence Duration (s)</label>
                  <input class="form-input" type="number" id="edit-min-silence" name="min_silence_duration" value="0.5" min="0.1" max="5" step="0.1">
                  <span class="form-hint">Minimum silence length to remove</span>
                </div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary" id="smart-edit-submit-btn">Smart Edit Video</button>
          </form>
        </div>
      </div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Tab switching
    const tabs = container.querySelectorAll('#reframe-tabs .tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const target = tab.dataset.tab;
        container.querySelector('#tab-reframe').style.display = target === 'reframe' ? '' : 'none';
        container.querySelector('#tab-smart-edit').style.display = target === 'smart-edit' ? '' : 'none';
      });
    });

    // Smoothing slider live value
    const smoothingSlider = container.querySelector('#reframe-smoothing');
    const smoothingValue = container.querySelector('#reframe-smoothing-value');
    if (smoothingSlider && smoothingValue) {
      smoothingSlider.addEventListener('input', () => {
        smoothingValue.textContent = parseFloat(smoothingSlider.value).toFixed(2);
      });
    }

    // Reframe form
    App.formHandler('reframe-form', 'reframe-submit-btn', async () => {
      const videoUrl = container.querySelector('#reframe-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        target_aspect: container.querySelector('#reframe-aspect').value,
        tracking_mode: container.querySelector('#reframe-tracking').value,
        smoothing: parseFloat(container.querySelector('#reframe-smoothing').value)
      };

      const res = await API.post('/api/video/reframe', payload);
      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Reframe job started!');
      } else {
        Toast.success('Video reframed successfully.');
      }
    });

    // Smart Edit form
    App.formHandler('smart-edit-form', 'smart-edit-submit-btn', async () => {
      const videoUrl = container.querySelector('#edit-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        silence_threshold: parseInt(container.querySelector('#edit-silence-threshold').value, 10),
        min_silence_duration: parseFloat(container.querySelector('#edit-min-silence').value)
      };

      const res = await API.post('/api/video/edit', payload);
      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Smart edit job started!');
      } else {
        Toast.success('Video edited successfully.');
      }
    });
  },

  destroy() {}
};
