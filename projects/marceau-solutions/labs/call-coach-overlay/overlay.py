#!/usr/bin/env python3
"""
Live Call Coach Overlay
macOS floating window — always on top, semi-transparent
Listens via MacBook mic → Whisper transcription → Claude next-best-response

Usage: python3 overlay.py
Put call on speakerphone → MacBook mic captures both sides
"""

import os
import sys
import json
import time
import queue
import threading
import tempfile
import wave
import struct
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env from dev-sandbox root
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Colors ────────────────────────────────────────────────────
BG = "#1a1a1a"
GOLD = "#C9963C"
WHITE = "#f0f0f0"
DIM = "#888888"
GREEN = "#22c55e"
RED = "#ef4444"
BLUE = "#60a5fa"
ORANGE = "#f97316"

STAGE_COLORS = {
    "Rapport":     "#60a5fa",   # blue
    "Pain":        "#f97316",   # orange
    "Objection":   "#ef4444",   # red
    "Close":       "#22c55e",   # green
    "Unknown":     "#888888",
}

STAGE_PROMPTS = {
    "Rapport":    "rapport building and mirroring",
    "Pain":       "deep pain discovery questions",
    "Objection":  "objection handling",
    "Close":      "closing language and next-step commitment",
    "Unknown":    "open-ended qualification",
}

# ── Audio settings ─────────────────────────────────────────────
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SECONDS = 4      # transcribe every 4 seconds
CHUNK_SIZE = SAMPLE_RATE * CHUNK_SECONDS

# ── State ──────────────────────────────────────────────────────
audio_queue = queue.Queue()
full_transcript = []
current_stage = "Unknown"
call_active = False


# ── Transcription (Whisper) ────────────────────────────────────
def transcribe_chunk(pcm_data: bytes) -> str:
    """Send raw PCM to Whisper, return text."""
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_KEY)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
            with wave.open(f, "wb") as wav:
                wav.setnchannels(CHANNELS)
                wav.setsampwidth(2)   # 16-bit
                wav.setframerate(SAMPLE_RATE)
                wav.writeframes(pcm_data)

        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
            )
        os.unlink(tmp_path)
        return result.text.strip()
    except Exception as e:
        return f"[transcription error: {e}]"


# ── Stage detection + suggestion (Claude) ─────────────────────
def get_suggestion(transcript_lines: list[str]) -> tuple[str, str, str]:
    """
    Returns (stage, suggestion, reasoning).
    transcript_lines: last N lines of transcript.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

        recent = "\n".join(transcript_lines[-20:]) if transcript_lines else "(no transcript yet)"

        prompt = f"""You are a real-time sales call coach for William, who sells AI automation services ($497/mo) to small businesses in Naples FL.

Transcript so far (most recent at bottom):
---
{recent}
---

Analyze the conversation and respond with JSON only:
{{
  "stage": "Rapport|Pain|Objection|Close|Unknown",
  "suggestion": "The single best thing William should say or ask next (1-2 sentences max, natural spoken language)",
  "reasoning": "Why this is the right move (10 words max)"
}}

Stage rules:
- Rapport: small talk, relationship building, not yet in pain discovery
- Pain: asking about missed calls, business challenges, what it costs them
- Objection: prospect pushes back (price, timing, trust, "we're fine")
- Close: prospect is interested, moving toward decision
- Unknown: can't tell yet

The suggestion must be something William can say OUT LOUD immediately. Keep it concise and conversational."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        return data.get("stage", "Unknown"), data.get("suggestion", ""), data.get("reasoning", "")
    except Exception as e:
        return "Unknown", f"[coach error: {e}]", ""


# ── Audio capture thread ───────────────────────────────────────
def audio_capture_thread():
    """Capture mic in CHUNK_SECONDS blocks, push raw PCM to queue."""
    try:
        import sounddevice as sd
        import numpy as np

        def callback(indata, frames, time_info, status):
            if call_active:
                pcm = (indata[:, 0] * 32767).astype("int16").tobytes()
                audio_queue.put(pcm)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=CHUNK_SIZE,
            callback=callback,
        ):
            while True:
                time.sleep(0.1)
                if not call_active:
                    time.sleep(0.5)
    except ImportError:
        # sounddevice not installed — simulation mode
        while True:
            time.sleep(4)
            if call_active:
                audio_queue.put(b"SIMULATION")


