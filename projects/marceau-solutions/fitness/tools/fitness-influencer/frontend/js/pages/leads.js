const LeadsPage = {
  title: 'Leads & Email',
  _activeTab: 'submit',

  async init() {
    this._activeTab = 'submit';
  },

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Leads & Email Management</h1>
        <p>Manage leads, email digests, and opt-ins</p>
      </div>

      <div class="tabs" id="leads-tabs">
        <button class="tab active" data-tab="submit">Submit Lead</button>
        <button class="tab" data-tab="digest">Email Digest</button>
        <button class="tab" data-tab="optin">Opt-in</button>
      </div>

      <div id="leads-tab-content"></div>
    `;

    this._bindTabs(container);
    this._renderTab(container);
  },

  _bindTabs(container) {
    container.querySelector('#leads-tabs').addEventListener('click', (e) => {
      const tab = e.target.closest('.tab');
      if (!tab) return;
      container.querySelectorAll('#leads-tabs .tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      this._activeTab = tab.dataset.tab;
      this._renderTab(container);
    });
  },

  _renderTab(container) {
    const content = container.querySelector('#leads-tab-content');
    if (!content) return;

    switch (this._activeTab) {
      case 'submit':
        this._renderSubmitTab(content);
        break;
      case 'digest':
        this._renderDigestTab(content);
        break;
      case 'optin':
        this._renderOptinTab(content);
        break;
    }
  },

  _renderSubmitTab(content) {
    content.innerHTML = `
      <div class="card" style="margin-top:16px">
        <div class="card-header">
          <h2 class="card-title">Submit a New Lead</h2>
        </div>
        <form id="lead-submit-form">
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="lead-name">Name</label>
              <input class="form-input" type="text" id="lead-name" name="name" placeholder="Full name" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="lead-email">Email</label>
              <input class="form-input" type="email" id="lead-email" name="email" placeholder="email@example.com" required>
            </div>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="lead-phone">Phone</label>
              <input class="form-input" type="tel" id="lead-phone" name="phone" placeholder="+1 555-123-4567">
              <span class="form-hint">Optional</span>
            </div>
            <div class="form-group">
              <label class="form-label" for="lead-source">Source</label>
              <select class="form-select" id="lead-source" name="source">
                <option value="website">Website</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
                <option value="youtube">YouTube</option>
                <option value="referral">Referral</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <button type="submit" class="btn btn-primary" id="lead-submit-btn">Submit Lead</button>
        </form>
      </div>
    `;

    App.formHandler('lead-submit-form', 'lead-submit-btn', async () => {
      const name = document.getElementById('lead-name').value.trim();
      const email = document.getElementById('lead-email').value.trim();
      const phone = document.getElementById('lead-phone').value.trim();
      const source = document.getElementById('lead-source').value;

      if (!name || !email) { Toast.error('Name and email are required'); return; }

      await API.post('/api/leads/submit', { name, email, phone, source });
      Toast.success('Lead submitted successfully');
      document.getElementById('lead-submit-form').reset();
    });
  },

  _renderDigestTab(content) {
    content.innerHTML = `
      <div class="card" style="margin-top:16px">
        <div class="card-header">
          <h2 class="card-title">Email Digest</h2>
        </div>
        <p style="color:var(--text-secondary);margin-bottom:16px">Generate a summary digest of recent email activity and lead interactions.</p>
        <button class="btn btn-primary" id="digest-generate-btn">Generate Digest</button>
        <div id="digest-results" style="margin-top:16px"></div>
      </div>
    `;

    document.getElementById('digest-generate-btn').addEventListener('click', async () => {
      const btn = document.getElementById('digest-generate-btn');
      btn.disabled = true;
      btn.textContent = 'Generating...';

      try {
        const res = await API.post('/api/email/digest');
        const resultsEl = document.getElementById('digest-results');
        if (!resultsEl) return;

        const digest = res.digest || res;
        resultsEl.innerHTML = `
          <div class="section-divider"><span>Digest Results</span></div>
          <div class="card">
            <div class="card-header">
              <span class="card-title">Summary</span>
              <span style="font-size:12px;color:var(--text-muted)">${digest.generated_at || new Date().toLocaleString()}</span>
            </div>
            ${digest.total_emails != null ? `<p style="margin-bottom:8px"><strong>Total Emails:</strong> ${digest.total_emails}</p>` : ''}
            ${digest.new_leads != null ? `<p style="margin-bottom:8px"><strong>New Leads:</strong> ${digest.new_leads}</p>` : ''}
            ${digest.summary ? `<p style="color:var(--text-secondary)">${digest.summary}</p>` : ''}
            ${digest.items ? `
              <div style="margin-top:12px">
                ${digest.items.map(item => `
                  <div style="padding:8px 0;border-top:1px solid var(--border-default);font-size:13px">
                    <strong>${item.subject || item.title || '--'}</strong>
                    <span style="color:var(--text-muted);margin-left:8px">${item.from || item.sender || ''}</span>
                  </div>
                `).join('')}
              </div>
            ` : ''}
          </div>
        `;
        Toast.success('Digest generated');
      } catch (err) {
        Toast.error('Failed to generate digest: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Digest';
      }
    });
  },

  _renderOptinTab(content) {
    content.innerHTML = `
      <div class="grid-2" style="margin-top:16px">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">Email Opt-in</h2>
          </div>
          <form id="email-optin-form">
            <div class="form-group">
              <label class="form-label" for="optin-email">Email Address</label>
              <input class="form-input" type="email" id="optin-email" name="email" placeholder="subscriber@example.com" required>
            </div>
            <button type="submit" class="btn btn-primary" id="email-optin-btn">Subscribe Email</button>
          </form>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">SMS Opt-in</h2>
          </div>
          <form id="sms-optin-form">
            <div class="form-group">
              <label class="form-label" for="optin-phone">Phone Number</label>
              <input class="form-input" type="tel" id="optin-phone" name="phone" placeholder="+1 555-123-4567" required>
            </div>
            <button type="submit" class="btn btn-primary" id="sms-optin-btn">Subscribe SMS</button>
          </form>
        </div>
      </div>
    `;

    App.formHandler('email-optin-form', 'email-optin-btn', async () => {
      const email = document.getElementById('optin-email').value.trim();
      if (!email) { Toast.error('Please enter an email address'); return; }
      await API.post('/api/email/optin', { email });
      Toast.success('Email opt-in successful');
      document.getElementById('optin-email').value = '';
    });

    App.formHandler('sms-optin-form', 'sms-optin-btn', async () => {
      const phone = document.getElementById('optin-phone').value.trim();
      if (!phone) { Toast.error('Please enter a phone number'); return; }
      await API.post('/api/sms/optin', { phone });
      Toast.success('SMS opt-in successful');
      document.getElementById('optin-phone').value = '';
    });
  },

  destroy() {
    this._activeTab = 'submit';
  }
};
