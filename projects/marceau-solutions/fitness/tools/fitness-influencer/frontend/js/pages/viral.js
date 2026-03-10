const ViralPage = {
  title: 'Viral Moments',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Viral Moments Detection</h1>
        <p>Find the most shareable clips in your video</p>
      </div>

      <form id="viral-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('viral-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Detection Settings</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="viral-top-count">Top Clips to Find</label>
              <input class="form-input" type="number" id="viral-top-count" value="5" min="1" max="20">
              <span class="form-hint">Number of viral moments to detect</span>
            </div>

            <div class="form-group">
              <label class="form-label" for="viral-min-score">Minimum Score: <strong id="viral-score-display">0.6</strong></label>
              <input type="range" id="viral-min-score" min="0" max="1" step="0.05" value="0.6" style="width:100%;margin-top:8px">
              <span class="form-hint">Only show clips scoring above this threshold</span>
            </div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="viral-min-duration">Min Duration (seconds)</label>
              <input class="form-input" type="number" id="viral-min-duration" value="3" min="1" max="60">
            </div>

            <div class="form-group">
              <label class="form-label" for="viral-max-duration">Max Duration (seconds)</label>
              <input class="form-input" type="number" id="viral-max-duration" value="60" min="1" max="300">
            </div>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="viral-submit-btn">Detect Viral Moments</button>
      </form>

      <div id="viral-results" style="display:none"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Slider display update
    const slider = container.querySelector('#viral-min-score');
    const display = container.querySelector('#viral-score-display');
    slider.addEventListener('input', () => {
      display.textContent = parseFloat(slider.value).toFixed(2);
    });

    App.formHandler('viral-form', 'viral-submit-btn', async () => {
      const videoUrl = container.querySelector('#viral-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        top_count: parseInt(container.querySelector('#viral-top-count').value, 10) || 5,
        min_score: parseFloat(container.querySelector('#viral-min-score').value) || 0.6,
        min_duration: parseInt(container.querySelector('#viral-min-duration').value, 10) || 3,
        max_duration: parseInt(container.querySelector('#viral-max-duration').value, 10) || 60
      };

      const res = await API.post('/api/video/viral-moments', payload);

      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Viral detection job started! You will be notified when it completes.');
        return;
      }

      this._renderResults(container, res);
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#viral-results');
    resultsEl.style.display = 'block';

    const clips = data.viral_moments || data.clips || data.moments || [];

    if (!clips.length) {
      resultsEl.innerHTML = `
        <div class="section-divider"><span>Results</span></div>
        <div class="card"><p style="color:var(--text-muted);padding:16px">No viral moments found above the minimum score threshold.</p></div>
      `;
      return;
    }

    resultsEl.innerHTML = `
      <div class="section-divider"><span>Viral Moments Found: ${clips.length}</span></div>

      <div style="display:flex;flex-direction:column;gap:16px">
        ${clips.map((clip, i) => {
          const score = clip.score || clip.viral_score || 0;
          const pct = Math.round(score * 100);
          const scoreColor = pct >= 80 ? 'var(--status-success)' : pct >= 60 ? 'var(--status-processing)' : 'var(--text-muted)';

          return `
            <div class="card">
              <div class="card-header">
                <span class="card-title" style="display:flex;align-items:center;gap:8px">
                  <span style="background:${scoreColor};color:#fff;border-radius:50%;width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:700">${i + 1}</span>
                  ${clip.title || clip.description || 'Viral Clip #' + (i + 1)}
                </span>
                ${clip.category ? `<span class="tag">${clip.category}</span>` : ''}
              </div>

              <div class="grid-3" style="margin-bottom:12px">
                <div>
                  <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase">Start</div>
                  <div style="font-weight:600">${this._formatTime(clip.start_time || clip.start || 0)}</div>
                </div>
                <div>
                  <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase">End</div>
                  <div style="font-weight:600">${this._formatTime(clip.end_time || clip.end || 0)}</div>
                </div>
                <div>
                  <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase">Duration</div>
                  <div style="font-weight:600">${this._formatDuration(clip.start_time || clip.start || 0, clip.end_time || clip.end || 0)}</div>
                </div>
              </div>

              ${clip.description && clip.title ? `<p style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">${clip.description}</p>` : ''}

              <div style="display:flex;align-items:center;gap:12px">
                <div style="font-size:13px;font-weight:600;min-width:42px;color:${scoreColor}">${pct}%</div>
                <div style="flex:1;height:8px;background:var(--surface-2);border-radius:4px;overflow:hidden">
                  <div style="width:${pct}%;height:100%;background:${scoreColor};border-radius:4px;transition:width 0.3s"></div>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    resultsEl.scrollIntoView({ behavior: 'smooth' });
  },

  _formatTime(seconds) {
    if (typeof seconds !== 'number') return seconds;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  },

  _formatDuration(start, end) {
    if (typeof start !== 'number' || typeof end !== 'number') return '--';
    const dur = Math.max(0, end - start);
    return dur.toFixed(1) + 's';
  }
};