# ── Processing thread ──────────────────────────────────────────
def processing_thread(app):
    """Pull audio chunks, transcribe, get suggestion, update UI."""
    sim_lines = [
        "Hey is this Mike? Mike this is William from Marceau Solutions",
        "I sent you a quick email last week about missed calls, not sure if you caught it",
        "Got 2 minutes?",
        "So what happens when you miss a call, especially after hours?",
        "Right, so if you're missing even 3 or 4 calls a week and average job is 400 bucks",
        "That's over 6000 a month going to whoever answers first",
        "We text every missed caller back in 10 seconds automatically",
        "First 2 weeks are completely free, I set the whole thing up",
        "It's 497 a month after that, but one recovered job pays for it",
        "Want me to get that set up this week?",
    ]
    sim_idx = 0

    while True:
        try:
            pcm = audio_queue.get(timeout=1)
        except queue.Empty:
            continue

        if pcm == b"SIMULATION":
            if sim_idx < len(sim_lines):
                text = sim_lines[sim_idx]
                sim_idx += 1
            else:
                text = "Any questions or should I just walk you through how it works?"
        else:
            text = transcribe_chunk(pcm)

        if text and not text.startswith("["):
            full_transcript.append(text)
            app.add_transcript_line(text)

        stage, suggestion, reasoning = get_suggestion(full_transcript)
        app.update_suggestion(stage, suggestion, reasoning)


