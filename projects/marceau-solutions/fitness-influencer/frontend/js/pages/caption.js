const CaptionPage = {
  title: 'Caption Studio',
  _styles: [],
  _fonts: [],
  _selectedStyle: null,

  async init() {
    try {
      const [stylesRes, fontsRes] = await Promise.all([
        API.get('/api/captions/styles'),
        API.get('/api/captions/fonts')
      ]);
      this._styles = stylesRes.styles || [];
      this._fonts = fontsRes.fonts || [];
    } catch (err) {
      Toast.error('Failed to load caption options: ' + err.message);
      this._styles = [];
      this._fonts = [];
    }
  },

  render(container) {
    const styleCards = this._styles.map(s => `
      <div class="style-card" data-style="${s.id || s.name}" tabindex="0">
        <strong>${s.name || s}</strong>
        ${s.description ? `<p>${s.description}</p>` : ''}
      </div>
    `).join('');

    const fontOptions = this._fonts.map(f =>
      `<option value="${f.id || f}">${f.name || f}</option>`
    ).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Caption Studio</h1>
        <p>Add styled captions to your videos</p>
      </div>

      <form id="caption-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          <div class="form-group">
            <label class="form-label" for="caption-video-url">Video URL</label>
            ${App.videoUrlField('caption-video-url')}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Caption Style</h2>
          </div>
          <div class="grid-3" id="caption-style-grid">
            ${styleCards || '<p>No styles available</p>'}
          </div>
          <input type="hidden" id="caption-style" name="style" value="">
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Caption Settings</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="caption-position">Position</label>
              <select class="form-select" id="caption-position" name="position">
                <option value="bottom">Bottom</option>
                <option value="middle">Middle</option>
                <option value="top">Top</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="caption-language">Language</label>
              <input class="form-input" type="text" id="caption-language" name="language" value="en" placeholder="e.g. en, es, fr">
              <span class="form-hint">ISO 639-1 language code</span>
            </div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="caption-max-words">Max Words Per Line</label>
              <input class="form-input" type="number" id="caption-max-words" name="max_words_per_line" value="5" min="1" max="20">
            </div>

            <div class="form-group">
              <label class="form-checkbox">
                <input type="checkbox" id="caption-word-highlight" name="word_highlight" checked>
                <span>Word Highlight</span>
              </label>
              <span class="form-hint">Highlight each word as it is spoken</span>
            </div>
          </div>

          ${fontOptions ? `
          <div class="form-group">
            <label class="form-label" for="caption-font">Font</label>
            <select class="form-select" id="caption-font" name="font">
              ${fontOptions}
            </select>
          </div>
          ` : ''}
        </div>

        <button type="submit" class="btn btn-primary" id="caption-submit-btn">Generate Captions</button>
      </form>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    const styleGrid = container.querySelector('#caption-style-grid');
    if (styleGrid) {
      styleGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.style-card');
        if (!card) return;
        styleGrid.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this._selectedStyle = card.dataset.style;
        container.querySelector('#caption-style').value = this._selectedStyle;
      });
    }

    App.formHandler('caption-form', 'caption-submit-btn', async () => {
      const videoUrl = container.querySelector('#caption-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }
      if (!this._selectedStyle) { Toast.error('Please select a caption style'); return; }

      const payload = {
        video_url: videoUrl,
        style: this._selectedStyle,
        position: container.querySelector('#caption-position').value,
        language: container.querySelector('#caption-language').value.trim() || 'en',
        word_highlight: container.querySelector('#caption-word-highlight').checked,
        max_words_per_line: parseInt(container.querySelector('#caption-max-words').value, 10) || 5
      };

      const res = await API.post('/api/video/caption', payload);
      if (res.job_id) {
        JobPoller.start(res.job_id);
        Toast.success('Caption job started! You will be notified when it completes.');
      } else {
        Toast.success('Captions generated successfully.');
      }
    });
  },

  destroy() {
    this._styles = [];
    this._fonts = [];
    this._selectedStyle = null;
  }
};
