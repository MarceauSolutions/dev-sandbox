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
import time
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
CLAUDE_TIMEOUT = 600  # 10 min max per task

# Attachment inbox (images, PDFs, text/code files sent via Telegram)
INBOX_DIR = Path("/tmp/panacea-inbox")
INBOX_DIR.mkdir(parents=True, exist_ok=True)
INBOX_FILE_MAX_BYTES = 25 * 1024 * 1024      # 25 MB per file
INBOX_TOTAL_MAX_BYTES = 500 * 1024 * 1024    # 500 MB total across all files
INBOX_TTL_SECONDS = 3600                      # sweep anything older than 1 hour

# File extensions Claude's Read tool can handle meaningfully
READABLE_SUFFIXES = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp",
    ".pdf", ".ipynb",
    ".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".env",
    ".html", ".css", ".scss", ".sh", ".bash", ".zsh",
    ".sql", ".csv", ".log", ".xml",
}

PANACEA_SYSTEM_PROMPT = (
    "You are Panacea, William's personal AI assistant on Telegram. "
    "You are NOT in a dev session — do NOT read git status, do NOT offer to commit files, do NOT list capabilities unprompted. "
    "KEEP RESPONSES SHORT. This is Telegram on a phone — 2-4 sentences for conversational replies. "
    "Only give long responses when William asks for detailed information or a complex task produces output. "
    "When executing tasks (file edits, commands, deploys), do the work silently and report the result briefly. "
    "You have full access to the dev-sandbox repo, bash, git, and all tools. Use them when the task requires it. "
    "When William's prompt begins with one or more '[attached file: <path>]' lines, use the Read tool on each path "
    "before responding — those are files (images, PDFs, documents) he sent via Telegram. If there is no accompanying "
    "text, briefly describe or analyze what you see. "
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
# Attachment inbox — storage-bounded scratch dir for Telegram media
# ---------------------------------------------------------------------------

def _sweep_inbox() -> None:
    """Delete files older than TTL, then evict oldest until under total cap."""
    try:
        entries = list(INBOX_DIR.iterdir())
    except OSError:
        return

    now = time.time()
    for p in entries:
        try:
            if now - p.stat().st_mtime > INBOX_TTL_SECONDS:
                p.unlink()
        except OSError:
            pass

    try:
        remaining = sorted(INBOX_DIR.iterdir(), key=lambda p: p.stat().st_mtime)
    except OSError:
        return
    total = 0
    sizes: list[tuple[Path, int]] = []
    for p in remaining:
        try:
            sz = p.stat().st_size
        except OSError:
            continue
        sizes.append((p, sz))
        total += sz
    i = 0
    while total > INBOX_TOTAL_MAX_BYTES and i < len(sizes):
        p, sz = sizes[i]
        try:
            p.unlink()
            total -= sz
        except OSError:
            pass
        i += 1


def _delete_attachments(files: list[Path]) -> None:
    """Best-effort cleanup of a task's downloaded files."""
    for f in files or []:
        try:
            f.unlink()
        except OSError:
            pass


async def _download_attachment(bot, file_id: str, suffix: str) -> Optional[Path]:
    """Download a Telegram file into the inbox. Returns path or None on failure."""
    try:
        tg_file = await bot.get_file(file_id)
    except Exception as e:
        logger.error(f"get_file failed: {e}")
        return None
    if tg_file.file_size and tg_file.file_size > INBOX_FILE_MAX_BYTES:
        logger.warning(f"Attachment too large: {tg_file.file_size} bytes (cap {INBOX_FILE_MAX_BYTES})")
        return None
    dest = INBOX_DIR / f"{uuid.uuid4().hex}{suffix}"
    try:
        await tg_file.download_to_drive(custom_path=str(dest))
    except Exception as e:
        logger.error(f"download_to_drive failed: {e}")
        return None
    return dest


# ---------------------------------------------------------------------------
# Stage 1: Message Buffer
# ---------------------------------------------------------------------------

async def _fire_buffer(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Assemble buffered messages (and any attached files) into one prompt and process it."""
    buf = _buffers.pop(chat_id, None)
    if not buf or (not buf["messages"] and not buf["files"]):
        return
    text_part = "\n".join(buf["messages"])
    files: list[Path] = buf["files"]
    if files:
        attached_lines = "\n".join(f"[attached file: {p}]" for p in files)
        full_prompt = f"{attached_lines}\n\n{text_part}".strip()
    else:
        full_prompt = text_part
    logger.info(f"Buffer fired for {chat_id}: {len(buf['messages'])} msg(s), {len(files)} file(s)")
    await _process_prompt(chat_id, full_prompt, context, files)


async def _buffer_message(
    chat_id: int,
    text: str,
    files: list[Path],
    context: ContextTypes.DEFAULT_TYPE,
):
    """Add message and/or files to buffer. Fire immediately if text ends with '.', else wait 5s."""
    if chat_id not in _buffers:
        _buffers[chat_id] = {"messages": [], "files": [], "timer": None}

    if text:
        _buffers[chat_id]["messages"].append(text)
    if files:
        _buffers[chat_id]["files"].extend(files)

    # Cancel existing timer
    if _buffers[chat_id]["timer"] is not None:
        _buffers[chat_id]["timer"].cancel()

    # Fire immediately if text ends with period (text-only signal)
    if text and text.rstrip().endswith("."):
        await _fire_buffer(chat_id, context)
        return

    # Otherwise set 5-second timer — gives albums/multi-message sends time to arrive
    async def _timer():
        await asyncio.sleep(BUFFER_SECONDS)
        await _fire_buffer(chat_id, context)

    _buffers[chat_id]["timer"] = asyncio.ensure_future(_timer())


# ---------------------------------------------------------------------------
# Stage 2: Structured Pre-Filters (DISABLED)
# ---------------------------------------------------------------------------
# Pre-filters removed. The old clawdbot_handlers.py route_message() was built
# for Clawdbot which couldn't execute code. Panacea uses claude -p which can
# do everything natively. Accountability check-ins (morning/EOD) are not
# running anyway — rebuild them properly once core systems are stable.

def _try_prefilters(text: str) -> Optional[str]:
    """Pre-filters disabled. Always returns None (fall through to Grok + Claude)."""
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

def _start_claude(chat_id: int, prompt: str, session_id: str, resume: bool = False, grok_append: str = "") -> subprocess.Popen:
    """Start claude -p as a non-blocking subprocess. Returns Popen handle."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--system-prompt", PANACEA_SYSTEM_PROMPT,
        "--dangerously-skip-permissions",
    ]
    if grok_append:
        cmd.extend(["--append-system-prompt", grok_append])
    if resume:
        cmd.extend(["--resume", session_id])
    else:
        cmd.extend(["--session-id", session_id])

    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)  # Force Max subscription — not API billing
    env["CLAUDE_CODE_OAUTH_TOKEN"] = CLAUDE_OAUTH_TOKEN

    logger.info(f"Running: claude -p (session={session_id[:8]}..., resume={resume})")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )
    state = _get_task_state(chat_id)
    state["process"] = proc
    return proc