# ── Main overlay window ────────────────────────────────────────
class CallCoachOverlay:
    def __init__(self, root):
        self.root = root
        self._setup_window()
        self._build_ui()
        self._start_threads()

    def _setup_window(self):
        self.root.title("Call Coach")
        self.root.geometry("420x520+50+50")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.93)
        # Allow dragging
        self.root.bind("<Button-1>", self._click_start)
        self.root.bind("<B1-Motion>", self._drag_window)
        self._drag_x = 0
        self._drag_y = 0

    def _click_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_window(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG, pady=8)
        header.pack(fill="x", padx=12)

        tk.Label(header, text="CALL COACH", bg=BG, fg=GOLD,
                 font=("Helvetica Neue", 13, "bold")).pack(side="left")

        self.status_dot = tk.Label(header, text="●", bg=BG, fg=DIM, font=("Helvetica Neue", 16))
        self.status_dot.pack(side="right")

        self.start_btn = tk.Button(
            header, text="▶  START", bg=GOLD, fg="#1a1a1a",
            font=("Helvetica Neue", 10, "bold"), relief="flat",
            padx=10, pady=3,
            command=self._toggle_call
        )
        self.start_btn.pack(side="right", padx=8)

        # Divider
        tk.Frame(self.root, bg="#333333", height=1).pack(fill="x", padx=12)

        # Stage indicator
        stage_frame = tk.Frame(self.root, bg=BG, pady=6)
        stage_frame.pack(fill="x", padx=12)

        tk.Label(stage_frame, text="STAGE", bg=BG, fg=DIM,
                 font=("Helvetica Neue", 9)).pack(side="left")

        self.stage_label = tk.Label(stage_frame, text="Waiting...", bg=BG, fg=DIM,
                                    font=("Helvetica Neue", 11, "bold"))
        self.stage_label.pack(side="left", padx=8)

        # Suggestion box
        suggestion_outer = tk.Frame(self.root, bg="#252525", padx=10, pady=10)
        suggestion_outer.pack(fill="x", padx=12, pady=(2, 8))

        tk.Label(suggestion_outer, text="SAY THIS:", bg="#252525", fg=DIM,
                 font=("Helvetica Neue", 9, "bold")).pack(anchor="w")

        self.suggestion_text = tk.Text(
            suggestion_outer, bg="#252525", fg=WHITE,
            font=("Helvetica Neue", 12), wrap="word",
            height=4, relief="flat", cursor="arrow",
            state="disabled",
        )
        self.suggestion_text.pack(fill="x", pady=(4, 0))

        self.reasoning_label = tk.Label(
            suggestion_outer, text="", bg="#252525", fg=DIM,
            font=("Helvetica Neue", 9, "italic"), wraplength=370, anchor="w", justify="left"
        )
        self.reasoning_label.pack(anchor="w", pady=(4, 0))

        # Transcript scroll
        tk.Frame(self.root, bg="#333333", height=1).pack(fill="x", padx=12)

        tx_header = tk.Frame(self.root, bg=BG, pady=4)
        tx_header.pack(fill="x", padx=12)
        tk.Label(tx_header, text="TRANSCRIPT", bg=BG, fg=DIM,
                 font=("Helvetica Neue", 9)).pack(side="left")

        self.clear_btn = tk.Button(
            tx_header, text="Clear", bg=BG, fg=DIM,
            font=("Helvetica Neue", 9), relief="flat",
            command=self._clear_transcript
        )
        self.clear_btn.pack(side="right")

        tx_frame = tk.Frame(self.root, bg=BG)
        tx_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.transcript_box = tk.Text(
            tx_frame, bg="#111111", fg="#aaaaaa",
            font=("Helvetica Neue", 10), wrap="word",
            relief="flat", state="disabled",
        )
        scrollbar = tk.Scrollbar(tx_frame, command=self.transcript_box.yview, bg=BG)
        self.transcript_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.transcript_box.pack(side="left", fill="both", expand=True)

        # Footer
        footer = tk.Frame(self.root, bg=BG, pady=4)
        footer.pack(fill="x", padx=12)
        tk.Label(footer, text="calls.marceausolutions.com  •  drag to move",
                 bg=BG, fg="#555555", font=("Helvetica Neue", 8)).pack()

    def _toggle_call(self):
        global call_active
        call_active = not call_active
        if call_active:
            self.start_btn.configure(text="⏹  STOP", bg=RED)
            self.status_dot.configure(fg=GREEN)
            self.stage_label.configure(text="Listening...", fg=WHITE)
        else:
            self.start_btn.configure(text="▶  START", bg=GOLD)
            self.status_dot.configure(fg=DIM)

    def _clear_transcript(self):
        global full_transcript
        full_transcript = []
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

    def add_transcript_line(self, text: str):
        self.root.after(0, self._do_add_transcript, text)

    def _do_add_transcript(self, text: str):
        self.transcript_box.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.transcript_box.insert("end", f"[{timestamp}] {text}\n")
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def update_suggestion(self, stage: str, suggestion: str, reasoning: str):
        self.root.after(0, self._do_update_suggestion, stage, suggestion, reasoning)

    def _do_update_suggestion(self, stage: str, suggestion: str, reasoning: str):
        global current_stage
        current_stage = stage
        color = STAGE_COLORS.get(stage, DIM)

        self.stage_label.configure(text=stage.upper(), fg=color)

        self.suggestion_text.configure(state="normal")
        self.suggestion_text.delete("1.0", "end")
        self.suggestion_text.insert("1.0", suggestion)
        self.suggestion_text.configure(state="disabled", fg=color)

        self.reasoning_label.configure(text=reasoning)

    def _start_threads(self):
        t1 = threading.Thread(target=audio_capture_thread, daemon=True)
        t1.start()

        t2 = threading.Thread(target=processing_thread, args=(self,), daemon=True)
        t2.start()


def main():
    # Check for missing keys and warn (but still launch in simulation mode)
    missing = []
    if not ANTHROPIC_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not OPENAI_KEY:
        missing.append("OPENAI_API_KEY")

    root = tk.Tk()
    app = CallCoachOverlay(root)

    if missing:
        app.update_suggestion(
            "Unknown",
            f"Missing API keys: {', '.join(missing)} — running in simulation mode",
            "Add keys to .env to enable live coaching"
        )

    root.mainloop()


if __name__ == "__main__":
    main()
