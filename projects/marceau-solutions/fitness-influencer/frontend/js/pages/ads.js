const AdsPage = {
  title: 'Ad Creator',

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Ad Creator</h1>
        <p>Generate ad copy and creatives for your fitness products</p>
      </div>

      <form id="ads-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Product Information</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="ads-product-name">Product Name</label>
              <input class="form-input" type="text" id="ads-product-name" name="product_name"
                placeholder="e.g. 12-Week Shred Program">
            </div>

            <div class="form-group">
              <label class="form-label" for="ads-target-audience">Target Audience</label>
              <input class="form-input" type="text" id="ads-target-audience" name="target_audience"
                placeholder="e.g. Women 25-40 wanting to lose weight">
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="ads-description">Product Description</label>
            <textarea class="form-textarea" id="ads-description" name="description" rows="3"
              placeholder="Describe your product, its benefits, and what makes it unique"></textarea>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Ad Configuration</h2>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="ads-platform">Platform</label>
              <select class="form-select" id="ads-platform" name="platform">
                <option value="facebook">Facebook</option>
                <option value="instagram">Instagram</option>
                <option value="google">Google</option>
                <option value="tiktok">TikTok</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="ads-ad-type">Ad Type</label>
              <select class="form-select" id="ads-ad-type" name="ad_type">
                <option value="image">Image Ad</option>
                <option value="video">Video Ad</option>
                <option value="carousel">Carousel Ad</option>
              </select>
            </div>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="ads-submit-btn">Create Ad</button>
      </form>

      <div id="ads-results"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('ads-form', 'ads-submit-btn', async () => {
      const productName = container.querySelector('#ads-product-name').value.trim();
      if (!productName) { Toast.error('Please enter a product name'); return; }

      const targetAudience = container.querySelector('#ads-target-audience').value.trim();
      if (!targetAudience) { Toast.error('Please enter a target audience'); return; }

      const payload = {
        product_name: productName,
        target_audience: targetAudience,
        platform: container.querySelector('#ads-platform').value,
        ad_type: container.querySelector('#ads-ad-type').value,
        description: container.querySelector('#ads-description').value.trim()
      };

      const res = await API.post('/api/ads/create', payload);

      if (res.job_id) {
        JobPoller.startPolling(res.job_id, {
          onComplete: (data) => this._renderResults(container, data.result)
        });
        Toast.success('Ad creation started!');
      } else {
        this._renderResults(container, res);
        Toast.success('Ad created successfully.');
      }
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#ads-results');
    if (!resultsEl) return;

    const headlines = data?.headlines || [];
    const descriptions = data?.descriptions || [];
    const primaryText = data?.primary_text || data?.ad_copy || data?.copy || '';
    const cta = data?.cta || data?.call_to_action || '';
    const platform = data?.platform || '';

    let html = '<div class="section-divider" style="margin-top:24px"><span>Generated Ad Content</span></div>';

    // Primary text / Ad copy
    if (primaryText) {
      html += `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Ad Copy</h2>
            ${platform ? `<span class="tag">${platform}</span>` : ''}
          </div>
          <p style="white-space:pre-wrap;line-height:1.6">${primaryText}</p>
          ${cta ? `<div style="margin-top:12px"><span class="tag active">${cta}</span></div>` : ''}
        </div>`;
    }

    // Headlines
    if (headlines.length) {
      html += `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Headlines</h2>
          </div>
          ${headlines.map((h, i) => `
            <div style="display:flex;align-items:center;gap:8px;padding:8px 0;${i > 0 ? 'border-top:1px solid var(--border-subtle)' : ''}">
              <span style="font-weight:600;color:var(--accent-primary);min-width:24px">${i + 1}.</span>
              <span>${typeof h === 'string' ? h : h.text || h.headline}</span>
            </div>
          `).join('')}
        </div>`;
    }

    // Descriptions
    if (descriptions.length) {
      html += `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Descriptions</h2>
          </div>
          ${descriptions.map((d, i) => `
            <div style="padding:8px 0;${i > 0 ? 'border-top:1px solid var(--border-subtle)' : ''}">
              <p style="color:var(--text-secondary)">${typeof d === 'string' ? d : d.text || d.description}</p>
            </div>
          `).join('')}
        </div>`;
    }

    // Fallback: show raw data if nothing matched
    if (!primaryText && !headlines.length && !descriptions.length) {
      html += `
        <div class="card">
          <pre style="white-space:pre-wrap;font-size:13px;color:var(--text-secondary)">${JSON.stringify(data, null, 2)}</pre>
        </div>`;
    }

    resultsEl.innerHTML = html;
  }
};
