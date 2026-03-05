/* ============================================================
   Toast Notification System
   ============================================================ */

const Toast = {
  container: null,

  init() {
    if (this.container) return;
    this.container = document.createElement('div');
    this.container.className = 'toast-container';
    document.body.appendChild(this.container);
  },

  show(message, type = 'info', duration = 5000) {
    this.init();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
      success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
      error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
      warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
      info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>'
    };

    toast.innerHTML = `
      <span style="color:var(--status-${type === 'info' ? 'info' : type})">${icons[type] || icons.info}</span>
      <span style="flex:1">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    this.container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => {
        toast.style.animation = 'toast-out 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
      }, duration);
    }

    return toast;
  },

  showWithUndo(message, actionId, undoCallback, duration = 10000) {
    this.init();
    const toast = document.createElement('div');
    toast.className = 'toast success toast-with-undo';

    const icons = {
      success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>'
    };

    toast.innerHTML = `
      <span style="color:var(--status-success)">${icons.success}</span>
      <span style="flex:1">${message}</span>
      <button class="toast-undo-btn" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);color:#fff;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap">UNDO</button>
      <div class="toast-countdown" style="position:absolute;bottom:0;left:0;height:3px;background:var(--accent-primary,#C9963C);width:100%;border-radius:0 0 8px 8px;transition:width linear"></div>
    `;

    const undoBtn = toast.querySelector('.toast-undo-btn');
    let undone = false;

    undoBtn.addEventListener('click', async () => {
      if (undone) return;
      undone = true;
      undoBtn.textContent = '...';
      undoBtn.disabled = true;
      try {
        await undoCallback(actionId);
        toast.querySelector('span:nth-child(2)').textContent = 'Action undone';
        undoBtn.style.display = 'none';
        setTimeout(() => {
          toast.style.animation = 'toast-out 0.3s ease forwards';
          setTimeout(() => toast.remove(), 300);
        }, 1500);
      } catch (err) {
        undoBtn.textContent = 'Failed';
        setTimeout(() => toast.remove(), 2000);
      }
    });

    this.container.appendChild(toast);

    // Animate countdown bar
    const bar = toast.querySelector('.toast-countdown');
    requestAnimationFrame(() => {
      bar.style.width = '0%';
      bar.style.transitionDuration = duration + 'ms';
    });

    // Auto-remove after duration
    setTimeout(() => {
      if (!undone) {
        toast.style.animation = 'toast-out 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
      }
    }, duration);

    return toast;
  },

  success(msg, dur) { return this.show(msg, 'success', dur); },
  error(msg, dur) { return this.show(msg, 'error', dur); },
  warning(msg, dur) { return this.show(msg, 'warning', dur); },
  info(msg, dur) { return this.show(msg, 'info', dur); }
};
