const QuotaPage = {
  title: 'Quota & Usage',
  _quota: null,
  _tiers: [],

  async init() {
    try {
      const [quotaRes, tiersRes] = await Promise.allSettled([
        API.get('/api/quota/status'),
        API.get('/api/quota/tiers')
      ]);
      this._quota = quotaRes.status === 'fulfilled' ? quotaRes.value : null;
      this._tiers = tiersRes.status === 'fulfilled' ? (tiersRes.value.tiers || tiersRes.value || []) : [];
    } catch {
      this._quota = null;
      this._tiers = [];
    }
  },

  render(container) {
    const q = this._quota || {};
    const tier = q.tier || q.plan || 'free';
    const tierLabel = tier.charAt(0).toUpperCase() + tier.slice(1);

    const usageBars = this._renderUsageBars(q);
    const tierTable = this._renderTierTable(tier);

    container.innerHTML = `
      <div class="page-header">
        <h1>Quota & Usage</h1>
        <p>Monitor your resource usage and plan limits</p>
      </div>

      <div class="card" style="margin-bottom:24px;border-left:4px solid var(--accent-primary)">
        <div class="card-header">
          <h2 class="card-title">Current Plan</h2>
          <span class="tag active">${tierLabel}</span>
        </div>
        <div style="font-size:14px;color:var(--text-secondary);margin-bottom:16px">
          ${q.description || 'Your current subscription tier and usage limits.'}
        </div>
        ${q.resets_at ? `<div style="font-size:12px;color:var(--text-muted)">Usage resets: ${new Date(q.resets_at).toLocaleDateString()}</div>` : ''}
      </div>

      <div class="section-divider"><span>Usage</span></div>

      <div class="grid-3" style="margin-bottom:24px">
        ${usageBars}
      </div>

      <div class="section-divider"><span>Plan Comparison</span></div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Available Tiers</h2>
        </div>
        <div class="table-wrap">
          ${tierTable}
        </div>
      </div>
    `;
  },

  _renderUsageBars(q) {
    const metrics = [
      {
        label: 'Video Jobs',
        used: q.video_jobs_used ?? q.video_used ?? 0,
        limit: q.video_jobs_limit ?? q.video_limit ?? 10,
        color: 'var(--accent-primary)'
      },
      {
        label: 'Caption Jobs',
        used: q.caption_jobs_used ?? q.caption_used ?? 0,
        limit: q.caption_jobs_limit ?? q.caption_limit ?? 20,
        color: 'var(--accent-secondary)'
      },
      {
        label: 'Export Jobs',
        used: q.export_jobs_used ?? q.export_used ?? 0,
        limit: q.export_jobs_limit ?? q.export_limit ?? 15,
        color: 'var(--status-processing)'
      }
    ];

    return metrics.map(m => {
      const percent = m.limit > 0 ? Math.min(100, Math.round((m.used / m.limit) * 100)) : 0;
      const isNearLimit = percent >= 80;

      return `
        <div class="card" style="text-align:center">
          <div style="font-weight:700;font-size:24px;color:${isNearLimit ? 'var(--status-error)' : m.color}">${m.used}</div>
          <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">${m.label}</div>
          <div class="job-progress" style="height:8px;border-radius:4px;margin-bottom:4px">
            <div class="job-progress-fill" style="width:${percent}%;${isNearLimit ? 'background:var(--status-error)' : ''}"></div>
          </div>
          <div style="font-size:11px;color:var(--text-muted)">${m.used} / ${m.limit} used (${percent}%)</div>
        </div>
      `;
    }).join('');
  },

  _renderTierTable(currentTier) {
    if (!this._tiers.length) {
      return '<p style="color:var(--text-muted);padding:12px">No tier information available</p>';
    }

    const headers = ['Feature', ...this._tiers.map(t => t.name || t.id)];
    const features = ['video_jobs', 'caption_jobs', 'export_jobs', 'ai_chats', 'storage_gb', 'price'];
    const featureLabels = {
      video_jobs: 'Video Jobs',
      caption_jobs: 'Caption Jobs',
      export_jobs: 'Export Jobs',
      ai_chats: 'AI Chats',
      storage_gb: 'Storage (GB)',
      price: 'Price'
    };

    return `
      <table>
        <thead>
          <tr>
            ${headers.map(h => `<th>${h}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${features.map(f => `
            <tr>
              <td><strong>${featureLabels[f] || f}</strong></td>
              ${this._tiers.map(t => {
                const val = t[f] ?? t.limits?.[f] ?? '--';
                const isCurrent = (t.name || t.id || '').toLowerCase() === currentTier.toLowerCase();
                const display = f === 'price' ? (val === 0 || val === 'free' ? 'Free' : '$' + val + '/mo') : (val === -1 || val === 'unlimited' ? 'Unlimited' : val);
                return `<td style="${isCurrent ? 'font-weight:700;color:var(--accent-primary)' : ''}">${display}</td>`;
              }).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  },

  destroy() {
    this._quota = null;
    this._tiers = [];
  }
};
