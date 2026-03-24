"""
signing-portal/app.py — Marceau Solutions client signing portal.

Routes:
  GET  /{token}        — Show branded signing page
  POST /{token}/sign   — Process signature
  GET  /success        — Success confirmation page
  GET  /health         — Health check

Local:  http://localhost:8797/{token}
Prod:   https://sign.marceausolutions.com/{token}
"""

import os
import smtplib
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template_string, request, url_for

# ── Path / env setup ──────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[3]          # dev-sandbox/
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(_REPO_ROOT / ".env")

# Hyphenated dir can't be dotted-imported; load models directly by path
import importlib.util as _ilu
_models_path = _HERE / "models.py"
_spec = _ilu.spec_from_file_location("signing_portal_models", str(_models_path))
_models = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_models)
get_db           = _models.get_db
create_agreement = _models.create_agreement
get_agreement    = _models.get_agreement
mark_signed      = _models.mark_signed

app = Flask(__name__)
PORT = int(os.getenv("SIGNING_PORTAL_PORT", "8797"))

# ── Tier config (mirrors close_deal.py) ──────────────────────────────────────
TIER_CONFIG = {
    1: {"name": "Tier 1 — Starter",  "monthly": "$497/month"},
    2: {"name": "Tier 2 — Growth",   "monthly": "$997/month"},
    3: {"name": "Tier 3 — Pro",      "monthly": "$1,497/month"},
    4: {"name": "Tier 4 — Elite",    "monthly": "$2,497/month"},
}

# ── Brand colours ─────────────────────────────────────────────────────────────
GOLD    = "#C9963C"
BG      = "#0d1117"
CARD    = "#161b22"
SURFACE = "#21262d"
BORDER  = "#30363d"
TEXT    = "#e6edf3"
MUTED   = "#8b949e"

# ── HTML helpers ──────────────────────────────────────────────────────────────
BASE_CSS = f"""
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: {BG};
    color: {TEXT};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px 16px 64px;
}}
.wrap {{
    width: 100%;
    max-width: 720px;
}}
.header {{
    background: linear-gradient(135deg, #1a1a2e, {CARD});
    border: 1px solid {BORDER};
    border-radius: 14px 14px 0 0;
    padding: 28px 32px 24px;
    text-align: center;
    border-bottom: 2px solid {GOLD};
}}
.logo-text {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: {GOLD};
    margin-bottom: 8px;
}}
.header h1 {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT};
}}
.header p {{
    font-size: 13px;
    color: {MUTED};
    margin-top: 4px;
}}
.body {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-top: none;
    border-radius: 0 0 14px 14px;
    padding: 28px 32px;
}}
.callout {{
    background: linear-gradient(135deg, #1a1200, #1a1000);
    border: 1px solid {GOLD}55;
    border-left: 4px solid {GOLD};
    border-radius: 0 10px 10px 0;
    padding: 16px 20px;
    margin: 20px 0 24px;
    font-size: 14px;
    color: {TEXT};
}}
.callout strong {{ color: {GOLD}; font-size: 15px; }}
.section {{ margin-bottom: 28px; }}
.section h3 {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: {MUTED};
    border-bottom: 1px solid {BORDER};
    padding-bottom: 6px;
    margin-bottom: 12px;
}}
.terms-block {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 13px;
    color: {TEXT};
    line-height: 1.7;
    margin-bottom: 10px;
}}
.terms-block h4 {{
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: {GOLD};
    margin-bottom: 6px;
}}
.terms-block ul {{
    padding-left: 18px;
}}
.terms-block li {{ margin-bottom: 4px; }}
.kv-row {{
    display: flex;
    justify-content: space-between;
    padding: 7px 0;
    border-bottom: 1px solid {BORDER}44;
    font-size: 13px;
}}
.kv-row:last-child {{ border-bottom: none; }}
.kv-label {{ color: {MUTED}; }}
.kv-value {{ font-weight: 600; color: {TEXT}; }}
.kv-value.gold {{ color: {GOLD}; }}
.sign-area {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 20px 24px;
    margin-top: 24px;
}}
.sign-area h3 {{
    font-size: 14px;
    font-weight: 700;
    color: {TEXT};
    margin-bottom: 14px;
}}
.form-group {{ margin-bottom: 14px; }}
.form-group label {{
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: {MUTED};
    margin-bottom: 5px;
    text-transform: uppercase;
    letter-spacing: .4px;
}}
.form-group input[type=text] {{
    width: 100%;
    background: {BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 10px 14px;
    font-size: 15px;
    font-family: inherit;
    transition: border-color .15s, box-shadow .15s;
}}
.form-group input[type=text]:focus {{
    outline: none;
    border-color: {GOLD};
    box-shadow: 0 0 0 3px {GOLD}22;
}}
.checkbox-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 13px;
    color: {MUTED};
    margin-bottom: 18px;
    cursor: pointer;
}}
.checkbox-row input[type=checkbox] {{
    width: 16px;
    height: 16px;
    margin-top: 2px;
    accent-color: {GOLD};
    flex-shrink: 0;
    cursor: pointer;
}}
.btn-sign {{
    display: block;
    width: 100%;
    padding: 14px;
    background: {GOLD};
    color: #1a1000;
    font-size: 15px;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-family: inherit;
    letter-spacing: .3px;
    transition: opacity .15s;
}}
.btn-sign:hover {{ opacity: .92; }}
.btn-sign:disabled {{ opacity: .5; cursor: not-allowed; }}
.error-box {{
    background: #2d0a0a;
    border: 1px solid #f8514944;
    border-radius: 8px;
    padding: 16px 20px;
    color: #f85149;
    font-size: 14px;
    margin-top: 16px;
}}
.footer {{
    margin-top: 24px;
    text-align: center;
    font-size: 11px;
    color: {MUTED};
    line-height: 1.8;
}}
@media (max-width: 600px) {{
    body {{ padding: 12px 8px 48px; }}
    .header, .body {{ padding: 20px 18px; }}
    .sign-area {{ padding: 16px 14px; }}
}}
"""

