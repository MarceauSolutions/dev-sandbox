/* ── LaunchPad Frontend ──────────────────────────────────────────────────── */

let activeProduct = null;
let refreshTimer  = null;
const REFRESH_INTERVAL = 30000; // 30 seconds

// ── Init ──────────────────────────────────────────────────────────────────

async function init() {
  await loadProducts();
  await refresh();
  startAutoRefresh();
}

// ── Products ──────────────────────────────────────────────────────────────

async function loadProducts() {
  try {
    const data = await api('/api/products');
    activeProduct = data.active;

    const sel = document.getElementById('productSelect');
    sel.innerHTML = '';
    (data.products || []).forEach(p => {
      const opt = document.createElement('option');
      opt.value    = p.id;
      opt.text     = p.label;
      opt.selected = (p.id === activeProduct);
      sel.appendChild(opt);
    });

    sel.addEventListener('change', () => {
      activeProduct = sel.value;
      refresh();
    });
  } catch (e) {
    console.error('loadProducts:', e);
  }
}

// ── Refresh ───────────────────────────────────────────────────────────────

async function refresh() {
  await Promise.all([
    loadState(),
    loadMetrics(),
    loadPlatforms(),
    loadConnections(),
  ]);
}

function startAutoRefresh() {
  clearInterval(refreshTimer);
  refreshTimer = setInterval(refresh, REFRESH_INTERVAL);
}

// ── State & Phases ────────────────────────────────────────────────────────

async function loadState() {
  try {
    const data = await api('/api/state' + productParam());
    renderPhases(data.phases || []);
    renderTimeMetric(data);
    renderGateDecision(data.gate_decision);
  } catch (e) {
    console.error('loadState:', e);
  }
}

function renderPhases(phases) {
  const el = document.getElementById('phaseTimeline');
  el.innerHTML = '';

  phases.forEach((phase, i) => {
    const step = document.createElement('div');
    step.className = `phase-step ${phase.status}`;

    const isLast = i === phases.length - 1;
    step.innerHTML = `
      <div class="phase-node">
        <div class="phase-circle">${phase.status === 'done' ? '✓' : phase.order}</div>
        <div class="phase-label">${phase.label}</div>
      </div>
      ${!isLast ? '<div class="phase-connector"></div>' : ''}
    `;
    el.appendChild(step);
  });
}

function renderTimeMetric(data) {
  document.getElementById('timeRemaining').textContent = data.time_remaining || '—';
  document.getElementById('timeBar').style.width = (data.pct_elapsed || 0) + '%';
  if (data.validation_started) {
    const d = new Date(data.validation_started);
    document.getElementById('validationStarted').textContent =
      'Started: ' + d.toLocaleString();
  }
}

function renderGateDecision(decision) {
  const el = document.getElementById('gateDecision');
  el.textContent = decision ? decision.toUpperCase() : 'PENDING';
  el.className = 'metric-value gate-value';
  if (decision === 'go')    el.classList.add('go');
  if (decision === 'pivot') el.classList.add('pivot');
  if (decision === 'no-go') el.classList.add('no-go');
}

// ── Metrics ───────────────────────────────────────────────────────────────

async function loadMetrics() {
  try {
    const data = await api('/api/metrics' + productParam());
    renderSignupMetric(data);
    renderPostsMetric(data);
    renderUTM(data.by_source || {});
  } catch (e) {
    console.error('loadMetrics:', e);
  }
}

function renderSignupMetric(data) {
  const count = data.signups || 0;
  const goal  = data.goal || 100;
  const pct   = Math.min(count / goal * 100, 100);

  document.getElementById('signupCount').textContent = count;
  document.getElementById('signupBar').style.width   = pct + '%';
  document.getElementById('signupGoal').textContent  = 'Goal: ' + goal;
  if (data.velocity) {
    document.getElementById('signupVelocity').textContent =
      `+${data.velocity.toFixed(1)}/hr velocity`;
  }
}

function renderPostsMetric(data) {
  const done  = data.posts_done  || 0;
  const total = data.posts_total || 10;
  const pct   = total ? Math.min(done / total * 100, 100) : 0;

  document.getElementById('postsCount').textContent = done + ' / ' + total;
  document.getElementById('postsBar').style.width   = pct + '%';
  document.getElementById('postsGoal').textContent  = `of ${total} platforms`;

  const milestones = data.milestones || [];
  if (milestones.length) {
    document.getElementById('milestonesHit').textContent =
      '🏁 ' + milestones.join(' · ');
  }
}

function renderUTM(bySource) {
  const section = document.getElementById('utmSection');
  const grid    = document.getElementById('utmGrid');
  const entries = Object.entries(bySource);

  if (!entries.length) {
    section.style.display = 'none';
    return;
  }

  section.style.display = '';
  grid.innerHTML = '';

  entries.sort((a, b) => b[1] - a[1]).forEach(([src, cnt]) => {
    const chip = document.createElement('div');
    chip.className = 'utm-chip';
    chip.innerHTML = `
      <span class="utm-source">${src}</span>
      <span class="utm-count">${cnt}</span>
    `;
    grid.appendChild(chip);
  });
}

