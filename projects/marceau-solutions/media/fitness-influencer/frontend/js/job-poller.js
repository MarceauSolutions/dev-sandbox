/* ============================================================
   Job Queue Poller - Progressive polling for async jobs
   ============================================================ */

const JobPoller = {
  activeJobs: new Map(),
  listeners: [],

  INTERVALS: {
    initial: 2000,   // First 10s: every 2s
    normal: 5000,    // 10s-60s: every 5s
    slow: 15000      // >60s: every 15s
  },

  getInterval(elapsedMs) {
    if (elapsedMs < 10000) return this.INTERVALS.initial;
    if (elapsedMs < 60000) return this.INTERVALS.normal;
    return this.INTERVALS.slow;
  },

  startPolling(jobId, { onUpdate, onComplete, onError } = {}) {
    if (this.activeJobs.has(jobId)) return;

    const job = {
      id: jobId,
      startTime: Date.now(),
      elapsed: 0,
      intervalId: null,
      status: 'queued',
      progress: 0,
      type: '',
      onUpdate,
      onComplete,
      onError
    };

    const poll = async () => {
      try {
        const data = await API.get(`/api/jobs/${jobId}/status`);
        job.status = data.status || data.state || 'unknown';
        job.progress = data.progress || 0;
        job.type = data.job_type || data.type || '';
        job.result = data.result;
        job.error = data.error;
        job.elapsed = Date.now() - job.startTime;

        if (onUpdate) onUpdate(data);
        this._notifyListeners();

        if (job.status === 'complete' || job.status === 'completed') {
          this.stopPolling(jobId);
          if (onComplete) onComplete(data);
          Toast.success(`Job complete: ${job.type || jobId}`);
        } else if (job.status === 'failed' || job.status === 'error') {
          this.stopPolling(jobId);
          if (onError) onError(data);
          Toast.error(`Job failed: ${data.error || 'Unknown error'}`);
        } else {
          // Adjust interval based on elapsed time
          clearInterval(job.intervalId);
          job.intervalId = setInterval(poll, this.getInterval(job.elapsed));
        }
      } catch (err) {
        console.error('Poll error for job', jobId, err);
      }
    };

    job.intervalId = setInterval(poll, this.INTERVALS.initial);
    this.activeJobs.set(jobId, job);
    poll(); // immediate first poll
    this._notifyListeners();
  },

  stopPolling(jobId) {
    const job = this.activeJobs.get(jobId);
    if (job) {
      clearInterval(job.intervalId);
      // Keep in map for display but mark as done
      setTimeout(() => {
        this.activeJobs.delete(jobId);
        this._notifyListeners();
      }, 30000); // keep for 30s after completion
    }
  },

  cancelJob(jobId) {
    API.post(`/api/jobs/${jobId}/cancel`).then(() => {
      this.stopPolling(jobId);
      Toast.info('Job cancelled');
    }).catch(err => {
      Toast.error('Failed to cancel: ' + err.message);
    });
  },

  getActiveJobs() {
    return Array.from(this.activeJobs.values());
  },

  getCounts() {
    const jobs = this.getActiveJobs();
    return {
      processing: jobs.filter(j => j.status === 'processing' || j.status === 'running').length,
      queued: jobs.filter(j => j.status === 'queued' || j.status === 'pending').length,
      completed: jobs.filter(j => j.status === 'complete' || j.status === 'completed').length
    };
  },

  onUpdate(fn) {
    this.listeners.push(fn);
  },

  _notifyListeners() {
    this.listeners.forEach(fn => fn(this.getCounts(), this.getActiveJobs()));
  }
};
