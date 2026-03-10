const AdsPage = {
  title: 'Ad Creator',
  _selectedPlatform: 'instagram',
  _selectedAdType: 'image',

  _adTypes: [
    { id: 'image', icon: '\uD83D\uDDBC\uFE0F', name: 'Image Ad', desc: 'Single static image' },
    { id: 'video', icon: '\uD83C\uDFAC', name: 'Video Ad', desc: 'Short-form video' },
    { id: 'carousel', icon: '\uD83D\uDCF0', name: 'Carousel', desc: 'Multi-slide story' },
    { id: 'story', icon: '\uD83D\uDCF1', name: 'Story Ad', desc: 'Full-screen vertical' }
  ],

  _platformOptions: [
    { id: 'facebook', icon: '\uD83D\uDC4D', name: 'Facebook' },
    { id: 'instagram', icon: '\uD83D\uDCF7', name: 'Instagram' },
    { id: 'google', icon: '\uD83C\uDF10', name: 'Google' },
    { id: 'tiktok', icon: '\uD83C\uDFB5', name: 'TikTok' },
    { id: 'youtube', icon: '\u25B6\uFE0F', name: 'YouTube' }
  ],

  render(container) {
    const adTypeCards = this._adTypes.map(t => `
      <div class="template-card${t.id === this._selectedAdType ? ' selected' : ''}"
           data-type="${t.id}" tabindex="0">
        <div class="template-icon" style="background:var(--accent-secondary-dim);color:var(--accent-secondary)">
          ${t.icon}
        </div>
        <div class="template-name">${t.name}</div>
        <div class="template-desc">${t.desc}</div>
      </div>
    `).join('');

    const platformCards = this._platformOptions.map(p => `
      <div class="platform-card${p.id === this._selectedPlatform ? ' selected' : ''}"
           data-platform="${p.id}" tabindex="0">
        <div class="plat-icon">${p.icon}</div>
        <div class="plat-name">${p.name}</div>
      </div>
    `).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Ad Creator</h1>
        <p>Generate ad copy and creatives for your fitness products</p>
      </div>

      <div class="grid-4" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">5</div>
          <div class="stat-label">Platforms</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-secondary)">4</div>
          <div class="stat-label">Ad Formats</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-warning)">AI</div>
          <div class="stat-label">Copy Generator</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-processing)">Auto</div>
          <div class="stat-label">Optimization</div>
        </div>
      </div>

      <div class="section-divider"><span>Ad Format</span></div>

      <div class="grid-4" id="ads-type-grid" style="margin-bottom:24px">
        ${adTypeCards}
      </div>

      <div class="section-divider"><span>Target Platform</span></div>

      <div class="grid-5" id="ads-platform-grid" style="margin-bottom:24px">
        ${platformCards}
      </div>

      <form id="ads-form">
        <div class="form-layout-2col">
          <div>
            <div class="card">
              <div class="card-header">
                <h2 class="card-title">Product Information</h2>
              </div>

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

              <div class="form-group">
                <label class="form-label" for="ads-description">Product Description</label>
                <textarea class="form-textarea" id="ads-description" name="description" rows="3"
                  placeholder="Describe your product, its benefits, and what makes it unique"></textarea>
              </div>

              <div class="grid-2">
                <div class="form-group">
                  <label class="form-label" for="ads-cta">Call to Action</label>
                  <select class="form-select" id="ads-cta" name="cta">
                    <option value="Learn More">Learn More</option>
                    <option value="Sign Up">Sign Up</option>
                    <option value="Shop Now">Shop Now</option>
                    <option value="Get Started">Get Started</option>
                    <option value="Book Now">Book Now</option>
                    <option value="Download">Download</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label" for="ads-tone">Tone</label>
                  <select class="form-select" id="ads-tone" name="tone">
                    <option value="professional">Professional</option>
                    <option value="motivational">Motivational</option>
                    <option value="casual">Casual</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg" id="ads-submit-btn"
                    style="width:100%;justify-content:center;margin-top:12px">
              Generate Ad
            </button>
          </div>

          <div>
            <div class="card" id="ads-preview-area">
              <div class="card-header">
                <h2 class="card-title">Ad Preview</h2>
              </div>
              <div class="ad-preview-card">
                <div class="ad-preview-header">
                  <div style="width:32px;height:32px;border-radius:50%;background:var(--accent-primary-dim);display:flex;align-items:center;justify-content:center;font-size:14px">\uD83C\uDFCB\uFE0F</div>
                  <div>
                    <div style="font-size:13px;font-weight:600" id="ads-preview-name">Your Brand</div>
                    <div style="font-size:11px;color:var(--text-muted)">Sponsored</div>
                  </div>
                </div>
                <div class="ad-preview-body">
                  <div style="width:100%;aspect-ratio:1;background:var(--surface-3);border-radius:var(--radius-md);display:flex;align-items:center;justify-content:center;color:var(--text-muted);margin-bottom:12px">
                    <span style="font-size:48px">\uD83D\uDCF7</span>
                  </div>
                  <p id="ads-preview-desc" style="font-size:13px;color:var(--text-secondary);line-height:1.5">
                    Your ad copy will appear here after generation...
                  </p>
                </div>
                <div class="ad-preview-cta">
                  <span class="btn btn-sm btn-primary" id="ads-preview-cta-btn">Learn More</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </form>

      <div id="ads-results"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Ad type selection
    const typeGrid = container.querySelector('#ads-type-grid');
    if (typeGrid) {
      typeGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.template-card');
        if (!card) return;
        typeGrid.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this._selectedAdType = card.dataset.type;
      });
    }

    // Platform selection
    const platformGrid = container.querySelector('#ads-platform-grid');
    if (platformGrid) {
      platformGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.platform-card');
        if (!card) return;
        platformGrid.querySelectorAll('.platform-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this._selectedPlatform = card.dataset.platform;
      });
    }

    // Live preview: update brand name as user types
    const productInput = container.querySelector('#ads-product-name');
    if (productInput) {
      productInput.addEventListener('input', () => {
        const nameEl = container.querySelector('#ads-preview-name');
        if (nameEl) nameEl.textContent = productInput.value || 'Your Brand';
      });
    }

    // Live preview: update CTA button text
    const ctaSelect = container.querySelector('#ads-cta');
    if (ctaSelect) {
      ctaSelect.addEventListener('change', () => {
        const ctaBtn = container.querySelector('#ads-preview-cta-btn');
        if (ctaBtn) ctaBtn.textContent = ctaSelect.value;
      });
    }

    // Form submission
    App.formHandler('ads-form', 'ads-submit-btn', async () => {
      const productName = container.querySelector('#ads-product-name').value.trim();
      if (!productName) { Toast.error('Please enter a product name'); return; }

      const targetAudience = container.querySelector('#ads-target-audience').value.trim();
      if (!targetAudience) { Toast.error('Please enter a target audience'); return; }

      const payload = {
        product_name: productName,
        target_audience: targetAudience,
        platform: this._selectedPlatform,
        ad_type: this._selectedAdType,
        description: container.querySelector('#ads-description').value.trim(),
        call_to_action: container.querySelector('#ads-cta').value,
        tone: container.querySelector('#ads-tone').value
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

    // Update the live preview with generated copy
    const previewDesc = container.querySelector('#ads-preview-desc');
    const primaryText = data?.primary_text || data?.ad_copy || data?.copy || '';
    if (previewDesc && primaryText) {
      previewDesc.textContent = primaryText.substring(0, 200) + (primaryText.length > 200 ? '...' : '');
    }

    const headlines = data?.headlines || [];
    const descriptions = data?.descriptions || [];
    const cta = data?.cta || data?.call_to_action || '';
    const platform = data?.platform || '';

    let html = '<div class="section-divider" style="margin-top:24px"><span>Generated Ad Content</span></div>';

    if (primaryText) {
      html += `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Ad Copy</h2>
            <div style="display:flex;gap:8px">
              ${platform ? `<span class="tag">${platform}</span>` : ''}
              <button class="btn btn-sm btn-ghost copy-btn" data-copy-target="ad-copy-text">Copy</button>
            </div>
          </div>
          <p id="ad-copy-text" style="white-space:pre-wrap;line-height:1.6">${primaryText}</p>
          ${cta ? `<div style="margin-top:12px"><span class="tag active">${cta}</span></div>` : ''}
        </div>`;
    }

    if (headlines.length) {
      html += `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Headlines</h2>
          </div>
          ${headlines.map((h, i) => {
            const text = typeof h === 'string' ? h : (h.text || h.headline || '');
            return `
            <div style="display:flex;align-items:center;gap:8px;padding:8px 0;${i > 0 ? 'border-top:1px solid var(--border-muted)' : ''}">
              <span style="font-weight:600;color:var(--accent-primary);min-width:24px">${i + 1}.</span>
              <span style="flex:1">${text}</span>
              <button class="btn btn-sm btn-ghost copy-btn" data-copy-text="${text.replace(/"/g, '&quot;')}">Copy</button>
            </div>`;
          }).join('')}
        </div>`;
    }

    if (descriptions.length) {
      html += `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Descriptions</h2>
          </div>
          ${descriptions.map((d, i) => `
            <div style="padding:8px 0;${i > 0 ? 'border-top:1px solid var(--border-muted)' : ''}">
              <p style="color:var(--text-secondary)">${typeof d === 'string' ? d : (d.text || d.description || '')}</p>
            </div>
          `).join('')}
        </div>`;
    }

    if (!primaryText && !headlines.length && !descriptions.length) {
      html += `
        <div class="card">
          <pre style="white-space:pre-wrap;font-size:13px;color:var(--text-secondary)">${JSON.stringify(data, null, 2)}</pre>
        </div>`;
    }

    resultsEl.innerHTML = html;

    // Bind copy buttons
    resultsEl.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.copyTarget;
        const text = targetId
          ? (document.getElementById(targetId)?.textContent || '')
          : (btn.dataset.copyText || '');
        navigator.clipboard.writeText(text).then(() => Toast.success('Copied!'));
      });
    });
  },

  destroy() {
    this._selectedPlatform = 'instagram';
    this._selectedAdType = 'image';
  }
};