// ── Platform Cards ────────────────────────────────────────────────────────

async function loadPlatforms() {
  try {
    const data = await api('/api/platforms' + productParam());
    renderPlatforms(data.platforms || []);
  } catch (e) {
    console.error('loadPlatforms:', e);
  }
}

function renderPlatforms(platforms) {
  const grid = document.getElementById('platformsGrid');
  grid.innerHTML = '';

  platforms.forEach(p => {
    const card = buildPlatformCard(p);
    grid.appendChild(card);
  });
}

function buildPlatformCard(p) {
  const card = document.createElement('div');
  card.className = `platform-card status-${p.status}`;
  card.id = `card-${p.key}`;

  // Badge: status
  const statusLabels = { done: 'Done', ready: 'Ready', scheduled: 'Scheduled' };
  const statusBadge = `<span class="badge badge-status-${p.status}">${statusLabels[p.status] || p.status}</span>`;

  // Badge: autonomy
  const autMap = { 3: 'auto', 2: 'browser', 1: 'manual' };
  const autCls = autMap[p.autonomy] || 'manual';
  const autBadge = `<span class="badge badge-${autCls}">${p.autonomy_label}</span>`;

  // Badge: connection
  const connMap = { connected: 'connected', pending: 'pending', not_connected: 'not-connected', manual: 'manual-conn' };
  const connLabel = { connected: 'Connected', pending: 'API Pending', not_connected: 'Not Connected', manual: 'Manual' };
  const connBadge = `<span class="badge badge-${connMap[p.connection] || 'manual-conn'}">${connLabel[p.connection] || 'Manual'}</span>`;

  // Image section
  let imageHtml;
  if (p.has_image) {
    imageHtml = `
      <div class="card-image">
        <img src="/api/content/${p.key}/image${productParam()}" alt="${p.label}" />
        <div class="generate-overlay">
          <button class="btn btn-sm btn-outline" onclick="generateImage('${p.key}', true)">Regenerate</button>
        </div>
      </div>`;
  } else if (p.image_style) {
    imageHtml = `
      <div class="card-image">
        <div class="card-image-placeholder">
          <span>No image yet</span>
        </div>
        <div class="generate-overlay">
          <button class="btn btn-sm btn-gold" onclick="generateImage('${p.key}')">Generate Image</button>
        </div>
      </div>`;
  } else {
    imageHtml = '';
  }

  // Copy section
  const copyHtml = `
    <div class="card-copy">
      ${p.copy_title ? `<div class="card-copy-title">${escHtml(p.copy_title)}</div>` : ''}
      ${p.copy_excerpt ? `<div class="card-copy-body">${escHtml(p.copy_excerpt)}</div>` : '<div class="card-copy-body" style="color:var(--text-muted)">No copy available</div>'}
    </div>`;

  // Time
  let timeHtml = '';
  if (p.post_time && p.status === 'scheduled') {
    const d = new Date(p.post_time);
    timeHtml = `<div class="card-time">Posts at: ${d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</div>`;
  } else if (p.done_at) {
    const d = new Date(p.done_at);
    timeHtml = `<div class="card-time">
      <span class="done-stamp">✓ Done ${d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span>
    </div>`;
  }

  // Actions
  let actionsHtml = buildCardActions(p);

  card.innerHTML = `
    <div class="card-header">
      <div class="card-meta">
        <div class="card-order">#${p.order}</div>
        <div class="card-title">${escHtml(p.label)}</div>
        <div class="card-badges">
          ${statusBadge}${autBadge}${connBadge}
        </div>
      </div>
    </div>
    ${imageHtml}
    ${copyHtml}
    ${timeHtml}
    <div class="card-actions">${actionsHtml}</div>
  `;

  return card;
}

function buildCardActions(p) {
  const actions = [];

  // View copy button
  actions.push(`<button class="btn btn-sm btn-outline" onclick="showCopy('${p.key}')">View Copy</button>`);

  // Image action (if no image yet and has style)
  if (!p.has_image && p.image_style) {
    actions.push(`<button class="btn btn-sm btn-outline" onclick="generateImage('${p.key}')">Gen Image</button>`);
  }

  // Download zip
  actions.push(`<a class="btn btn-sm btn-outline" href="/api/content/${p.key}/download${productParam()}" download>⬇ Download</a>`);

  // Post / Done actions
  if (p.status === 'done') {
    actions.push(`<button class="btn btn-sm btn-danger" onclick="unmarkDone('${p.key}')">Undo Done</button>`);
  } else if (p.status === 'ready') {
    actions.push(`<button class="btn btn-sm btn-gold" onclick="markDone('${p.key}')">✓ Mark Done</button>`);
  } else {
    actions.push(`<button class="btn btn-sm btn-ghost" onclick="markDone('${p.key}')" title="Mark done early">Mark Done</button>`);
  }

  return actions.join('');
}

// ── Connections Panel ─────────────────────────────────────────────────────

