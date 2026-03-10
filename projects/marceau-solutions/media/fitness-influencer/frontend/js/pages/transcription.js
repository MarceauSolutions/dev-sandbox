const TranscriptionPage = {
  title: 'Transcription',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Transcription</h1>
        <p>Transcribe your video audio to text</p>
      </div>

      <form id="transcription-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Video Source</h2>
          </div>
          <div class="form-group">
            <label class="form-label" for="transcription-video-url">Video URL</label>
            ${App.videoUrlField('transcription-video-url')}
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Transcription Settings</h2>
          </div>

          <div class="form-group">
            <label class="form-label" for="transcription-language">Language</label>
            <select class="form-select" id="transcription-language" name="language">
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="pt">Portuguese</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="ja">Japanese</option>
              <option value="ko">Korean</option>
              <option value="zh">Chinese</option>
              <option value="ar">Arabic</option>
              <option value="hi">Hindi</option>
              <option value="ru">Russian</option>
              <option value="nl">Dutch</option>
              <option value="sv">Swedish</option>
              <option value="pl">Polish</option>
            </select>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="transcription-submit-btn">Transcribe</button>
      </form>

      <div id="transcription-results" style="display: none;">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Transcription Result</h2>
            <button class="btn btn-ghost btn-sm" id="transcription-copy-btn">Copy to Clipboard</button>
          </div>
          <div class="form-group">
            <textarea class="form-textarea" id="transcription-output" rows="16" readonly placeholder="Transcription will appear here..."></textarea>
          </div>
        </div>
      </div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('transcription-form', 'transcription-submit-btn', async () => {
      const videoUrl = container.querySelector('#transcription-video-url').value.trim();
      if (!videoUrl) { Toast.error('Please enter a video URL'); return; }

      const payload = {
        video_url: videoUrl,
        language: container.querySelector('#transcription-language').value
      };

      const res = await API.post('/api/transcription', payload);

      const text = res.transcription || res.text || '';
      const resultsSection = container.querySelector('#transcription-results');
      const output = container.querySelector('#transcription-output');

      output.value = text;
      resultsSection.style.display = '';

      if (text) {
        Toast.success('Transcription complete.');
      } else {
        Toast.error('No transcription returned. The video may not contain speech.');
      }
    });

    container.querySelector('#transcription-copy-btn').addEventListener('click', () => {
      const output = container.querySelector('#transcription-output');
      const text = output.value;
      if (!text) {
        Toast.error('Nothing to copy');
        return;
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          Toast.success('Copied to clipboard!');
        }).catch(() => {
          this._fallbackCopy(output);
        });
      } else {
        this._fallbackCopy(output);
      }
    });
  },

  _fallbackCopy(textarea) {
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);
    try {
      document.execCommand('copy');
      Toast.success('Copied to clipboard!');
    } catch (err) {
      Toast.error('Failed to copy. Please select and copy manually.');
    }
  },

  destroy() {}
};
