"""
KeyVault — UI Templates

Complete SaaS UI with landing page, auth, dashboard, and all management pages.
Mobile-first, dark + gold Marceau Solutions branding.
"""

import html
from datetime import datetime


def _esc(s) -> str:
    """HTML-escape user-supplied strings to prevent XSS."""
    return html.escape(str(s)) if s else ""

# ─── Brand ───────────────────────────────────────────────────
GOLD = "#C9963C"
CHARCOAL = "#333333"
DARK_BG = "#0d1117"
CARD_BG = "#161b22"
SURFACE = "#21262d"
BORDER = "#30363d"
TEXT = "#e6edf3"
TEXT_MUTED = "#8b949e"
RED = "#f85149"
GREEN = "#3fb950"
YELLOW = "#d29922"
BLUE = "#58a6ff"


def _status_badge(status: str) -> str:
    colors = {"active": GREEN, "expired": RED, "revoked": RED, "retired": TEXT_MUTED, "empty": YELLOW, "warning": YELLOW}
    c = colors.get(status, TEXT_MUTED)
    return f'<span class="badge" style="--badge-color:{c}">{status.upper()}</span>'


def _sync_badge(in_sync: bool) -> str:
    if in_sync:
        return f'<span class="badge" style="--badge-color:{GREEN}">SYNCED</span>'
    return f'<span class="badge" style="--badge-color:{RED}">DRIFTED</span>'