def _wait_for_claude(proc: subprocess.Popen) -> str:
    """Wait for claude -p to finish and return output. Blocking — run in executor."""
    try:
        stdout, stderr = proc.communicate(timeout=CLAUDE_TIMEOUT)
        if proc.returncode != 0 and stderr:
            logger.error(f"claude -p stderr: {stderr[:500]}")
            return f"Error from Claude Code: {stderr[:500]}"
        return stdout.strip() or "(No response from Claude Code)"
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return "Task timed out after 10 minutes. Send the request again or break it into smaller pieces."
    except Exception as e:
        logger.error(f"claude -p failed: {e}")
        return f"Claude Code execution failed: {e}"


# ---------------------------------------------------------------------------
# Main Processing Pipeline
# ---------------------------------------------------------------------------

async def _process_prompt(
    chat_id: int,
    prompt: str,
    context: ContextTypes.DEFAULT_TYPE,
    files: Optional[list[Path]] = None,
):
    """Process an assembled prompt through stages 2-6."""
    files = files or []
    lower = prompt.lower().strip()

    # Stage 2: Pre-filters
    prefilter_response = _try_prefilters(prompt)
    if prefilter_response:
        _delete_attachments(files)
        await context.bot.send_message(chat_id=chat_id, text=prefilter_response)
        return

    # Stage 4 control keywords (bypass Grok — these are task management, not AI)
    if lower in ("stop", "cancel"):
        _delete_attachments(files)
        logger.info(f"Stop/cancel received. is_running={_is_running(chat_id)}")
        if _is_running(chat_id):
            logger.info("Killing current claude -p process")
            _kill_current(chat_id)
            state = _get_task_state(chat_id)
            if state["queue"]:
                await context.bot.send_message(chat_id=chat_id, text="Cancelled. Starting next queued task...")
                entry = state["queue"].pop(0)
                await _execute_task(chat_id, entry["prompt"], context, entry.get("files") or [])
            else:
                await context.bot.send_message(chat_id=chat_id, text="Cancelled. What do you need?")
        else:
            await context.bot.send_message(chat_id=chat_id, text="Nothing running to cancel.")
        return

    if lower.startswith("add:"):
        _delete_attachments(files)
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
        state["queue"].append({"prompt": prompt, "files": files})
        pos = len(state["queue"])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Working on your previous request. Queued (#{pos}). Send 'stop' to cancel current task."
        )
        return

    # Stage 3 + 5 + 6: Grok -> Claude -> Respond
    await _execute_task(chat_id, prompt, context, files)


