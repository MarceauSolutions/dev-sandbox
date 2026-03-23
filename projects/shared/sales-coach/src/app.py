#!/usr/bin/env python3
"""
AI Sales Coach — Mock Call Practice Tool
Simulates a Naples business owner so William can practice pitching,
handling objections, and refining his Missed Call Text-Back sales approach.

Launch: python projects/shared/sales-coach/src/app.py
URL: http://127.0.0.1:8796
"""

import json
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, session
import anthropic

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = Path(__file__).parent.parent / "data" / "sessions.db"
DB_PATH.parent.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Personas ──────────────────────────────────────────────────────────────────

PERSONAS = {
    "hvac_skeptic": {
        "name": "Mike Kowalski",
        "business": "Kowalski Cooling & Heating",
        "industry": "HVAC",
        "personality": "Skeptical, busy, seen too many vendors. Has been burned by software before. Values ROI proof.",
        "pain": "Misses 8-10 calls/week during busy season, loses $2-4K/week to competitors",
        "objections": ["too expensive", "tried something like this before, didn't work", "I don't trust AI", "too busy to deal with setup"],
        "avatar": "🔧",
        "difficulty": "medium"
    },
    "dental_polite": {
        "name": "Dr. Sandra Chen",
        "business": "Chen Family Dentistry",
        "industry": "Dental",
        "personality": "Polite but cautious. Has an office manager who handles operations. Concerned about patient privacy (HIPAA). Professional, analytical.",
        "pain": "New patient calls go to voicemail after hours, loses 15-20 new patient inquiries/month",
        "objections": ["HIPAA compliance concerns", "need to check with my office manager", "we already have a answering service", "what about patient data security"],
        "avatar": "🦷",
        "difficulty": "hard"
    },
    "plumber_friendly": {
        "name": "Tony Russo",
        "business": "Russo Plumbing",
        "industry": "Plumbing",
        "personality": "Friendly, straight-shooter, one-man band with 2 employees. Open to new ideas if they're simple and cheap.",
        "pain": "Can't answer phone when under a sink. Loses emergency calls to competitors constantly.",
        "objections": ["sounds complicated", "I'm not tech-savvy", "let me think about it"],
        "avatar": "🔩",
        "difficulty": "easy"
    },
    "medspa_owner": {
        "name": "Jessica Laurent",
        "business": "Luxe Med Spa Naples",
        "industry": "Med Spa",
        "personality": "Savvy entrepreneur, has tried multiple marketing tools. Wants results fast. Will ask hard ROI questions.",
        "pain": "After-hours consultation requests go unanswered. Competitors offer online booking. Losing high-value clients ($500-2000/visit).",
        "objections": ["we already use a CRM", "what's your track record", "can you integrate with our booking system", "I need to see a demo"],
        "avatar": "💆",
        "difficulty": "hard"
    },
    "restaurant_owner": {
        "name": "Carlos Mendez",
        "business": "Mendez Kitchen",
        "industry": "Restaurant",
        "personality": "Overwhelmed, running on thin margins. Very price-sensitive. Needs to see immediate value.",
        "pain": "Misses reservation calls during dinner rush. Lost several large party bookings last month.",
        "objections": ["can't afford another expense right now", "my margins are too thin", "how is this different from OpenTable"],
        "avatar": "🍽️",
        "difficulty": "medium"
    }
}

SYSTEM_PROMPT_TEMPLATE = """You are {name}, owner of {business} in Naples, FL.

Personality: {personality}
Hidden pain point: {pain}
Your likely objections: {objections}

You are on a call or in a conversation with William Marceau, who is trying to sell you an AI Missed Call Text-Back service for $297/month. When a call goes to voicemail, his system sends an automatic text to the customer within 10 seconds.

RULES FOR HOW YOU RESPOND:
1. Stay in character as {name} the entire time. Never break character.
2. Be realistic — don't make it too easy or too hard. You're a real business owner with real concerns.
3. Raise objections naturally when William makes claims. Don't accept everything at face value.
4. If William handles an objection well, soften your resistance. If he fumbles it, get more skeptical.
5. If William asks good diagnostic questions, reveal your pain point gradually.
6. Keep responses SHORT (2-4 sentences max) — you're a busy business owner, not a chatbot.
7. React to William's specific words. If he says something that resonates, say so. If he uses jargon, push back.
8. After 8-10 exchanges, if William has handled objections well, you can move toward agreeing to a trial.
9. If William is clearly not landing the pitch, get more dismissive and busy.

Current conversation difficulty: {difficulty}
Industry-specific concern to eventually raise: {industry_concern}"""