def _days_until(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        exp = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
        delta = (exp - datetime.now()).days
        if delta < 0:
            return f'<span style="color:{RED};font-weight:700">{abs(delta)}d overdue</span>'
        elif delta < 7:
            return f'<span style="color:{RED};font-weight:700">{delta}d</span>'
        elif delta < 30:
            return f'<span style="color:{YELLOW}">{delta}d</span>'
        return f'<span style="color:{GREEN}">{delta}d</span>'
    except Exception:
        return ""


def _health_dot(ok) -> str:
    if ok is None:
        return f'<span style="color:{TEXT_MUTED}" title="Not checked">○</span>'
    return f'<span style="color:{GREEN}" title="Healthy">●</span>' if ok else f'<span style="color:{RED}" title="Failed">●</span>'


# ─── Base CSS ────────────────────────────────────────────────
CSS = f"""
* {{ margin:0;padding:0;box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ background:{DARK_BG};color:{TEXT};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Roboto,sans-serif;line-height:1.5;font-size:14px; }}
a {{ color:{GOLD};text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.container {{ max-width:1200px;margin:0 auto;padding:16px 20px; }}
.flex {{ display:flex;align-items:center;gap:12px; }}
.flex-between {{ display:flex;align-items:center;justify-content:space-between; }}
.grid-2 {{ display:grid;grid-template-columns:1fr 1fr;gap:12px; }}
.grid-3 {{ display:grid;grid-template-columns:repeat(3,1fr);gap:12px; }}
.grid-4 {{ display:grid;grid-template-columns:repeat(4,1fr);gap:12px; }}

/* Nav */
.topnav {{ background:{CARD_BG};border-bottom:1px solid {BORDER};padding:0 20px;position:sticky;top:0;z-index:100; }}
.topnav-inner {{ max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:56px; }}
.logo {{ font-size:20px;font-weight:700;color:{GOLD};letter-spacing:-0.5px; }}
.logo span {{ color:{TEXT}; }}
.nav-links {{ display:flex;gap:4px; }}
.nav-links a {{ padding:8px 14px;border-radius:8px;font-size:13px;font-weight:500;color:{TEXT_MUTED};transition:all .15s; }}
.nav-links a:hover,.nav-links a.active {{ background:{SURFACE};color:{TEXT};text-decoration:none; }}
.nav-links a.active {{ color:{GOLD}; }}
.user-menu {{ font-size:13px;color:{TEXT_MUTED}; }}
.user-menu a {{ color:{GOLD};margin-left:12px; }}

/* Cards */
.card {{ background:{CARD_BG};border:1px solid {BORDER};border-radius:12px;padding:20px;margin-bottom:16px; }}
.card h2 {{ font-size:16px;font-weight:600;margin-bottom:12px;color:{TEXT}; }}
.card h3 {{ font-size:14px;font-weight:600;margin-bottom:8px;color:{TEXT}; }}
.card-header {{ display:flex;align-items:center;justify-content:space-between;margin-bottom:16px; }}

/* Stats */
.stat-grid {{ display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:20px; }}
.stat {{ background:{SURFACE};border:1px solid {BORDER};border-radius:10px;padding:14px;text-align:center; }}
.stat .value {{ font-size:28px;font-weight:700;color:{GOLD}; }}
.stat .label {{ font-size:11px;color:{TEXT_MUTED};margin-top:2px;text-transform:uppercase;letter-spacing:0.5px; }}
.stat.alert .value {{ color:{RED}; }}
.stat.warn .value {{ color:{YELLOW}; }}
.stat.ok .value {{ color:{GREEN}; }}

/* Tables */
table {{ width:100%;border-collapse:collapse; }}
th {{ text-align:left;padding:10px 12px;color:{TEXT_MUTED};font-size:11px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid {BORDER}; }}
td {{ padding:10px 12px;border-bottom:1px solid rgba(48,54,61,0.5);font-size:13px; }}
tr:hover td {{ background:rgba(201,150,60,0.03); }}
code {{ background:{SURFACE};padding:2px 6px;border-radius:4px;font-size:12px;font-family:'SF Mono',Menlo,monospace; }}

/* Badges */
.badge {{ display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;background:color-mix(in srgb,var(--badge-color) 20%,transparent);color:var(--badge-color);border:1px solid color-mix(in srgb,var(--badge-color) 30%,transparent); }}
.category-tag {{ background:{SURFACE};padding:2px 8px;border-radius:6px;font-size:11px;color:{GOLD};border:1px solid rgba(201,150,60,0.2); }}

/* Forms */
input,select,textarea {{ background:{SURFACE};color:{TEXT};border:1px solid {BORDER};border-radius:8px;padding:10px 14px;font-size:14px;width:100%;transition:border-color .15s;font-family:inherit; }}
input:focus,select:focus,textarea:focus {{ outline:none;border-color:{GOLD};box-shadow:0 0 0 3px rgba(201,150,60,0.1); }}
label {{ font-size:12px;color:{TEXT_MUTED};margin-bottom:4px;display:block;font-weight:500; }}
.form-group {{ margin-bottom:14px; }}
.form-grid {{ display:grid;grid-template-columns:1fr 1fr;gap:14px; }}

/* Buttons */
.btn {{ display:inline-flex;align-items:center;gap:6px;padding:10px 20px;border-radius:8px;font-weight:600;font-size:14px;cursor:pointer;border:none;transition:all .15s;text-decoration:none;font-family:inherit; }}
.btn:hover {{ text-decoration:none;opacity:0.9; }}
.btn-primary {{ background:{GOLD};color:{CHARCOAL}; }}
.btn-secondary {{ background:{SURFACE};color:{TEXT};border:1px solid {BORDER}; }}
.btn-danger {{ background:rgba(248,81,73,0.15);color:{RED};border:1px solid rgba(248,81,73,0.3); }}
.btn-sm {{ padding:6px 12px;font-size:12px; }}
.btn-ghost {{ background:transparent;color:{TEXT_MUTED};padding:6px 12px;font-size:12px; }}
.btn-ghost:hover {{ color:{TEXT};background:{SURFACE}; }}

/* Alerts */
.alert {{ padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:13px; }}
.alert-error {{ background:rgba(248,81,73,0.1);border:1px solid rgba(248,81,73,0.3);color:{RED}; }}
.alert-warn {{ background:rgba(210,153,34,0.1);border:1px solid rgba(210,153,34,0.3);color:{YELLOW}; }}
.alert-success {{ background:rgba(63,185,80,0.1);border:1px solid rgba(63,185,80,0.3);color:{GREEN}; }}

/* Misc */
.muted {{ color:{TEXT_MUTED};font-size:12px; }}
.empty-state {{ text-align:center;padding:60px 20px;color:{TEXT_MUTED}; }}
.empty-state h3 {{ font-size:18px;margin-bottom:8px;color:{TEXT}; }}
.divider {{ border:none;border-top:1px solid {BORDER};margin:20px 0; }}
.consumers {{ font-size:11px;color:{TEXT_MUTED}; }}
.pill {{ display:inline-block;background:{SURFACE};border:1px solid {BORDER};padding:4px 10px;border-radius:16px;font-size:12px;margin:2px; }}
.reveal-btn {{ cursor:pointer;color:{GOLD};font-size:12px; }}

@media(max-width:768px) {{
    .form-grid {{ grid-template-columns:1fr; }}
    .stat-grid {{ grid-template-columns:repeat(2,1fr); }}
    .grid-2,.grid-3,.grid-4 {{ grid-template-columns:1fr; }}
    .nav-links {{ overflow-x:auto;flex-wrap:nowrap; }}
    .nav-links a {{ white-space:nowrap;font-size:12px;padding:6px 10px; }}
    .topnav-inner {{ flex-direction:column;height:auto;padding:10px 0;gap:8px; }}
    td,th {{ padding:6px 8px;font-size:12px; }}
    .hide-mobile {{ display:none; }}
}}
"""


# ─── Page shell ──────────────────────────────────────────────

def _shell(title: str, content: str, nav: str = "", active_tab: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — KeyVault™</title>
<style>{CSS}</style>
</head><body>
{nav}
<div class="container">{content}</div>
<script>
function revealKey(keyId) {{
    fetch('/keys/' + keyId + '/reveal', {{method:'POST'}})
        .then(r => r.json())
        .then(d => {{
            let el = document.getElementById('val-' + keyId);
            if (el) {{ el.textContent = d.value; el.style.color = '{YELLOW}'; }}
        }}).catch(e => alert('Access denied or no stored value'));
}}
function copyKey(keyId) {{
    fetch('/keys/' + keyId + '/reveal', {{method:'POST'}})
        .then(r => r.json())
        .then(d => {{
            navigator.clipboard.writeText(d.value);
            let btn = document.getElementById('copy-' + keyId);
            if (btn) {{ btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = 'Copy', 1500); }}
        }}).catch(e => alert('Access denied'));
}}
</script>
</body></html>"""


def _nav(active: str = "", user: dict = None) -> str:
    tabs = [
        ("dashboard", "Dashboard"), ("keys", "Keys"), ("services", "Services"),
        ("environments", "Envs"), ("deprecations", "Deprecations"),
        ("reminders", "Reminders"), ("audit", "Audit"), ("settings", "Settings"),
    ]
    links = ""
    for tab_id, label in tabs:
        cls = ' class="active"' if tab_id == active else ""
        links += f'<a href="/{tab_id}"{cls}>{label}</a>'

    user_info = ""
    if user:
        user_info = f'<div class="user-menu">{_esc(user.get("email", ""))} <a href="/billing">Billing</a> <a href="/logout">Log out</a></div>'

    return f"""<nav class="topnav"><div class="topnav-inner">
        <a href="/dashboard" class="logo">Key<span>Vault™</span></a>
        <div class="nav-links">{links}</div>
        {user_info}
    </div></nav>"""


# ─── Page renderers ──────────────────────────────────────────

def render_landing() -> str:
    content = f"""
    <nav class="topnav"><div class="topnav-inner">
        <a href="/" class="logo">Key<span>Vault™</span></a>
        <div class="nav-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="/login">Log In</a>
            <a href="/signup" style="background:{GOLD};color:{CHARCOAL};border-radius:8px">Sign Up Free</a>
        </div>
    </div></nav>

    <div class="container">
    <!-- Hero -->
    <div style="text-align:center;padding:80px 20px 60px">
        <h1 style="font-size:48px;font-weight:800;line-height:1.1;margin-bottom:16px">
            Stop losing access.<br><span style="color:{GOLD}">Manage every API key.</span>
        </h1>
        <p style="font-size:18px;color:{TEXT_MUTED};max-width:600px;margin:0 auto 32px">
            KeyVault™ tracks every credential across every environment. Get alerts before keys expire,
            catch drift between servers, and never debug a "key expired" error at 2am again.
        </p>
        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
            <a href="/signup" class="btn btn-primary" style="padding:14px 32px;font-size:16px">Start Free — 25 Keys</a>
            <a href="#features" class="btn btn-secondary" style="padding:14px 32px;font-size:16px">See Features</a>
        </div>
        <p class="muted" style="margin-top:16px">No credit card required. Free forever for small teams.</p>
    </div>

    <!-- Social proof -->
    <div style="text-align:center;padding:20px;margin-bottom:40px">
        <div style="display:flex;gap:40px;justify-content:center;flex-wrap:wrap;color:{TEXT_MUTED}">
            <div><span style="font-size:24px;font-weight:700;color:{GOLD}">67+</span><br>Keys tracked</div>
            <div><span style="font-size:24px;font-weight:700;color:{GOLD}">30+</span><br>Services</div>
            <div><span style="font-size:24px;font-weight:700;color:{GOLD}">0</span><br>Surprise expirations</div>
            <div><span style="font-size:24px;font-weight:700;color:{GOLD}">AES-256</span><br>Encryption</div>
        </div>
    </div>

    <!-- Features -->
    <div id="features" style="padding:40px 0">
        <h2 style="text-align:center;font-size:28px;margin-bottom:32px">Everything you need to manage credentials</h2>
        <div class="grid-3" style="gap:20px">
            <div class="card">
                <h3 style="color:{GOLD}">🔐 Encrypted Storage</h3>
                <p class="muted">Store actual key values with Fernet (AES-256) encryption at rest. Reveal with one click, copy to clipboard. Role-based access control.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">🔄 Environment Sync</h3>
                <p class="muted">Track credentials across dev, staging, production, and custom environments. Detect drift automatically. One-click sync.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">⏰ Expiration Alerts</h3>
                <p class="muted">Get notified 14 days before any key expires via email, SMS, Telegram, or webhook. Never scramble for a renewal again.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">📊 Health Monitoring</h3>
                <p class="muted">Automated health checks verify your keys actually work. Catch revoked or rate-limited credentials before your users do.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">⚠️ Deprecation Tracking</h3>
                <p class="muted">Log API deprecation notices with migration notes and deadlines. Track resolution status across your team.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">👥 Multi-Tenant</h3>
                <p class="muted">Organizations, team members with role-based access (owner, admin, member, viewer). Full audit log of every action.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">🔑 API Access</h3>
                <p class="muted">RESTful API with bearer token auth. Integrate KeyVault™ into your CI/CD, monitoring, and automation pipelines.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">📱 Mobile First</h3>
                <p class="muted">Fully responsive dashboard. Check key status, get alerts, and manage credentials from your phone.</p>
            </div>
            <div class="card">
                <h3 style="color:{GOLD}">📋 Audit Trail</h3>
                <p class="muted">Every key creation, reveal, deletion, and setting change is logged with user, timestamp, and IP address.</p>
            </div>
        </div>
    </div>

    <!-- Pricing -->
    <div id="pricing" style="padding:60px 0">
        <h2 style="text-align:center;font-size:28px;margin-bottom:8px">Simple, transparent pricing</h2>
        <p style="text-align:center;color:{TEXT_MUTED};margin-bottom:32px">Start free. Upgrade when you need more.</p>
        <div class="grid-3" style="gap:20px;max-width:900px;margin:0 auto">
            <div class="card" style="text-align:center;border-color:{BORDER}">
                <h3 style="margin-bottom:4px">Free</h3>
                <div style="font-size:36px;font-weight:800;color:{TEXT};margin:8px 0">$0</div>
                <p class="muted" style="margin-bottom:20px">Forever free for solo devs</p>
                <div style="text-align:left">
                    <div class="pill">25 API keys</div>
                    <div class="pill">2 environments</div>
                    <div class="pill">1 team member</div>
                    <div class="pill">Encrypted storage</div>
                    <div class="pill">Expiry alerts</div>
                    <div class="pill">Dashboard</div>
                </div>
                <a href="/signup" class="btn btn-secondary" style="margin-top:20px;width:100%;justify-content:center">Get Started</a>
            </div>
            <div class="card" style="text-align:center;border-color:{GOLD};border-width:2px;position:relative">
                <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:{GOLD};color:{CHARCOAL};padding:2px 16px;border-radius:12px;font-size:12px;font-weight:700">POPULAR</div>
                <h3 style="margin-bottom:4px;color:{GOLD}">Pro</h3>
                <div style="font-size:36px;font-weight:800;color:{GOLD};margin:8px 0">$29<span style="font-size:16px;color:{TEXT_MUTED}">/mo</span></div>
                <p class="muted" style="margin-bottom:20px">For teams and agencies</p>
                <div style="text-align:left">
                    <div class="pill">100 API keys</div>
                    <div class="pill">10 environments</div>
                    <div class="pill">5 team members</div>
                    <div class="pill">Health monitoring</div>
                    <div class="pill">API access</div>
                    <div class="pill">Webhook alerts</div>
                    <div class="pill">Priority support</div>
                </div>
                <a href="/signup" class="btn btn-primary" style="margin-top:20px;width:100%;justify-content:center">Start Pro Trial</a>
            </div>
            <div class="card" style="text-align:center;border-color:{BORDER}">
                <h3 style="margin-bottom:4px">Enterprise</h3>
                <div style="font-size:36px;font-weight:800;color:{TEXT};margin:8px 0">$99<span style="font-size:16px;color:{TEXT_MUTED}">/mo</span></div>
                <p class="muted" style="margin-bottom:20px">For organizations at scale</p>
                <div style="text-align:left">
                    <div class="pill">1,000 API keys</div>
                    <div class="pill">50 environments</div>
                    <div class="pill">25 team members</div>
                    <div class="pill">SSO / SAML</div>
                    <div class="pill">Custom health checks</div>
                    <div class="pill">SLA guarantee</div>
                    <div class="pill">Dedicated support</div>
                </div>
                <a href="/signup" class="btn btn-secondary" style="margin-top:20px;width:100%;justify-content:center">Contact Sales</a>
            </div>
        </div>
    </div>

    <!-- CTA -->
    <div style="text-align:center;padding:60px 20px;border-top:1px solid {BORDER}">
        <h2 style="font-size:28px;margin-bottom:12px">Ready to stop fighting expired keys?</h2>
        <p style="color:{TEXT_MUTED};margin-bottom:24px">Join teams who trust KeyVault™ to manage their credentials.</p>
        <a href="/signup" class="btn btn-primary" style="padding:14px 40px;font-size:16px">Start Free Today</a>
    </div>

    <!-- Footer -->
    <footer style="text-align:center;padding:30px;border-top:1px solid {BORDER};color:{TEXT_MUTED};font-size:12px">
        <p>KeyVault™ by <a href="https://marceausolutions.com" style="color:{GOLD}">Marceau Solutions™</a> — Embrace the Pain &amp; Defy the Odds</p>
        <p style="margin-top:4px">© {datetime.now().year} Marceau Solutions™ LLC. All rights reserved.</p>
    </footer>
    </div>"""

    return f"""<!DOCTYPE html><html lang="en"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>KeyVault™ — API Key Management Platform</title>
    <meta name="description" content="Stop losing API access. KeyVault™ tracks every credential across every environment with encrypted storage, expiration alerts, and health monitoring.">
    <style>{CSS}</style>
    </head><body>{content}</body></html>"""


def render_page(page: str, title: str, data: dict, error: str = "") -> str:
    user = data.get("user")
    nav = _nav(page, user) if user else ""
    error_html = f'<div class="alert alert-error">{html.escape(error)}</div>' if error else ""

    if page == "login":
        return _shell(title, error_html + _login_page(), nav)
    elif page == "signup":
        return _shell(title, error_html + _signup_page(), nav)
    elif page == "onboarding":
        return _shell(title, _onboarding_page(data), nav)
    elif page == "dashboard":
        return _shell(title, error_html + _dashboard_page(data), nav, "dashboard")
    elif page == "keys":
        return _shell(title, error_html + _keys_page(data), nav, "keys")
    elif page == "add_key":
        return _shell(title, _add_key_page(data), nav, "keys")
    elif page == "key_detail":
        return _shell(title, _key_detail_page(data), nav, "keys")
    elif page == "services":
        return _shell(title, _services_page(data), nav, "services")
    elif page == "environments":
        return _shell(title, error_html + _environments_page(data), nav, "environments")
    elif page == "deprecations":
        return _shell(title, _deprecations_page(data), nav, "deprecations")
    elif page == "reminders":
        return _shell(title, _reminders_page(data), nav, "reminders")
    elif page == "audit":
        return _shell(title, _audit_page(data), nav, "audit")
    elif page == "settings":
        return _shell(title, error_html + _settings_page(data), nav, "settings")
    elif page == "billing":
        return _shell(title, error_html + _billing_page(data), nav)
    elif page == "token_created":
        return _shell(title, _token_created_page(data), nav, "settings")
    return _shell(title, "<p>Page not found</p>", nav)


# ─── Auth pages ──────────────────────────────────────────────

def _login_page() -> str:
    return f"""
    <div style="max-width:400px;margin:80px auto">
        <div style="text-align:center;margin-bottom:32px">
            <div class="logo" style="font-size:28px;margin-bottom:8px">Key<span>Vault</span></div>
            <p class="muted">Log in to your account</p>
        </div>
        <div class="card">
            <form method="POST" action="/login">
                <div class="form-group"><label>Email</label><input type="email" name="email" required autofocus></div>
                <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">Log In</button>
            </form>
        </div>
        <p style="text-align:center;margin-top:16px" class="muted">Don't have an account? <a href="/signup">Sign up free</a></p>
    </div>"""


def _signup_page() -> str:
    return f"""
    <div style="max-width:400px;margin:60px auto">
        <div style="text-align:center;margin-bottom:32px">
            <div class="logo" style="font-size:28px;margin-bottom:8px">Key<span>Vault</span></div>
            <p class="muted">Create your account — free forever for solo devs</p>
        </div>
        <div class="card">
            <form method="POST" action="/signup">
                <div class="form-group"><label>Your Name</label><input type="text" name="name" required autofocus placeholder="William Marceau"></div>
                <div class="form-group"><label>Organization Name</label><input type="text" name="org_name" required placeholder="Marceau Solutions"></div>
                <div class="form-group"><label>Email</label><input type="email" name="email" required placeholder="you@company.com"></div>
                <div class="form-group"><label>Password (8+ characters)</label><input type="password" name="password" required minlength="8"></div>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">Create Account</button>
            </form>
        </div>
        <p style="text-align:center;margin-top:16px" class="muted">Already have an account? <a href="/login">Log in</a></p>
    </div>"""


def _onboarding_page(data: dict) -> str:
    return f"""
    <div style="max-width:600px;margin:60px auto">
        <div style="text-align:center;margin-bottom:32px">
            <h1 style="font-size:28px;margin-bottom:8px">Welcome to KeyVault!</h1>
            <p class="muted">Let's get you set up in 3 steps.</p>
        </div>
        <div class="card">
            <h2>Step 1: Add your first service</h2>
            <p class="muted" style="margin-bottom:16px">A service is any external API you connect to (Stripe, AWS, OpenAI, etc.)</p>
            <a href="/keys/add" class="btn btn-primary">Add Your First Key</a>
        </div>
        <div class="card">
            <h2>Step 2: Set up environments</h2>
            <p class="muted" style="margin-bottom:16px">Track where your keys are deployed (local dev, staging, production).</p>
            <a href="/environments" class="btn btn-secondary">Configure Environments</a>
        </div>
        <div class="card">
            <h2>Step 3: Enable notifications</h2>
            <p class="muted" style="margin-bottom:16px">Get alerted when keys expire or environments drift out of sync.</p>
            <a href="/settings" class="btn btn-secondary">Set Up Alerts</a>
        </div>
        <div style="text-align:center;margin-top:24px">
            <a href="/dashboard" class="btn btn-ghost">Skip — go to dashboard →</a>
        </div>
    </div>"""


# ─── Dashboard ───────────────────────────────────────────────

def _dashboard_page(data: dict) -> str:
    s = data["summary"]
    expiring = data.get("expiring", [])
    deprecations = data.get("deprecations", [])
    limits = data.get("limits", {})
    audit = data.get("audit", [])

    # Stats
    stats = f"""<div class="stat-grid">
        <div class="stat"><div class="value">{s['total_active_keys']}</div><div class="label">Active Keys</div></div>
        <div class="stat"><div class="value">{s['total_services']}</div><div class="label">Services</div></div>
        <div class="stat"><div class="value">{s['total_consumers']}</div><div class="label">Consumers</div></div>
        <div class="stat {'alert' if s['out_of_sync_envs']>0 else 'ok'}"><div class="value">{s['out_of_sync_envs']}</div><div class="label">Out of Sync</div></div>
        <div class="stat {'warn' if s['expiring_within_30d']>0 else 'ok'}"><div class="value">{s['expiring_within_30d']}</div><div class="label">Expiring (30d)</div></div>
        <div class="stat {'alert' if s['expired_keys']>0 else 'ok'}"><div class="value">{s['expired_keys']}</div><div class="label">Expired</div></div>
        <div class="stat"><div class="value">${s['monthly_cost']:.0f}</div><div class="label">Monthly Cost</div></div>
        <div class="stat {'ok' if s['healthy_keys']>0 else ''}"><div class="value">{s['healthy_keys']}/{s['healthy_keys']+s['unhealthy_keys']}</div><div class="label">Healthy</div></div>
    </div>"""

    # Alerts
    alerts = ""
    if s['out_of_sync_envs'] > 0:
        alerts += f'<div class="alert alert-error">{s["out_of_sync_envs"]} credential(s) out of sync. <a href="/environments">Fix now →</a></div>'
    if s['expiring_within_30d'] > 0:
        alerts += f'<div class="alert alert-warn">{s["expiring_within_30d"]} key(s) expiring within 30 days.</div>'

    # Usage bar
    usage_pct = int((limits.get('current_keys', 0) / max(limits.get('max_keys', 1), 1)) * 100)
    usage_color = GREEN if usage_pct < 75 else (YELLOW if usage_pct < 90 else RED)
    usage = f"""<div class="card">
        <div class="flex-between"><h3>Plan Usage</h3><span class="muted">{limits.get('plan','free').upper()} plan</span></div>
        <div style="margin-top:8px">
            <div class="flex-between muted"><span>Keys: {limits.get('current_keys',0)}/{limits.get('max_keys',25)}</span><span>{usage_pct}%</span></div>
            <div style="background:{SURFACE};border-radius:4px;height:6px;margin-top:4px">
                <div style="background:{usage_color};height:6px;border-radius:4px;width:{min(usage_pct,100)}%"></div>
            </div>
        </div>
    </div>"""

    # Expiring table
    exp_section = ""
    if expiring:
        rows = ""
        for k in expiring:
            rows += f"<tr><td>{_esc(k['service_name'])}</td><td><code>{_esc(k['env_var_name'])}</code></td><td>{_days_until(k['expires_at'])}</td><td>{_esc(k['expires_at'][:10] if k['expires_at'] else '')}</td></tr>"
        exp_section = f'<div class="card"><h2>Expiring Soon</h2><table><tr><th>Service</th><th>Key</th><th>Time Left</th><th>Date</th></tr>{rows}</table></div>'

    # Recent activity
    activity = ""
    if audit:
        rows = ""
        for a in audit[:8]:
            rows += f"<tr><td class='muted'>{_esc(a['created_at'][:16] if a['created_at'] else '')}</td><td>{_esc(a['action'])}</td><td class='muted'>{_esc(a['details'] or '')}</td></tr>"
        activity = f'<div class="card"><div class="card-header"><h2>Recent Activity</h2><a href="/audit" class="btn btn-ghost">View all</a></div><table><tr><th>Time</th><th>Action</th><th>Details</th></tr>{rows}</table></div>'

    return stats + alerts + usage + exp_section + activity


# ─── Keys page ───────────────────────────────────────────────

def _keys_page(data: dict) -> str:
    keys = data.get("keys", [])
    limits = data.get("limits", {})

    header = f"""<div class="card-header" style="margin-bottom:16px">
        <h2 style="margin:0">API Keys ({len(keys)})</h2>
        <a href="/keys/add" class="btn btn-primary btn-sm">+ Add Key</a>
    </div>"""

    if not keys:
        return header + '<div class="empty-state"><h3>No keys yet</h3><p class="muted">Add your first API key to start tracking.</p><a href="/keys/add" class="btn btn-primary" style="margin-top:16px">Add Your First Key</a></div>'

    rows = ""
    for k in keys:
        has_value = "🔐" if k.get("encrypted_value") else ""
        rows += f"""<tr>
            <td><span class="category-tag">{_esc(k['category'])}</span></td>
            <td><a href="/keys/{k['id']}"><strong>{_esc(k['service_name'])}</strong></a></td>
            <td><code>{_esc(k['env_var_name'])}</code> {has_value}</td>
            <td>{_status_badge(k['status'])}</td>
            <td>{_health_dot(k.get('last_verified_ok'))}</td>
            <td>{_days_until(k.get('expires_at',''))}</td>
            <td class="consumers hide-mobile">{_esc(k.get('consumers') or '—')}</td>
            <td class="hide-mobile">{'$'+str(k['monthly_cost']) if k.get('monthly_cost') else ''}</td>
        </tr>"""

    return header + f"""<div class="card" style="overflow-x:auto">
        <table><tr><th>Category</th><th>Service</th><th>Variable</th><th>Status</th><th>Health</th><th>Expires</th><th class="hide-mobile">Used By</th><th class="hide-mobile">Cost</th></tr>
        {rows}</table></div>"""


def _add_key_page(data: dict) -> str:
    services = data.get("services", [])
    opts = '<option value="">— Select existing service —</option>'
    for s in services:
        opts += f'<option value="{s["id"]}">{_esc(s["name"])}</option>'

    return f"""
    <div style="max-width:700px;margin:0 auto">
    <div class="card-header"><h2 style="margin:0">Add API Key</h2><a href="/keys" class="btn btn-ghost">← Back</a></div>
    <div class="card">
        <form method="POST" action="/keys/add">
            <div class="form-grid">
                <div class="form-group"><label>Existing Service</label><select name="service_id">{opts}</select></div>
                <div class="form-group"><label>Or New Service Name</label><input type="text" name="new_service_name" placeholder="e.g. Slack"></div>
                <div class="form-group"><label>Category</label>
                    <select name="category"><option value="ai">AI & Content</option><option value="communication">Communication</option><option value="business">Business & Payments</option><option value="social">Social Media</option><option value="monitoring">Monitoring</option><option value="infrastructure">Infrastructure</option><option value="other" selected>Other</option></select>
                </div>
                <div class="form-group"><label>Environment Variable *</label><input type="text" name="env_var_name" required placeholder="e.g. SLACK_API_KEY"></div>
                <div class="form-group"><label>Display Label</label><input type="text" name="label" placeholder="Friendly name (optional)"></div>
                <div class="form-group"><label>Key Type</label>
                    <select name="key_type"><option value="api_key">API Key</option><option value="secret_key">Secret Key</option><option value="access_token">Access Token</option><option value="refresh_token">Refresh Token</option><option value="oauth_client_id">OAuth Client ID</option><option value="oauth_client_secret">OAuth Client Secret</option><option value="bearer_token">Bearer Token</option><option value="bot_token">Bot Token</option><option value="webhook_secret">Webhook Secret</option><option value="app_password">App Password</option><option value="config">Config Value</option></select>
                </div>
            </div>
            <div class="form-group"><label>Key Value (encrypted at rest — optional)</label><input type="password" name="key_value" placeholder="sk-abc123... (stored encrypted with AES-256)"></div>
            <div class="form-grid">
                <div class="form-group"><label>Status</label><select name="status"><option value="active">Active</option><option value="empty">Empty</option><option value="retired">Retired</option></select></div>
                <div class="form-group"><label>Expires At</label><input type="date" name="expires_at"></div>
                <div class="form-group"><label>Monthly Cost ($)</label><input type="number" step="0.01" name="monthly_cost" placeholder="0.00"></div>
                <div class="form-group"><label>Dashboard URL</label><input type="url" name="dashboard_url" placeholder="https://console.example.com"></div>
            </div>
            <div class="form-group"><label>Notes</label><textarea name="notes" rows="2" placeholder="Renewal process, rate limits, usage notes..."></textarea></div>
            <div style="margin-top:8px"><button type="submit" class="btn btn-primary">Add Key</button></div>
        </form>
    </div></div>"""


def _key_detail_page(data: dict) -> str:
    k = data["key"]
    consumers = data.get("consumers", [])
    health = data.get("health", [])
    syncs = data.get("syncs", [])

    # Key info
    has_value = k.get("encrypted_value")
    value_section = ""
    if has_value:
        value_section = f"""<div class="form-group" style="margin-top:12px">
            <label>Stored Value</label>
            <div class="flex" style="gap:8px">
                <code id="val-{k['id']}" style="flex:1;padding:8px 12px">••••••••••••••••</code>
                <button onclick="revealKey({k['id']})" class="btn btn-sm btn-secondary">Reveal</button>
                <button id="copy-{k['id']}" onclick="copyKey({k['id']})" class="btn btn-sm btn-secondary">Copy</button>
            </div>
        </div>"""

    # Validate dashboard URL — only allow http/https in href
    _dash_url = k.get('dashboard_url') or ''
    _safe_dash = _dash_url if _dash_url.startswith(('http://', 'https://')) else ''

    info = f"""<div class="card">
        <div class="card-header">
            <div>
                <span class="category-tag">{_esc(k['category'])}</span>
                <h2 style="margin-top:8px">{_esc(k['service_name'])} — {_esc(k['label'])}</h2>
            </div>
            <div class="flex" style="gap:8px">
                {_status_badge(k['status'])}
                <form method="POST" action="/keys/{k['id']}/delete" onsubmit="return confirm('Delete this key?')">
                    <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                </form>
            </div>
        </div>
        <div class="grid-2">
            <div><label>Env Variable</label><code>{_esc(k['env_var_name'])}</code></div>
            <div><label>Key Type</label>{_esc(k['key_type'])}</div>
            <div><label>Auth Protocol</label>{_esc(k.get('auth_protocol') or '—')}</div>
            <div><label>Expires</label>{_esc(k.get('expires_at') or 'Never')} {_days_until(k.get('expires_at',''))}</div>
            <div><label>Monthly Cost</label>{'$'+str(k['monthly_cost']) if k.get('monthly_cost') else 'Free'}</div>
            <div><label>Last Verified</label>{_esc(k.get('last_verified_at') or 'Never')} {_health_dot(k.get('last_verified_ok'))}</div>
        </div>
        {value_section}
        {'<div style="margin-top:12px"><label>Notes</label><p class="muted">'+_esc(k['notes'])+'</p></div>' if k.get('notes') else ''}
        {'<div style="margin-top:12px"><label>Dashboard</label><a href="'+_safe_dash+'" target="_blank">'+_esc(_dash_url)+'</a></div>' if _safe_dash else ''}
    </div>"""

    # Consumers
    consumer_rows = ""
    for c in consumers:
        consumer_rows += f"<tr><td>{_esc(c['consumer_type'])}</td><td>{_esc(c['consumer_name'])}</td><td class='muted'>{_esc(c.get('consumer_path') or '')}</td><td class='muted'>{_esc(c.get('notes') or '')}</td></tr>"
    consumer_section = f"""<div class="card"><h2>Consumers ({len(consumers)})</h2>
        {'<table><tr><th>Type</th><th>Name</th><th>Path</th><th>Notes</th></tr>'+consumer_rows+'</table>' if consumer_rows else '<p class="muted">No consumers tracked yet.</p>'}
    </div>"""

    # Sync status
    sync_rows = ""
    for s in syncs:
        sync_rows += f"<tr><td>{_esc(s['env_name'])}</td><td>{_sync_badge(s['in_sync'])}</td><td class='muted'>{_esc(s.get('last_checked_at') or 'Never')}</td></tr>"
    sync_section = f"""<div class="card"><h2>Environment Sync</h2>
        {'<table><tr><th>Environment</th><th>Status</th><th>Last Checked</th></tr>'+sync_rows+'</table>' if sync_rows else '<p class="muted">No environments configured.</p>'}
    </div>"""

    # Health history
    health_rows = ""
    for h in health:
        health_rows += f"<tr><td class='muted'>{_esc(h['created_at'][:16])}</td><td>{_health_dot(h['is_healthy'])}</td><td>{h.get('response_ms') or ''}ms</td><td class='muted'>{_esc(h.get('error_message') or '')}</td></tr>"
    health_section = f"""<div class="card"><h2>Health History</h2>
        {'<table><tr><th>Time</th><th>Status</th><th>Latency</th><th>Error</th></tr>'+health_rows+'</table>' if health_rows else '<p class="muted">No health checks run yet.</p>'}
    </div>"""

    return f'<a href="/keys" class="btn btn-ghost" style="margin-bottom:16px">← Back to Keys</a>' + info + consumer_section + sync_section + health_section


# ─── Services page ───────────────────────────────────────────

def _services_page(data: dict) -> str:
    services = data.get("services", [])
    rows = ""
    for s in services:
        _svc_dash = s.get("dashboard_url") or ""
        _svc_safe_dash = _svc_dash if _svc_dash.startswith(('http://', 'https://')) else ''
        dash = f'<a href="{_svc_safe_dash}" target="_blank" class="btn btn-ghost btn-sm">Open →</a>' if _svc_safe_dash else "—"
        rows += f"""<tr>
            <td><span class="category-tag">{_esc(s['category'])}</span></td>
            <td><strong>{_esc(s['name'])}</strong></td>
            <td>{s['key_count']} keys ({s.get('active_count',0)} active)</td>
            <td>{dash}</td>
            <td class="muted hide-mobile">{_esc(s.get('notes') or '')}</td>
        </tr>"""
    return f"""<div class="card"><h2>Services ({len(services)})</h2>
        <table><tr><th>Category</th><th>Service</th><th>Keys</th><th>Dashboard</th><th class="hide-mobile">Notes</th></tr>{rows}</table></div>"""


# ─── Environments page ──────────────────────────────────────

def _environments_page(data: dict) -> str:
    envs = data.get("envs", [])
    syncs = data.get("syncs", [])
    limits = data.get("limits", {})

    env_rows = ""
    for e in envs:
        env_rows += f"<tr><td><strong>{_esc(e['name'])}</strong></td><td class='muted'>{_esc(e.get('env_file_path') or '')}</td><td class='muted'>{_esc(e.get('last_synced_at') or 'Never')}</td></tr>"

    sync_rows = ""
    for s in syncs:
        sync_rows += f"<tr><td>{_esc(s['service_name'])}</td><td><code>{_esc(s['env_var_name'])}</code></td><td>{_esc(s['env_name'])}</td><td>{_sync_badge(s['in_sync'])}</td><td class='muted'>{_esc(s.get('last_checked_at') or '')}</td></tr>"

    add_form = f"""<div class="card"><h3>Add Environment</h3>
        <form method="POST" action="/environments/add">
            <div class="form-grid">
                <div class="form-group"><label>Name *</label><input type="text" name="name" required placeholder="e.g. production"></div>
                <div class="form-group"><label>Env File Path</label><input type="text" name="env_file_path" placeholder="/home/app/.env"></div>
                <div class="form-group"><label>SSH Command</label><input type="text" name="ssh_command" placeholder="ssh user@host"></div>
                <div class="form-group"><label>Notes</label><input type="text" name="notes" placeholder="Production server"></div>
            </div>
            <button type="submit" class="btn btn-primary btn-sm">Add Environment</button>
        </form></div>"""

    return f"""
        <div class="card"><h2>Environments ({len(envs)})</h2>
            {'<table><tr><th>Name</th><th>Path</th><th>Last Synced</th></tr>'+env_rows+'</table>' if env_rows else '<p class="muted">No environments yet.</p>'}
        </div>
        {add_form}
        <div class="card"><h2>Sync Status</h2>
            {'<table><tr><th>Service</th><th>Key</th><th>Env</th><th>Status</th><th>Checked</th></tr>'+sync_rows+'</table>' if sync_rows else '<p class="muted">Run a sync check to see results.</p>'}
        </div>"""


# ─── Deprecations page ──────────────────────────────────────

def _deprecations_page(data: dict) -> str:
    deps = data.get("deprecations", [])
    rows = ""
    for d in deps:
        sc = GREEN if d["status"] == "resolved" else (RED if d["status"] == "active" else TEXT_MUTED)
        rows += f"""<tr><td>{_esc(d['service_name'])}</td><td>{_esc(d['description'])}</td><td>{_esc(d.get('notice_date',''))}</td>
            <td>{_esc(d.get('effective_date') or 'TBD')}</td><td><span style="color:{sc};font-weight:600">{_esc(d['status'].upper())}</span></td>
            <td class="muted hide-mobile">{_esc(d.get('migration_notes') or '')}</td></tr>"""
    if not rows:
        return '<div class="empty-state"><h3>No deprecation notices</h3><p class="muted">Deprecation notices will appear here when logged.</p></div>'
    return f"""<div class="card"><h2>Deprecation Notices ({len(deps)})</h2>
        <table><tr><th>Service</th><th>Description</th><th>Noticed</th><th>Effective</th><th>Status</th><th class="hide-mobile">Migration</th></tr>{rows}</table></div>"""


# ─── Reminders page ─────────────────────────────────────────

def _reminders_page(data: dict) -> str:
    reminders = data.get("reminders", [])
    rows = ""
    for r in reminders:
        sent = f'<span style="color:{GREEN}">SENT</span>' if r["sent"] else f'<span style="color:{YELLOW}">PENDING</span>'
        rows += f"""<tr><td>{_esc(r.get('service_name') or '—')}</td><td>{_esc(r['message'])}</td><td>{_esc(r['reminder_type'])}</td>
            <td>{_esc(r['remind_at'][:10] if r.get('remind_at') else '')}</td><td>{_esc(r.get('channel',''))}</td><td>{sent}</td></tr>"""
    if not rows:
        return '<div class="empty-state"><h3>No reminders</h3><p class="muted">Reminders are auto-created when you add keys with expiration dates.</p></div>'
    return f"""<div class="card"><h2>Reminders</h2>
        <table><tr><th>Service</th><th>Message</th><th>Type</th><th>Date</th><th>Channel</th><th>Status</th></tr>{rows}</table></div>"""


# ─── Audit page ──────────────────────────────────────────────

def _audit_page(data: dict) -> str:
    logs = data.get("logs", [])
    rows = ""
    for a in logs:
        rows += f"""<tr><td class="muted">{_esc(a['created_at'][:16] if a.get('created_at') else '')}</td>
            <td>{_esc(a.get('user_name') or a.get('user_email') or 'system')}</td>
            <td><strong>{_esc(a['action'])}</strong></td><td class="muted">{_esc(a.get('details') or '')}</td>
            <td class="muted hide-mobile">{_esc(a.get('ip_address') or '')}</td></tr>"""
    if not rows:
        return '<div class="empty-state"><h3>No activity yet</h3><p class="muted">Actions will be logged here.</p></div>'
    return f"""<div class="card"><h2>Audit Log</h2>
        <table><tr><th>Time</th><th>User</th><th>Action</th><th>Details</th><th class="hide-mobile">IP</th></tr>{rows}</table></div>"""


# ─── Settings page ──────────────────────────────────────────

def _settings_page(data: dict) -> str:
    org = data.get("org", {})
    members = data.get("members", [])
    tokens = data.get("tokens", [])
    notif_prefs = data.get("notif_prefs", [])
    limits = data.get("limits", {})

    # Org info
    org_section = f"""<div class="card"><h2>Organization</h2>
        <div class="grid-2">
            <div><label>Name</label><strong>{_esc(org['name'] if org else '')}</strong></div>
            <div><label>Plan</label><span class="badge" style="--badge-color:{GOLD}">{(org['plan'] if org else 'free').upper()}</span></div>
        </div></div>"""

    # Members
    member_rows = ""
    for m in members:
        member_rows += f"<tr><td>{_esc(m['name'])}</td><td>{_esc(m['email'])}</td><td>{_esc(m['role'])}</td><td class='muted'>{_esc(m.get('last_login_at') or 'Never')}</td></tr>"
    members_section = f"""<div class="card"><h2>Team Members ({len(members)}/{limits.get('max_members',1)})</h2>
        <table><tr><th>Name</th><th>Email</th><th>Role</th><th>Last Login</th></tr>{member_rows}</table>
        <hr class="divider">
        <h3>Invite Member</h3>
        <form method="POST" action="/settings/invite">
            <div class="form-grid">
                <div class="form-group"><label>Name</label><input type="text" name="name" required></div>
                <div class="form-group"><label>Email</label><input type="email" name="email" required></div>
                <div class="form-group"><label>Role</label><select name="role"><option value="admin">Admin</option><option value="member" selected>Member</option><option value="viewer">Viewer</option></select></div>
                <div class="form-group"><label>Temp Password</label><input type="password" name="password" required minlength="8"></div>
            </div>
            <button type="submit" class="btn btn-sm btn-primary">Invite</button>
        </form></div>"""

    # API tokens
    token_rows = ""
    for t in tokens:
        token_rows += f"<tr><td>{_esc(t['name'])}</td><td><code>{_esc(t['token_prefix'])}...</code></td><td>{_esc(t['scopes'])}</td><td class='muted'>{_esc(t.get('last_used_at') or 'Never')}</td></tr>"
    tokens_section = f"""<div class="card"><h2>API Tokens</h2>
        {'<table><tr><th>Name</th><th>Prefix</th><th>Scopes</th><th>Last Used</th></tr>'+token_rows+'</table>' if token_rows else '<p class="muted">No API tokens yet.</p>'}
        <hr class="divider">
        <h3>Create API Token</h3>
        <form method="POST" action="/settings/api-token">
            <div class="form-grid">
                <div class="form-group"><label>Token Name</label><input type="text" name="token_name" required placeholder="e.g. CI/CD Pipeline"></div>
                <div class="form-group"><label>Scopes</label><select name="scopes"><option value="read">Read Only</option><option value="read,write">Read + Write</option><option value="admin">Admin</option></select></div>
            </div>
            <button type="submit" class="btn btn-sm btn-primary">Create Token</button>
        </form></div>"""

    # Notifications
    notif_rows = ""
    for n in notif_prefs:
        notif_rows += f"<tr><td>{_esc(n['channel'])}</td><td>{_esc(n['destination'])}</td><td>{n['expiry_warn_days']}d</td><td>{'Active' if n['is_active'] else 'Disabled'}</td></tr>"
    notif_section = f"""<div class="card"><h2>Notifications</h2>
        {'<table><tr><th>Channel</th><th>Destination</th><th>Warn Before</th><th>Status</th></tr>'+notif_rows+'</table>' if notif_rows else '<p class="muted">No notification channels configured.</p>'}
        <hr class="divider">
        <h3>Add Notification Channel</h3>
        <form method="POST" action="/settings/notifications">
            <div class="form-grid">
                <div class="form-group"><label>Channel</label><select name="channel"><option value="email">Email</option><option value="sms">SMS</option><option value="telegram">Telegram</option><option value="webhook">Webhook</option></select></div>
                <div class="form-group"><label>Destination</label><input type="text" name="destination" required placeholder="email@example.com or +1234567890"></div>
                <div class="form-group"><label>Warn Days Before Expiry</label><input type="number" name="expiry_warn_days" value="14"></div>
            </div>
            <button type="submit" class="btn btn-sm btn-primary">Save</button>
        </form></div>"""

    return org_section + members_section + tokens_section + notif_section


# ─── Billing page ────────────────────────────────────────────

def _billing_page(data: dict) -> str:
    org = data.get("org", {})
    limits = data.get("limits", {})
    plan = (org["plan"] if org else "free")

    plans = {
        "free": {"price": "$0/mo", "keys": 25, "envs": 2, "members": 1},
        "pro": {"price": "$29/mo", "keys": 100, "envs": 10, "members": 5},
        "enterprise": {"price": "$99/mo", "keys": 1000, "envs": 50, "members": 25},
    }

    cards = ""
    for p_name, p_data in plans.items():
        is_current = p_name == plan
        border = f"border-color:{GOLD};border-width:2px" if is_current else ""
        btn = f'<span class="badge" style="--badge-color:{GREEN}">CURRENT PLAN</span>' if is_current else (
            f'<form method="POST" action="/billing/upgrade"><input type="hidden" name="plan" value="{p_name}"><button type="submit" class="btn btn-primary btn-sm">Upgrade</button></form>' if p_name != "free" else ""
        )
        cards += f"""<div class="card" style="text-align:center;{border}">
            <h3 style="color:{GOLD if is_current else TEXT}">{p_name.upper()}</h3>
            <div style="font-size:28px;font-weight:700;margin:8px 0">{p_data['price']}</div>
            <div class="muted">{p_data['keys']} keys · {p_data['envs']} envs · {p_data['members']} members</div>
            <div style="margin-top:16px">{btn}</div>
        </div>"""

    return f"""<div class="card"><h2>Current Plan: {plan.upper()}</h2>
        <div class="grid-3" style="margin-top:8px">
            <div><label>Keys</label>{limits.get('current_keys',0)} / {limits.get('max_keys',25)}</div>
            <div><label>Environments</label>{limits.get('current_envs',0)} / {limits.get('max_environments',2)}</div>
            <div><label>Members</label>{limits.get('current_members',0)} / {limits.get('max_members',1)}</div>
        </div></div>
        <div class="grid-3" style="margin-top:16px">{cards}</div>"""


# ─── Token created page ─────────────────────────────────────

def _token_created_page(data: dict) -> str:
    return f"""<div style="max-width:600px;margin:40px auto">
        <div class="alert alert-warn">Copy this token now — it won't be shown again!</div>
        <div class="card">
            <h2>API Token Created: {_esc(data.get('name',''))}</h2>
            <div style="margin-top:16px">
                <label>Your API Token</label>
                <div style="background:{SURFACE};padding:12px;border-radius:8px;word-break:break-all;font-family:monospace;font-size:13px;margin-top:4px">{_esc(data.get('token',''))}</div>
            </div>
            <div style="margin-top:16px" class="muted">
                <p>Use this token in the Authorization header:</p>
                <code>Authorization: Bearer {_esc(data.get('token','')[:15])}...</code>
            </div>
            <a href="/settings" class="btn btn-primary" style="margin-top:20px">Done</a>
        </div>
    </div>"""
