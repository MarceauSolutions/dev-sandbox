const FillerPage = {
  title: 'Filler Detection & Removal',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Filler Detection & Removal</h1>
        <p>Detect and remove filler words like "um", "uh", "like", "you know" from your videos</p>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Video Source</h2>
        </div>
        <div class="form-group">
          <label class="form-label" for="filler-video-url">Video URL</label>
          ${App.videoUrlField('filler-video-url')}
        </div>
      </div>

      <div class="section-divider">Detect Fillers</div>

      <form id="detect-filler-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Detection Settings</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="detect-sensitivity">Sensitivity</label>
              <select class="form-select" id="detect-sensitivity" name="sensitivity">
                <option value="low">Low</option>
                <option value="medium" selected>Medium</option>
                <option value="high">High</option>
              </select>
              <span class="form-hint">Higher sensitivity finds more fillers but may have false positives</span>
            </div>

            <div class="form-group">
              <label class="form-label" for="detect-confidence">Confidence Threshold</label>
              <input class="form-input" type="number" id="detect-confidence" name="confidence_threshold" value="0.7" min="0" max="1" step="0.05">
              <span class="form-hint">Minimum confidence score (0-1) to flag a filler</span>
            </div>
          </div>

          <button type="submit" class="btn btn-secondary" id="detect-filler-btn">Detect Fillers</button>
        </div>
      </form>

      <div id="filler-results" style="display: none;">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Detection Results</h2>
            <span id="filler-count" class="tag active"></span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Filler Word</th>
                  <th>Timestamp</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody id="filler-results-body"></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="section-divider">Remove Fillers</div>

      <form id="remove-filler-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Removal Settings</h2>
          </div>

          <div class="form-group">
            <label class="form-label" for="remove-sensitivity">Sensitivity</label>
            <select class="form-select" id="remove-sensitivity" name="sensitivity">
              <option value="low">Low</option>
              <option value="medium" selected>Medium</option>
              <option value="high">High</option>
            </select>
            <span class="form-hint">Controls which fillers are removed from the video</span>
          </div>

          <button type="submit" class="btn btn-primary" id="remove-filler-btn">Remove Fillers</button>
        </div>
      </form>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Detect fillers
    App.formHandler('detect-filler-form', 'detect-filler-btn', async () => {
      const videoUrl = container.querySelector('#filler-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        sensitivity: container.querySelector('#detect-sensitivity').value,
        confidence_threshold: parseFloat(container.querySelector('#detect-confidence').value)
      };

      const res = await API.post('/api/video/detect-fillers', payload);
      const fillers = res.fillers || [];

      const resultsSection = container.querySelector('#filler-results');
      const tbody = container.querySelector('#filler-results-body');
      const countBadge = container.querySelector('#filler-count');

      countBadge.textContent = fillers.length + ' filler' + (fillers.length !== 1 ? 's' : '') + ' found';

      if (fillers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; opacity: 0.6;">No fillers detected</td></tr>';
      } else {
        tbody.innerHTML = fillers.map(f => {
          const timestamp = typeof f.timestamp === 'number'
            ? new Date(f.timestamp * 1000).toISOString().substr(11, 8)
            : f.timestamp || '--';
          const confidence = typeof f.confidence === 'number'
            ? (f.confidence * 100).toFixed(1) + '%'
            : f.confidence || '--';
          return `
            <tr>
              <td><strong>${f.word || f.filler || '--'}</strong></td>
              <td>${timestamp}</td>
              <td>${confidence}</td>
            </tr>
          `;
        }).join('');
      }

      resultsSection.style.display = '';
      Toast.success('Detection complete: ' + fillers.length + ' filler(s) found.');
    });

    // Remove fillers
    App.formHandler('remove-filler-form', 'remove-filler-btn', async () => {
      const videoUrl = container.querySelector('#filler-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        sensitivity: container.querySelector('#remove-sensitivity').value
      };

      const res = await API.post('/api/video/remove-fillers', payload);
      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Filler removal job started!');
      } else {
        Toast.success('Fillers removed successfully.');
      }
    });
  },

  destroy() {}
};