INDUSTRY_CONCERNS = {
    "HVAC": "Seasonal volume — worried about paying $297/mo in slow season when calls drop",
    "Dental": "HIPAA compliance — worried about patient data in a text message",
    "Plumbing": "After-hours calls vs emergency dispatch — does text-back delay emergency response?",
    "Med Spa": "Integration with existing booking/CRM system",
    "Restaurant": "Reservation vs walk-in ratio — most customers just show up, is this worth it?"
}

# ── Database ──────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id TEXT,
            started_at TEXT,
            ended_at TEXT,
            turns INTEGER DEFAULT 0,
            outcome TEXT,
            score INTEGER,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            coach_note TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Coach Evaluation ──────────────────────────────────────────────────────────

def get_coach_note(user_message: str, conversation: list, persona: dict) -> str:
    """Quick coach feedback on William's last message."""
    eval_prompt = f"""You are a sales coach reviewing a pitch. William just said: "{user_message}"

Context: He's pitching Missed Call Text-Back ($297/mo, free 2-week trial) to {persona['name']} ({persona['industry']}).
Previous turns: {len(conversation)} exchanges so far.

In ONE sentence, give him specific coaching feedback. Focus on:
- Was that a strong opener/close/objection handle?
- What could he have said better?
- Did he use the right framework (pain → agitate → solution)?

Format: Start with ✅ (good), ⚠️ (okay), or ❌ (weak). Then one sentence."""

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{"role": "user", "content": eval_prompt}]
        )
        return resp.content[0].text
    except Exception:
        return ""

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Sales Coach — Mock Call Practice</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #1a1a1a; color: #f0f0f0; min-height: 100vh; }
  .header { background: linear-gradient(135deg, #1a2744 0%, #2d2d2d 100%);
            padding: 16px 24px; border-bottom: 2px solid #C9963C;
            display: flex; align-items: center; gap: 12px; }
  .header h1 { color: #C9963C; font-size: 20px; }
  .header p { color: #999; font-size: 13px; }
  .layout { display: grid; grid-template-columns: 280px 1fr; height: calc(100vh - 65px); }

  /* Sidebar */
  .sidebar { background: #222; border-right: 1px solid #333; padding: 16px; overflow-y: auto; }
  .sidebar h3 { color: #C9963C; font-size: 12px; text-transform: uppercase;
                letter-spacing: 1px; margin-bottom: 12px; }
  .persona-card { border: 1px solid #444; border-radius: 8px; padding: 12px;
                  margin-bottom: 10px; cursor: pointer; transition: all 0.2s; }
  .persona-card:hover { border-color: #C9963C; background: #2a2a2a; }
  .persona-card.active { border-color: #C9963C; background: #1a2744; }
  .persona-name { font-weight: bold; font-size: 14px; margin-bottom: 2px; }
  .persona-biz { color: #888; font-size: 12px; }
  .difficulty { display: inline-block; padding: 2px 8px; border-radius: 3px;
                font-size: 10px; font-weight: bold; margin-top: 4px; }
  .easy { background: #1a3a1a; color: #4ade80; }
  .medium { background: #3a2a00; color: #fbbf24; }
  .hard { background: #3a0000; color: #f87171; }

  .stats-box { background: #1a2744; border-radius: 8px; padding: 12px; margin-top: 16px; }
  .stat-row { display: flex; justify-content: space-between; padding: 4px 0;
              font-size: 12px; border-bottom: 1px solid #333; }
  .stat-row:last-child { border-bottom: none; }
  .stat-val { color: #C9963C; font-weight: bold; }

  /* Chat Area */
  .chat-area { display: flex; flex-direction: column; }
  .prospect-banner { background: #1a2744; padding: 12px 20px;
                     border-bottom: 1px solid #333; display: flex; align-items: center; gap: 12px; }
  .prospect-avatar { font-size: 32px; }
  .prospect-name { font-weight: bold; font-size: 16px; }
  .prospect-detail { color: #888; font-size: 12px; }
  .call-status { margin-left: auto; }
  .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
  .status-active { background: #1a3a1a; color: #4ade80; }
  .status-idle { background: #333; color: #888; }

  .messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 75%; }
  .msg.user { align-self: flex-end; }
  .msg.assistant { align-self: flex-start; }
  .bubble { padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
  .user .bubble { background: #C9963C; color: #1a1a1a; font-weight: 500;
                  border-bottom-right-radius: 4px; }
  .assistant .bubble { background: #2a2a2a; border: 1px solid #444;
                        border-bottom-left-radius: 4px; }
  .msg-label { font-size: 11px; color: #666; margin-bottom: 3px; }
  .user .msg-label { text-align: right; }
  .coach-note { font-size: 11px; margin-top: 4px; padding: 4px 8px;
                background: #1a2744; border-radius: 4px; color: #aaa;
                border-left: 2px solid #C9963C; }

  .input-area { padding: 16px 20px; background: #222; border-top: 1px solid #333; }
  .input-row { display: flex; gap: 10px; align-items: flex-end; }
  textarea { flex: 1; background: #2a2a2a; border: 1px solid #444; border-radius: 8px;
             color: #f0f0f0; padding: 10px 14px; font-size: 14px; resize: none;
             font-family: inherit; min-height: 44px; max-height: 120px; }
  textarea:focus { outline: none; border-color: #C9963C; }
  .send-btn { background: #C9963C; color: #1a1a1a; border: none; border-radius: 8px;
              padding: 10px 20px; font-weight: bold; cursor: pointer; font-size: 14px;
              white-space: nowrap; }
  .send-btn:hover { background: #d4af37; }
  .send-btn:disabled { background: #555; cursor: not-allowed; }
  .hint-row { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
  .hint { background: #2a2a2a; border: 1px solid #444; border-radius: 4px;
          padding: 3px 8px; font-size: 11px; color: #888; cursor: pointer; }
  .hint:hover { border-color: #C9963C; color: #C9963C; }

  .start-screen { flex: 1; display: flex; align-items: center; justify-content: center;
                  flex-direction: column; gap: 16px; text-align: center; padding: 40px; }
  .start-screen h2 { color: #C9963C; font-size: 24px; }
  .start-screen p { color: #888; max-width: 400px; line-height: 1.6; }
  .start-btn { background: #C9963C; color: #1a1a1a; border: none; border-radius: 8px;
               padding: 14px 32px; font-size: 16px; font-weight: bold; cursor: pointer; }

  .end-screen { display: none; padding: 24px; }
  .score-card { background: #1a2744; border-radius: 12px; padding: 24px; max-width: 500px; margin: 0 auto; }
  .score-big { font-size: 64px; color: #C9963C; text-align: center; font-weight: bold; }
  .score-label { text-align: center; color: #888; font-size: 14px; margin-top: 4px; }
  .outcome-badge { text-align: center; font-size: 18px; font-weight: bold; margin: 16px 0; }
  .feedback-list { margin-top: 16px; }
  .feedback-item { padding: 8px 0; border-bottom: 1px solid #333; font-size: 13px; }
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>🎯 AI Sales Coach</h1>
    <p>Mock call practice — Missed Call Text-Back pitch training</p>
  </div>
</div>

<div class="layout">
  <!-- Sidebar -->
  <div class="sidebar">
    <h3>Choose Your Prospect</h3>
    <div id="personaList"></div>

    <div class="stats-box" id="statsBox" style="display:none">
      <h3 style="color:#C9963C;font-size:11px;text-transform:uppercase;margin-bottom:8px;">Session Stats</h3>
      <div class="stat-row"><span>Calls Practiced</span><span class="stat-val" id="statTotal">0</span></div>
      <div class="stat-row"><span>Avg Score</span><span class="stat-val" id="statAvg">—</span></div>
      <div class="stat-row"><span>Trials Closed</span><span class="stat-val" id="statClosed">0</span></div>
      <div class="stat-row"><span>Toughest Objection</span><span class="stat-val" id="statTough">—</span></div>
    </div>
  </div>

  <!-- Chat -->
  <div class="chat-area" id="chatArea">
    <div class="start-screen" id="startScreen">
      <h2>Ready to Practice?</h2>
      <p>Select a prospect from the left, then hit Start Call. The AI will play the role of a Naples business owner. Pitch your Missed Call Text-Back service.</p>
      <p style="color:#C9963C;font-size:13px;">💡 Tip: Start with a pain question, not a pitch. "What happens when you miss a call?"</p>
    </div>
  </div>
</div>

<script>
const personas = {{ personas|tojson }};
let activePersona = null;
let sessionId = null;
let conversationHistory = [];
let isLoading = false;

// Build persona list
const personaList = document.getElementById('personaList');
Object.entries(personas).forEach(([id, p]) => {
  const card = document.createElement('div');
  card.className = 'persona-card';
  card.dataset.id = id;
  card.innerHTML = `
    <div class="persona-name">${p.avatar} ${p.name}</div>
    <div class="persona-biz">${p.business}</div>
    <span class="difficulty ${p.difficulty}">${p.difficulty.toUpperCase()}</span>
  `;
  card.onclick = () => selectPersona(id, card);
  personaList.appendChild(card);
});

function selectPersona(id, card) {
  document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
  activePersona = id;
  showStartScreen(personas[id]);
}

function showStartScreen(p) {
  const chatArea = document.getElementById('chatArea');
  chatArea.innerHTML = `
    <div class="prospect-banner">
      <div class="prospect-avatar">${p.avatar}</div>
      <div>
        <div class="prospect-name">${p.name}</div>
        <div class="prospect-detail">${p.business} · ${p.industry}</div>
      </div>
      <div class="call-status">
        <span class="status-badge status-idle">⏸ Ready</span>
      </div>
    </div>
    <div class="start-screen">
      <h2>Calling ${p.name}</h2>
      <p><strong>${p.business}</strong> — ${p.industry}</p>
      <p style="color:#888;font-size:13px;">Difficulty: <span class="difficulty ${p.difficulty}">${p.difficulty.toUpperCase()}</span></p>
      <button class="start-btn" onclick="startCall()">📞 Start Call</button>
    </div>
  `;
}

async function startCall() {
  if (!activePersona) return;
  const p = personas[activePersona];
  conversationHistory = [];

  const resp = await fetch('/start_session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({persona_id: activePersona})
  });
  const data = await resp.json();
  sessionId = data.session_id;

  const chatArea = document.getElementById('chatArea');
  chatArea.innerHTML = `
    <div class="prospect-banner">
      <div class="prospect-avatar">${p.avatar}</div>
      <div>
        <div class="prospect-name">${p.name}</div>
        <div class="prospect-detail">${p.business} · ${p.industry}</div>
      </div>
      <div class="call-status">
        <span class="status-badge status-active">🔴 Live Call</span>
      </div>
    </div>
    <div class="messages" id="messages">
      <div class="msg assistant">
        <div class="msg-label">${p.name}</div>
        <div class="bubble">${data.opening}</div>
      </div>
    </div>
    <div class="input-area">
      <div class="input-row">
        <textarea id="userInput" placeholder="What will you say?" rows="1"
          onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault();sendMessage();}"></textarea>
        <button class="send-btn" onclick="sendMessage()" id="sendBtn">Send</button>
      </div>
      <div class="hint-row">
        <div class="hint" onclick="useHint('What happens when you miss a call?')">Pain question</div>
        <div class="hint" onclick="useHint('What would that cost you per month?')">Agitate</div>
        <div class="hint" onclick="useHint('Here\\'s what I\\'d do — set it up free for 2 weeks.')">Free trial close</div>
        <div class="hint" onclick="useHint('The trial is completely free, no card required.')">No-risk offer</div>
        <div class="hint" onclick="endCall()">End Call</div>
      </div>
    </div>
  `;

  conversationHistory.push({role: 'assistant', content: data.opening});
  document.getElementById('userInput').focus();
}

function useHint(text) {
  document.getElementById('userInput').value = text;
  document.getElementById('userInput').focus();
}

async function sendMessage() {
  if (isLoading) return;
  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;

  isLoading = true;
  input.value = '';
  document.getElementById('sendBtn').disabled = true;

  const messages = document.getElementById('messages');

  // Add user message
  messages.innerHTML += `
    <div class="msg user">
      <div class="msg-label">You (William)</div>
      <div class="bubble">${escHtml(text)}</div>
    </div>`;
  messages.scrollTop = messages.scrollHeight;

  conversationHistory.push({role: 'user', content: text});

  try {
    const resp = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id: sessionId,
        persona_id: activePersona,
        message: text,
        history: conversationHistory
      })
    });
    const data = await resp.json();

    conversationHistory.push({role: 'assistant', content: data.reply});

    const p = personas[activePersona];
    let msgHtml = `
      <div class="msg assistant">
        <div class="msg-label">${p.name}</div>
        <div class="bubble">${escHtml(data.reply)}</div>`;
    if (data.coach_note) {
      msgHtml += `<div class="coach-note">💬 Coach: ${escHtml(data.coach_note)}</div>`;
    }
    msgHtml += `</div>`;
    messages.innerHTML += msgHtml;
    messages.scrollTop = messages.scrollHeight;

  } catch (e) {
    messages.innerHTML += `<div style="color:#f87171;font-size:12px;padding:8px;">Error — check console</div>`;
  }

  isLoading = false;
  document.getElementById('sendBtn').disabled = false;
  document.getElementById('userInput').focus();
}

async function endCall() {
  if (!sessionId) return;
  const resp = await fetch('/end_session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session_id: sessionId, history: conversationHistory})
  });
  const data = await resp.json();
  showResults(data);
  loadStats();
}

function showResults(data) {
  const p = personas[activePersona];
  const chatArea = document.getElementById('chatArea');
  chatArea.innerHTML = `
    <div style="padding:24px;overflow-y:auto;flex:1;">
      <div class="score-card">
        <div class="score-big">${data.score}</div>
        <div class="score-label">/ 100</div>
        <div class="outcome-badge" style="color:${data.outcome === 'closed' ? '#4ade80' : data.outcome === 'interested' ? '#fbbf24' : '#f87171'}">
          ${data.outcome === 'closed' ? '✅ Trial Closed!' : data.outcome === 'interested' ? '⚡ Still Warm' : '❌ Lost the Lead'}
        </div>
        <div style="color:#888;font-size:13px;text-align:center;margin-bottom:16px;">
          ${data.turns} exchanges with ${p.name}
        </div>
        <div style="font-size:14px;font-weight:bold;color:#C9963C;margin-bottom:8px;">Coach Feedback:</div>
        <div style="font-size:13px;color:#ccc;line-height:1.7;">${data.feedback.replace(/\\n/g,'<br>')}</div>
        <div style="margin-top:20px;display:flex;gap:10px;">
          <button class="start-btn" style="flex:1;" onclick="startCall()">🔄 Try Again</button>
          <button class="start-btn" style="flex:1;background:#2a2a2a;color:#C9963C;border:1px solid #C9963C;"
            onclick="document.getElementById('chatArea').innerHTML = document.getElementById('startScreen').outerHTML">
            Switch Prospect
          </button>
        </div>
      </div>
    </div>`;
}

async function loadStats() {
  const resp = await fetch('/stats');
  const data = await resp.json();
  document.getElementById('statsBox').style.display = 'block';
  document.getElementById('statTotal').textContent = data.total;
  document.getElementById('statAvg').textContent = data.avg_score ? data.avg_score + '/100' : '—';
  document.getElementById('statClosed').textContent = data.closed;
}

function escHtml(text) {
  return text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
             .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

loadStats();
</script>
</body>
</html>"""

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML, personas=PERSONAS)

@app.route("/start_session", methods=["POST"])
def start_session():
    data = request.json
    persona_id = data["persona_id"]
    p = PERSONAS[persona_id]

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO sessions (persona_id, started_at) VALUES (?, ?)",
        (persona_id, datetime.now().isoformat())
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()

    # Get opening line from prospect
    system = SYSTEM_PROMPT_TEMPLATE.format(
        name=p["name"], business=p["business"], industry=p["industry"],
        personality=p["personality"], pain=p["pain"],
        objections=", ".join(p["objections"]),
        difficulty=p["difficulty"],
        industry_concern=INDUSTRY_CONCERNS.get(p["industry"], "general concerns about ROI")
    )

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system=system,
        messages=[{"role": "user", "content": "[The phone rings. You answer it. William says: 'Hi, is this {name}? My name is William Marceau, I work with local businesses on AI automation — got a quick minute?']".format(name=p["name"])}]
    )
    opening = resp.content[0].text

    return jsonify({"session_id": session_id, "opening": opening})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    persona_id = data["persona_id"]
    p = PERSONAS[persona_id]
    history = data["history"]
    user_message = data["message"]

    system = SYSTEM_PROMPT_TEMPLATE.format(
        name=p["name"], business=p["business"], industry=p["industry"],
        personality=p["personality"], pain=p["pain"],
        objections=", ".join(p["objections"]),
        difficulty=p["difficulty"],
        industry_concern=INDUSTRY_CONCERNS.get(p["industry"], "general concerns about ROI")
    )

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=system,
        messages=history
    )
    reply = resp.content[0].text

    # Get coach feedback (fast, Haiku)
    coach_note = get_coach_note(user_message, history, p)

    # Save to DB
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp, coach_note) VALUES (?,?,?,?,?)",
        (data["session_id"], "user", user_message, datetime.now().isoformat(), "")
    )
    conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp, coach_note) VALUES (?,?,?,?,?)",
        (data["session_id"], "assistant", reply, datetime.now().isoformat(), coach_note)
    )
    conn.execute("UPDATE sessions SET turns = turns + 1 WHERE id = ?", (data["session_id"],))
    conn.commit()
    conn.close()

    return jsonify({"reply": reply, "coach_note": coach_note})

@app.route("/end_session", methods=["POST"])
def end_session():
    data = request.json
    history = data["history"]
    session_id = data["session_id"]

    # Ask Claude to score the session
    transcript = "\n".join([f"{'William' if m['role']=='user' else 'Prospect'}: {m['content']}" for m in history])

    eval_resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": f"""Score this sales call transcript (0-100) and determine the outcome.

TRANSCRIPT:
{transcript}

Evaluate:
1. Did William open with a pain question or lead with a pitch?
2. Did he agitate the pain with math/ROI?
3. Did he handle objections with the right framework?
4. Did he close with the free trial offer?
5. Was he natural or robotic?

Respond in this exact JSON format:
{{"score": 75, "outcome": "interested", "turns": 6, "feedback": "Strong pain questions in the opener. Lost momentum when the objection came — next time, acknowledge first ('that's fair') before countering. The trial close was good but came too early. Suggest: more agitation before the solution."}}

outcome options: "closed" (they agreed to trial), "interested" (warm, next step needed), "lost" (they shut it down)"""}]
    )

    try:
        result = json.loads(eval_resp.content[0].text)
    except Exception:
        result = {"score": 50, "outcome": "interested", "turns": len(history)//2,
                  "feedback": "Session completed. Keep practicing — consistency beats perfection."}

    conn = get_db()
    conn.execute(
        "UPDATE sessions SET ended_at=?, outcome=?, score=?, turns=? WHERE id=?",
        (datetime.now().isoformat(), result.get("outcome"), result.get("score"), result.get("turns"), session_id)
    )
    conn.commit()
    conn.close()

    return jsonify(result)

@app.route("/stats")
def stats():
    conn = get_db()
    rows = conn.execute("SELECT score, outcome FROM sessions WHERE score IS NOT NULL").fetchall()
    conn.close()
    total = len(rows)
    avg_score = round(sum(r["score"] for r in rows) / total) if total else 0
    closed = sum(1 for r in rows if r["outcome"] == "closed")
    return jsonify({"total": total, "avg_score": avg_score if total else None, "closed": closed})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("═" * 50)
    print("  AI Sales Coach")
    print("  http://127.0.0.1:8796")
    print("═" * 50)
    app.run(host="127.0.0.1", port=8796, debug=False)
