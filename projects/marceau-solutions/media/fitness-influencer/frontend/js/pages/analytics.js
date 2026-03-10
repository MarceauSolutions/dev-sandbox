const AnalyticsPage = {
  title: 'Revenue Analytics',

  async init() {},

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Revenue Analytics</h1>
        <p>Track your earnings across platforms</p>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Query Revenue Data</h2>
        </div>
        <form id="analytics-form">
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label" for="analytics-date-range">Date Range</label>
              <select class="form-select" id="analytics-date-range" name="date_range">
                <option value="last_7_days">Last 7 Days</option>
                <option value="last_30_days" selected>Last 30 Days</option>
                <option value="last_90_days">Last 90 Days</option>
                <option value="all_time">All Time</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="analytics-platform">Platform</label>
              <select class="form-select" id="analytics-platform" name="platform">
                <option value="all">All Platforms</option>
                <option value="youtube">YouTube</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
              </select>
            </div>
          </div>

          <button type="submit" class="btn btn-primary" id="analytics-submit-btn">Generate Report</button>
        </form>
      </div>

      <div id="analytics-results"></div>
    `;

    this._bindEvents(container);
  },

  _bindEvents(container) {
    App.formHandler('analytics-form', 'analytics-submit-btn', async () => {
      const date_range = container.querySelector('#analytics-date-range').value;
      const platform = container.querySelector('#analytics-platform').value;

      const res = await API.post('/api/analytics/revenue', { date_range, platform });
      this._renderResults(container, res);
    });
  },

  _renderResults(container, data) {
    const resultsEl = container.querySelector('#analytics-results');
    if (!resultsEl) return;

    const totalRevenue = data.total_revenue ?? data.total ?? 0;
    const avgPerPost = data.avg_per_post ?? data.average ?? 0;
    const topPlatform = data.top_platform ?? data.best_platform ?? 'N/A';
    const breakdown = data.breakdown || data.details || [];

    const breakdownRows = breakdown.length
      ? breakdown.map(row => `
        <tr>
          <td>${row.platform || row.source || '--'}</td>
          <td>${row.posts || row.count || 0}</td>
          <td>$${(row.revenue || row.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
          <td>$${(row.avg || row.average || 0).toFixed(2)}</td>
        </tr>
      `).join('')
      : '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No breakdown data available</td></tr>';

    resultsEl.innerHTML = `
      <div class="section-divider"><span>Results</span></div>

      <div class="grid-3" style="margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-primary)">$${totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
          <div class="stat-label">Total Revenue</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--accent-secondary)">$${avgPerPost.toFixed(2)}</div>
          <div class="stat-label">Avg Per Post</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color:var(--status-processing)">${topPlatform}</div>
          <div class="stat-label">Top Platform</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Revenue Breakdown</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Platform</th>
                <th>Posts</th>
                <th>Revenue</th>
                <th>Avg/Post</th>
              </tr>
            </thead>
            <tbody>
              ${breakdownRows}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }
};
