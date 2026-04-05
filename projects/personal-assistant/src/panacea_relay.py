#!/usr/bin/env python3
"""
Panacea Relay — Unified EC2 agent. Telegram bot + Grok strategy + Claude Code execution.

Replaces: Clawdbot (Telegram bot), Ralph (webhook executor), manual Grok relay.

6-stage pipeline:
  1. Message buffer (assembles multi-message prompts)
  2. Structured pre-filters (accountability, status — no AI)
  3. Grok strategic consultation (always, every AI request)
  4. Task queue + interrupt management
  5. Claude Code execution (claude -p with --resume)
  6. Response delivery to Telegram

Usage:
    REPO_ROOT=/home/ec2-user/dev-sandbox python3 panacea_relay.py
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(os.environ.get("REPO_ROOT", "/home/ec2-user/dev-sandbox"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8596701493:AAHvayxq-kUmRsI-39BmY-owi7PvFpx82gQ")
WILLIAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "5692454753"))
CLAUDE_OAUTH_TOKEN = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "")
BUFFER_SECONDS = 5
CLAUDE_TIMEOUT = 300  # 5 min max per task
PANACEA_SYSTEM_PROMPT = (
    "You are Panacea, William's personal AI assistant on Telegram. "
    "You are NOT in a dev session — do NOT read git status, offer to commit files, or behave like Claude Code in VS Code. "
    "You are a conversational assistant that can also execute tasks (edit files, run commands, deploy) when asked. "
    "Be concise — Telegram messages should be short and direct, not long explanations. "
    "You have full access to the dev-sandbox repo, bash, git, and all tools. Use them when the task requires it. "
    "William is a solo entrepreneur running Marceau Solutions (AI services + fitness coaching) in Naples, FL. "
    "He works 7am-3pm weekdays as an electrical technician at Collier County. Side hustle evenings/weekends."
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
logger = logging.getLogger("panacea")

# Add the src dir to path for imports
import sys
sys.path.insert(0, str(REPO_ROOT / "projects" / "personal-assistant" / "src"))

# ---------------------------------------------------------------------------
# State (per-chat)
# ---------------------------------------------------------------------------

# Message buffer: chat_id -> {messages: [], timer: asyncio.Task}
_buffers: dict[int, dict] = {}

# Task queue: chat_id -> {process: subprocess.Popen, queue: [], session_id: str, add_context: []}
_tasks: dict[int, dict] = {}

# ---------------------------------------------------------------------------
# Stage 1: Message Buffer
# ---------------------------------------------------------------------------

async def _fire_buffer(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Assemble buffered messages into one prompt and process it."""
    buf = _buffers.pop(chat_id, None)
    if not buf or not buf["messages"]:
        return
    full_prompt = "\n".join(buf["messages"])
    logger.info(f"Buffer fired for {chat_id}: {len(buf['messages'])} message(s)")
    await _process_prompt(chat_id, full_prompt, context)


async def _buffer_message(chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE):
    """Add message to buffer. Fire immediately if ends with '.', else wait 5s."""
    if chat_id not in _buffers:
        _buffers[chat_id] = {"messages": [], "timer": None}

    _buffers[chat_id]["messages"].append(text)

    # Cancel existing timer
    if _buffers[chat_id]["timer"] is not None:
        _buffers[chat_id]["timer"].cancel()

    # Fire immediately if message ends with period
    if text.rstrip().endswith("."):
        await _fire_buffer(chat_id, context)
        return

    # Otherwise set 5-second timer
    async def _timer():
        await asyncio.sleep(BUFFER_SECONDS)
        await _fire_buffer(chat_id, context)

    _buffers[chat_id]["timer"] = asyncio.ensure_future(_timer())


# ---------------------------------------------------------------------------
# Stage 2: Structured Pre-Filters
# ---------------------------------------------------------------------------

def _try_prefilters(text: str) -> Optional[str]:
    """Run structured pre-filters. Returns response string or None."""
    try:
        from clawdbot_handlers import route_message
        return route_message(text)
    except ImportError:
        logger.warning("clawdbot_handlers not importable — pre-filters disabled")
        return None
    except Exception as e:
        logger.error(f"Pre-filter error: {e}")
        return None