async def _execute_task(
    chat_id: int,
    prompt: str,
    context: ContextTypes.DEFAULT_TYPE,
    files: Optional[list[Path]] = None,
):
    """Execute a task: consult Grok, run Claude, deliver response. Cleans up attached files when done."""
    files = files or []
    state = _get_task_state(chat_id)
    response = ""

    try:
        # Stage 3: Grok consultation (always)
        await context.bot.send_message(chat_id=chat_id, text="Thinking...")
        grok_direction = _consult_grok(prompt)

        # Build Grok append prompt
        if grok_direction:
            grok_append = f"Strategic directive from Grok: {grok_direction}"
        else:
            grok_append = "Grok strategic consultation failed (logged). Proceed with best judgment."

        # Stage 5: Claude execution (non-blocking — Popen + wait in executor)
        is_resume = state.get("has_run", False)
        proc = _start_claude(chat_id, prompt, state["session_id"], is_resume, grok_append)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _wait_for_claude, proc)
        state["has_run"] = True
        state["process"] = None  # Completed

        # Stage 6: Response delivery
        # Telegram has a 4096 char limit per message
        if len(response) <= 4096:
            await context.bot.send_message(chat_id=chat_id, text=response)
        else:
            for i in range(0, len(response), 4096):
                await context.bot.send_message(chat_id=chat_id, text=response[i:i+4096])
    finally:
        # Primary cleanup — always runs even on error. Sweep catches anything missed.
        _delete_attachments(files)

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
        entry = state["queue"].pop(0)
        await context.bot.send_message(chat_id=chat_id, text="Starting next queued task...")
        await _execute_task(chat_id, entry["prompt"], context, entry.get("files") or [])


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages (text, photos, documents)."""
    if not update.message:
        return
    msg = update.message
    chat_id = update.effective_chat.id

    # Only respond to William (security)
    if chat_id != WILLIAM_CHAT_ID:
        logger.warning(f"Ignoring message from unknown chat_id: {chat_id}")
        return

    # Sweep stale orphans on every incoming message (cheap, runs <1ms usually)
    _sweep_inbox()

    # Text or caption
    text = (msg.text or msg.caption or "").strip()

    # Attempt to download any attached media
    attached: list[Path] = []

    if msg.photo:
        biggest = msg.photo[-1]  # PhotoSize list is sorted smallest→largest
        path = await _download_attachment(context.bot, biggest.file_id, ".jpg")
        if path:
            attached.append(path)
        else:
            await msg.reply_text("Image download failed (file may exceed 25 MB cap).")
            return

    if msg.document:
        doc = msg.document
        mime = (doc.mime_type or "").lower()
        name = doc.file_name or ""
        suffix = Path(name).suffix.lower() or ".bin"
        readable = (
            mime.startswith("image/")
            or mime == "application/pdf"
            or mime.startswith("text/")
            or suffix in READABLE_SUFFIXES
        )
        if not readable:
            await msg.reply_text(
                f"Unsupported file type: {mime or suffix}. "
                "I can read images, PDFs, and text/code files."
            )
            return
        path = await _download_attachment(context.bot, doc.file_id, suffix)
        if path:
            attached.append(path)
        else:
            await msg.reply_text("Document download failed (file may exceed 25 MB cap).")
            return

    if not text and not attached:
        return

    # Control keywords bypass the buffer — text-only path
    lower = text.lower().strip()
    if text and not attached and (lower in ("stop", "cancel") or lower.startswith("add:")):
        logger.info(f"Control keyword received: '{lower}' — bypassing buffer")
        await _process_prompt(chat_id, text, context)
        return

    # Stage 1: Buffer
    await _buffer_message(chat_id, text, attached, context)


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
    app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
            handle_message,
        )
    )

    logger.info("Panacea relay running. Polling for Telegram messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