SIGN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Service Agreement — {{ business_name }}</title>
  <style>{{ css }}</style>
</head>
<body>
<div class="wrap">

  <div class="header">
    <div class="logo-text">Marceau Solutions</div>
    <h1>Service Agreement</h1>
    <p>{{ business_name }}</p>
  </div>

  <div class="body">

    <div class="callout">
      <strong>Free 2-Week Trial — No charge until you decide to continue.</strong><br>
      You will not be billed anything during the free onboarding period. At the end of Week 2,
      you choose whether to activate your subscription. Cancel anytime after that with 30 days'
      written notice.
    </div>

    <!-- Key Terms Summary -->
    <div class="section">
      <h3>Key Terms Summary</h3>
      <div class="terms-block">
        <div class="kv-row"><span class="kv-label">Client</span><span class="kv-value">{{ client_name }} · {{ business_name }}</span></div>
        <div class="kv-row"><span class="kv-label">Selected Package</span><span class="kv-value">{{ tier_name }}</span></div>
        <div class="kv-row"><span class="kv-label">Monthly Rate</span><span class="kv-value gold">{{ monthly_rate }}</span></div>
        <div class="kv-row"><span class="kv-label">Setup Fee</span><span class="kv-value">$0</span></div>
        <div class="kv-row"><span class="kv-label">Free Trial</span><span class="kv-value gold">2 weeks — no charge</span></div>
        <div class="kv-row"><span class="kv-label">Cancellation</span><span class="kv-value">30 days written notice, anytime</span></div>
        <div class="kv-row"><span class="kv-label">Effective Date</span><span class="kv-value">{{ effective_date }}</span></div>
      </div>
    </div>

    <!-- What's Included -->
    <div class="section">
      <h3>What's Included</h3>
      <div class="terms-block">
        <ul>
          <li>AI phone &amp; text intake — answers calls and texts 24/7, qualifies leads automatically</li>
          <li>Automated follow-up sequences via SMS and email</li>
          <li>Monthly optimization — prompt tuning, workflow improvements, and reporting</li>
          <li>Dedicated onboarding in Week 1: kickoff call, build &amp; configuration</li>
          <li>Week 2 testing, refinements, and your review before activation</li>
          <li>Direct access to William Marceau during the engagement</li>
        </ul>
      </div>
    </div>

    <!-- Full Agreement -->
    <div class="section">
      <h3>Full Agreement Terms</h3>

      <div class="terms-block">
        <h4>1. Services</h4>
        <p>Marceau Solutions agrees to design, build, and maintain an AI-powered customer communication
        system for {{ business_name }} as described in the proposal. The specific system components are
        defined in the accompanying proposal document.</p>
      </div>

      <div class="terms-block">
        <h4>2. Free Trial Period</h4>
        <p>The first two (2) weeks of service constitute a free trial. No payment is required or
        collected during this period. At the end of the trial, Client may elect to activate the
        subscription or cancel with zero charges, no questions asked.</p>
      </div>

      <div class="terms-block">
        <h4>3. Billing &amp; Payment</h4>
        <p>Upon activation after the free trial, Client will be billed <strong>{{ monthly_rate }}</strong>
        per month. Billing begins at the start of Month 1 (after the 2-week free period). Payment is
        due on the 1st of each month via the Stripe payment link provided.</p>
      </div>

      <div class="terms-block">
        <h4>4. Cancellation Policy</h4>
        <p>Either party may cancel this agreement with <strong>30 days' written notice</strong>.
        Written notice may be sent via email to wmarceau@marceausolutions.com. There are no
        early-termination fees. Billing stops at the end of the notice period.</p>
      </div>

      <div class="terms-block">
        <h4>5. Intellectual Property</h4>
        <p>All custom workflows, prompts, and automations built for Client are owned by Client
        upon full payment. Underlying platform licenses (third-party tools) remain subject to their
        respective terms.</p>
      </div>

      <div class="terms-block">
        <h4>6. Confidentiality</h4>
        <p>Both parties agree to keep confidential any proprietary business information shared during
        the engagement. This includes client data, pricing, and internal processes.</p>
      </div>

      <div class="terms-block">
        <h4>7. Limitation of Liability</h4>
        <p>Marceau Solutions' total liability is limited to fees paid in the current billing month.
        Neither party is liable for indirect or consequential damages arising from this agreement.</p>
      </div>

      <div class="terms-block">
        <h4>8. Governing Law</h4>
        <p>This agreement is governed by the laws of the State of Florida. Any disputes shall be
        resolved in Collier County, Florida.</p>
      </div>
    </div>

    <!-- Signature Area -->
    <div class="sign-area">
      <h3>Sign This Agreement</h3>
      <form method="POST" action="/{{ token }}/sign" id="sign-form">
        <div class="form-group">
          <label>Type your full legal name to sign</label>
          <input type="text" name="signer_name" id="signer_name"
                 placeholder="e.g. John Smith"
                 autocomplete="name" required>
        </div>
        <div class="checkbox-row">
          <input type="checkbox" id="agree_check" name="agree" required>
          <label for="agree_check">
            I have read and agree to all terms above, including the free 2-week trial,
            the monthly rate of <strong style="color: {{ gold }}">{{ monthly_rate }}</strong>,
            and the 30-day cancellation policy.
          </label>
        </div>
        <button type="submit" class="btn-sign" id="sign-btn">
          Sign and Activate Free Trial &rarr;
        </button>
      </form>
    </div>

  </div><!-- /body -->

  <div class="footer">
    Marceau Solutions &nbsp;&middot;&nbsp; Naples, FL &nbsp;&middot;&nbsp;
    wmarceau@marceausolutions.com &nbsp;&middot;&nbsp; (239) 398-5676<br>
    <em>Embrace the Pain &amp; Defy the Odds</em>
  </div>

