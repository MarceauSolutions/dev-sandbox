/* ============================================================
   Login Page — Client Portal
   ============================================================ */

const LoginPage = {
  title: 'Login',

  init() {
    // Check for token in URL params (magic link flow)
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const token = params.get('token');
    if (token) {
      localStorage.setItem('client_token', token);
      location.hash = '';
      return;
    }
  },

  render(container) {
    // If already authenticated, redirect to dashboard
    if (localStorage.getItem('client_token')) {
      location.hash = '';
      return;
    }

    container.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;min-height:80vh">
        <div class="card" style="max-width:400px;width:100%;text-align:center;padding:40px">
          <div style="font-size:48px;margin-bottom:16px">&#127769;</div>
          <h1 style="font-size:24px;font-weight:800;margin-bottom:8px;
            background:linear-gradient(135deg,#C9963C,#D4AF37);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">
            Marceau Solutions
          </h1>
          <p style="color:var(--text-secondary);margin-bottom:32px">Enter your access code to continue</p>
          <form id="login-form">
            <input type="text" id="access-code" class="form-input" placeholder="Paste your access code"
              style="text-align:center;font-size:16px;padding:14px;margin-bottom:16px" autocomplete="off">
            <button type="submit" id="login-btn" class="btn btn-primary btn-lg" style="width:100%">Sign In</button>
          </form>
          <p id="login-error" style="color:var(--status-error);font-size:13px;margin-top:16px;display:none"></p>
          <p style="color:var(--text-muted);font-size:12px;margin-top:24px">
            Don't have a code? Contact your coach.
          </p>
        </div>
      </div>
    `;

    document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const code = document.getElementById('access-code').value.trim();
      if (!code) return;

      const btn = document.getElementById('login-btn');
      const errEl = document.getElementById('login-error');
      errEl.style.display = 'none';
      btn.disabled = true;
      btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;display:inline-block"></div> Signing in...';

      // Store token and verify
      localStorage.setItem('client_token', code);
      try {
        await API.get('/api/client/me');
        location.hash = '';
        location.reload();
      } catch {
        localStorage.removeItem('client_token');
        errEl.textContent = 'Invalid access code. Please try again.';
        errEl.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Sign In';
      }
    });

    // Auto-focus the input
    setTimeout(() => {
      const input = document.getElementById('access-code');
      if (input) input.focus();
    }, 100);
  }
};
