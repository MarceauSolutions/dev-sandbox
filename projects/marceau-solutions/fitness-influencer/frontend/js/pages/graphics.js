const GraphicsPage = {
  title: 'Educational Graphics',

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Educational Graphics</h1>
        <p>Create professional fitness infographics and visual content</p>
      </div>

      <form id="graphics-form">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Graphic Details</h2>
          </div>

          <div class="form-group">
            <label class="form-label" for="graphics-topic">Topic</label>
            <input class="form-input" type="text" id="graphics-topic" name="topic"
              placeholder="e.g. Benefits of Progressive Overload">
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="graphics-type">Graphic Type</label>
              <select class="form-select" id="graphics-type" name="type">
                <option value="infographic">Infographic</option>
                <option value="comparison">Comparison</option>
                <option value="tips_list">Tips List</option>
                <option value="myth_buster">Myth Buster</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="graphics-style">Visual Style</label>
              <select class="form-select" id="graphics-style" name="style">
                <option value="clean">Clean</option>
                <option value="bold">Bold</option>
                <option value="neon">Neon</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-checkbox">
              <input type="checkbox" id="graphics-sources" name="include_sources">
              <span>Include Sources</span>
            </label>
            <span class="form-hint">Add citations and research references to the graphic</span>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="graphics-submit-btn">Create Graphic</button>
      </form>

      <div id="graphics-results"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('graphics-form', 'graphics-submit-btn', async () => {
      const topic = container.querySelector('#graphics-topic').value.trim();
      if (!topic) { Toast.error('Please enter a topic'); return; }

      const payload = {
        topic,
        type: container.querySelector('#graphics-type').value,
        style: container.querySelector('#graphics-style').value,
        include_sources: container.querySelector('#graphics-sources').checked
      };

      const res = await API.post('/api/graphics/create', payload);

      if (res.job_id) {
        JobPoller.startPolling(res.job_id, {
          onComplete: (data) => this._renderResults(container, data.result)
        });
        Toast.success('Graphic creation started!');
      } else {
        this._renderResults(container, res);
        Toast.success('Graphic created successfully.');
      }
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#graphics-results');
    if (!resultsEl) return;

    const url = data?.url || data?.image_url || data?.graphic_url || '';
    const title = data?.title || data?.topic || '';
    const sections = data?.sections || data?.content || [];

    let html = '<div class="section-divider" style="margin-top:24px"><span>Generated Graphic</span></div>';

    if (url) {
      html += `
        <div class="card" style="padding:0;overflow:hidden">
          <img src="${url}" alt="${title}" style="width:100%;display:block">
          <div style="padding:12px;display:flex;gap:8px">
            <a href="${url}" download class="btn btn-sm btn-secondary">Download</a>
          </div>
        </div>`;
    } else if (Array.isArray(sections) && sections.length) {
      html += '<div class="card">';
      if (title) html += `<div class="card-header"><h2 class="card-title">${title}</h2></div>`;
      html += sections.map(s => `
        <div style="margin-bottom:12px">
          ${s.heading ? `<h3 style="margin-bottom:4px">${s.heading}</h3>` : ''}
          <p style="color:var(--text-secondary)">${s.text || s.content || JSON.stringify(s)}</p>
        </div>
      `).join('');
      html += '</div>';
    } else {
      html += `
        <div class="card">
          <pre style="white-space:pre-wrap;font-size:13px;color:var(--text-secondary)">${JSON.stringify(data, null, 2)}</pre>
        </div>`;
    }

    resultsEl.innerHTML = html;
  }
};