</div><!-- /wrap -->

<script>
document.getElementById('sign-btn').addEventListener('click', function(e) {
  var name = document.getElementById('signer_name').value.trim();
  var agreed = document.getElementById('agree_check').checked;
  if (!name || !agreed) { return; }
  this.disabled = true;
  this.textContent = 'Processing…';
});
</script>
</body>
</html>
"""

SUCCESS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>You're Signed! — Marceau Solutions</title>
  <style>{{ css }}</style>
</head>
<body>
<div class="wrap" style="max-width:560px;text-align:center;padding-top:60px">
  <div style="font-size:52px;margin-bottom:16px">✅</div>
  <div class="logo-text" style="color:{{ gold }};font-size:13px;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:8px">Marceau Solutions</div>
  <h1 style="font-size:26px;font-weight:800;color:{{ text }};margin-bottom:10px">You're signed!</h1>
  <p style="color:{{ muted }};font-size:14px;max-width:400px;margin:0 auto 28px">
    Your agreement for <strong style="color:{{ text }}">{{ business_name }}</strong> has been recorded.
    William will be in touch within the hour to kick off your free 2-week onboarding.
  </p>
  <div style="background:{{ card }};border:1px solid {{ border }};border-radius:10px;padding:18px 22px;text-align:left;max-width:400px;margin:0 auto 32px;font-size:13px">
    <div class="kv-row"><span class="kv-label">Signed by</span><span class="kv-value">{{ signer_name }}</span></div>
    <div class="kv-row"><span class="kv-label">Package</span><span class="kv-value">{{ tier_name }}</span></div>
    <div class="kv-row"><span class="kv-label">Monthly Rate</span><span class="kv-value gold">{{ monthly_rate }}</span></div>
    <div class="kv-row" style="border-bottom:none"><span class="kv-label">Signed at</span><span class="kv-value">{{ signed_at }}</span></div>
  </div>
  <p style="color:{{ muted }};font-size:12px">
    A confirmation email has been sent to {{ client_email }}.
  </p>
  <div class="footer" style="margin-top:32px">
    Marceau Solutions &nbsp;&middot;&nbsp; Naples, FL<br>
    wmarceau@marceausolutions.com &nbsp;&middot;&nbsp; (239) 398-5676
  </div>
</div>
</body>
</html>
"""

