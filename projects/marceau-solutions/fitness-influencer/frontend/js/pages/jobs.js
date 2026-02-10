const JobsPage = {
  title: 'Job History',
  _jobs: [],
  _filter: 'all',

  async init() {
    try {
      const res = await API.get('/api/jobs');
      this._jobs = res.jobs || res || [];
    } catch {
      this._jobs = [];
    }
    this._filter = 'all';
  },

  render(container) {
    container.innerHTML = `
      <div class="page-header">
        <h1>Job History</h1>
        <p>Track all your processing jobs</p>
        <button class="btn btn-sm btn-secondary" id="jobs-refresh-btn" style="margin-left:auto">Refresh</button>
      </div>

      <div class="tabs" id="jobs-filter-tabs" style="margin-bottom:16px">
        <button class="tab active" data-filter="all">All</button>
        <button class="tab" data-filter="processing">Processing</button>
        <button class="tab" data-filter="completed">Completed</button>
        <button class="tab" data-filter="failed">Failed</button>
      </div>

      <div class="card">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="jobs-table-body">
              ${this._renderRows()}
            </tbody>
          </table>
        </div>
      </div>
    `;

    this._bindEvents(container);
  },

  _renderRows() {
    const filtered = this._filter === 'all'
      ? this._jobs
      : this._jobs.filter(j => j.status === this._filter || (this._filter === 'processing' && j.status === 'queued'));

    if (!filtered.length) {
      return `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:24px">No jobs found</td></tr>`;
    }

    return filtered.map(j => {
      const statusColors = {
        completed: 'var(--status-completed)',
        processing: 'var(--status-processing)',
        queued: 'var(--status-processing)',
        failed: 'var(--status-failed)',
        cancelled: 'var(--text-muted)'
      };
      const statusColor = statusColors[j.status] || 'var(--text-muted)';
      const progress = j.progress != null ? j.progress : (j.status === 'completed' ? 100 : j.status === 'failed' ? 0 : null);
      const isActive = j.status === 'processing' || j.status === 'queued';
      const jobId = j.job_id || j.id || '--';
      const shortId = String(jobId).length > 12 ? String(jobId).slice(0, 12) + '...' : jobId;
      const created = j.created_at || j.created || j.timestamp;

      return `
        <tr>
          <td style="font-family:monospace;font-size:12px" title="${jobId}">${shortId}</td>
          <td>${j.job_type || j.type || '--'}</td>
          <td>
            <span style="display:inline-flex;align-items:center;gap:6px">
              <span style="width:8px;height:8px;border-radius:50%;background:${statusColor};display:inline-block"></span>
              ${j.status || 'unknown'}
            </span>
          </td>
          <td>
            ${progress != null ? `
              <div style="display:flex;align-items:center;gap:8px">
                <div class="job-progress" style="flex:1;height:6px;border-radius:3px">
                  <div class="job-progress-fill" style="width:${progress}%"></div>
                </div>
                <span style="font-size:11px;color:var(--text-muted)">${progress}%</span>
              </div>
            ` : '<span style="color:var(--text-muted);font-size:12px">--</span>'}
          </td>
          <td style="font-size:12px;color:var(--text-muted)">${created ? new Date(created).toLocaleString() : '--'}</td>
          <td>
            ${isActive ? `
              <button class="btn btn-sm btn-ghost job-cancel-btn" data-job-id="${jobId}">Cancel</button>
            ` : ''}
          </td>
        </tr>
      `;
    }).join('');
  },

  _bindEvents(container) {
    container.querySelector('#jobs-filter-tabs').addEventListener('click', (e) => {
      const tab = e.target.closest('.tab');
      if (!tab) return;
      container.querySelectorAll('#jobs-filter-tabs .tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      this._filter = tab.dataset.filter;
      container.querySelector('#jobs-table-body').innerHTML = this._renderRows();
      this._bindTableEvents(container);
    });

    container.querySelector('#jobs-refresh-btn').addEventListener('click', async () => {
      const btn = container.querySelector('#jobs-refresh-btn');
      btn.disabled = true;
      btn.textContent = 'Refreshing...';

      try {
        const res = await API.get('/api/jobs');
        this._jobs = res.jobs || res || [];
        container.querySelector('#jobs-table-body').innerHTML = this._renderRows();
        this._bindTableEvents(container);
        Toast.success('Jobs refreshed');
      } catch (err) {
        Toast.error('Failed to refresh: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Refresh';
      }
    });

    this._bindTableEvents(container);
  },

  _bindTableEvents(container) {
    const tbody = container.querySelector('#jobs-table-body');
    if (!tbody) return;

    // Remove old listeners by cloning
    const newTbody = tbody.cloneNode(true);
    tbody.parentNode.replaceChild(newTbody, tbody);

    newTbody.addEventListener('click', async (e) => {
      const btn = e.target.closest('.job-cancel-btn');
      if (!btn) return;

      const jobId = btn.dataset.jobId;
      if (!confirm('Cancel job ' + jobId + '?')) return;

      btn.disabled = true;
      btn.textContent = 'Cancelling...';

      try {
        await API.post('/api/jobs/' + encodeURIComponent(jobId) + '/cancel');
        Toast.success('Job cancelled');
        const job = this._jobs.find(j => String(j.job_id || j.id) === String(jobId));
        if (job) job.status = 'cancelled';
        container.querySelector('#jobs-table-body').innerHTML = this._renderRows();
        this._bindTableEvents(container);
      } catch (err) {
        Toast.error('Failed to cancel: ' + err.message);
        btn.disabled = false;
        btn.textContent = 'Cancel';
      }
    });
  },

  destroy() {
    this._jobs = [];
    this._filter = 'all';
  }
};
