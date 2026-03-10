const ExportPage = {
  title: 'Multi-Platform Export',
  _platforms: [],
  _selectedPlatforms: new Set(),

  async init() {
    try {
      const res = await API.get('/api/video/export/platforms');
      this._platforms = res.platforms || [];
    } catch (err) {
      Toast.error('Failed to load platforms: ' + err.message);
      this._platforms = [];
    }
  },

  render(container) {
    const platformEmojis = {
      tiktok: '\uD83C\uDFB5',
      instagram: '\uD83D\uDCF7',
      youtube: '\u25B6\uFE0F',
      facebook: '\uD83D\uDC4D',
      twitter: '\uD83D\uDC26',
      x: '\u2716\uFE0F',
      linkedin: '\uD83D\uDCBC',
      pinterest: '\uD83D\uDCCC',
      snapchat: '\uD83D\uDC7B'
    };

    const platformCards = this._platforms.map(p => {
      const id = p.id || p.name.toLowerCase();
      const emoji = platformEmojis[id] || '\uD83C\uDF10';
      return `
        <div class="platform-card" data-platform="${id}" tabindex="0">
          <div style="font-size: 2rem;">${emoji}</div>
          <strong>${p.name}</strong>
          <div style="font-size: 0.85rem; opacity: 0.7;">
            ${p.aspect_ratio || ''} ${p.resolution ? '&middot; ' + p.resolution : ''}
          </div>
          ${p.max_duration ? `<div style="font-size: 0.85rem; opacity: 0.7;">Max ${p.max_duration}s</div>` : ''}
        </div>
      `;
    }).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Multi-Platform Export</h1>
        <p>Export your video optimized for multiple platforms at once</p>
      </div>

      <form id="export-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          <div class="form-group">
            <label class="form-label" for="export-video-url">Video URL</label>
            ${App.videoUrlField('export-video-url')}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Select Platforms</h2>
          </div>
          <div class="grid-3" id="export-platform-grid">
            ${platformCards || '<p>No platforms available</p>'}
          </div>
          <span class="form-hint">Click to select one or more platforms</span>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Export Options</h2>
          </div>

          <div class="form-group">
            <label class="form-label" for="export-category">Category</label>
            <select class="form-select" id="export-category" name="category">
              <option value="fitness">Fitness</option>
              <option value="workout">Workout</option>
              <option value="nutrition">Nutrition</option>
              <option value="motivation">Motivation</option>
              <option value="tutorial">Tutorial</option>
              <option value="lifestyle">Lifestyle</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" id="export-descriptions" name="generate_descriptions" checked>
                <span>Generate Descriptions</span>
              </label>
              <span class="form-hint">Auto-generate platform-specific descriptions</span>
            </div>

            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" id="export-hashtags" name="include_hashtags" checked>
                <span>Include Hashtags</span>
              </label>
              <span class="form-hint">Add trending hashtags for each platform</span>
            </div>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="export-submit-btn">Export to Platforms</button>
      </form>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    const grid = container.querySelector('#export-platform-grid');
    if (grid) {
      grid.addEventListener('click', (e) => {
        const card = e.target.closest('.platform-card');
        if (!card) return;
        const platform = card.dataset.platform;
        if (this._selectedPlatforms.has(platform)) {
          this._selectedPlatforms.delete(platform);
          card.classList.remove('selected');
        } else {
          this._selectedPlatforms.add(platform);
          card.classList.add('selected');
        }
      });
    }

    App.formHandler('export-form', 'export-submit-btn', async () => {
      const videoUrl = container.querySelector('#export-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }
      if (this._selectedPlatforms.size === 0) { Toast.error('Please select at least one platform'); return; }

      const payload = {
        video_url: videoUrl,
        platforms: Array.from(this._selectedPlatforms),
        generate_descriptions: container.querySelector('#export-descriptions').checked,
        include_hashtags: container.querySelector('#export-hashtags').checked,
        category: container.querySelector('#export-category').value
      };

      const res = await API.post('/api/video/export', payload);
      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Export job started! Processing for ' + payload.platforms.length + ' platform(s).');
      } else {
        Toast.success('Export completed successfully.');
      }
    });
  },

  destroy() {
    this._platforms = [];
    this._selectedPlatforms.clear();
  }
};