ERROR_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }} — Marceau Solutions</title>
  <style>{{ css }}</style>
</head>
<body>
<div class="wrap" style="max-width:560px;text-align:center;padding-top:80px">
  <div style="font-size:48px;margin-bottom:16px">{{ icon }}</div>
  <div class="logo-text" style="color:{{ gold }};font-size:13px;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:8px">Marceau Solutions</div>
  <h1 style="font-size:22px;font-weight:700;color:{{ text }};margin-bottom:10px">{{ title }}</h1>
  <p style="color:{{ muted }};font-size:14px;max-width:400px;margin:0 auto">{{ message }}</p>
  <p style="margin-top:28px;font-size:13px;color:{{ muted }}">
    Questions? Email <a href="mailto:wmarceau@marceausolutions.com" style="color:{{ gold }}">wmarceau@marceausolutions.com</a>
    or call <a href="tel:+12393985676" style="color:{{ gold }}">(239) 398-5676</a>.
  </p>
</div>
</body>
</html>
"""


def _render(template: str, **kwargs):
    ctx = dict(
        css=BASE_CSS, gold=GOLD, bg=BG, card=CARD, surface=SURFACE,
        border=BORDER, text=TEXT, muted=MUTED,
    )
    ctx.update(kwargs)
    return render_template_string(template, **ctx)


# ── Notifications ─────────────────────────────────────────────────────────────

def _send_confirmation_email(agreement, signer_name: str):
    """Send a confirmation email to the client after signing."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        port     = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        if not username or not password:
            print("  [signing-portal] SMTP not configured — skipping confirmation email")
            return

        tier_cfg = TIER_CONFIG.get(agreement["tier"], TIER_CONFIG[1])
        first = agreement["client_name"].split()[0] if agreement["client_name"] else "there"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Agreement Confirmed — {agreement['business_name']}"
        msg["From"]    = f"William Marceau <{username}>"
        msg["To"]      = agreement["client_email"]

        signed_at = agreement["signed_at"] or datetime.now().isoformat()
        signed_at_fmt = signed_at[:19].replace("T", " ")

        text = f"""Hi {first},

Your service agreement with Marceau Solutions has been signed and confirmed.

Business:     {agreement['business_name']}
Package:      {tier_cfg['name']}
Monthly Rate: {tier_cfg['monthly']}
Signed by:    {signer_name}
Signed at:    {signed_at_fmt}

Your free 2-week onboarding kicks off now. I'll be reaching out within the hour
to schedule our kickoff call and get everything set up.

Any questions, just reply here.

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com
(239) 398-5676
marceausolutions.com
"""
        html = f"""
<html><body style="font-family:-apple-system,sans-serif;color:#1a1a2e;max-width:580px;margin:0 auto;padding:20px">
  <div style="background:linear-gradient(135deg,#333333,#2d2d2d);padding:24px;border-radius:10px 10px 0 0;text-align:center">
    <h1 style="color:#C9963C;margin:0;font-size:20px">Agreement Confirmed</h1>
    <p style="color:#94a3b8;margin:6px 0 0;font-size:13px">{agreement['business_name']}</p>
  </div>
  <div style="background:#fff;padding:24px;border-radius:0 0 10px 10px;box-shadow:0 2px 10px rgba(0,0,0,.1)">
    <p>Hi {first},</p>
    <p>Your service agreement has been signed and confirmed. Your free 2-week onboarding kicks off now — I'll reach out within the hour to schedule our kickoff call.</p>
    <div style="background:#FDF8EF;border-left:4px solid #C9963C;padding:14px 18px;margin:20px 0;border-radius:0 8px 8px 0;font-size:13px">
      <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #e2e8f0">
        <span style="color:#64748b">Package</span><strong>{tier_cfg['name']}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #e2e8f0">
        <span style="color:#64748b">Monthly Rate</span><strong style="color:#C9963C">{tier_cfg['monthly']}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #e2e8f0">
        <span style="color:#64748b">Free Trial</span><strong style="color:#C9963C">2 weeks — no charge</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:5px 0">
        <span style="color:#64748b">Signed at</span><strong>{signed_at_fmt}</strong>
      </div>
    </div>
    <p style="font-size:13px;color:#475569">Any questions, just reply here.</p>
    <p style="margin-top:16px"><strong>William Marceau</strong><br>
      <a href="mailto:wmarceau@marceausolutions.com" style="color:#C9963C">wmarceau@marceausolutions.com</a><br>
      (239) 398-5676 | <a href="https://marceausolutions.com" style="color:#C9963C">marceausolutions.com</a>
    </p>
  </div>
</body></html>
"""
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(host, port) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(username, password)
            s.send_message(msg)
        print(f"  [signing-portal] Confirmation email sent to {agreement['client_email']}")
    except Exception as e:
        print(f"  [signing-portal] Email error: {e}")


