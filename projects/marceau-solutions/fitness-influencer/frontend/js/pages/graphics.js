const GraphicsPage = {
  title: 'Educational Graphics',
  _selectedType: 'infographic',
  _selectedPlatform: 'instagram_post',
  _recentGraphics: [],

  _graphicTypes: [
    { id: 'infographic', icon: '\uD83D\uDCCA', name: 'Infographic', desc: 'Data-driven visual breakdown' },
    { id: 'comparison', icon: '\u2696\uFE0F', name: 'Comparison', desc: 'Side-by-side analysis' },
    { id: 'tips_list', icon: '\u2705', name: 'Tips List', desc: 'Numbered tips & advice' },
    { id: 'myth_buster', icon: '\uD83D\uDCA5', name: 'Myth Buster', desc: 'Fact vs fiction format' },
    { id: 'exercise_guide', icon: '\uD83C\uDFCB\uFE0F', name: 'Exercise Guide', desc: 'Step-by-step form guide' },
    { id: 'nutrition_facts', icon: '\uD83E\uDD57', name: 'Nutrition Facts', desc: 'Macro/micro breakdowns' }
  ],

  _platformOptions: [
    { id: 'instagram_post', icon: '\uD83D\uDCF7', name: 'IG Post', specs: '1080\u00D71080' },
    { id: 'instagram_story', icon: '\uD83D\uDCF1', name: 'IG Story', specs: '1080\u00D71920' },
    { id: 'youtube_thumbnail', icon: '\u25B6\uFE0F', name: 'YouTube', specs: '1280\u00D7720' },
    { id: 'tiktok', icon: '\uD83C\uDFB5', name: 'TikTok', specs: '1080\u00D71920' }
  ],

  _topicSuggestions: [
    'Progressive Overload Basics',
    'Protein Timing Myths',
    '5 Compound Movements',
    'HIIT vs Steady State',
    'Creatine Benefits',
    'Sleep & Recovery',
    'Warm-Up Routine',
    'Rep Ranges Explained',
    'Hydration Tips',
    'Mind-Muscle Connection'
  ],

  render(container) {
    const typeCards = this._graphicTypes.map(t => `
      <div class="template-card${t.id === this._selectedType ? ' selected' : ''}"
           data-type="${t.id}" tabindex="0">
        <div class="template-icon" style="background:var(--accent-primary-dim);color:var(--accent-primary)">
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
        <div class="plat-specs">${p.specs}</div>
      </div>
    `).join('');

    const topicChips = this._topicSuggestions.map(t =>
      `<span class="topic-chip" data-topic="${t}">${t}</span>`
    ).join('');

    container.innerHTML = `
      <div class="page-header">
        <h1>Educational Graphics</h1>
        <p>Create professional fitness infographics and visual content</p>
      </div>

      <div class="grid-4" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">${this._recentGraphics.length}</div>
          <div class="stat-label">Created This Session</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-secondary)">6</div>
          <div class="stat-label">Template Types</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-warning)">4</div>
          <div class="stat-label">Platforms</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-processing)">AI</div>
          <div class="stat-label">Powered By</div>
        </div>
      </div>

      <div class="section-divider"><span>Choose Template</span></div>

      <div class="grid-3" id="graphics-type-grid" style="margin-bottom:24px">
        ${typeCards}
      </div>

      <form id="graphics-form">
        <div class="form-layout-2col">
          <div>
            <div class="card">
              <div class="card-header">
                <h2 class="card-title">Graphic Details</h2>
              </div>

              <div class="form-group">
                <label class="form-label" for="graphics-title">Title</label>
                <input class="form-input" type="text" id="graphics-title" name="title"
                  placeholder="e.g. Benefits of Progressive Overload">
              </div>

              <div class="form-group">
                <label class="form-label" for="graphics-points">Key Points</label>
                <textarea class="form-textarea" id="graphics-points" name="points" rows="4"
                  placeholder="Enter each point on a new line:&#10;Increases muscle tension over time&#10;Prevents plateaus&#10;Measurable progress tracking"></textarea>
                <span class="form-hint">One point per line. These become the bullet points on your graphic.</span>
              </div>

              <div class="form-group">
                <label class="form-label">Quick Topics</label>
                <div class="topic-chips" id="graphics-topic-chips">
                  ${topicChips}
                </div>
              </div>
            </div>

            <div class="card" style="margin-top:16px">
              <div class="card-header">
                <h2 class="card-title">Target Platform</h2>
              </div>
              <div class="grid-4" id="graphics-platform-grid">
                ${platformCards}
              </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg" id="graphics-submit-btn"
                    style="width:100%;justify-content:center;margin-top:12px">
              Create Graphic
            </button>
          </div>

          <div>
            <div class="card" id="graphics-preview-area">
              <div class="card-header">
                <h2 class="card-title">Preview</h2>
              </div>
              <div id="graphics-preview-empty" class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21 15 16 10 5 21"/>
                </svg>
                <p>Your generated graphic will appear here</p>
              </div>
              <div id="graphics-result-display" style="display:none"></div>
            </div>

            ${this._recentGraphics.length > 0 ? `
              <div class="card" style="margin-top:16px">
                <div class="card-header">
                  <h2 class="card-title">Recent Creations</h2>
                </div>
                <div class="grid-2">
                  ${this._recentGraphics.slice(0, 4).map(g => `
                    <div class="preview-card">
                      <img src="${g.image_data}" alt="${g.title || 'Graphic'}">
                      <div class="preview-overlay">
                        <span class="preview-label">${g.platform || ''}</span>
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            ` : ''}
          </div>
        </div>
      </form>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Type card selection
    const typeGrid = container.querySelector('#graphics-type-grid');
    if (typeGrid) {
      typeGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.template-card');
        if (!card) return;
        typeGrid.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this._selectedType = card.dataset.type;
      });
    }

    // Platform card selection
    const platformGrid = container.querySelector('#graphics-platform-grid');
    if (platformGrid) {
      platformGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.platform-card');
        if (!card) return;
        platformGrid.querySelectorAll('.platform-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this._selectedPlatform = card.dataset.platform;
      });
    }

    // Topic chip click -> fills title
    const topicChips = container.querySelector('#graphics-topic-chips');
    if (topicChips) {
      topicChips.addEventListener('click', (e) => {
        const chip = e.target.closest('.topic-chip');
        if (!chip) return;
        container.querySelector('#graphics-title').value = chip.dataset.topic;
      });
    }

    // Form submission
    App.formHandler('graphics-form', 'graphics-submit-btn', async () => {
      const title = container.querySelector('#graphics-title').value.trim();
      if (!title) { Toast.error('Please enter a title'); return; }

      const pointsRaw = container.querySelector('#graphics-points').value.trim();
      const points = pointsRaw
        ? pointsRaw.split('\n').map(p => p.trim()).filter(Boolean)
        : [];

      if (points.length === 0) { Toast.error('Please enter at least one key point'); return; }

      const payload = {
        title,
        points,
        platform: this._selectedPlatform,
        graphic_type: this._selectedType
      };

      const res = await API.post('/api/graphics/create', payload);

      if (res.job_id) {
        JobPoller.startPolling(res.job_id, {
          onComplete: (data) => this._showResult(container, data.result)
        });
        Toast.success('Graphic creation started!');
      } else {
        this._showResult(container, res);
        Toast.success('Graphic created successfully.');
      }
    });
  },

  _showResult(container, data) {
    const previewEmpty = container.querySelector('#graphics-preview-empty');
    const previewDisplay = container.querySelector('#graphics-result-display');
    if (!previewDisplay) return;

    if (previewEmpty) previewEmpty.style.display = 'none';
    previewDisplay.style.display = 'block';

    const imageData = data?.image_data || data?.url || data?.image_url || data?.graphic_url || '';
    const platform = data?.platform || this._selectedPlatform;
    const title = data?.title || '';

    if (imageData) {
      this._recentGraphics.unshift({ image_data: imageData, platform, title });
      if (this._recentGraphics.length > 8) this._recentGraphics.pop();

      previewDisplay.innerHTML = `
        <img src="${imageData}" alt="Generated graphic"
             style="width:100%;border-radius:var(--radius-md);margin-bottom:12px">
        <div style="display:flex;gap:8px">
          <a href="${imageData}" download="fitness-graphic.png"
             class="btn btn-sm btn-primary" style="flex:1;text-align:center">Download</a>
          <button class="btn btn-sm btn-secondary" id="graphics-create-another">Create Another</button>
        </div>
      `;

      const btn = previewDisplay.querySelector('#graphics-create-another');
      if (btn) btn.addEventListener('click', () => this.render(container));
    } else if (Array.isArray(data?.sections) && data.sections.length) {
      previewDisplay.innerHTML = `
        ${title ? `<h3 style="margin-bottom:12px">${title}</h3>` : ''}
        ${data.sections.map(s => `
          <div style="margin-bottom:12px">
            ${s.heading ? `<h4 style="margin-bottom:4px">${s.heading}</h4>` : ''}
            <p style="color:var(--text-secondary)">${s.text || s.content || JSON.stringify(s)}</p>
          </div>
        `).join('')}
      `;
    } else {
      previewDisplay.innerHTML = `
        <pre style="white-space:pre-wrap;font-size:12px;color:var(--text-secondary)">${JSON.stringify(data, null, 2)}</pre>
      `;
    }
  },

  destroy() {
    this._selectedType = 'infographic';
    this._selectedPlatform = 'instagram_post';
  }
};
