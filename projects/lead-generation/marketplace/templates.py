"""Jinja template strings + render helper. Mobile-first, brand gold/charcoal."""
from flask import render_template_string
import config

BASE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ brand.name }}</title>
<style>
  :root{ --gold:{{ brand.gold }}; --charcoal:{{ brand.charcoal }}; }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
       background:#f4f4f4;color:var(--charcoal);line-height:1.5}
  header{background:var(--charcoal);color:#fff;padding:14px 18px;display:flex;
         justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
  header .brand{font-weight:700;color:var(--gold);font-size:1.1rem;text-decoration:none}
  header a{color:#fff;text-decoration:none;margin-left:14px;font-size:.9rem}
  header a:hover{color:var(--gold)}
  .wrap{max-width:880px;margin:0 auto;padding:18px}
  .card{background:#fff;border-radius:10px;padding:18px;margin:14px 0;
        box-shadow:0 1px 4px rgba(0,0,0,.08)}
  .gold{color:var(--gold)} .muted{color:#777;font-size:.88rem}
  .bal{font-size:1.6rem;font-weight:700;color:var(--gold)}
  .btn{display:inline-block;background:var(--gold);color:#fff;border:0;padding:11px 18px;
       border-radius:8px;font-weight:600;cursor:pointer;text-decoration:none;font-size:1rem}
  .btn:hover{filter:brightness(1.07)} .btn.sec{background:var(--charcoal)}
  .btn.ghost{background:#fff;color:var(--charcoal);border:1px solid #ccc}
  input,select,textarea{width:100%;padding:10px;margin:6px 0 12px;border:1px solid #ccc;
       border-radius:7px;font-size:1rem;font-family:inherit}
  label{font-weight:600;font-size:.9rem}
  table{width:100%;border-collapse:collapse;font-size:.92rem}
  th,td{text-align:left;padding:9px 8px;border-bottom:1px solid #eee}
  th{color:#666;font-weight:600;font-size:.8rem;text-transform:uppercase}
  .pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.78rem;font-weight:600}
  .pill.available{background:#eaf6ea;color:#256b25}
  .pill.sold{background:#f0eadf;color:#8a6a1f}
  .pill.draft{background:#eee;color:#666}
  .pill.refunded{background:#fbe9e9;color:#a33}
  .flash{padding:11px 14px;border-radius:8px;margin:10px 0}
  .flash.ok{background:#eaf6ea;color:#256b25} .flash.err{background:#fbe9e9;color:#a33}
  .reveal{background:#fff8ec;border:1px solid var(--gold);border-radius:8px;padding:14px;margin-top:10px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .right{text-align:right}.center{text-align:center}
  .warn{background:#fff3cd;border:1px solid #e0c97a;border-radius:8px;padding:10px 13px;font-size:.88rem}
</style></head><body>
<header>
  <a class="brand" href="/">{{ brand.name }}</a>
  <nav>
  {% if contractor %}
    <a href="/dashboard">Dashboard</a><a href="/credits">Buy Credits</a><a href="/logout">Log out</a>
  {% elif is_admin %}
    <a href="/admin">Admin</a><a href="/admin/logout">Log out</a>
  {% else %}
    <a href="/login">Log in</a>
  {% endif %}
  </nav>
</header>
<div class="wrap">
  {% for cat,msg in messages %}<div class="flash {{ cat }}">{{ msg }}</div>{% endfor %}
  {{ body }}
</div>
<footer class="wrap muted center">{{ brand.name }} · {{ brand.support_email }} · {{ brand.support_phone }}</footer>
<script>
  // Inject CSRF token into every same-origin POST form (avoids editing each form).
  document.querySelectorAll('form[method="post"], form[method="POST"]').forEach(function(f){
    if (f.querySelector('[name="_csrf"]')) return;
    var i = document.createElement('input');
    i.type = 'hidden'; i.name = '_csrf'; i.value = '{{ csrf_token }}';
    f.appendChild(i);
  });
</script>
</body></html>"""


def render(body_template, **ctx):
    from flask import get_flashed_messages
    messages = get_flashed_messages(with_categories=True)
    body = render_template_string(body_template, brand=config.BRAND, dollars=config.dollars, **ctx)
    return render_template_string(
        BASE, brand=config.BRAND, body=body, messages=messages,
        contractor=ctx.get("contractor"), is_admin=ctx.get("is_admin"))


# ---- page bodies ----

LANDING = """
<div class="card center">
  <h1 class="gold">{{ brand.tagline }}</h1>
  <p class="muted">Confirmed, pre-qualified HVAC appointments in your area. Spend credits only on
  the jobs you want — exclusive to you, never resold.</p>
  {% if promo_cents %}<p><b>New accounts get {{ dollars(promo_cents) }} in free credits.</b></p>{% endif %}
  <p>
    {% if public_signup %}<a class="btn" href="/register">Create contractor account</a>{% endif %}
    <a class="btn ghost" href="/login">Contractor log in</a>
  </p>
  {% if not public_signup %}<p class="muted">Contractor signup is currently invite-only.</p>{% endif %}
  <hr>
  <p><b>Homeowner?</b> <a class="btn sec" href="/request-service">Request HVAC service →</a></p>
</div>
<div class="card">
  <h3>How it works</h3>
  <ol>
    <li>We confirm a homeowner appointment (address, time, scope) — with consent.</li>
    <li>You see the job (area, type, window, price) — contact details stay hidden.</li>
    <li>Spend credits to win it. The address & phone unlock instantly, only for you.</li>
  </ol>
</div>"""

LOGIN = """
<div class="card" style="max-width:420px;margin:30px auto">
  <h2>{{ title or 'Contractor log in' }}</h2>
  <form method="post">
    <label>Email</label><input name="email" type="email" required autofocus>
    <label>Password</label><input name="password" type="password" required>
    <button class="btn" type="submit">{{ title or 'Log in' }}</button>
  </form>
  {% if show_register and public_signup %}<p class="muted">No account? <a href="/register">Create one</a>.</p>{% endif %}
</div>"""

REGISTER = """
<div class="card" style="max-width:480px;margin:24px auto">
  <h2>Create your contractor account</h2>
  {% if promo_cents %}<div class="warn">You'll get {{ dollars(promo_cents) }} in free appointment credits.</div>{% endif %}
  <form method="post">
    <label>Company name</label><input name="company_name" required>
    <label>Your name</label><input name="contact_name" required>
    <label>Email</label><input name="email" type="email" required>
    <label>Mobile phone (for appointment alerts)</label><input name="phone" required>
    <label>Service area (cities/zips)</label><input name="service_area" placeholder="Naples, Bonita Springs 34110">
    <label>Password</label><input name="password" type="password" minlength="8" required>
    {% if promo_required %}<label>Promo code</label><input name="promo" placeholder="Required for free credits">{% endif %}
    <button class="btn" type="submit">Create account</button>
  </form>
</div>"""

DASHBOARD = """
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap">
    <div><div class="muted">Welcome, {{ contractor['company_name'] }}</div>
      <div class="muted">Credit balance</div><div class="bal">{{ dollars(contractor['balance_cents']) }}</div></div>
    <a class="btn" href="/credits">Buy credits</a>
  </div>
</div>
<div class="card">
  <h3>Available appointments ({{ available|length }})</h3>
  {% if not available %}<p class="muted">No appointments available right now. Check back soon.</p>{% endif %}
  {% for a in available %}
  <div style="border-bottom:1px solid #eee;padding:10px 0">
    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px">
      <div>
        <b>{{ a['service_type'] }}</b> — {{ a['city'] }} {{ a['zip'] }}
        <div class="muted">{{ a['scheduled_time'] }}{% if a['est_job_value_cents'] %} · est. ticket {{ dollars(a['est_job_value_cents']) }}{% endif %}</div>
        <div class="muted">{{ a['job_summary'] }}</div>
      </div>
      <div class="right">
        <div class="gold" style="font-weight:700">{{ dollars(a['price_cents']) }}</div>
        <form method="post" action="/appointments/{{ a['id'] }}/buy"
              onsubmit="return confirm('Spend {{ dollars(a['price_cents']) }} credits to win this appointment exclusively?')">
          <button class="btn" type="submit">Buy</button>
        </form>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
<div class="card">
  <h3>My purchased appointments ({{ purchased|length }})</h3>
  {% for a in purchased %}
  <div class="reveal">
    <b>{{ a['service_type'] }}</b> — {{ a['scheduled_time'] }}<br>
    <b>{{ a['homeowner_name'] }}</b> · {{ a['address_full'] }}<br>
    📞 <a href="tel:{{ a['homeowner_phone'] }}">{{ a['homeowner_phone'] }}</a>
    {% if a['homeowner_email'] %} · ✉ {{ a['homeowner_email'] }}{% endif %}<br>
    <span class="muted">{{ a['private_notes'] or a['job_summary'] }}</span>
  </div>
  {% else %}<p class="muted">Nothing purchased yet.</p>{% endfor %}
</div>
<div class="card">
  <h3>Recent activity</h3>
  <table><tr><th>When</th><th>Type</th><th class="right">Amount</th><th class="right">Balance</th></tr>
  {% for t in tx %}<tr><td class="muted">{{ t['created_at'][:16].replace('T',' ') }}</td>
    <td>{{ t['kind'].replace('_',' ') }}</td>
    <td class="right">{{ dollars(t['amount_cents']) }}</td>
    <td class="right">{{ dollars(t['balance_after']) }}</td></tr>{% endfor %}
  </table>
</div>"""

CREDITS = """
<div class="card" style="max-width:480px;margin:0 auto">
  <h2>Buy credits</h2>
  <p class="muted">Balance: <b class="gold">{{ dollars(contractor['balance_cents']) }}</b></p>
  {% if mode == 'manual' %}
    <div class="warn">Online card payment isn't enabled yet for this account. To add credits,
    contact {{ brand.support_phone }} / {{ brand.support_email }} and they'll be applied instantly.</div>
  {% else %}
    {% if stripe_live %}<div class="warn">⚠ LIVE payment mode — real card will be charged.</div>{% endif %}
    <form method="post">
      <label>Amount (USD)</label>
      <input name="amount" type="number" min="{{ min_dollars }}" step="1" value="300" required>
      <button class="btn" type="submit">Continue to payment</button>
    </form>
    <p class="muted">Minimum {{ dollars(min_cents) }}. Credits never expire.</p>
  {% endif %}
</div>"""

REQUEST_FORM = """
<div class="card" style="max-width:560px;margin:0 auto">
  <h2 class="gold">Request HVAC service</h2>
  <p class="muted">Tell us what's going on. A local, vetted HVAC pro will reach out to confirm
  your appointment — usually same day.</p>
  <form method="post">
    <div class="grid">
      <div><label>Your name *</label><input name="homeowner_name" required></div>
      <div><label>Mobile phone *</label><input name="homeowner_phone" type="tel" required></div>
    </div>
    <label>Email</label><input name="homeowner_email" type="email">
    <label>Service address *</label><input name="address_full" required placeholder="Street, City, FL ZIP">
    <div class="grid">
      <div><label>City *</label><input name="city" required></div>
      <div><label>ZIP *</label><input name="zip" required></div>
    </div>
    <label>What do you need? *</label>
    <select name="service_type" required>
      <option value="">Select…</option>
      <option>AC Not Cooling — Repair</option>
      <option>No Heat — Repair</option>
      <option>New System — Quote/Install</option>
      <option>Maintenance / Tune-up</option>
      <option>Other</option>
    </select>
    <label>Describe the problem</label>
    <textarea name="job_summary" rows="3" placeholder="e.g. AC running but blowing warm, ~10 yr old unit"></textarea>
    <label>Preferred time</label><input name="scheduled_time" placeholder="e.g. weekday afternoons">
    <div class="warn" style="margin-top:10px">
      <label style="font-weight:400">
        <input type="checkbox" name="consent" required style="width:auto">
        I authorize {{ brand.name }} and a matched HVAC contractor to contact me at the phone
        number/email above (including by call, text/SMS, and email) about my service request.
        Message/data rates may apply; consent is not a condition of purchase. I can opt out anytime.
      </label>
    </div>
    <button class="btn" type="submit" style="margin-top:12px">Request my appointment</button>
  </form>
  <p class="muted center" style="margin-top:10px">Are you a contractor? <a href="/login">Log in here</a>.</p>
</div>"""

THANKYOU = """
<div class="card center" style="max-width:520px;margin:30px auto">
  <h2 class="gold">Request received ✓</h2>
  <p>Thanks, {{ name }}. A local HVAC pro will call <b>{{ phone }}</b> shortly to confirm your
  appointment. If you need help now, call {{ brand.support_phone }}.</p>
  <a class="btn ghost" href="/request-service">Submit another request</a>
</div>"""

ADMIN = """
<div class="card">
  <h2>Admin · {{ brand.name }}</h2>
  <p class="muted">Payment mode: <b>{{ payment_mode }}</b>{% if stripe_live %} <span class="gold">(LIVE key)</span>{% endif %}
   · Public signup: <b>{{ 'ON' if public_signup else 'OFF (invite-only)' }}</b></p>
  {% if ledger_bad %}<div class="flash err">LEDGER MISMATCH on {{ ledger_bad|length }} account(s)! Investigate.</div>
  {% else %}<div class="flash ok">Ledger integrity OK ({{ contractors|length }} accounts).</div>{% endif %}
</div>
<div class="card">
  <h3>New appointment</h3>
  <form method="post" action="/admin/appointments/new">
    <div class="grid">
      <div><label>Service type</label><input name="service_type" required placeholder="AC Repair"></div>
      <div><label>Price (USD credits)</label><input name="price" type="number" step="1" required value="75"></div>
      <div><label>City</label><input name="city" required></div>
      <div><label>ZIP</label><input name="zip" required></div>
      <div><label>Scheduled time</label><input name="scheduled_time" required placeholder="2026-06-10 14:00"></div>
      <div><label>Est. job value (USD)</label><input name="est_job_value" type="number" step="1" placeholder="3500"></div>
    </div>
    <label>Job summary (public, non-identifying)</label><input name="job_summary" required
       placeholder="3-ton system, 12yr old, not cooling; homeowner ready to schedule">
    <hr><b class="muted">Private (revealed only to buyer)</b>
    <div class="grid">
      <div><label>Homeowner name</label><input name="homeowner_name" required></div>
      <div><label>Homeowner phone</label><input name="homeowner_phone" required></div>
      <div><label>Full address</label><input name="address_full" required></div>
      <div><label>Homeowner email</label><input name="homeowner_email" type="email"></div>
    </div>
    <label>Private notes</label><input name="private_notes">
    <div class="grid">
      <div><label><input type="checkbox" name="consent_captured" style="width:auto"> Homeowner consent captured (TCPA)</label></div>
      <div><label>Consent source</label><input name="consent_source" placeholder="web form / inbound call"></div>
    </div>
    <label><input type="checkbox" name="publish" style="width:auto"> Publish immediately (requires consent)</label>
    <button class="btn" type="submit">Create appointment</button>
  </form>
</div>
<div class="card">
  <h3>Appointments</h3>
  <table><tr><th>ID</th><th>Type</th><th>Area</th><th>Time</th><th class="right">Price</th><th>Status</th><th>Buyer</th><th></th></tr>
  {% for a in appointments %}<tr>
    <td>{{ a['id'] }}</td><td>{{ a['service_type'] }}</td><td>{{ a['city'] }} {{ a['zip'] }}</td>
    <td class="muted">{{ a['scheduled_time'] }}</td><td class="right">{{ dollars(a['price_cents']) }}</td>
    <td><span class="pill {{ a['status'] }}">{{ a['status'] }}</span>
        {% if not a['consent_captured'] %}<br><span class="muted">no consent</span>{% endif %}
        {% if a['origin'] %}<br><span class="muted">{{ a['origin'] }}</span>{% endif %}</td>
    <td>{{ a['sold_to'] or '' }}</td>
    <td>
      {% if a['status']=='draft' %}
        <form method="post" action="/admin/appointments/{{ a['id'] }}/price" style="display:flex;gap:4px;margin-bottom:4px">
          <input name="price" type="number" step="1" placeholder="USD" value="{{ (a['price_cents']//100) or '' }}" style="width:70px;margin:0">
          <button class="btn ghost">Price</button></form>
        <form method="post" action="/admin/appointments/{{ a['id'] }}/publish"><button class="btn ghost">Publish</button></form>
      {% endif %}
      {% if a['status']=='sold' %}<form method="post" action="/admin/appointments/{{ a['id'] }}/refund" onsubmit="return confirm('Refund this appointment?')"><button class="btn ghost">Refund</button></form>{% endif %}
      {% if a['status'] != 'sold' %}<form method="post" action="/admin/appointments/{{ a['id'] }}/delete" onsubmit="return confirm('Delete appointment #{{ a['id'] }}?')" style="margin-top:4px"><button class="btn ghost" style="color:#a33">Delete</button></form>{% endif %}
    </td></tr>
    {% if a['consent_source'] %}<tr><td></td><td colspan="7" class="muted" style="font-size:.78rem">consent: {{ a['consent_source'] }}</td></tr>{% endif %}
    {% endfor %}
  </table>
</div>
<div class="card">
  <h3>Contractors</h3>
  <table><tr><th>ID</th><th>Company</th><th>Email</th><th class="right">Balance</th><th>Add credits</th></tr>
  {% for c in contractors %}<tr>
    <td>{{ c['id'] }}</td><td>{{ c['company_name'] }}{% if c['is_seed'] %} <span class="pill draft">seed</span>{% endif %}
      {% if c['source_deal_id'] %}<br><span class="muted">deal #{{ c['source_deal_id'] }} · {{ c['source'] }}</span>
        {% if c['contact_raw'] and c['contact_raw'] != c['contact_name'] %}<br><span class="muted">raw: {{ c['contact_raw'] }}</span>{% endif %}{% endif %}
      <br>{% if c['verified'] %}<span class="pill available">✓ verified</span>{% elif c['source_deal_id'] %}<span class="pill refunded">⚠ unverified</span>{% endif %}</td>
    <td class="muted">{{ c['email'] }}{% if c['email_confidence'] %}<br><span class="muted">conf: {{ c['email_confidence'] }}</span>{% endif %}</td>
    <td class="right gold">{{ dollars(c['balance_cents']) }}</td>
    <td><form method="post" action="/admin/contractors/{{ c['id'] }}/credits" style="display:flex;gap:6px;margin-bottom:4px">
        <input name="amount" type="number" step="1" placeholder="USD" style="width:90px;margin:0">
        <button class="btn ghost">Add</button></form>
        {% if c['source_deal_id'] and not c['verified'] %}<form method="post" action="/admin/contractors/{{ c['id'] }}/verify" onsubmit="return confirm('Confirm you have verified this contact + company are real?')"><button class="btn ghost">Mark verified</button></form>{% endif %}</td>
  </tr>{% endfor %}</table>
  <h4>Invite a contractor</h4>
  <form method="post" action="/admin/contractors/new">
    <div class="grid">
      <div><input name="company_name" placeholder="Company" required></div>
      <div><input name="contact_name" placeholder="Contact name" required></div>
      <div><input name="email" type="email" placeholder="Email" required></div>
      <div><input name="phone" placeholder="Phone"></div>
      <div><input name="password" placeholder="Temp password (min 8)" minlength="8" required></div>
      <div><label><input type="checkbox" name="is_seed" style="width:auto"> Seed/internal (Marceau Air)</label></div>
    </div>
    <button class="btn ghost" type="submit">Create contractor</button>
  </form>
</div>"""