def _send_telegram_notification(agreement, signer_name: str):
    """Send William a Telegram notification when a client signs."""
    try:
        token   = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "5692454753")
        if not token:
            print("  [signing-portal] TELEGRAM_BOT_TOKEN not set — skipping notification")
            return

        tier_cfg = TIER_CONFIG.get(agreement["tier"], TIER_CONFIG[1])
        signed_at = (agreement["signed_at"] or datetime.now().isoformat())[:19].replace("T", " ")
        text = (
            f"CONTRACT SIGNED\n\n"
            f"Client: {agreement['client_name']}\n"
            f"Business: {agreement['business_name']}\n"
            f"Package: {tier_cfg['name']}\n"
            f"Rate: {tier_cfg['monthly']}\n"
            f"Signed by: {signer_name}\n"
            f"At: {signed_at}\n\n"
            f"Follow up within the hour to kick off their free 2-week build."
        )
        import urllib.parse
        params = urllib.parse.urlencode({"chat_id": chat_id, "text": text})
        url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
        with urllib.request.urlopen(url, timeout=8) as resp:
            resp.read()
        print(f"  [signing-portal] Telegram notification sent (chat {chat_id})")
    except Exception as e:
        print(f"  [signing-portal] Telegram error: {e}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string("""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Marceau Solutions — Client Portal</title>
<style>*{box-sizing:border-box;margin:0;padding:0}body{background:#0d1117;color:#e6edf3;font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:40px;max-width:480px;width:100%;text-align:center}
.logo{color:#C9963C;font-size:22px;font-weight:700;margin-bottom:8px}
.tagline{color:#8b949e;font-size:14px;margin-bottom:32px}
h1{font-size:18px;margin-bottom:12px}
p{color:#8b949e;font-size:14px;line-height:1.6}
</style></head>
<body><div class="card">
<div class="logo">Marceau Solutions</div>
<div class="tagline">Embrace the Pain &amp; Defy the Odds</div>
<h1>Client Signing Portal</h1>
<p>This portal is accessed via a personalized link sent to you by William Marceau.<br><br>
If you received a proposal, please use the link in your email to review and sign your agreement.</p>
</div></body></html>""")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "signing-portal", "port": PORT})


@app.route("/<token>", methods=["GET"])
def signing_page(token: str):
    conn = get_db()
    agreement = get_agreement(conn, token)
    conn.close()

    if not agreement:
        return _render(ERROR_PAGE,
            icon="🔍", title="Link Not Found",
            message="This signing link is invalid or has expired. Please contact William for a new link."
        ), 404

    if agreement["status"] == "signed":
        tier_cfg = TIER_CONFIG.get(agreement["tier"], TIER_CONFIG[1])
        signed_at = (agreement["signed_at"] or "")[:19].replace("T", " ")
        return _render(ERROR_PAGE,
            icon="✅", title="Already Signed",
            message=(
                f"This agreement was already signed by {agreement['signer_name']} on {signed_at}. "
                f"Your free 2-week onboarding for {agreement['business_name']} is in progress."
            )
        )

    if agreement["status"] == "expired":
        return _render(ERROR_PAGE,
            icon="⏰", title="Link Expired",
            message="This signing link has expired. Please contact William for a fresh link."
        ), 410

    tier_cfg = TIER_CONFIG.get(agreement["tier"], TIER_CONFIG[1])
    return _render(SIGN_PAGE,
        token=token,
        business_name=agreement["business_name"],
        client_name=agreement["client_name"],
        tier_name=tier_cfg["name"],
        monthly_rate=tier_cfg["monthly"],
        effective_date=agreement["effective_date"],
    )


@app.route("/<token>/sign", methods=["POST"])
def process_signature(token: str):
    conn = get_db()
    agreement = get_agreement(conn, token)

    if not agreement:
        conn.close()
        return _render(ERROR_PAGE,
            icon="🔍", title="Link Not Found",
            message="This signing link is invalid. Please contact William for a new link."
        ), 404

    if agreement["status"] != "pending":
        conn.close()
        return _render(ERROR_PAGE,
            icon="⚠️", title="Already Processed",
            message="This agreement has already been signed or expired."
        )

    signer_name = (request.form.get("signer_name") or "").strip()
    if not signer_name:
        conn.close()
        return _render(ERROR_PAGE,
            icon="⚠️", title="Signature Required",
            message="Please type your full legal name to sign."
        ), 400

    # Grab client IP (support proxies)
    signer_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if signer_ip and "," in signer_ip:
        signer_ip = signer_ip.split(",")[0].strip()

    # Mark as signed
    mark_signed(conn, token, signer_name, signer_ip)
    # Re-fetch to get signed_at timestamp
    agreement = get_agreement(conn, token)
    conn.close()

    # Notify
    _send_confirmation_email(agreement, signer_name)
    _send_telegram_notification(agreement, signer_name)

    tier_cfg = TIER_CONFIG.get(agreement["tier"], TIER_CONFIG[1])
    signed_at = (agreement["signed_at"] or "")[:19].replace("T", " ")

    return _render(SUCCESS_PAGE,
        business_name=agreement["business_name"],
        client_name=agreement["client_name"],
        client_email=agreement["client_email"],
        tier_name=tier_cfg["name"],
        monthly_rate=tier_cfg["monthly"],
        signer_name=signer_name,
        signed_at=signed_at,
    )


@app.route("/success")
def success_generic():
    return _render(SUCCESS_PAGE,
        business_name="your business",
        client_name="",
        client_email="",
        tier_name="",
        monthly_rate="",
        signer_name="",
        signed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  Marceau Signing Portal → http://localhost:{PORT}/health\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
