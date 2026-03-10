const RetentionPage = {
  title: 'Retention Predictor',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Retention Predictor</h1>
        <p>Predict where viewers will drop off and how to keep them watching</p>
      </div>

      <form id="retention-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('retention-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Prediction Settings</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="retention-platform">Platform</label>
              <select class="form-select" id="retention-platform">
                <option value="tiktok">TikTok</option>
                <option value="instagram">Instagram Reels</option>
                <option value="youtube">YouTube Shorts</option>
                <option value="linkedin">LinkedIn</option>
              </select>
              <span class="form-hint">Platform algorithms affect retention expectations</span>
            </div>

            <div class="form-group">
              <label class="form-label" for="retention-cliff">Cliff Threshold</label>
              <input class="form-input" type="number" id="retention-cliff" value="0.2" min="0" max="1" step="0.05">
              <span class="form-hint">Drop-off percentage to flag as a "cliff" (0-1)</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="retention-interval">Sample Interval (seconds)</label>
            <input class="form-input" type="number" id="retention-interval" value="1" min="0.5" max="10" step="0.5" style="max-width:200px">
            <span class="form-hint">How often to sample retention data points</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="retention-submit-btn">Predict Retention</button>
      </form>

      <div id="retention-results" style="display:none"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('retention-form', 'retention-submit-btn', async () => {
      const videoUrl = container.querySelector('#retention-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        platform: container.querySelector('#retention-platform').value,
        cliff_threshold: parseFloat(container.querySelector('#retention-cliff').value) || 0.2,
        sample_interval: parseFloat(container.querySelector('#retention-interval').value) || 1
      };

      const res = await API.post('/api/video/predict-retention', payload);

      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Retention prediction job started! You will be notified when it completes.');
        return;
      }

      this._renderResults(container, res);
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#retention-results');
    resultsEl.style.display = 'block';

    const retention = data.predicted_retention || data.retention || data.retention_rate || data.overall_retention || 0;
    const pct = Math.round(typeof retention === 'number' && retention <= 1 ? retention * 100 : retention);
    const retColor = pct >= 60 ? 'var(--status-success)' : pct >= 35 ? 'var(--status-processing)' : 'var(--status-error)';

    const dropOffs = data.drop_off_points || data.dropoffs || data.cliffs || [];
    const suggestions = data.suggestions || data.improvements || data.recommendations || [];
    const curveData = data.retention_curve || data.curve || [];

    resultsEl.innerHTML = `
      <div class="section-divider"><span>Retention Prediction</span></div>

      <div class="card" style="text-align:center;margin-bottom:24px;padding:32px">
        <div style="font-size:56px;font-weight:800;color:${retColor};line-height:1">${pct}%</div>
        <div style="font-size:14px;color:var(--text-secondary);margin-top:4px">Predicted Average Retention</div>
        <div style="width:200px;height:8px;background:var(--surface-2);border-radius:4px;margin:16px auto 0;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:${retColor};border-radius:4px"></div>
        </div>
      </div>

      ${curveData.length ? `
        <div class="card" style="margin-bottom:16px">
          <div class="card-header"><span class="card-title">Retention Curve</span></div>
          <div class="timeline-bar" style="height:40px;display:flex;border-radius:6px;overflow:hidden">
            ${curveData.map((point, i) => {
              const val = point.retention || point.value || point;
              const v = typeof val === 'number' ? (val <= 1 ? val : val / 100) : 0;
              const bg = v >= 0.6 ? 'var(--status-success)' : v >= 0.35 ? 'var(--status-processing)' : 'var(--status-error)';
              return `<div class="timeline-segment" style="flex:1;background:${bg};opacity:${0.4 + v * 0.6}" title="${this._formatTime(point.time || i)}s: ${Math.round(v * 100)}%"></div>`;
            }).join('')}
          </div>
          <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-top:4px">
            <span>0:00</span>
            <span>End</span>
          </div>
        </div>
      ` : ''}

      ${dropOffs.length ? `
        <div class="card" style="margin-bottom:16px">
          <div class="card-header"><span class="card-title">Drop-Off Points</span></div>
          <div style="display:flex;flex-direction:column;gap:12px">
            ${dropOffs.map((d, i) => {
              const time = d.time || d.timestamp || d.at || 0;
              const drop = d.drop || d.severity || d.percentage || 0;
              const dropPct = Math.round(typeof drop === 'number' && drop <= 1 ? drop * 100 : drop);
              const reason = d.reason || d.cause || d.description || 'Viewer attention lost';
              return `
                <div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid var(--border-default)">
                  <div style="min-width:50px;font-weight:700;color:var(--status-error)">${this._formatTime(time)}</div>
                  <div style="flex:1">
                    <div style="font-size:14px;font-weight:500">${reason}</div>
                  </div>
                  <div style="min-width:60px;text-align:right">
                    <span style="font-weight:700;color:var(--status-error)">-${dropPct}%</span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      ` : ''}

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
  },

  _formatTime(seconds) {
    if (typeof seconds !== 'number') return seconds;
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }
};