# ---------------------------------------------------------------------------
# Stage 3: Grok Strategic Consultation
# ---------------------------------------------------------------------------

def _consult_grok(prompt: str) -> Optional[str]:
    """Always consult Grok. Returns direction or None (logged, not silent)."""
    try:
        from grok_strategic_layer import consult_grok
        return consult_grok(prompt)
    except ImportError:
        logger.error("grok_strategic_layer not importable — Grok consultation FAILED (logged)")
        return None
    except Exception as e:
        logger.error(f"Grok consultation error (logged): {e}")
        return None


# ---------------------------------------------------------------------------
# Stage 4: Task Queue + Interrupt
# ---------------------------------------------------------------------------

def _get_task_state(chat_id: int) -> dict:
    """Get or create task state for a chat."""
    if chat_id not in _tasks:
        _tasks[chat_id] = {
            "process": None,
            "queue": [],
            "session_id": str(uuid.uuid4()),
            "add_context": [],
        }
    return _tasks[chat_id]


def _is_running(chat_id: int) -> bool:
    """Check if a claude -p process is currently running for this chat."""
    state = _get_task_state(chat_id)
    proc = state["process"]
    return proc is not None and proc.poll() is None


def _kill_current(chat_id: int):
    """Kill the running claude -p process for this chat."""
    state = _get_task_state(chat_id)
    proc = state["process"]
    if proc and proc.poll() is None:
        logger.info(f"Killing claude -p process for chat {chat_id}")
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    state["process"] = None


# ---------------------------------------------------------------------------
# Stage 5: Claude Code Execution
# ---------------------------------------------------------------------------

