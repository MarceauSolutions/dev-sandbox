const BrandPage = {
  title: 'Brand Research',
  _brands: [],

  async init() {
    try {
      const res = await API.get('/api/brand/list');
      this._brands = res.brands || res || [];
    } catch {
      this._brands = [];
    }
  },

  render(container) {
    const brandCards = this._brands.length
      ? this._brands.map(b => `
        <div class="card" data-handle="${b.handle || b.name}">
          <div class="card-header">
            <span class="card-title">@${b.handle || b.name}</span>
            <button class="btn btn-sm btn-ghost brand-delete-btn" data-handle="${b.handle || b.name}">Delete</button>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px">
            ${(b.platforms || []).map(p => `<span class="tag">${p}</span>`).join('')}
          </div>
          ${b.followers ? `<div style="font-size:13px;color:var(--text-secondary);margin-top:8px">Followers: ${b.followers.toLocaleString()}</div>` : ''}
          ${b.engagement_rate ? `<div style="font-size:13px;color:var(--text-secondary)">Engagement: ${b.engagement_rate}%</div>` : ''}
        </div>
      `).join('')
      : '<div class="empty-state">No brands researched yet. Use the form above to research a brand.</div>';

    container.innerHTML = `
      <div class="page-header">
        <h1>Brand Research</h1>
        <p>Research influencer brands across platforms</p>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Research a Brand</h2>
        </div>
        <form id="brand-research-form">
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="brand-handle">Handle / Username</label>
              <input class="form-input" type="text" id="brand-handle" name="handle" placeholder="@username" required>
              <span class="form-hint">Enter the brand's social media handle</span>
            </div>

            <div class="form-group">
              <label class="form-label">Platforms</label>
              <div style="display:flex;gap:12px;margin-top:6px">
                <label class="form-checkbox">
                  <input type="checkbox" name="platforms" value="instagram" checked>
                  <span>Instagram</span>
                </label>
                <label class="form-checkbox">
                  <input type="checkbox" name="platforms" value="tiktok">
                  <span>TikTok</span>
                </label>
                <label class="form-checkbox">
                  <input type="checkbox" name="platforms" value="youtube">
                  <span>YouTube</span>
                </label>
              </div>
            </div>
          </div>

          <button type="submit" class="btn btn-primary" id="brand-research-btn">Research Brand</button>
        </form>
      </div>

      <div class="section-divider"><span>Researched Brands</span></div>

      <div class="grid-2" id="brand-list">
        ${brandCards}
      </div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('brand-research-form', 'brand-research-btn', async () => {
      const handle = container.querySelector('#brand-handle').value.trim().replace(/^@/, '');
      if (!handle) { Toast.error('Please enter a handle'); return; }

      const checkboxes = container.querySelectorAll('input[name="platforms"]:checked');
      const platforms = Array.from(checkboxes).map(cb => cb.value);
      if (!platforms.length) { Toast.error('Please select at least one platform'); return; }

      const res = await API.post('/api/brand/research', { handle, platforms });
      Toast.success('Brand research started for @' + handle);

      if (res.job_id) {
        JobPoller.start(res.job_id);
      } else {
        this._brands.unshift(res.brand || res);
        this._refreshList(container);
      }
    });

    container.querySelector('#brand-list').addEventListener('click', async (e) => {
      const btn = e.target.closest('.brand-delete-btn');
      if (!btn) return;
      const handle = btn.dataset.handle;
      if (!confirm('Delete brand @' + handle + '?')) return;

      try {
        await API.delete('/api/brand/profile/' + encodeURIComponent(handle));
        Toast.success('Brand @' + handle + ' deleted');
        this._brands = this._brands.filter(b => (b.handle || b.name) !== handle);
        this._refreshList(container);
      } catch (err) {
        Toast.error('Failed to delete: ' + err.message);
      }
    });
  },

  _refreshList(container) {
    const listEl = container.querySelector('#brand-list');
    if (!listEl) return;

    if (!this._brands.length) {
      listEl.innerHTML = '<div class="empty-state">No brands researched yet. Use the form above to research a brand.</div>';
      return;
    }

    listEl.innerHTML = this._brands.map(b => `
      <div class="card" data-handle="${b.handle || b.name}">
        <div class="card-header">
          <span class="card-title">@${b.handle || b.name}</span>
          <button class="btn btn-sm btn-ghost brand-delete-btn" data-handle="${b.handle || b.name}">Delete</button>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px">
          ${(b.platforms || []).map(p => `<span class="tag">${p}</span>`).join('')}
        </div>
        ${b.followers ? `<div style="font-size:13px;color:var(--text-secondary);margin-top:8px">Followers: ${b.followers.toLocaleString()}</div>` : ''}
        ${b.engagement_rate ? `<div style="font-size:13px;color:var(--text-secondary)">Engagement: ${b.engagement_rate}%</div>` : ''}
      </div>
    `).join('');
  },

  destroy() {
    this._brands = [];
  }
};
