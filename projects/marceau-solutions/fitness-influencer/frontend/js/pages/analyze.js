const AnalyzePage = {
  title: 'Video Analysis',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Video Analysis</h1>
        <p>Break down your video into segments with AI-powered analysis</p>
      </div>

      <form id="analyze-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          ${App.videoUrlField('analyze-video-url')}
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Analysis Options</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="analyze-segment-count">Segment Count</label>
              <input class="form-input" type="number" id="analyze-segment-count" value="5" min="1" max="50">
              <span class="form-hint">Number of segments to divide the video into</span>
            </div>
            <div></div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" id="analyze-audio" checked>
                <span>Analyze Audio</span>
              </label>
              <span class="form-hint">Transcribe and analyze speech content</span>
            </div>

            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" id="analyze-scenes" checked>
                <span>Detect Scenes</span>
              </label>
              <span class="form-hint">Detect scene transitions and cuts</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-checkbox">
              <input type="checkbox" id="analyze-keywords" checked>
              <span>Extract Keywords</span>
            </label>
            <span class="form-hint">Identify key topics and themes</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="analyze-submit-btn">Analyze Video</button>
      </form>

      <div id="analyze-results" style="display:none"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('analyze-form', 'analyze-submit-btn', async () => {
      const videoUrl = container.querySelector('#analyze-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        analyze_audio: container.querySelector('#analyze-audio').checked,
        detect_scenes: container.querySelector('#analyze-scenes').checked,
        extract_keywords: container.querySelector('#analyze-keywords').checked,
        segment_count: parseInt(container.querySelector('#analyze-segment-count').value, 10) || 5
      };

      const res = await API.post('/api/video/analyze', payload);

      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Analysis job started! You will be notified when it completes.');
        return;
      }

      this._renderResults(container, res);
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#analyze-results');
    resultsEl.style.display = 'block';

    const duration = data.duration || data.video_duration || '--';
    const segments = data.segments || [];
    const keywords = data.keywords || [];

    resultsEl.innerHTML = `
      <div class="section-divider"><span>Analysis Results</span></div>

      <div class="grid-3" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">${typeof duration === 'number' ? duration.toFixed(1) + 's' : duration}</div>
          <div class="stat-label">Duration</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-secondary)">${segments.length}</div>
          <div class="stat-label">Segments Found</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-processing)">${keywords.length}</div>
          <div class="stat-label">Keywords</div>
        </div>
      </div>

      ${keywords.length ? `
        <div class="card" style="margin-bottom:16px">
          <div class="card-header"><span class="card-title">Keywords</span></div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            ${keywords.map(k => `<span class="tag">${typeof k === 'string' ? k : k.word || k.keyword}</span>`).join('')}
          </div>
        </div>
      ` : ''}

      ${segments.length ? `
        <div class="card">
          <div class="card-header"><span class="card-title">Video Segments</span></div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Type</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                ${segments.map((seg, i) => `
                  <tr>
                    <td>${i + 1}</td>
                    <td><span class="tag">${seg.type || seg.segment_type || 'segment'}</span></td>
                    <td>${this._formatTime(seg.start_time || seg.start || 0)}</td>
                    <td>${this._formatTime(seg.end_time || seg.end || 0)}</td>
                    <td>${seg.description || seg.content || '--'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      ` : '<div class="card"><p style="color:var(--text-muted);padding:16px">No segments detected.</p></div>'}
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
