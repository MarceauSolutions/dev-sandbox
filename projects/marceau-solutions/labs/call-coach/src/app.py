"""
Call Coach — Sales Coaching Backend
FastAPI service: receive audio → Whisper transcription → Claude scoring → SQLite storage
Port: 8798  |  Subdomain: calls.marceausolutions.com
"""
import os
import json
import sqlite3
import tempfile
import re
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import openai

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "call_coach.db"
PORT = int(os.getenv("CALL_COACH_PORT", "8798"))

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SCORING_DIMENSIONS = [
    ("rapport",       "Rapport Building",     "Did you establish warmth, relate to their situation, make them feel heard?"),
    ("pain_discovery","Pain Discovery",        "Did you ask deep questions to uncover real business pain and quantify it?"),
    ("value",         "Value Articulation",    "Did you clearly connect your solution to their specific pain with concrete outcomes?"),
    ("objections",    "Objection Handling",    "Did you acknowledge, reframe, and resolve objections without getting defensive?"),
    ("tonality",      "Tonality & Confidence", "Did you sound certain, calm, and in control — not desperate or tentative?"),
    ("close",         "Closing Attempt",       "Did you ask for the business, propose a clear next step, or set a commitment?"),
]

app = FastAPI(title="Call Coach", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── DB ──────────────────────────────────────────────────────────────────────────
def _init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                business    TEXT DEFAULT '',
                transcript  TEXT NOT NULL,
                rapport     INTEGER,
                pain_discovery INTEGER,
                value       INTEGER,
                objections  INTEGER,
                tonality    INTEGER,
                close       INTEGER,
                overall     REAL,
                feedback    TEXT,
                tags        TEXT DEFAULT ''
            )
        """)
        conn.commit()

_init_db()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ── Scoring ─────────────────────────────────────────────────────────────────────
SCORE_PROMPT = """You are a world-class sales coach specializing in psychological persuasion and consultative selling. Analyze this sales call transcript/narration and score the salesperson on 6 dimensions.

Transcript:
{transcript}

Score each dimension from 1–10 (1=very poor, 5=average, 10=exceptional). Be honest and strict — a 7+ means genuinely good, not just attempted.

