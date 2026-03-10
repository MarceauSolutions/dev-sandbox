const ImagesPage = {
  title: 'AI Image Generation',
  _selectedCount: 1,
  _selectedTier: 'standard',
  _results: [],

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>AI Image Generation</h1>
        <p>Generate fitness-themed images with AI</p>
      </div>

      <form id="images-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Image Prompt</h2>
          </div>
          <div class="form-group">
            <label class="form-label" for="images-prompt">Describe the image you want</label>
            <textarea class="form-textarea" id="images-prompt" name="prompt" rows="4"
              placeholder="e.g. A dynamic fitness athlete doing kettlebell swings in a modern gym, dramatic lighting"></textarea>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Options</h2>
          </div>

          <div class="form-group">
            <label class="form-label">Number of Images</label>
            <div class="grid-auto" id="images-count-tags">
              <span class="tag active" data-count="1">1</span>
              <span class="tag" data-count="2">2</span>
              <span class="tag" data-count="4">4</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Quality Tier</label>
            <div class="grid-auto" id="images-tier-tags">
              <span class="tag" data-tier="budget">Budget</span>
              <span class="tag active" data-tier="standard">Standard</span>
              <span class="tag" data-tier="premium">Premium</span>
            </div>
            <span class="form-hint">Higher tiers produce better quality but cost more</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="images-submit-btn">Generate Images</button>
      </form>

      <div id="images-results"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Count tag selection
    const countTags = container.querySelector('#images-count-tags');
    countTags.addEventListener('click', (e) => {
      const tag = e.target.closest('.tag');
      if (!tag) return;
      countTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
      tag.classList.add('active');
      this._selectedCount = parseInt(tag.dataset.count, 10);
    });

    // Tier tag selection
    const tierTags = container.querySelector('#images-tier-tags');
    tierTags.addEventListener('click', (e) => {
      const tag = e.target.closest('.tag');
      if (!tag) return;
      tierTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
      tag.classList.add('active');
      this._selectedTier = tag.dataset.tier;
    });

    App.formHandler('images-form', 'images-submit-btn', async () => {
      const prompt = container.querySelector('#images-prompt').value.trim();
      if (!prompt) { Toast.error('Please enter an image prompt'); return; }

      const res = await API.post('/api/images/generate', {
        prompt,
        count: this._selectedCount,
        tier: this._selectedTier
      });

      if (res.job_id) {
        JobPoller.startPolling(res.job_id, {
          onComplete: (data) => this._renderResults(container, data.result)
        });
        Toast.success('Image generation started!');
      } else {
        this._renderResults(container, res);
        Toast.success('Images generated successfully.');
      }
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#images-results');
    if (!resultsEl) return;

    const images = data?.images || data?.urls || [];
    if (!images.length) {
      resultsEl.innerHTML = `
        <div class="card" style="margin-top:24px">
          <p style="color:var(--text-muted)">No images were returned.</p>
        </div>`;
      return;
    }

    resultsEl.innerHTML = `
      <div class="section-divider" style="margin-top:24px"><span>Generated Images</span></div>
      <div class="grid-${images.length >= 4 ? '4' : images.length >= 2 ? '2' : '2'}">
        ${images.map((img, i) => {
          const url = typeof img === 'string' ? img : img.url;
          return `
            <div class="card" style="padding:0;overflow:hidden">
              <img src="${url}" alt="Generated image ${i + 1}"
                style="width:100%;display:block;aspect-ratio:1;object-fit:cover">
              <div style="padding:12px;display:flex;gap:8px">
                <a href="${url}" download class="btn btn-sm btn-secondary" style="flex:1;text-align:center">Download</a>
              </div>
            </div>`;
        }).join('')}
      </div>
    `;
  },

  destroy() {
    this._selectedCount = 1;
    this._selectedTier = 'standard';
    this._results = [];
  }
};