def _run_claude(prompt: str, session_id: str, resume: bool = False) -> str:
    """Run claude -p as subprocess. Returns response text."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--system-prompt", PANACEA_SYSTEM_PROMPT,
    ]
    if resume:
        cmd.extend(["--resume", session_id])
    else:
        cmd.extend(["--session-id", session_id])

    env = os.environ.copy()
    env["CLAUDE_CODE_OAUTH_TOKEN"] = CLAUDE_OAUTH_TOKEN

    logger.info(f"Running: claude -p (session={session_id[:8]}..., resume={resume})")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            cwd=str(REPO_ROOT),
            env=env,
        )
        if proc.returncode != 0 and proc.stderr:
            logger.error(f"claude -p stderr: {proc.stderr[:500]}")
            return f"Error from Claude Code: {proc.stderr[:500]}"
        return proc.stdout.strip() or "(No response from Claude Code)"
    except subprocess.TimeoutExpired:
        return "Task timed out after 5 minutes. Send the request again or break it into smaller pieces."
    except Exception as e:
        logger.error(f"claude -p failed: {e}")
        return f"Claude Code execution failed: {e}"


# ---------------------------------------------------------------------------
# Main Processing Pipeline
# ---------------------------------------------------------------------------

async def _process_prompt(chat_id: int, prompt: str, context: ContextTypes.DEFAULT_TYPE):
    """Process an assembled prompt through stages 2-6."""
    lower = prompt.lower().strip()

    # Stage 2: Pre-filters
    prefilter_response = _try_prefilters(prompt)
    if prefilter_response:
        await context.bot.send_message(chat_id=chat_id, text=prefilter_response)
        return

    # Stage 4 control keywords (bypass Grok — these are task management, not AI)
    if lower in ("stop", "cancel"):
        if _is_running(chat_id):
            _kill_current(chat_id)
            state = _get_task_state(chat_id)
            if state["queue"]:
                await context.bot.send_message(chat_id=chat_id, text="Cancelled. Starting next queued task...")
                next_prompt = state["queue"].pop(0)
                await _execute_task(chat_id, next_prompt, context)
            else:
                await context.bot.send_message(chat_id=chat_id, text="Cancelled. What do you need?")
        else:
            await context.bot.send_message(chat_id=chat_id, text="Nothing running to cancel.")
        return

    if lower.startswith("add:"):
        additional = prompt[4:].strip()
        if _is_running(chat_id):
            state = _get_task_state(chat_id)
            state["add_context"].append(additional)
            await context.bot.send_message(
                chat_id=chat_id,
                text="Context noted. Will include when current task finishes."
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="No task running. Send your full request instead."
            )
        return

    # Stage 4: Queue management
    if _is_running(chat_id):
        state = _get_task_state(chat_id)
        state["queue"].append(prompt)
        pos = len(state["queue"])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Working on your previous request. Queued (#{pos}). Send 'stop' to cancel current task."
        )
        return

    # Stage 3 + 5 + 6: Grok -> Claude -> Respond
    await _execute_task(chat_id, prompt, context)


async def _execute_task(chat_id: int, prompt: str, context: ContextTypes.DEFAULT_TYPE):
    """Execute a task: consult Grok, run Claude, deliver response."""
    state = _get_task_state(chat_id)

    # Stage 3: Grok consultation (always)
    await context.bot.send_message(chat_id=chat_id, text="Thinking...")
    grok_direction = _consult_grok(prompt)

    # Build Claude prompt with Grok's direction
    if grok_direction:
        claude_prompt = (
            f"STRATEGIC DIRECTION (from Grok): {grok_direction}\n\n"
            f"USER REQUEST: {prompt}"
        )
    else:
        claude_prompt = (
            f"NOTE: Grok strategic consultation failed (logged). Proceed with best judgment.\n\n"
            f"USER REQUEST: {prompt}"
        )

    # Stage 5: Claude execution (in thread to not block)
    is_resume = state.get("has_run", False)
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        _run_claude, claude_prompt, state["session_id"], is_resume
    )
    state["has_run"] = True
    state["process"] = None  # Completed

    # Stage 6: Response delivery
    # Telegram has a 4096 char limit per message
    if len(response) <= 4096:
        await context.bot.send_message(chat_id=chat_id, text=response)
    else:
        for i in range(0, len(response), 4096):
            await context.bot.send_message(chat_id=chat_id, text=response[i:i+4096])

    # Handle add: context that came in during execution
    if state["add_context"]:
        additional = "\n".join(state["add_context"])
        state["add_context"] = []
        followup_prompt = (
            f"Previous result: {response[:1000]}\n\n"
            f"Additional context from William: {additional}"
        )
        await _execute_task(chat_id, followup_prompt, context)
        return

    # Advance queue
    if state["queue"]:
        next_prompt = state["queue"].pop(0)
        await context.bot.send_message(chat_id=chat_id, text="Starting next queued task...")
        await _execute_task(chat_id, next_prompt, context)


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages."""
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # Only respond to William (security)
    if chat_id != WILLIAM_CHAT_ID:
        logger.warning(f"Ignoring message from unknown chat_id: {chat_id}")
        return

    if not text:
        return

    # Control keywords bypass the buffer
    lower = text.lower().strip()
    if lower in ("stop", "cancel") or lower.startswith("add:"):
        await _process_prompt(chat_id, text, context)
        return

    # Stage 1: Buffer
    await _buffer_message(chat_id, text, context)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "Panacea online. Send me anything — Grok advises, Claude executes."
    )


# ---------------------------------------------------------------------------
# Webhook Input (replaces Ralph)
# ---------------------------------------------------------------------------

# TODO: Add Flask/aiohttp webhook endpoint for PRD/task execution
# POST /task {prompt: "...", context: "..."} -> same pipeline as Telegram


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not CLAUDE_OAUTH_TOKEN:
        logger.error("CLAUDE_CODE_OAUTH_TOKEN not set. Cannot run.")
        sys.exit(1)

    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Cannot run.")
        sys.exit(1)

    logger.info(f"Panacea starting — REPO_ROOT={REPO_ROOT}")
    logger.info(f"William chat_id={WILLIAM_CHAT_ID}")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Panacea relay running. Polling for Telegram messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
