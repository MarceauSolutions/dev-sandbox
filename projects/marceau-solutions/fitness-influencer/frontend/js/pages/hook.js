const HookPage = {
  title: 'Hook Analyzer',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Hook Analyzer</h1>
        <p>Evaluate the opening seconds of your video for maximum engagement</p>
      </div>

      <form id="hook-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('hook-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Hook Settings</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="hook-platform">Platform</label>
              <select class="form-select" id="hook-platform">
                <option value="tiktok">TikTok</option>
                <option value="instagram">Instagram Reels</option>
                <option value="youtube">YouTube Shorts</option>
                <option value="linkedin">LinkedIn</option>
              </select>
              <span class="form-hint">Scoring adjusts based on platform best practices</span>
            </div>

            <div class="form-group">
              <label class="form-label" for="hook-duration">Hook Duration (seconds)</label>
              <input class="form-input" type="number" id="hook-duration" value="3" min="1" max="15">
              <span class="form-hint">How many opening seconds to analyze</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="hook-variants">Number of Variants</label>
            <input class="form-input" type="number" id="hook-variants" value="3" min="1" max="10" style="max-width:200px">
            <span class="form-hint">AI will generate this many alternative hook suggestions</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="hook-submit-btn">Analyze Hook</button>
      </form>

      <div id="hook-results" style="display:none"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('hook-form', 'hook-submit-btn', async () => {
      const videoUrl = container.querySelector('#hook-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        platform: container.querySelector('#hook-platform').value,
        hook_duration: parseInt(container.querySelector('#hook-duration').value, 10) || 3,
        num_variants: parseInt(container.querySelector('#hook-variants').value, 10) || 3
      };

      const res = await API.post('/api/video/analyze-hook', payload);

      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Hook analysis job started! You will be notified when it completes.');
        return;
      }

      this._renderResults(container, res);
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#hook-results');
    resultsEl.style.display = 'block';

    const score = data.hook_score || data.score || data.overall_score || 0;
    const pct = Math.round(typeof score === 'number' && score <= 1 ? score * 100 : score);
    const scoreColor = pct >= 80 ? 'var(--status-success)' : pct >= 50 ? 'var(--status-processing)' : 'var(--status-error)';

    // Extract component scores
    const components = data.components || data.breakdown || data.scores || {};
    const componentKeys = [
      { key: 'visual_impact', label: 'Visual Impact' },
      { key: 'audio_hook', label: 'Audio Hook' },
      { key: 'text_overlay', label: 'Text Overlay' },
      { key: 'pacing', label: 'Pacing' },
      { key: 'curiosity_gap', label: 'Curiosity Gap' },
      { key: 'pattern_interrupt', label: 'Pattern Interrupt' }
    ];

    const suggestions = data.suggestions || data.improvements || data.recommendations || [];

    resultsEl.innerHTML = `
      <div class="section-divider"><span>Hook Analysis Results</span></div>

      <div class="card" style="text-align:center;margin-bottom:24px;padding:32px">
        <div style="font-size:56px;font-weight:800;color:${scoreColor};line-height:1">${pct}</div>
        <div style="font-size:14px;color:var(--text-secondary);margin-top:4px">Hook Score out of 100</div>
        <div style="width:200px;height:8px;background:var(--surface-2);border-radius:4px;margin:16px auto 0;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:${scoreColor};border-radius:4px"></div>
        </div>
      </div>

      <div class="grid-3" style="margin-bottom:24px">
        ${componentKeys.map(c => {
          const val = components[c.key];
          if (val === undefined && !Object.keys(components).length) return '';
          const v = val !== undefined ? val : '--';
          const display = typeof v === 'number' ? (v <= 1 ? Math.round(v * 100) : Math.round(v)) : v;
          const cColor = typeof display === 'number' ? (display >= 70 ? 'var(--status-success)' : display >= 40 ? 'var(--status-processing)' : 'var(--status-error)') : 'var(--text-primary)';
          return `
            <div class="stat-card">
              <div class="stat-value" style="color:${cColor}">${display}</div>
              <div class="stat-label">${c.label}</div>
            </div>
          `;
        }).join('')}
      </div>

      ${suggestions.length ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Improvement Suggestions</span></div>
          <ul style="margin:0;padding-left:20px;display:flex;flex-direction:column;gap:8px">
            ${suggestions.map(s => {
              const text = typeof s === 'string' ? s : s.suggestion || s.text || s.description || '';
              return `<li style="font-size:14px;color:var(--text-secondary)">${text}</li>`;
            }).join('')}
          </ul>
        </div>
      ` : ''}
    `;

    resultsEl.scrollIntoView({ behavior: 'smooth' });
  }
};