Respond ONLY with valid JSON in this exact format:
{{
  "rapport": <1-10>,
  "pain_discovery": <1-10>,
  "value": <1-10>,
  "objections": <1-10>,
  "tonality": <1-10>,
  "close": <1-10>,
  "strengths": ["<specific strength 1>", "<specific strength 2>"],
  "improvements": ["<specific coaching point 1>", "<specific coaching point 2>", "<specific coaching point 3>"],
  "one_liner": "<one sentence of the most important insight from this call>"
}}"""


def score_transcript(transcript: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": SCORE_PROMPT.format(transcript=transcript)}]
    )
    raw = msg.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    client_oa = openai.OpenAI(api_key=OPENAI_KEY)
    suffix = Path(filename).suffix or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    try:
        with open(tmp_path, "rb") as f:
            result = client_oa.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en"
            )
        return result.text
    finally:
        os.unlink(tmp_path)


# ── Rolling average helpers ──────────────────────────────────────────────────────
def rolling_averages(calls: list[dict], window: int = 10) -> dict:
    """Compute rolling average of last `window` calls for each dimension."""
    recent = calls[-window:]
    if not recent:
        return {}
    dims = ["rapport", "pain_discovery", "value", "objections", "tonality", "close", "overall"]
    return {d: round(sum(c[d] for c in recent if c[d]) / len(recent), 1) for d in dims}


# ── Routes ──────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"service": "call-coach", "status": "ok", "port": PORT}


@app.post("/calls/submit")
async def submit_call(
    audio: UploadFile = File(None),
    transcript_text: str = Form(None),
    business: str = Form(""),
):
    """Accept either an audio file (gets Whisper-transcribed) or raw text."""
    if not audio and not transcript_text:
        raise HTTPException(400, "Provide audio file or transcript_text")

    # Transcribe if audio provided
    if audio:
        audio_bytes = await audio.read()
        transcript = transcribe_audio(audio_bytes, audio.filename or "call.m4a")
    else:
        transcript = transcript_text.strip()

    if not transcript:
        raise HTTPException(422, "Empty transcript after processing")

    # Score with Claude
    scores = score_transcript(transcript)
    overall = round(
        sum(scores[d] for d in ["rapport", "pain_discovery", "value", "objections", "tonality", "close"]) / 6,
        1
    )

    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO calls
              (recorded_at, business, transcript, rapport, pain_discovery, value,
               objections, tonality, close, overall, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now, business, transcript,
            scores["rapport"], scores["pain_discovery"], scores["value"],
            scores["objections"], scores["tonality"], scores["close"],
            overall,
            json.dumps({
                "strengths": scores.get("strengths", []),
                "improvements": scores.get("improvements", []),
                "one_liner": scores.get("one_liner", "")
            })
        ))
        conn.commit()
        call_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return JSONResponse({
        "ok": True,
        "call_id": call_id,
        "transcript": transcript,
        "scores": {
            "rapport": scores["rapport"],
            "pain_discovery": scores["pain_discovery"],
            "value": scores["value"],
            "objections": scores["objections"],
            "tonality": scores["tonality"],
            "close": scores["close"],
            "overall": overall,
        },
        "feedback": {
            "strengths": scores.get("strengths", []),
            "improvements": scores.get("improvements", []),
            "one_liner": scores.get("one_liner", ""),
        }
    })


@app.get("/calls")
def list_calls(limit: int = 50):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM calls ORDER BY recorded_at DESC LIMIT ?", (limit,)
        ).fetchall()
    calls = [dict(r) for r in rows]
    return {"calls": calls, "rolling_avg": rolling_averages(list(reversed(calls)))}


@app.get("/calls/{call_id}")
def get_call(call_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM calls WHERE id=?", (call_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Call not found")
    return dict(row)


def _personal_bests(calls: list[dict]) -> dict:
    """Return personal best score per dimension."""
    dims = ["rapport", "pain_discovery", "value", "objections", "tonality", "close", "overall"]
    bests = {}
    for d in dims:
        vals = [c[d] for c in calls if c.get(d)]
        bests[d] = max(vals) if vals else 0
    return bests


@app.get("/", response_class=HTMLResponse)
def dashboard():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM calls ORDER BY recorded_at ASC").fetchall()
    calls = [dict(r) for r in rows]
    total = len(calls)
    avg = rolling_averages(calls)
    bests = _personal_bests(calls)
    recent10 = calls[-10:][::-1]
    last_call = calls[-1] if calls else None

    dim_keys = ["rapport", "pain_discovery", "value", "objections", "tonality", "close"]
    dim_labels = ["Rapport", "Pain Discovery", "Value", "Objections", "Tonality", "Close"]

    def score_color(s):
        if not s:
            return "#666"
        if s >= 8:
            return "#4ade80"
        if s >= 6:
            return "#C9963C"
        return "#ef4444"

    def bar(score):
        pct = int((score or 0) * 10)
        color = score_color(score)
        return (f'<div style="background:#1a1a1a;border-radius:4px;height:6px;width:100%;margin-top:2px">'
                f'<div style="background:{color};height:6px;border-radius:4px;width:{pct}%"></div></div>')

    # Radar chart data: rolling avg vs last call
    avg_vals = [avg.get(k, 0) for k in dim_keys]
    last_vals = [last_call.get(k, 0) if last_call else 0 for k in dim_keys]
    avg_js = "[" + ",".join(str(v) for v in avg_vals) + "]"
    last_js = "[" + ",".join(str(v) for v in last_vals) + "]"
    labels_js = "[" + ",".join(f'"{l}"' for l in dim_labels) + "]"

    # Personal bests bar
    pb_html = ""
    for k, label in zip(dim_keys, dim_labels):
        pb = bests.get(k, 0)
        last = last_call.get(k, 0) if last_call else 0
        is_pb = last and last >= pb and total > 1
        pb_html += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:7px 0;border-bottom:1px solid #222">'
            f'<span style="color:#999;font-size:13px">{label}</span>'
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<span style="color:#555;font-size:11px">PB {pb}</span>'
            f'<span style="color:{score_color(avg.get(k,0))};font-weight:700">{avg.get(k,0)} avg</span>'
            + (f'<span style="color:#4ade80;font-size:11px">🔥 PB!</span>' if is_pb else '') +
            f'</div></div>'
        )

    # Call cards
    call_cards = ""
    for c in recent10:
        fb = json.loads(c["feedback"]) if c["feedback"] else {}
        improvements = "".join(
            f'<li style="color:#bbb;margin:3px 0;font-size:12px">{i}</li>'
            for i in fb.get("improvements", [])
        )
        strengths = "".join(
            f'<li style="color:#C9963C;margin:3px 0;font-size:12px">{s}</li>'
            for s in fb.get("strengths", [])
        )
        dim_scores = ""
        for key, label in zip(dim_keys, dim_labels):
            s = c.get(key)
            pb_val = bests.get(key, 0)
            is_pb_call = s and s >= pb_val and total > 1
            pb_flag = ' <span style="color:#4ade80;font-size:10px">PB</span>' if is_pb_call else ''
            dim_scores += (
                f'<div style="margin:4px 0">'
                f'<span style="color:#888;font-size:11px">{label}{pb_flag}</span>'
                f'<span style="float:right;color:{score_color(s)};font-weight:700">{s or "—"}</span>'
                f'{bar(s)}</div>'
            )
        dt = c["recorded_at"][:10] if c["recorded_at"] else "—"
        biz = c["business"] or "Unknown business"
        call_cards += (
            f'<div style="background:#1e1e1e;border:1px solid #333;border-radius:10px;'
            f'padding:16px;margin-bottom:12px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
            f'<div><span style="color:#fff;font-weight:700">{biz}</span>'
            f'<span style="color:#666;font-size:12px;margin-left:8px">{dt}</span></div>'
            f'<span style="background:#C9963C;color:#000;font-weight:800;font-size:18px;'
            f'padding:4px 12px;border-radius:6px">{c["overall"] or "—"}</span></div>'
            f'{dim_scores}'
            f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid #2a2a2a">'
            f'<p style="color:#C9963C;font-size:12px;margin:0 0 4px">'
            f'<strong>Key insight:</strong> {fb.get("one_liner","—")}</p>'
            f'<ul style="margin:6px 0 0;padding-left:16px">{strengths}</ul>'
            f'<ul style="margin:4px 0 0;padding-left:16px">{improvements}</ul>'
            f'</div></div>'
        )

    avg_overall = avg.get("overall", 0)
    avg_color = score_color(avg_overall)

    no_calls_msg = '<p style="color:#555;text-align:center;padding:40px 0">No calls yet — paste a transcript to get started.</p>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Call Coach</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #111; color: #fff; font-family: -apple-system, sans-serif; padding: 16px; max-width: 640px; margin: 0 auto; }}
    h1 {{ color: #C9963C; font-size: 22px; margin-bottom: 4px; }}
    h2 {{ color: #fff; font-size: 15px; margin-bottom: 12px; }}
    textarea {{ width:100%;background:#1e1e1e;border:1px solid #444;border-radius:8px;
      color:#fff;padding:12px;font-size:14px;min-height:100px;resize:vertical; }}
    input[type=text] {{ width:100%;background:#1e1e1e;border:1px solid #444;border-radius:8px;
      color:#fff;padding:10px 12px;font-size:14px;margin-bottom:8px; }}
    button {{ background:#C9963C;color:#000;border:none;border-radius:8px;
      padding:12px 24px;font-size:15px;font-weight:700;cursor:pointer;width:100%; }}
    button:active {{ opacity:0.8; }}
    #result {{ margin-top:12px;padding:12px;background:#1e1e1e;border-radius:8px;display:none; }}
  </style>
</head>
<body>
  <div style="margin-bottom:20px">
    <h1>Call Coach</h1>
    <p style="color:#666;font-size:13px">{total} calls logged · 10-call rolling average</p>
  </div>

  <!-- Submit form -->
  <div style="background:#1e1e1e;border:1px solid #333;border-radius:10px;padding:16px;margin-bottom:16px">
    <h2>Submit a Call</h2>
    <input type="text" id="biz" placeholder="Business name (optional)">
    <textarea id="transcript" placeholder="Paste transcript or narrate what happened on the call..."></textarea>
    <div style="height:8px"></div>
    <button onclick="submitCall()">Score This Call →</button>
    <div id="result"></div>
  </div>

  <!-- Radar chart -->
  <div style="background:#1e1e1e;border:1px solid #333;border-radius:10px;padding:16px;margin-bottom:16px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <p style="color:#999;font-size:13px">Sales Fingerprint · 10-call avg vs last call</p>
      <span style="color:{avg_color};font-size:26px;font-weight:800">{avg_overall}</span>
    </div>
    <canvas id="radar" style="max-height:280px"></canvas>
    {"" if total == 0 else ""}
  </div>

  <!-- Personal bests -->
  <div style="background:#1e1e1e;border:1px solid #333;border-radius:10px;padding:16px;margin-bottom:20px">
    <h2>Personal Bests</h2>
    {pb_html if pb_html else '<p style="color:#555;font-size:13px">Log calls to track personal bests.</p>'}
  </div>

  <h2>Recent Calls</h2>
  {call_cards if call_cards else no_calls_msg}

  <script>
  // Radar chart
  const radarCtx = document.getElementById('radar').getContext('2d');
  new Chart(radarCtx, {{
    type: 'radar',
    data: {{
      labels: {labels_js},
      datasets: [
        {{
          label: '10-Call Avg',
          data: {avg_js},
          borderColor: '#C9963C',
          backgroundColor: 'rgba(201,150,60,0.15)',
          borderWidth: 2,
          pointBackgroundColor: '#C9963C',
          pointRadius: 4,
        }},
        {{
          label: 'Last Call',
          data: {last_js},
          borderColor: '#4ade80',
          backgroundColor: 'rgba(74,222,128,0.1)',
          borderWidth: 2,
          pointBackgroundColor: '#4ade80',
          pointRadius: 4,
        }}
      ]
    }},
    options: {{
      responsive: true,
      scales: {{
        r: {{
          min: 0, max: 10,
          ticks: {{ stepSize: 2, color: '#555', backdropColor: 'transparent', font: {{ size: 10 }} }},
          grid: {{ color: '#2a2a2a' }},
          pointLabels: {{ color: '#999', font: {{ size: 11 }} }},
          angleLines: {{ color: '#2a2a2a' }}
        }}
      }},
      plugins: {{
        legend: {{ labels: {{ color: '#999', font: {{ size: 12 }} }} }}
      }}
    }}
  }});

  // Submit call via fetch
  async function submitCall() {{
    const transcript = document.getElementById('transcript').value.trim();
    const business = document.getElementById('biz').value.trim();
    const btn = document.querySelector('button');
    const result = document.getElementById('result');
    if (!transcript) {{ result.style.display='block'; result.innerHTML='<p style="color:#ef4444">Paste a transcript first.</p>'; return; }}
    btn.textContent = 'Scoring…';
    btn.disabled = true;
    result.style.display = 'none';
    try {{
      const fd = new FormData();
      fd.append('transcript_text', transcript);
      fd.append('business', business);
      const res = await fetch('/calls/submit', {{ method:'POST', body: fd }});
      const data = await res.json();
      if (!data.ok) throw new Error(data.detail || 'Error');
      const s = data.scores;
      result.style.display = 'block';
      result.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <strong style="color:#fff">Overall</strong>
          <span style="color:#C9963C;font-size:24px;font-weight:800">${{s.overall}}</span>
        </div>
        <p style="color:#C9963C;font-size:13px;margin-bottom:8px">${{data.feedback.one_liner}}</p>
        <ul style="padding-left:16px;font-size:12px;color:#bbb">${{data.feedback.improvements.map(i=>`<li style="margin:3px 0">${{i}}</li>`).join('')}}</ul>
        <p style="color:#4ade80;font-size:12px;margin-top:8px">✓ Saved. Reload to see updated radar.</p>
      `;
      document.getElementById('transcript').value = '';
      document.getElementById('biz').value = '';
    }} catch(e) {{
      result.style.display = 'block';
      result.innerHTML = `<p style="color:#ef4444">${{e.message}}</p>`;
    }}
    btn.textContent = 'Score This Call →';
    btn.disabled = false;
  }}
  </script>
</body>
</html>""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=False)
