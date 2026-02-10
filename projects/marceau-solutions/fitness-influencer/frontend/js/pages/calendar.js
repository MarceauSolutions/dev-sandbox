const CalendarPage = {
  title: 'Content Calendar',
  _weekPlan: null,
  _selectedDay: null,

  async init() {
    try {
      const res = await API.get('/api/content/calendar/week/plan');
      this._weekPlan = res.days || res.week || res.plan || res;
    } catch (err) {
      Toast.error('Failed to load weekly plan: ' + err.message);
      this._weekPlan = null;
    }
  },

  render(container) {
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    // Normalize week plan into an array or object keyed by day
    const plan = this._normalizePlan(days);

    container.innerHTML = `
      <div class="page-header">
        <h1>Content Calendar</h1>
        <p>Your weekly content strategy at a glance</p>
      </div>

      <div class="card" style="margin-bottom:24px">
        <div class="card-header">
          <span class="card-title">This Week</span>
          <button class="btn btn-sm btn-ghost" id="cal-refresh-btn">Refresh</button>
        </div>

        <div class="cal-week" style="display:grid;grid-template-columns:repeat(7,1fr);gap:12px">
          ${days.map((day, i) => {
            const d = plan[day] || {};
            const theme = d.theme || d.day_theme || '--';
            const format = d.format || d.content_format || '';
            const today = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase() === day;

            return `
              <div class="cal-day card" data-day="${day}" style="cursor:pointer;padding:16px;text-align:center;${today ? 'border:2px solid var(--accent-primary)' : ''}" tabindex="0">
                <div style="font-size:12px;font-weight:700;text-transform:uppercase;color:${today ? 'var(--accent-primary)' : 'var(--text-muted)'};margin-bottom:8px">${dayLabels[i]}</div>
                <div style="font-size:14px;font-weight:600;margin-bottom:4px;color:var(--text-primary)">${theme}</div>
                ${format ? `<div style="font-size:11px;color:var(--text-muted)">${format}</div>` : ''}
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <div id="cal-day-detail" style="display:none"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    // Day click handlers
    container.querySelectorAll('.cal-day').forEach(el => {
      el.addEventListener('click', () => {
        // Highlight selected
        container.querySelectorAll('.cal-day').forEach(d => d.style.outline = 'none');
        el.style.outline = '2px solid var(--accent-secondary)';
        el.style.outlineOffset = '2px';

        const day = el.dataset.day;
        this._selectedDay = day;
        this._loadDayDetail(container, day);
      });
    });

    // Refresh button
    const refreshBtn = container.querySelector('#cal-refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        refreshBtn.textContent = 'Loading...';
        try {
          const res = await API.get('/api/content/calendar/week/plan');
          this._weekPlan = res.days || res.week || res.plan || res;
          Toast.success('Calendar refreshed');
          this.render(container);
        } catch (err) {
          Toast.error('Failed to refresh: ' + err.message);
        } finally {
          refreshBtn.disabled = false;
          refreshBtn.textContent = 'Refresh';
        }
      });
    }
  },

  async _loadDayDetail(container, day) {
    const detailEl = container.querySelector('#cal-day-detail');
    detailEl.style.display = 'block';
    detailEl.innerHTML = `
      <div class="card">
        <div style="display:flex;align-items:center;justify-content:center;padding:24px">
          <div class="spinner"></div>
          <span style="margin-left:12px;color:var(--text-muted)">Loading ${day}'s plan...</span>
        </div>
      </div>
    `;

    try {
      const [dayData, captionsData] = await Promise.allSettled([
        API.get(`/api/content/calendar/${day}`),
        API.get(`/api/content/calendar/captions/${day}`)
      ]);

      const d = dayData.status === 'fulfilled' ? dayData.value : {};
      const c = captionsData.status === 'fulfilled' ? captionsData.value : {};

      this._renderDayDetail(detailEl, day, d, c);
    } catch (err) {
      detailEl.innerHTML = `
        <div class="card">
          <p style="color:var(--status-error);padding:16px">Failed to load details: ${err.message}</p>
        </div>
      `;
    }
  },

  _renderDayDetail(detailEl, day, dayData, captionsData) {
    const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);
    const theme = dayData.theme || dayData.day_theme || '--';
    const topic = dayData.topic || dayData.hook_idea || '--';
    const hookIdea = dayData.hook_idea || dayData.hook || '--';
    const format = dayData.format || dayData.content_format || '--';
    const filmingTips = dayData.filming_tips || dayData.tips || [];
    const captions = captionsData.captions || captionsData.platform_captions || captionsData;

    detailEl.innerHTML = `
      <div class="section-divider"><span>${dayLabel}'s Content Plan</span></div>

      <div class="grid-2" style="margin-bottom:16px">
        <div class="card">
          <div class="card-header"><span class="card-title">Theme & Topic</span></div>
          <div style="margin-bottom:12px">
            <div style="font-size:11px;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px">Theme</div>
            <div style="font-size:18px;font-weight:700;color:var(--accent-primary)">${theme}</div>
          </div>
          <div style="margin-bottom:12px">
            <div style="font-size:11px;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px">Topic</div>
            <div style="font-size:14px;color:var(--text-primary)">${topic}</div>
          </div>
          <div>
            <div style="font-size:11px;text-transform:uppercase;color:var(--text-muted);margin-bottom:4px">Format</div>
            <div><span class="tag">${format}</span></div>
          </div>
        </div>

        <div class="card">
          <div class="card-header"><span class="card-title">Hook Idea</span></div>
          <div style="font-size:15px;line-height:1.6;color:var(--text-secondary);font-style:italic">"${hookIdea}"</div>

          ${filmingTips.length || typeof filmingTips === 'string' ? `
            <div style="margin-top:16px">
              <div style="font-size:11px;text-transform:uppercase;color:var(--text-muted);margin-bottom:8px">Filming Tips</div>
              ${typeof filmingTips === 'string'
                ? `<p style="font-size:13px;color:var(--text-secondary)">${filmingTips}</p>`
                : `<ul style="margin:0;padding-left:18px;font-size:13px;color:var(--text-secondary)">
                    ${filmingTips.map(t => `<li>${typeof t === 'string' ? t : t.tip || t.text}</li>`).join('')}
                  </ul>`
              }
            </div>
          ` : ''}
        </div>
      </div>

      ${this._renderCaptions(captions)}
    `;

    detailEl.scrollIntoView({ behavior: 'smooth' });
  },

  _renderCaptions(captions) {
    if (!captions || (typeof captions === 'object' && !Object.keys(captions).length)) {
      return '';
    }

    // captions could be an object keyed by platform or an array
    if (Array.isArray(captions)) {
      return `
        <div class="card">
          <div class="card-header"><span class="card-title">Platform Captions</span></div>
          <div style="display:flex;flex-direction:column;gap:12px">
            ${captions.map(c => {
              const platform = c.platform || 'General';
              const text = c.caption || c.text || c;
              return `
                <div style="padding:12px;background:var(--bg-secondary);border-radius:8px">
                  <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--accent-secondary);margin-bottom:6px">${platform}</div>
                  <div style="font-size:13px;color:var(--text-primary);white-space:pre-wrap">${text}</div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    // Object keyed by platform name
    const platforms = Object.entries(captions).filter(([k]) => k !== 'day' && k !== 'status');
    if (!platforms.length) return '';

    return `
      <div class="card">
        <div class="card-header"><span class="card-title">Platform Captions</span></div>
        <div style="display:flex;flex-direction:column;gap:12px">
          ${platforms.map(([platform, text]) => {
            const caption = typeof text === 'object' ? (text.caption || text.text || JSON.stringify(text)) : text;
            return `
              <div style="padding:12px;background:var(--bg-secondary);border-radius:8px">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:var(--accent-secondary);margin-bottom:6px">${platform}</div>
                <div style="font-size:13px;color:var(--text-primary);white-space:pre-wrap">${caption}</div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  },

  _normalizePlan(days) {
    const plan = {};
    if (!this._weekPlan) return plan;

    // If weekPlan is an array, map by index
    if (Array.isArray(this._weekPlan)) {
      this._weekPlan.forEach((d, i) => {
        if (i < days.length) {
          plan[days[i]] = d;
        }
      });
      return plan;
    }

    // If weekPlan is an object keyed by day name
    if (typeof this._weekPlan === 'object') {
      days.forEach(day => {
        plan[day] = this._weekPlan[day] || this._weekPlan[day.charAt(0).toUpperCase() + day.slice(1)] || {};
      });
      return plan;
    }

    return plan;
  },

  destroy() {
    this._weekPlan = null;
    this._selectedDay = null;
  }
};