async function loadConnections() {
  try {
    const data = await api('/api/connections');
    renderConnections(data.connections || {});
  } catch (e) {
    console.error('loadConnections:', e);
  }
}

function renderConnections(connections) {
  const grid = document.getElementById('connectionsGrid');
  grid.innerHTML = '';

  Object.entries(connections).forEach(([ptype, info]) => {
    const card = document.createElement('div');
    card.className = 'connection-card';

    const dotClass = info.status.replace('_', '-');

    let keysHtml = '';
    if (info.keys && info.keys.length) {
      const present = info.present || (info.status === 'connected' ? info.keys : []);
      const missing = info.missing || (info.status === 'not_connected' ? info.keys : []);
      keysHtml = `<div class="conn-keys">
        ${present.map(k => `<span class="conn-key present">✓ ${k}</span>`).join('')}
        ${missing.map(k => `<span class="conn-key missing">✗ ${k}</span>`).join('')}
      </div>`;
    }

    const statusText = {
      connected: 'Connected — auto-post enabled',
      pending: info.note || 'API application pending',
      not_connected: 'Not connected — manual mode',
      manual: 'Manual only — no API',
    };

    card.innerHTML = `
      <div class="conn-header">
        <span class="conn-name">${ptype.replace('_', ' ')}</span>
        <span class="conn-status-dot ${info.status.replace('_','-')}"></span>
      </div>
      <div class="conn-note">${statusText[info.status] || info.status}</div>
      ${keysHtml}
    `;
    grid.appendChild(card);
  });
}

// ── Copy Modal ────────────────────────────────────────────────────────────

async function showCopy(key) {
  try {
    const data = await api(`/api/content/${key}/copy${productParam()}`);

    document.getElementById('modalTitle').textContent = data.label;

    const titleBlock = document.getElementById('modalCopyTitle');
    if (data.title) {
      titleBlock.style.display = '';
      document.getElementById('modalTitleText').textContent = data.title;
    } else {
      titleBlock.style.display = 'none';
    }

    document.getElementById('modalBodyText').textContent = data.body || data.raw || '(no copy)';

    document.getElementById('copyModal').classList.add('open');
  } catch (e) {
    toast('Failed to load copy', 'error');
  }
}

function closeCopyModal(event) {
  if (event && event.target !== document.getElementById('copyModal')) return;
  document.getElementById('copyModal').classList.remove('open');
}

function copyText(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    toast('Copied to clipboard!', 'success');
  });
}

// ── Actions ───────────────────────────────────────────────────────────────

async function markDone(key) {
  try {
    await api(`/api/mark/${key}${productParam()}`, { method: 'POST' });
    toast(`✓ Marked as done`, 'success');
    loadPlatforms();
    loadMetrics();
  } catch (e) {
    toast('Failed to mark done', 'error');
  }
}

async function unmarkDone(key) {
  try {
    await api(`/api/unmark/${key}${productParam()}`, { method: 'POST' });
    toast('Unmarked', 'success');
    loadPlatforms();
    loadMetrics();
  } catch (e) {
    toast('Failed to unmark', 'error');
  }
}

async function generateImage(key, force = false) {
  toast(`Generating image for ${key}…`);
  try {
    const data = await api(`/api/generate/${key}${productParam()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force }),
    });
    if (data.ok) {
      toast('Image generated!', 'success');
      loadPlatforms();
    } else {
      toast(data.error || 'Generation failed', 'error');
    }
  } catch (e) {
    toast('Image generation failed', 'error');
  }
}

async function generateAllImages() {
  toast('Generating all images… (~$0.42)');
  const { platforms } = await api('/api/platforms' + productParam());
  const needsImage = (platforms || []).filter(p => p.image_style && !p.has_image);
  for (const p of needsImage) {
    await generateImage(p.key);
  }
  toast('All images generated', 'success');
}

async function runGate() {
  const btn = document.getElementById('runGateBtn');
  btn.disabled = true;
  btn.textContent = 'Running…';
  try {
    const data = await api('/api/gate' + productParam(), { method: 'POST' });
    if (data.decision) {
      renderGateDecision(data.decision);
      toast(`Gate: ${data.decision.toUpperCase()}`, data.decision === 'go' ? 'success' : 'error');
    } else {
      toast('Gate ran — check output', 'success');
    }
    loadState();
  } catch (e) {
    toast('Gate evaluation failed', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Gate Now';
  }
}

async function downloadReport() {
  window.location.href = '/api/report' + productParam();
  toast('Generating report…');
}

// ── Helpers ───────────────────────────────────────────────────────────────

function productParam() {
  return activeProduct ? `?product=${activeProduct}` : '';
}

async function api(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

function escHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

let toastTimer;
function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show' + (type ? ' ' + type : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.remove('show');
  }, 3000);
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.getElementById('copyModal').classList.remove('open');
  }
  if (e.key === 'r' && !e.metaKey && !e.ctrlKey) {
    const active = document.activeElement;
    if (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA') return;
    refresh();
    toast('Refreshed');
  }
});

// ── Boot ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
