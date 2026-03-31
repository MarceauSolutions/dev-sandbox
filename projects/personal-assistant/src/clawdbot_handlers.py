#!/usr/bin/env python3
"""
Clawdbot PA Handlers — Drop-in command handlers for the Telegram bot on EC2.

Ralph deploys this to EC2 and wires it into Clawdbot's existing bot.
Each handler calls the Personal Assistant Flask API on William's Mac
via SSH tunnel (localhost:5011 on EC2 → Mac:5011).

Prerequisites:
  1. SSH tunnel running: ssh -R 5011:localhost:5011 ec2-user@34.193.98.97
  2. PA Flask app running on Mac: cd projects/personal-assistant && python -m src.app
  3. This file copied to EC2 Clawdbot directory

Usage (in Clawdbot's main bot.py):
    from clawdbot_handlers import handle_schedule, handle_approve, handle_digest, handle_health

    # In message handler:
    if "schedule" in text.lower():
        response = handle_schedule()
        bot.send_message(chat_id, response, parse_mode="Markdown")
"""

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger("clawdbot_pa")

# Module-level REPO_ROOT — used by all handler functions.
# On Mac: auto-detected from file location (4 parents up from src/)
# On EC2: set via REPO_ROOT environment variable
if os.environ.get("REPO_ROOT"):
    _REPO_ROOT = Path(os.environ["REPO_ROOT"])
else:
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# PA API base URL (via SSH tunnel: EC2 localhost:5011 → Mac:5011)
PA_API = "http://localhost:5011"
TIMEOUT = 15


def _call_pa(endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
    """Call the Personal Assistant API."""
    try:
        url = f"{PA_API}{endpoint}"
        if data:
            req = urllib.request.Request(
                url, data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"}, method=method,
            )
        else:
            req = urllib.request.Request(url, method=method)
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        return json.loads(resp.read())
    except Exception as e:
        logger.error(f"PA API call failed ({endpoint}): {e}")
        return None


def handle_schedule() -> str:
    """Handle 'What's my schedule?' / 'schedule' / 'plan'.

    Tries Flask API first, falls back to local execution.
    """
    result = _call_pa("/scheduler/today")
    if result and result.get("success"):
        formatted = result.get("formatted", "")
        if formatted:
            return formatted
        schedule = result.get("schedule", {})
        blocks = schedule.get("proposed_blocks", [])
        if not blocks:
            return "No scheduled blocks for today. Pipeline is in outreach mode."
        lines = ["TODAY'S PLAN"]
        for b in blocks:
            lines.append(f"  {b.get('calendar_summary', '?')}")
        return "\n".join(lines)

    # Local fallback: run scheduler directly
    try:
        import importlib.util
        from pathlib import Path
        repo_root = _REPO_ROOT
        spec = importlib.util.spec_from_file_location(
            "daily_scheduler", repo_root / "projects" / "personal-assistant" / "src" / "daily_scheduler.py"
        )
        ds = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ds)
        schedule = ds.generate_proposed_schedule()
        return ds.format_for_digest(schedule) or "No blocks to schedule today."
    except Exception as e:
        return f"Schedule generation failed: {e}"


def handle_approve() -> str:
    """Handle 'yes schedule' / 'approve schedule'."""
    result = _call_pa("/scheduler/approve", method="POST")
    if not result or not result.get("success"):
        return "⚠️ Could not approve schedule. Is the Mac awake?"

    created = result.get("created", [])
    errors = result.get("errors", [])

    if created:
        lines = [f"✅ {len(created)} block(s) added to Google Calendar:"]
        for c in created:
            lines.append(f"  • {c}")
        return "\n".join(lines)
    elif errors:
        return f"⚠️ Calendar errors: {'; '.join(errors)}"
    else:
        return "No pending schedule to approve."


def handle_digest() -> str:
    """Handle 'morning briefing' / 'digest' / 'what did I miss?'.

    Tries Flask API first, falls back to local execution.
    """
    result = _call_pa("/scheduler/digest")
    if result and result.get("success"):
        return result.get("digest", "No digest available.")

    # Local fallback: generate digest directly
    try:
        import importlib.util
        from pathlib import Path
        repo_root = _REPO_ROOT
        spec = importlib.util.spec_from_file_location(
            "unified_morning_digest",
            repo_root / "projects" / "personal-assistant" / "src" / "unified_morning_digest.py"
        )
        umd = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(umd)
        return umd.generate_digest(hours_back=12, preview=True) or "No digest data."
    except Exception as e:
        return f"Digest generation failed: {e}"


def handle_health() -> str:
    """Handle 'system status' / 'health' / 'how's the system?'.

    Tries Flask API first, falls back to local execution.
    """
    result = _call_pa("/scheduler/health-check")
    if result:
        healthy = result.get("healthy", False)
        if healthy:
            return "SYSTEM HEALTH: All checks pass"
        checks = result.get("checks", {})
        lines = ["SYSTEM HEALTH: Issues detected"]
        for name, data in checks.items():
            ok = data.get("ok", False) if isinstance(data, dict) else data == 0
            lines.append(f"  {'OK' if ok else 'FAIL'}: {name}")
        return "\n".join(lines)

    # Local fallback: run health check directly
    try:
        import importlib.util
        from pathlib import Path
        repo_root = _REPO_ROOT
        spec = importlib.util.spec_from_file_location(
            "system_health_check",
            repo_root / "projects" / "personal-assistant" / "src" / "system_health_check.py"
        )
        shc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(shc)
        result = shc.run_all_checks()
        return shc.format_for_digest(result) or "Health check ran but no output."
    except Exception:
        # On EC2, system_health_check.py may not exist — provide basic status
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "pipeline_db", _REPO_ROOT / "execution" / "pipeline_db.py"
            )
            pdb = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pdb)
            conn = pdb.get_db()
            total = conn.execute("SELECT COUNT(*) FROM deals").fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM deals WHERE stage NOT IN ('Closed Lost','Archived')").fetchone()[0]
            conn.close()
            return f"SYSTEM: Running on EC2\n  Pipeline: {total} deals ({active} active)\n  PA service: healthy\n  Full health check: available on Mac only"
        except Exception as e2:
            return f"System status unavailable: {e2}"


def _load_goal_manager():
    """Load goal_manager.py via importlib (works without Flask or package context)."""
    import importlib.util
    repo_root = _REPO_ROOT
    spec = importlib.util.spec_from_file_location(
        "goal_manager", repo_root / "projects" / "personal-assistant" / "src" / "goal_manager.py"
    )
    gm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gm)
    return gm


def _load_goal_progress():
    """Load goal_progress.py via importlib (works without Flask or package context)."""
    import importlib.util
    repo_root = _REPO_ROOT
    spec = importlib.util.spec_from_file_location(
        "goal_progress", repo_root / "projects" / "personal-assistant" / "src" / "goal_progress.py"
    )
    gp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gp)
    return gp


def handle_goals(text: str) -> str:
    """Handle goal management commands from Telegram.

    ALL commands use local imports so they work without Flask running.
    Flask API is not required -- this runs directly against pipeline.db.

    Supports: "goal show", "goal progress", "goal alerts",
    "goal short: [text]", "goal medium: [text]", "goal long: [text]"
    """
    lower = text.lower().strip()

    try:
        if lower in ("goal progress", "goals progress", "goal status"):
            gp = _load_goal_progress()
            return gp.format_for_digest() or "No goal progress data available."

        if lower in ("goal alerts", "goals alerts"):
            gp = _load_goal_progress()
            alerts = gp.check_alerts()
            return "\n".join(alerts) if alerts else "All goals on track."

        if lower.startswith("goal ") and ":" in lower:
            gm = _load_goal_manager()
            return gm.quick_set(text)

        # Default: "goal show" / "goal" / "goals"
        gm = _load_goal_manager()
        return gm.quick_set("goal show")

    except Exception as e:
        return f"Goal command failed: {e}"


def handle_tasks(text: str) -> str:
    """Handle task queue commands from Telegram.

    Supports: "tasks", "tasks pending", "tasks add [text]", "tasks status"
    """
    lower = text.lower().strip()

    import importlib.util, sys, json as _json
    from pathlib import Path
    repo_root = _REPO_ROOT

    try:
        spec = importlib.util.spec_from_file_location(
            "orchestrator", repo_root / "execution" / "grok_claude_orchestrator.py"
        )
        orch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orch)
    except Exception as e:
        return f"Orchestrator unavailable: {e}"

    if lower in ("tasks", "tasks pending", "task list"):
        return orch.format_pending_for_telegram()

    if lower in ("tasks status", "task status"):
        status = orch.get_status()
        by_agent = status.get("by_agent", {})
        lines = ["Agent workload:"]
        for agent, counts in by_agent.items():
            parts = [f"{s}:{c}" for s, c in counts.items()]
            lines.append(f"  {agent}: {', '.join(parts)}")
        compliance = status.get("research_compliance", {})
        lines.append(f"  Research compliance: {compliance.get('compliance_pct', 0)}%")
        return "\n".join(lines)

    if lower.startswith("task add ") or lower.startswith("tasks add "):
        task_text = text.split(" ", 2)[2] if len(text.split(" ", 2)) > 2 else ""
        if not task_text:
            return "Usage: task add [description]"
        task_id = orch.add_task(task_text, agent="claude", priority="medium", source="telegram")
        return f"Task #{task_id} added to Claude's queue"

    return (
        "Task commands:\n"
        "  tasks -- show pending\n"
        "  tasks status -- agent workload\n"
        "  task add [text] -- add task"
    )


def handle_outcome(text: str) -> str:
    """Record an outcome from a visit, call, or interaction via Telegram.

    Reduces William's friction to record what happened after outreach.
    Without outcome recording, the learning system can't activate (needs 5+).

    Format:
        "result [company]: [outcome]"
        "result [company]: [outcome] - [notes]"
        "outcome [company]: [outcome]"

    Outcomes: conversation, meeting_booked, proposal_sent, callback,
              interested, not_interested, no_show, client_won

    Examples:
        "result Dolphin Cooling: meeting_booked"
        "result Antimidators: callback - Call back Thursday 2pm"
        "result PlumbingPro: not_interested - Already has vendor"
    """
    import importlib.util
    repo_root = _REPO_ROOT

    # Parse: "result Company Name: outcome - optional notes"
    # Strip prefix
    cleaned = text.strip()
    for prefix in ["result ", "outcome "]:
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    if ":" not in cleaned:
        return (
            "Format: result [company]: [outcome]\n"
            "Outcomes: conversation, meeting_booked, proposal_sent, "
            "callback, interested, not_interested, no_show, client_won\n"
            "Example: result Dolphin Cooling: meeting_booked - Great call"
        )

    company_part, outcome_part = cleaned.split(":", 1)
    company = company_part.strip()
    outcome_and_notes = outcome_part.strip()

    # Split outcome from notes (separated by " - ")
    if " - " in outcome_and_notes:
        outcome, notes = outcome_and_notes.split(" - ", 1)
    else:
        outcome = outcome_and_notes
        notes = ""

    outcome = outcome.strip().lower().replace(" ", "_")
    notes = notes.strip()

    valid_outcomes = [
        "conversation", "meeting_booked", "proposal_sent", "callback",
        "interested", "not_interested", "no_show", "client_won",
    ]
    if outcome not in valid_outcomes:
        return (
            f"Unknown outcome: '{outcome}'\n"
            f"Valid: {', '.join(valid_outcomes)}"
        )

    # Find the deal and record outcome
    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        # Fuzzy match company name
        deal = conn.execute(
            "SELECT id, company, stage FROM deals WHERE company LIKE ? "
            "ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()

        if not deal:
            conn.close()
            return f"No deal found matching '{company}'"

        deal = dict(deal)
        deal_id = deal["id"]

        # Log as scheduled outcome
        pdb.log_scheduled_task(conn, deal_id, "manual_outreach", deal["company"])
        last_id = conn.execute("SELECT MAX(id) FROM scheduled_outcomes").fetchone()[0]
        pdb.record_outcome(conn, last_id, completed=True, outcome=outcome,
                           resulted_in=outcome, notes=notes)

        # Update deal stage if outcome warrants it
        stage_map = {
            "meeting_booked": "Scheduling",
            "proposal_sent": "Proposal Sent",
            "client_won": "Closed Won",
            "not_interested": "Closed Lost",
        }
        new_stage = stage_map.get(outcome)
        if new_stage and deal["stage"] != new_stage:
            pdb.update_deal(conn, deal_id, stage=new_stage)

        conn.close()

        # Count total outcomes for learning system status
        conn2 = pdb.get_db()
        total = conn2.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes WHERE completed=1"
        ).fetchone()[0]
        conn2.close()

        response = f"Recorded: {deal['company']} -> {outcome}"
        if notes:
            response += f"\n  Notes: {notes}"
        if new_stage:
            response += f"\n  Stage -> {new_stage}"
        response += f"\n  Learning system: {total}/5 outcomes"
        if total >= 5:
            response += " (READY!)"

        # Self-improving: update learned preferences after every outcome
        try:
            ol_spec = importlib.util.spec_from_file_location(
                "outcome_learner", repo_root / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
            )
            ol = importlib.util.module_from_spec(ol_spec)
            ol_spec.loader.exec_module(ol)
            prefs = ol.save_preferences()
            if prefs and prefs.get("insights"):
                response += f"\n  Learned: {prefs['insights'][0][:60]}"
        except Exception:
            pass
        
        # Also update followup prioritizer industry rates
        try:
            fp_spec = importlib.util.spec_from_file_location(
                "followup_prioritizer", repo_root / "execution" / "followup_prioritizer.py"
            )
            fp = importlib.util.module_from_spec(fp_spec)
            fp_spec.loader.exec_module(fp)
            prioritizer = fp.FollowupPrioritizer()
            prioritizer.learn_from_outcomes()
        except Exception:
            pass

        return response

    except Exception as e:
        return f"Outcome recording failed: {e}"


def handle_leads() -> str:
    """Show actionable leads ranked by closeness to cash.

    This is the call sheet: who to call today, in priority order.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        lines = ["CALL SHEET — priority order:\n"]

        priority_stages = [
            ("Trial Active", "TRIAL — close the deal"),
            ("Proposal Sent", "PROPOSAL — follow up to close"),
            ("Qualified", "QUALIFIED — call to book meeting"),
        ]

        total = 0
        for stage, label in priority_stages:
            leads = conn.execute(
                "SELECT company, contact_name, contact_phone, industry "
                "FROM deals WHERE stage = ? ORDER BY updated_at DESC LIMIT 5",
                (stage,)
            ).fetchall()
            if leads:
                lines.append(f"{label} ({len(leads)}):")
                for r in leads:
                    d = dict(r)
                    name = d.get("contact_name") or "?"
                    phone = d.get("contact_phone") or "no phone"
                    lines.append(f"  {d['company']} — {name} {phone}")
                    total += 1
                lines.append("")

        conn.close()

        if total == 0:
            return "No actionable leads right now. Pipeline is in outreach mode."

        lines.append(f"Total: {total} leads to call")
        lines.append("Record results: result [company]: [outcome]")
        return "\n".join(lines)

    except Exception as e:
        return f"Lead list failed: {e}"


def handle_call_scripts() -> str:
    """Generate compact call scripts for all qualified leads.

    Designed for phone screen — short, actionable, personalized.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        leads = conn.execute(
            "SELECT company, contact_name, contact_phone, industry, stage "
            "FROM deals WHERE stage IN ('Trial Active','Proposal Sent','Qualified') "
            "AND contact_phone IS NOT NULL AND contact_phone != '' "
            "ORDER BY CASE stage "
            "  WHEN 'Trial Active' THEN 1 WHEN 'Proposal Sent' THEN 2 ELSE 3 END"
        ).fetchall()
        conn.close()

        if not leads:
            return "No callable leads."

        pain_map = {
            "hvac": "missing after-hours emergency calls",
            "med spa": "no-shows and missed booking follow-ups",
            "plumb": "emergency calls going to voicemail",
            "chiro": "missed new patient follow-ups",
            "auto": "service reminders and missed calls",
            "roof": "missing storm-season calls on jobsites",
            "dental": "appointment no-shows",
            "pest": "missed service call follow-ups",
        }

        lines = [f"CALL SCRIPTS ({len(leads)} leads)\n"]

        for r in leads:
            d = dict(r)
            name = d.get("contact_name") or "?"
            first = name.split()[0] if name != "?" else ""
            industry = (d.get("industry") or "business").lower()
            pain = "missed calls and manual follow-ups"
            for key, val in pain_map.items():
                if key in industry:
                    pain = val
                    break

            if d["stage"] == "Trial Active":
                opener = f"How's the trial going? Getting value?"
                close = "Ready to lock in?"
            elif d["stage"] == "Proposal Sent":
                opener = f"Did you see the proposal? Questions?"
                close = "What would it take to start this week?"
            else:
                opener = f"I help stop {pain}. 2 min?"
                close = "$497/mo pilot, ROI in week 1. 15 min demo?"

            lines.append(f"{d['company']}")
            lines.append(f"  {first} {d['contact_phone']}")
            lines.append(f"  {opener}")
            lines.append(f"  Close: {close}")
            lines.append("")

        lines.append("After each: result [company]: [outcome]")
        return "\n".join(lines)

    except Exception as e:
        return f"Scripts failed: {e}"


def handle_call_prep(text: str) -> str:
    """Generate a quick call prep for a specific company.

    Usage: prep Dolphin Cooling
    Shows: contact info, notes, talking points, suggested approach.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["prep "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: prep [company name]"

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT * FROM deals WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()

        if not deal:
            conn.close()
            return f"No deal found matching '{company}'"

        d = dict(deal)

        # Get recent activities
        activities = conn.execute(
            "SELECT activity_type, description, created_at FROM activities "
            "WHERE deal_id = ? ORDER BY created_at DESC LIMIT 3",
            (d["id"],)
        ).fetchall()

        # Get outreach history
        outreach = conn.execute(
            "SELECT channel, message_summary, response, created_at FROM outreach_log "
            "WHERE deal_id = ? ORDER BY created_at DESC LIMIT 3",
            (d["id"],)
        ).fetchall()

        conn.close()

        # Build prep
        lines = [f"CALL PREP: {d['company']}\n"]
        lines.append(f"Contact: {d.get('contact_name') or '?'}")
        lines.append(f"Phone: {d.get('contact_phone') or 'none'}")
        lines.append(f"Email: {d.get('contact_email') or 'none'}")
        lines.append(f"Industry: {d.get('industry') or '?'} | {d.get('city') or ''}")
        lines.append(f"Stage: {d.get('stage')} | Score: {d.get('lead_score') or '?'}")

        if d.get("notes"):
            # Show first 200 chars of notes
            notes = d["notes"][:200]
            lines.append(f"\nNotes: {notes}")

        if activities:
            lines.append(f"\nRecent activity:")
            for a in activities:
                a = dict(a)
                lines.append(f"  {a['activity_type']}: {(a.get('description') or '')[:60]}")

        if outreach:
            lines.append(f"\nOutreach history:")
            for o in outreach:
                o = dict(o)
                resp = f" -> {o['response'][:40]}" if o.get("response") else ""
                lines.append(f"  {o['channel']}: {(o.get('message_summary') or '')[:40]}{resp}")

        # Talking points based on industry
        industry = (d.get("industry") or "").lower()
        lines.append(f"\nTalking points:")
        lines.append(f"  1. What's your biggest headache with [phones/scheduling/follow-ups]?")
        lines.append(f"  2. How many calls/leads do you miss after hours?")
        lines.append(f"  3. Would a 30-day pilot at $497/mo be worth testing?")

        lines.append(f"\nAfter call: result {d['company']}: [outcome]")

        return "\n".join(lines)

    except Exception as e:
        return f"Call prep failed: {e}"


def handle_reactivate(text: str) -> str:
    """Reactivate a Closed Lost deal back to Qualified.

    Usage: reactivate Cloud 9 Med Spa
    Moves the deal from Closed Lost to Qualified with a note.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["reactivate "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: reactivate [company name]"

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT id, company, stage, notes FROM deals WHERE company LIKE ? LIMIT 1",
            (f"%{company}%",)
        ).fetchone()

        if not deal:
            conn.close()
            return f"No deal found matching '{company}'"

        d = dict(deal)
        if d["stage"] != "Closed Lost":
            conn.close()
            return f"{d['company']} is currently '{d['stage']}', not Closed Lost."

        from datetime import datetime
        note_addition = f"\n[{datetime.now().strftime('%Y-%m-%d')}] Reactivated from Closed Lost. Re-approaching with adjusted framing."
        new_notes = (d.get("notes") or "") + note_addition

        pdb.update_deal(conn, d["id"], stage="Qualified", notes=new_notes)
        pdb.log_activity(conn, d["id"], "stage_changed",
                         "Reactivated from Closed Lost to Qualified")
        conn.close()

        return f"Reactivated: {d['company']} -> Qualified\nNow appears in 'leads' and 'next' commands."

    except Exception as e:
        return f"Reactivation failed: {e}"


def handle_next() -> str:
    """The most important command: what should William do RIGHT NOW?

    Uses the FollowupPrioritizer to find the highest-ROI action.
    Eliminates decision fatigue with data-driven prioritization.
    
    Factors: deal stage, days since contact, response history, 
    expected value, industry conversion rate, and time decay.
    """
    import importlib.util
    from pathlib import Path
    from datetime import datetime
    repo_root = _REPO_ROOT

    try:
        # Use the new priority engine
        spec = importlib.util.spec_from_file_location(
            "followup_prioritizer", repo_root / "execution" / "followup_prioritizer.py"
        )
        fp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fp)
        
        lead = fp.get_highest_priority_lead()
        
        if not lead:
            # Fall back to checking for reactivation candidates
            pdb_spec = importlib.util.spec_from_file_location(
                "pipeline_db", repo_root / "execution" / "pipeline_db.py"
            )
            pdb = importlib.util.module_from_spec(pdb_spec)
            pdb_spec.loader.exec_module(pdb)
            conn = pdb.get_db()
            
            reactivatable = conn.execute(
                "SELECT id, company, contact_phone, notes FROM deals "
                "WHERE stage = 'Closed Lost' AND contact_phone IS NOT NULL "
                "AND notes LIKE '%interest%' AND notes NOT LIKE '%DO NOT CONTACT%' "
                "LIMIT 3"
            ).fetchall()
            conn.close()

            if reactivatable:
                lines = ["No active leads to call. But there are reactivation candidates:\n"]
                for r in reactivatable:
                    d = dict(r)
                    notes_snippet = (d["notes"] or "")[:80]
                    lines.append(f"  {d['company']} — {d['contact_phone']}")
                    lines.append(f"    {notes_snippet}")
                lines.append(f"\nTo reactivate: reactivate [company name]")
                return "\n".join(lines)

            return (
                "No leads to call right now.\n"
                "All callable leads were contacted today, or none have phone numbers.\n"
                "Check: leads"
            )

        # Build the one-screen action message with priority data
        name = lead.contact_name or "the owner"
        phone = lead.contact_phone
        company = lead.company
        industry = lead.industry or "local business"
        
        # Urgency emoji
        urgency_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "⚪"
        }.get(lead.urgency, "⚪")
        
        lines = [
            f"{urgency_emoji} NEXT ACTION: Call {company}",
            f"",
            f"WHY: {lead.reason}",
            f"💰 Expected Value: ${lead.expected_value:,.0f}",
            f"📊 Priority Score: {lead.priority_score:.1f}",
            f"",
            f"CALL: {name} at {phone}",
            f"Industry: {industry} | Stage: {lead.stage}",
        ]
        
        # Days since contact
        if lead.days_since_contact >= 0:
            lines.append(f"Last contact: {lead.days_since_contact} day(s) ago")
            if lead.decay_rate > 2:
                lines.append(f"⚠️ Decaying at {lead.decay_rate}%/day — act fast!")
        
        # Talking points from priority engine
        if lead.talking_points:
            lines.append(f"")
            lines.append(f"💬 Talking Points:")
            for tp in lead.talking_points[:3]:
                lines.append(f"  • {tp}")

        # Self-improving: add learned recommendation for this industry
        try:
            ol_spec = importlib.util.spec_from_file_location(
                "outcome_learner", repo_root / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
            )
            ol = importlib.util.module_from_spec(ol_spec)
            ol_spec.loader.exec_module(ol)
            rec = ol.get_recommendation_for_lead(industry)
            lines.append(f"")
            lines.append(f"🧠 Learned: {rec}")
        except Exception:
            pass

        first_name = name.split()[0] if name != "the owner" else ""
        lines.extend([
            f"",
            f"Opening: \"Hi {first_name}, this is William "
            f"from Marceau Solutions. I help {industry} businesses automate their "
            f"customer follow-ups so they never miss a lead. Do you have 2 minutes?\"",
            f"",
            f"After call: result {company}: [outcome]",
        ])

        return "\n".join(lines)

    except Exception as e:
        import traceback
        return f"Next action failed: {e}\n{traceback.format_exc()}"


def handle_help() -> str:
    """Show all available Telegram commands."""
    return (
        "COMMANDS:\n"
        "\n"
        "ACTION:\n"
        "  next — what to do right now (highest ROI action)\n"
        "  priorities — top 5 follow-ups ranked by expected value\n"
        "  leads — full call sheet by priority\n"
        "  prep [company] — detailed call prep\n"
        "  result [company]: [outcome] — record what happened\n"
        "  reactivate [company] — re-open a closed lost deal\n"
        "  scripts — all call scripts at once\n"
        "  demo [type] — AI receptionist demo (hvac/medspa/plumber)\n"
        "  send demo [company] — email demo to prospect\n"
        "  proposal [company] — generate branded PDF proposal\n"
        "  send proposal [company] — email proposal to client\n"
        "  agreement [company] — generate service agreement PDF\n"
        "  onboard [company] — Stripe link + welcome email + Closed Won\n"
        "  decisions — everything needing your yes/no (hospital mode)\n"
        "\n"
        "PLANNING:\n"
        "  schedule — today's data-driven plan\n"
        "  digest — morning briefing on demand\n"
        "\n"
        "GOALS:\n"
        "  goal progress — pipeline stats vs targets\n"
        "  goal show — all goals with deadlines\n"
        "  goal alerts — off-track warnings\n"
        "  goal short: [text] — update short-term goal\n"
        "\n"
        "AUTONOMOUS:\n"
        "  run [goal] — autonomous Grok-Claude loop\n"
        "  runs — show recent goal runs\n"
        "  learned — what the system has learned from outcomes\n"
        "\n"
        "SYSTEM:\n"
        "  health — system check\n"
        "  tasks — orchestrator queue\n"
        "  task add [text] — add task\n"
        "  help — this message"
    )


def handle_goal_run(text: str) -> str:
    """Run an autonomous goal via the Grok-Claude loop.

    Usage: run Audit pipeline data quality
    Triggers goal_runner.py which calls Grok API for strategy
    and executes steps locally.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    goal = text.strip()
    for prefix in ["run ", "goal-run "]:
        if goal.lower().startswith(prefix):
            goal = goal[len(prefix):]
            break

    if not goal:
        return "Usage: run [goal description]"

    try:
        spec = importlib.util.spec_from_file_location(
            "goal_runner", repo_root / "execution" / "goal_runner.py"
        )
        gr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gr)

        result = gr.run_goal(goal, max_steps=3)
        return gr.format_result(result)

    except Exception as e:
        return f"Goal run failed: {e}"


def handle_goal_run_status() -> str:
    """Show recent autonomous goal runs."""
    import importlib.util
    repo_root = _REPO_ROOT

    try:
        spec = importlib.util.spec_from_file_location(
            "goal_runner", repo_root / "execution" / "goal_runner.py"
        )
        gr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gr)

        status = gr.show_status()
        if not status.get("recent"):
            return "No goal runs yet."

        lines = [f"Recent goal runs ({status['total']} total):\n"]
        for run in status["recent"]:
            lines.append(f"  [{run['status']}] {run['goal'][:50]}")
            lines.append(f"    {run['steps']} steps | {run['completed_at'][:16]}")
        return "\n".join(lines)

    except Exception as e:
        return f"Goal run status failed: {e}"


def handle_learned() -> str:
    """Show what the system has learned from recorded outcomes.

    Self-improving: displays insights about what's working and what isn't.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    try:
        spec = importlib.util.spec_from_file_location(
            "outcome_learner", repo_root / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
        )
        ol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ol)
        insights = ol.get_insights()

        lines = [f"LEARNED ({insights['total_outcomes']} outcomes):\n"]

        for i in insights.get("insights", []):
            lines.append(f"  {i}")

        channels = insights.get("by_channel", {})
        if channels:
            lines.append(f"\nChannel effectiveness:")
            for ch, stats in sorted(channels.items(), key=lambda x: -x[1]["response_rate"]):
                lines.append(f"  {ch}: {stats['sent']} sent, {stats['response_rate']}% response")

        if insights.get("learning_system_ready"):
            lines.append(f"\nLearning system: ACTIVE")
        else:
            lines.append(f"\nLearning system: {insights['total_outcomes']}/5 outcomes needed")

        return "\n".join(lines)

    except Exception as e:
        return f"Learning insights failed: {e}"


def handle_priorities(text: str = "") -> str:
    """Show prioritized follow-up list ranked by expected ROI.
    
    Uses the FollowupPrioritizer engine for data-driven rankings.
    Factors: deal stage, days since contact, response history, 
    expected value, industry conversion rate, and time decay.
    
    Usage:
        priorities          # Top 5
        priorities all      # All ranked leads
        priorities learn    # Update learnings from outcomes
    """
    import importlib.util
    repo_root = _REPO_ROOT
    
    try:
        spec = importlib.util.spec_from_file_location(
            "followup_prioritizer", repo_root / "execution" / "followup_prioritizer.py"
        )
        fp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fp)
        
        prioritizer = fp.FollowupPrioritizer()
        
        text = text.strip().lower()
        
        if text == "learn":
            learnings = prioritizer.learn_from_outcomes()
            lines = ["Updated industry conversion rates:\n"]
            for entry in learnings.get("learning_log", []):
                lines.append(f"  {entry['industry']}: {entry['old_rate']:.1%} → {entry['new_rate']:.1%} (n={entry['sample_size']})")
            if not learnings.get("learning_log"):
                lines.append("  No changes — need more conversion data")
            return "\n".join(lines)
        
        limit = 50 if text == "all" else 5
        leads = prioritizer.get_prioritized_leads(limit=limit)
        
        return prioritizer.format_daily_list(leads)
        
    except Exception as e:
        import traceback
        return f"Priorities failed: {e}\n{traceback.format_exc()}"


def handle_decisions() -> str:
    """Show everything that needs William's yes/no decision.

    One screen: all items requiring human judgment, prioritized.
    Designed for hospital-stay mode — check once a day, make decisions, done.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        lines = ["DECISIONS NEEDED:\n"]
        count = 0

        # 1. Trial active — needs conversion decision
        trials = conn.execute(
            "SELECT company, contact_name, contact_phone FROM deals "
            "WHERE stage = 'Trial Active'"
        ).fetchall()
        for r in trials:
            d = dict(r)
            count += 1
            lines.append(f"{count}. CONVERT TRIAL: {d['company']}")
            lines.append(f"   {d.get('contact_name', '?')} {d.get('contact_phone', '')}")
            lines.append(f"   -> onboard {d['company']}  OR  result {d['company']}: not_interested")
            lines.append("")

        # 2. Proposals sent >3 days — needs follow-up call or close
        stale = conn.execute(
            "SELECT company, contact_name, contact_phone, updated_at FROM deals "
            "WHERE stage = 'Proposal Sent' AND updated_at < datetime('now', '-3 days')"
        ).fetchall()
        for r in stale:
            d = dict(r)
            count += 1
            lines.append(f"{count}. FOLLOW UP PROPOSAL: {d['company']}")
            lines.append(f"   Sent: {d['updated_at'][:10]}")
            lines.append(f"   -> Call {d.get('contact_phone', 'no phone')} and ask for decision")
            lines.append("")

        # 3. Qualified leads with phone — needs call
        qualified = conn.execute(
            "SELECT company, contact_phone FROM deals "
            "WHERE stage = 'Qualified' AND contact_phone IS NOT NULL "
            "ORDER BY updated_at DESC LIMIT 5"
        ).fetchall()
        if qualified:
            count += 1
            lines.append(f"{count}. CALL {len(qualified)} QUALIFIED LEADS:")
            for r in qualified:
                d = dict(r)
                lines.append(f"   {d['company']} — {d['contact_phone']}")
            lines.append(f"   -> Use 'next' for call prep + script")
            lines.append("")

        # 4. Goal alerts
        try:
            gp_spec = importlib.util.spec_from_file_location(
                "goal_progress", repo_root / "projects" / "personal-assistant" / "src" / "goal_progress.py"
            )
            gp = importlib.util.module_from_spec(gp_spec)
            gp_spec.loader.exec_module(gp)
            alerts = gp.check_alerts()
            if alerts:
                count += 1
                lines.append(f"{count}. GOAL ALERT:")
                for a in alerts:
                    lines.append(f"   {a}")
                lines.append("")
        except Exception:
            pass

        conn.close()

        if count == 0:
            return "No decisions needed right now. System is running autonomously."

        lines.append(f"Total: {count} item(s) needing your decision")
        return "\n".join(lines)

    except Exception as e:
        return f"Decision check failed: {e}"


def handle_away_status() -> str:
    """Show the full system status for away-mode — everything in one screen.

    Combines: goal progress + decisions + pipeline + learning + next action
    into one message so William can assess everything with one command.
    """
    import importlib.util
    repo_root = _REPO_ROOT
    lines = []

    try:
        # Goal progress
        gp_spec = importlib.util.spec_from_file_location(
            "goal_progress", repo_root / "projects" / "personal-assistant" / "src" / "goal_progress.py"
        )
        gp = importlib.util.module_from_spec(gp_spec)
        gp_spec.loader.exec_module(gp)
        progress = gp.calculate_goal_progress()
        short = progress.get("short_term", {})
        if short:
            lines.append(f"GOAL: {short.get('goal', '?')} [{short.get('overall_pct', 0)}% | {short.get('days_left', '?')}d]")

        summary = progress.get("_summary", {})
        lines.append(f"Pipeline: {summary.get('total_deals', '?')} deals, {summary.get('warm_plus_leads', '?')} warm+")
        lines.append(f"Outreach 7d: {summary.get('recent_outreach_7d', '?')}")
        lines.append("")
    except Exception:
        pass

    # Decisions
    try:
        decisions_result = handle_decisions()
        # Count decisions
        decision_count = decisions_result.count(". ") if "DECISIONS" in decisions_result else 0
        lines.append(f"DECISIONS: {decision_count} item(s)")
        # Show first 2 items
        for line in decisions_result.split("\n"):
            if line.strip().startswith(("1.", "2.")):
                lines.append(f"  {line.strip()[:60]}")
        lines.append("")
    except Exception:
        pass

    # Learning
    try:
        ol_spec = importlib.util.spec_from_file_location(
            "outcome_learner", repo_root / "projects" / "personal-assistant" / "src" / "outcome_learner.py"
        )
        ol = importlib.util.module_from_spec(ol_spec)
        ol_spec.loader.exec_module(ol)
        insights = ol.get_insights()
        lines.append(f"LEARNING: {insights['total_outcomes']}/5 outcomes")
        if insights.get("insights"):
            lines.append(f"  {insights['insights'][0][:60]}")
        lines.append("")
    except Exception:
        pass

    # Next action (just the headline)
    try:
        next_result = handle_next()
        for line in next_result.split("\n"):
            if "NEXT ACTION" in line or "CALL:" in line:
                lines.append(line.strip())
    except Exception:
        pass

    lines.append("")
    lines.append("Commands: next | decisions | leads | demo | proposal | help")

    return "\n".join(lines) if lines else "System status unavailable."


def handle_demo(text: str) -> str:
    """Generate an AI receptionist demo conversation for a prospect.

    Usage: demo hvac | demo medspa | demo plumber
    Generates a sample AI call and returns the transcript.
    """
    import importlib.util
    import asyncio
    repo_root = _REPO_ROOT

    business_type = text.strip().lower()
    for prefix in ["demo "]:
        if business_type.startswith(prefix):
            business_type = business_type[len(prefix):]
            break

    # Map prospect industry to demo type
    type_map = {
        "hvac": "hvac", "ac": "hvac", "air": "hvac", "cooling": "hvac", "heating": "hvac",
        "med spa": "medspa", "medspa": "medspa", "aesthetics": "medspa", "botox": "medspa",
        "plumber": "plumber", "plumbing": "plumber", "pipe": "plumber",
        "marceau": "marceau", "us": "marceau",
    }
    demo_type = type_map.get(business_type, "hvac")

    # Demo messages per industry
    demo_messages = {
        "hvac": "Hi, my AC stopped working and it's really hot. I need someone out here today.",
        "medspa": "Hi, I'm interested in Botox and fillers. How much and when can I come in?",
        "plumber": "We have a burst pipe in the kitchen and water is everywhere. We need help now.",
        "marceau": "Hi, I run an HVAC company and I keep missing calls after hours. Can you help?",
    }
    caller_msg = demo_messages.get(demo_type, demo_messages["hvac"])

    demo_configs = {
        "hvac": {"name": "Naples Comfort HVAC", "type": "hvac",
                 "greeting": "Thank you for calling Naples Comfort HVAC! How can I help you today?",
                 "services": [{"name": "AC Repair", "description": "Same-day", "pricing": "$89 diagnostic"},
                              {"name": "24/7 Emergency", "description": "Always available", "pricing": "No overtime"}]},
        "medspa": {"name": "Glow Med Spa", "type": "med_spa",
                   "greeting": "Thank you for calling Glow Med Spa!",
                   "services": [{"name": "Botox", "description": "Wrinkle treatment", "pricing": "$12/unit"},
                                {"name": "Filler", "description": "Enhancement", "pricing": "From $650"}]},
        "plumber": {"name": "Pro Plumbing Naples", "type": "plumbing",
                    "greeting": "Pro Plumbing Naples, how can I help?",
                    "services": [{"name": "Emergency", "description": "24/7", "pricing": "No trip fee"},
                                 {"name": "Drain", "description": "All drains", "pricing": "$149"}]},
        "marceau": {"name": "Marceau Solutions", "type": "ai_automation",
                    "greeting": "Thank you for calling Marceau Solutions!",
                    "services": [{"name": "Voice AI", "description": "24/7 answering", "pricing": "$497/mo"}]},
    }

    config = demo_configs.get(demo_type, demo_configs["hvac"])
    services_text = "\n".join(f"- {s['name']}: {s['description']} ({s['pricing']})" for s in config["services"])
    system_prompt = f"You are a professional AI receptionist for {config['name']}. Answer the caller's question naturally and helpfully. Services:\n{services_text}"

    try:
        import os, ssl, json, urllib.request, certifi
        api_key = os.getenv("XAI_API_KEY", "") or os.getenv("GROK_API_KEY", "")
        if not api_key:
            return "XAI_API_KEY/GROK_API_KEY not set — cannot run demo"

        ctx = ssl.create_default_context(cafile=certifi.where())
        data = json.dumps({
            "model": "grok-3-mini",
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": caller_msg},
            ],
            "temperature": 0.7,
        }).encode()

        req = urllib.request.Request(
            "https://api.x.ai/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
        )
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        result = json.loads(resp.read())
        ai_response = result["choices"][0]["message"]["content"]

        return (
            f"AI DEMO: {config['name']}\n\n"
            f"Caller: {caller_msg}\n\n"
            f"AI: {ai_response}\n\n"
            f"---\nThis is what your AI receptionist sounds like.\n"
            f"$497/mo, live in 7 days. Book a demo: calendly.com/wmarceau/ai-services-discovery"
        )

    except Exception as e:
        return f"Demo generation failed: {e}"


def handle_agreement(text: str) -> str:
    """Generate a branded service agreement PDF for a client.

    Usage: agreement Dolphin Cooling
    Generates a service agreement with $497/mo pricing, 30-day terms,
    and emails it to William for review before sending to client.
    """
    import importlib.util
    from datetime import datetime
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["agreement ", "contract "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: agreement [company name]"

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT * FROM deals WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()
        if not deal:
            conn.close()
            return f"No deal matching '{company}'"

        d = dict(deal)
        conn.close()

        # Build agreement data
        import sys
        sys.path.insert(0, str(repo_root / "projects" / "fitness-influencer" / "src"))
        import pdf_templates.agreement_template
        from branded_pdf_engine import BrandedPDFEngine

        agreement_data = {
            "client_business_name": d["company"],
            "client_owner_name": d.get("contact_name") or "",
            "effective_date": datetime.now().strftime("%B %d, %Y"),
            "setup_fee": "$0",
            "monthly_rate": "$497/month",
            "tier_name": "AI Automation — Starter",
            "client_title": "Owner",
        }

        engine = BrandedPDFEngine()
        output_dir = repo_root / "projects" / "personal-assistant" / "logs" / "agreements"
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = d["company"].replace(" ", "_").replace("/", "-").replace("&", "_")[:30]
        filename = f"agreement_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = output_dir / filename

        engine.generate_to_file("agreement", agreement_data, str(output_path))
        size_kb = output_path.stat().st_size // 1024

        # Email to William for review
        try:
            gm_spec = importlib.util.spec_from_file_location(
                "gmail_api", repo_root / "projects" / "personal-assistant" / "src" / "gmail_api.py"
            )
            gm = importlib.util.module_from_spec(gm_spec)
            gm_spec.loader.exec_module(gm)
            gm.send_email(
                to="wmarceau@marceausolutions.com",
                subject=f"Agreement ready for review: {d['company']}",
                body=f"Service agreement generated for {d['company']}.\n\nReview the attached PDF before sending to client.\nClient email: {d.get('contact_email', 'not on file')}",
                attachments=[str(output_path)],
            )
        except Exception:
            pass

        response = f"Agreement generated: {d['company']}\n  File: {filename} ({size_kb}KB)"
        if d.get("contact_email"):
            response += f"\n  Client email: {d['contact_email']}"
        response += f"\n  Review at: {output_path}"
        response += f"\n  To send: email the PDF to {d.get('contact_email', 'client')}"
        return response

    except Exception as e:
        return f"Agreement generation failed: {e}"


def handle_proposal(text: str) -> str:
    """Generate a branded AI services proposal PDF for a lead.

    Usage: proposal Dolphin Cooling
    Pulls lead data from pipeline.db, generates PDF, emails it to William.
    """
    import importlib.util
    from pathlib import Path
    from datetime import datetime
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["proposal "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: proposal [company name]"

    try:
        # Get deal data
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT * FROM deals WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()

        if not deal:
            conn.close()
            return f"No deal found matching '{company}'"

        d = dict(deal)
        conn.close()

        # Industry-specific pain points and solutions
        industry = (d.get("industry") or "business").lower()
        pain_map = {
            "hvac": ("Missing after-hours emergency calls. Customers call competitors who answer first.",
                     "AI Phone Agent + Automated Follow-Up System",
                     ["24/7 AI phone answering for emergency calls",
                      "Automatic SMS follow-up within 60 seconds of missed calls",
                      "Lead qualification and service booking integration",
                      "Monthly analytics dashboard with call volume and conversion rates"]),
            "med spa": ("No-shows and missed booking follow-ups costing revenue every week.",
                        "AI Booking Assistant + Smart Follow-Up Engine",
                        ["Automated appointment reminders (SMS + email)",
                         "No-show recovery sequences with rebooking links",
                         "New client intake automation",
                         "Monthly retention and rebooking analytics"]),
            "plumb": ("Emergency calls going to voicemail after hours while competitors answer.",
                      "AI Emergency Call Handler + Lead Capture System",
                      ["24/7 emergency call answering and dispatch",
                       "Automatic lead capture and follow-up sequences",
                       "Service reminder automation for existing customers",
                       "Monthly call analytics and lead conversion tracking"]),
            "chiro": ("New patient follow-ups falling through the cracks, reducing retention.",
                      "AI Patient Engagement System",
                      ["Automated new patient intake and onboarding",
                       "Appointment reminder sequences (reduces no-shows 40%)",
                       "Re-engagement campaigns for inactive patients",
                       "Monthly patient retention analytics"]),
        }

        # Default
        pain = "Manual follow-ups and missed opportunities costing time and revenue."
        solution = "AI Automation System — Phone, Email, and SMS"
        details = ["24/7 automated response to inquiries",
                    "Smart follow-up sequences via SMS and email",
                    "Lead qualification and appointment booking",
                    "Monthly analytics and ROI dashboard"]

        for key, (p, s, det) in pain_map.items():
            if key in industry:
                pain, solution, details = p, s, det
                break

        # Build proposal data
        contact = d.get("contact_name") or ""
        proposal_data = {
            "client_name": contact,
            "business_name": d["company"],
            "industry": d.get("industry") or "Local Business",
            "problem_statement": pain,
            "solution": solution,
            "solution_details": details,
            "timeline": "7 days to full deployment",
            "investment": {"setup": "$0 setup", "monthly": "$497/mo"},
            "guarantee": "30-day money-back guarantee. If you don't see measurable ROI in the first month, you pay nothing.",
            "next_steps": "Book a 15-minute demo: calendly.com/wmarceau/ai-services-discovery",
        }

        # Generate PDF
        import sys
        sys.path.insert(0, str(repo_root / "projects" / "fitness-influencer" / "src"))
        import pdf_templates.proposal_template  # registers the template
        from branded_pdf_engine import BrandedPDFEngine

        engine = BrandedPDFEngine()
        output_dir = repo_root / "projects" / "personal-assistant" / "logs" / "proposals"
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_name = d["company"].replace(" ", "_").replace("/", "-")[:30]
        filename = f"proposal_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        output_path = output_dir / filename

        engine.generate_to_file("proposal", proposal_data, str(output_path))
        size_kb = output_path.stat().st_size // 1024

        # Email to William
        email_sent = False
        try:
            gm_spec = importlib.util.spec_from_file_location(
                "gmail_api", repo_root / "projects" / "personal-assistant" / "src" / "gmail_api.py"
            )
            gm = importlib.util.module_from_spec(gm_spec)
            gm_spec.loader.exec_module(gm)
            result = gm.send_email(
                to="wmarceau@marceausolutions.com",
                subject=f"Proposal ready: {d['company']}",
                body=f"Proposal PDF generated for {d['company']}.\nAttached for review.\n\nClient email: {d.get('contact_email') or 'no email on file'}\nTo send to client: send proposal {d['company']}",
                attachments=[str(output_path)],
            )
            email_sent = result.get("success", False)
        except Exception:
            pass

        response = f"Proposal generated: {d['company']}\n  File: {filename} ({size_kb}KB)"
        if d.get("contact_email"):
            response += f"\n  Client email: {d['contact_email']}"
        if email_sent:
            response += "\n  Emailed to wmarceau@marceausolutions.com"
        response += f"\n  Path: {output_path}"
        return response

    except Exception as e:
        return f"Proposal generation failed: {e}"


def handle_send_demo(text: str) -> str:
    """Email a personalized AI demo to a prospect.

    Usage: send demo Dolphin Cooling
    Generates a demo conversation based on the prospect's industry
    and emails it to their contact email with the Calendly link.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["send demo "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: send demo [company name]"

    try:
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT id, company, contact_name, contact_email, industry FROM deals "
            "WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()
        if not deal:
            conn.close()
            return f"No deal matching '{company}'"
        d = dict(deal)
        conn.close()

        if not d.get("contact_email"):
            return f"No email on file for {d['company']}. Add email first."

        # Map industry to demo type
        industry = (d.get("industry") or "").lower()
        demo_type = "hvac"
        for key, dtype in [("hvac", "hvac"), ("med spa", "medspa"), ("aesthet", "medspa"),
                           ("plumb", "plumber"), ("chiro", "hvac"), ("auto", "hvac")]:
            if key in industry:
                demo_type = dtype
                break

        # Generate demo conversation
        demo_result = handle_demo(f"demo {demo_type}")
        if not demo_result or "failed" in demo_result.lower():
            return f"Demo generation failed for {d['company']}"

        # Build email
        contact = d.get("contact_name") or ""
        first_name = contact.split()[0] if contact else ""
        greeting = f"Hi {first_name}" if first_name else "Hi"

        subject = f"Here's what your AI receptionist sounds like — {d['company']}"
        body = (
            f"{greeting},\n\n"
            f"I wanted to show you exactly what an AI receptionist would sound like "
            f"for {d['company']}. Here's a sample conversation:\n\n"
            f"---\n{demo_result}\n---\n\n"
            f"This is a live AI system — not a recording. It handles calls 24/7, "
            f"books appointments, captures lead info, and never misses a call.\n\n"
            f"Ready to see it in action for your business? Book a 15-minute demo:\n"
            f"https://calendly.com/wmarceau/ai-services-discovery\n\n"
            f"William Marceau\n"
            f"Marceau Solutions\n"
            f"wmarceau@marceausolutions.com\n"
            f"(239) 398-5676"
        )

        gm_spec = importlib.util.spec_from_file_location(
            "gmail_api", repo_root / "projects" / "personal-assistant" / "src" / "gmail_api.py"
        )
        gm = importlib.util.module_from_spec(gm_spec)
        gm_spec.loader.exec_module(gm)
        result = gm.send_email(to=d["contact_email"], subject=subject, body=body)

        if result.get("success"):
            # Log the outreach
            conn2 = pdb.get_db()
            pdb.log_activity(conn2, d["id"], "outreach",
                             f"AI demo email sent to {d['contact_email']}")
            conn2.close()
            return (f"Demo sent to {d['contact_email']}\n"
                    f"  Company: {d['company']}\n"
                    f"  Industry demo: {demo_type}")
        else:
            return f"Email failed: {result.get('error', 'unknown')}"

    except Exception as e:
        return f"Send demo failed: {e}"


def handle_send_proposal(text: str) -> str:
    """Send a previously generated proposal to the client's email.

    Usage: send proposal Dolphin Cooling
    Finds the most recent proposal PDF, sends to the client's email on file.
    """
    import importlib.util
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["send proposal ", "send-proposal "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: send proposal [company name]"

    try:
        # Find deal
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT id, company, contact_name, contact_email, industry FROM deals "
            "WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()
        if not deal:
            conn.close()
            return f"No deal matching '{company}'"
        d = dict(deal)
        conn.close()

        if not d.get("contact_email"):
            return f"No email on file for {d['company']}. Add email first."

        # Find most recent proposal PDF
        proposals_dir = repo_root / "projects" / "personal-assistant" / "logs" / "proposals"
        safe_name = d["company"].replace(" ", "_").replace("/", "-").replace("&", "_")[:30]
        matching = sorted(proposals_dir.glob(f"proposal_{safe_name}*"), reverse=True)

        if not matching:
            return f"No proposal PDF found for {d['company']}. Generate first: proposal {d['company']}"

        pdf_path = matching[0]
        contact = d.get("contact_name") or ""
        first_name = contact.split()[0] if contact else ""
        greeting = f"Hi {first_name}" if first_name else "Hi"

        # Send email with proposal info
        gm_spec = importlib.util.spec_from_file_location(
            "gmail_api", repo_root / "projects" / "personal-assistant" / "src" / "gmail_api.py"
        )
        gm = importlib.util.module_from_spec(gm_spec)
        gm_spec.loader.exec_module(gm)

        subject = f"AI Automation Proposal for {d['company']} — Marceau Solutions"
        body = (
            f"{greeting},\n\n"
            f"Thank you for taking the time to speak with me about {d['company']}. "
            f"As promised, I've put together a proposal for how we can help automate your "
            f"customer follow-ups and ensure you never miss another lead.\n\n"
            f"I've attached the proposal for your review. The key highlights:\n"
            f"- Custom AI system tailored for {d.get('industry', 'your industry')}\n"
            f"- $497/month with no long-term commitment\n"
            f"- 30-day money-back guarantee\n"
            f"- Live in 7 days\n\n"
            f"Would you be open to a 15-minute call to walk through it together?\n"
            f"Here's my calendar: https://calendly.com/wmarceau/ai-services-discovery\n\n"
            f"Looking forward to hearing from you.\n\n"
            f"William Marceau\n"
            f"Marceau Solutions\n"
            f"wmarceau@marceausolutions.com\n"
            f"(239) 398-5676"
        )

        result = gm.send_email(to=d["contact_email"], subject=subject, body=body,
                               attachments=[str(pdf_path)])

        if result.get("success"):
            # Update deal stage
            conn2 = pdb.get_db()
            pdb.update_deal(conn2, d["id"], stage="Proposal Sent",
                            next_action="follow_up_proposal")
            pdb.log_activity(conn2, d["id"], "outreach",
                             f"Proposal email sent to {d['contact_email']}")
            conn2.close()
            return (f"Proposal sent to {d['contact_email']}\n"
                    f"  Company: {d['company']}\n"
                    f"  Stage -> Proposal Sent\n"
                    f"  Follow up in 2-3 days if no response")
        else:
            return f"Email failed: {result.get('error', 'unknown')}"

    except Exception as e:
        return f"Send proposal failed: {e}"


def handle_onboard(text: str) -> str:
    """Trigger client onboarding when a deal is won.

    Usage: onboard Dolphin Cooling
    Generates onboarding packet, creates Stripe payment link, sends welcome email.
    """
    import importlib.util
    import ssl
    from pathlib import Path
    from datetime import datetime
    repo_root = _REPO_ROOT

    company = text.strip()
    for prefix in ["onboard "]:
        if company.lower().startswith(prefix):
            company = company[len(prefix):]
            break

    if not company:
        return "Usage: onboard [company name]"

    try:
        # Get deal
        spec = importlib.util.spec_from_file_location(
            "pipeline_db", repo_root / "execution" / "pipeline_db.py"
        )
        pdb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdb)
        conn = pdb.get_db()

        deal = conn.execute(
            "SELECT * FROM deals WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
            (f"%{company}%",)
        ).fetchone()
        if not deal:
            conn.close()
            return f"No deal matching '{company}'"
        d = dict(deal)

        # Update to Closed Won
        pdb.update_deal(conn, d["id"], stage="Closed Won")
        pdb.log_activity(conn, d["id"], "stage_changed", "Client won — onboarding started")
        conn.close()

        lines = [f"CLIENT WON: {d['company']}\n"]

        # 1. Stripe payment link
        stripe_link = _create_stripe_link(d, repo_root)
        if stripe_link:
            lines.append(f"Stripe: {stripe_link}")
        else:
            lines.append("Stripe: Could not create link (check API key)")

        # 2. Welcome email
        if d.get("contact_email"):
            email_sent = _send_welcome_email(d, stripe_link, repo_root)
            lines.append(f"Welcome email: {'sent' if email_sent else 'failed'}")
        else:
            lines.append("Welcome email: no email on file")

        # 3. Record outcome
        conn2 = pdb.get_db()
        pdb.log_scheduled_task(conn2, d["id"], "onboarding", d["company"])
        last_id = conn2.execute("SELECT MAX(id) FROM scheduled_outcomes").fetchone()[0]
        pdb.record_outcome(conn2, last_id, completed=True, outcome="client_won",
                           resulted_in="client_won", notes="Onboarded via Telegram command")
        total_outcomes = conn2.execute(
            "SELECT COUNT(*) FROM scheduled_outcomes WHERE completed=1"
        ).fetchone()[0]
        conn2.close()

        lines.append(f"Stage: Closed Won")
        lines.append(f"Outcomes: {total_outcomes}/5 toward learning system")
        if total_outcomes >= 5:
            lines.append("Learning system: ACTIVATED!")
        lines.append(f"\nNext: Confirm payment received, then deploy AI system")

        return "\n".join(lines)

    except Exception as e:
        return f"Onboarding failed: {e}"


def _create_stripe_link(deal: dict, repo_root) -> str:
    """Create a Stripe payment link for a new client."""
    import os, ssl, json, urllib.request
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()

    key = os.getenv("STRIPE_SECRET_KEY", "")
    if not key:
        return ""

    try:
        # Use existing $497/mo price or create one
        # First check for existing prices
        req = urllib.request.Request(
            "https://api.stripe.com/v1/prices?limit=10&active=true",
            headers={"Authorization": f"Bearer {key}"}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        prices = json.loads(resp.read())

        # Find a $497 monthly price
        target_price = None
        for p in prices.get("data", []):
            if (p.get("unit_amount") == 49700 and
                p.get("recurring", {}).get("interval") == "month"):
                target_price = p["id"]
                break

        if not target_price:
            # Create the price
            data = urllib.parse.urlencode({
                "unit_amount": "49700",
                "currency": "usd",
                "recurring[interval]": "month",
                "product_data[name]": f"AI Automation - {deal.get('company', 'Client')}",
            }).encode()
            req = urllib.request.Request(
                "https://api.stripe.com/v1/prices",
                data=data,
                headers={"Authorization": f"Bearer {key}"}
            )
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            price_data = json.loads(resp.read())
            target_price = price_data["id"]

        # Create payment link
        import urllib.parse
        data = urllib.parse.urlencode({
            "line_items[0][price]": target_price,
            "line_items[0][quantity]": "1",
        }).encode()
        req = urllib.request.Request(
            "https://api.stripe.com/v1/payment_links",
            data=data,
            headers={"Authorization": f"Bearer {key}"}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        link_data = json.loads(resp.read())
        return link_data.get("url", "")

    except Exception as e:
        return ""


def _send_welcome_email(deal: dict, stripe_link: str, repo_root) -> bool:
    """Send welcome/onboarding email to new client."""
    import importlib.util

    contact = deal.get("contact_name") or ""
    first_name = contact.split()[0] if contact else ""
    greeting = f"Hi {first_name}" if first_name else "Hi"

    subject = f"Welcome to Marceau Solutions — {deal['company']} Onboarding"
    body = (
        f"{greeting},\n\n"
        f"Welcome to Marceau Solutions! I'm excited to get your AI automation "
        f"system up and running for {deal['company']}.\n\n"
        f"Here's what happens next:\n\n"
        f"1. PAYMENT: Complete your subscription here:\n"
        f"   {stripe_link or 'Payment link coming separately'}\n\n"
        f"2. ONBOARDING CALL: We'll schedule a 30-minute setup call to:\n"
        f"   - Map your current phone/email workflow\n"
        f"   - Configure your AI phone agent\n"
        f"   - Set up automated follow-up sequences\n"
        f"   Book here: https://calendly.com/wmarceau/ai-services-discovery\n\n"
        f"3. DEPLOYMENT: Your system will be live within 7 days of our call.\n\n"
        f"4. GUARANTEE: If you don't see measurable ROI in 30 days, "
        f"you get a full refund. No questions asked.\n\n"
        f"Looking forward to working together!\n\n"
        f"William Marceau\n"
        f"Marceau Solutions\n"
        f"wmarceau@marceausolutions.com\n"
        f"(239) 398-5676"
    )

    try:
        spec = importlib.util.spec_from_file_location(
            "gmail_api", repo_root / "projects" / "personal-assistant" / "src" / "gmail_api.py"
        )
        gm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gm)
        result = gm.send_email(to=deal["contact_email"], subject=subject, body=body)
        return result.get("success", False)
    except Exception:
        return False


def route_message(text: str) -> Optional[str]:
    """Route a Telegram message to the right handler.

    Supports both exact commands AND natural language.
    Natural language routing uses keyword matching so William can type
    conversationally (e.g., "who should I call" -> leads,
    "generate a proposal for dolphin" -> proposal dolphin).

    Returns response string, or None if not a PA command.
    """
    lower = text.lower().strip()

    # --- Exact command routing (fast path) ---

    if lower in ("away", "status", "dashboard", "overview", "sitrep"):
        return handle_away_status()

    if lower in ("next", "what next", "what should i do", "what now"):
        return handle_next()

    if lower in ("decisions", "decision", "what needs my attention",
                  "anything need me", "what do i need to decide"):
        return handle_decisions()

    if lower in ("learned", "insights", "what have you learned",
                  "what works", "what working"):
        return handle_learned()

    if lower.startswith("priorities") or lower in ("priority", "top 5", "top5", "followups", "follow ups"):
        arg = lower.replace("priorities", "").strip() if lower.startswith("priorities") else ""
        return handle_priorities(arg)

    if lower in ("help", "commands", "?"):
        return handle_help()

    if lower in ("yes schedule", "approve schedule", "approve"):
        return handle_approve()

    if lower.startswith("goal") or lower.startswith("goals"):
        return handle_goals(text)

    if lower.startswith("task") or lower.startswith("tasks"):
        return handle_tasks(text)

    if lower.startswith("result ") or lower.startswith("outcome "):
        return handle_outcome(text)

    if lower.startswith("reactivate "):
        return handle_reactivate(text)

    if lower.startswith("leads") or lower == "pipeline":
        return handle_leads()

    if lower == "scripts" or lower == "call scripts":
        return handle_call_scripts()

    if lower.startswith("prep me for ") or lower.startswith("prep for "):
        # Natural: "prep me for Dolphin" -> extract company after prefix
        company = lower.split("prep me for ", 1)[1] if "prep me for " in lower else lower.split("prep for ", 1)[1]
        return handle_call_prep(f"prep {company.strip()}")

    if lower.startswith("prep "):
        return handle_call_prep(text)

    if lower.startswith("send demo "):
        return handle_send_demo(text)

    if lower.startswith("send proposal "):
        return handle_send_proposal(text)

    if lower.startswith("proposal "):
        return handle_proposal(text)

    if lower.startswith("demo ") or lower == "demo":
        return handle_demo(text if lower != "demo" else "demo hvac")

    if lower.startswith("agreement ") or lower.startswith("contract "):
        return handle_agreement(text)

    if lower.startswith("onboard "):
        return handle_onboard(text)

    if lower.startswith("run ") or lower.startswith("goal-run "):
        return handle_goal_run(text)

    if lower == "runs" or lower == "goal runs":
        return handle_goal_run_status()

    # --- Natural language routing (fuzzy matching) ---

    # Next action / what to do
    if any(kw in lower for kw in ["what do i do", "whats next", "what's next",
                                   "what now", "what should i", "what to do"]):
        return handle_next()

    # Call-related
    if any(kw in lower for kw in ["who should i call", "who to call",
                                   "who do i call", "call list", "call sheet"]):
        return handle_leads()

    # Hot leads / pipeline
    if any(kw in lower for kw in ["hot lead", "any leads", "pipeline",
                                   "show leads", "show me lead", "warm lead"]):
        return handle_leads()

    # Schedule / plan
    if any(kw in lower for kw in ["schedule", "plan", "what's my", "today's plan",
                                   "my day", "what's today", "whats today"]):
        return handle_schedule()

    # Digest / briefing
    if any(kw in lower for kw in ["digest", "briefing", "morning", "what did i miss",
                                   "catch me up", "what happened", "overnight"]):
        return handle_digest()

    # Proposal generation (natural: "generate a proposal for dolphin")
    if any(kw in lower for kw in ["generate a proposal", "make a proposal",
                                   "create a proposal", "write a proposal",
                                   "proposal for", "build a proposal"]):
        # Extract company name
        company = _extract_company_from_natural(lower, [
            "generate a proposal for ", "make a proposal for ",
            "create a proposal for ", "write a proposal for ",
            "proposal for ", "build a proposal for ",
        ])
        if company:
            return handle_proposal(f"proposal {company}")
        return "Which company? Usage: proposal [company name]"

    # Send proposal (natural: "send the proposal to antimidators")
    if any(kw in lower for kw in ["send the proposal", "email the proposal",
                                   "send proposal to"]):
        company = _extract_company_from_natural(lower, [
            "send the proposal to ", "email the proposal to ",
            "send proposal to ",
        ])
        if company:
            return handle_send_proposal(f"send proposal {company}")
        return "Which company? Usage: send proposal [company name]"

    # Call prep (natural: "prep me for dolphin cooling")
    if any(kw in lower for kw in ["prep me for", "prepare me for", "prepare for",
                                   "prep for", "call prep for", "brief me on"]):
        # Longest prefixes first to avoid partial matches
        company = _extract_company_from_natural(lower, [
            "call prep for ", "prep me for ", "prepare me for ",
            "brief me on ", "prepare for ", "prep for ",
        ])
        if company:
            return handle_call_prep(f"prep {company}")
        return "Which company? Usage: prep [company name]"

    # Onboarding (natural: "onboard dolphin cooling")
    if any(kw in lower for kw in ["onboard ", "start onboarding", "close the deal"]):
        company = _extract_company_from_natural(lower, [
            "onboard ", "start onboarding for ", "start onboarding ",
            "close the deal with ", "close the deal for ",
        ])
        if company:
            return handle_onboard(f"onboard {company}")
        return "Which company? Usage: onboard [company name]"

    # Away status (natural: "how's the business", "give me the overview")
    if any(kw in lower for kw in ["how's the business", "hows the business",
                                   "give me the overview", "business status",
                                   "how's everything", "hows everything",
                                   "sitrep", "full status"]):
        return handle_away_status()

    # Decisions (natural: "anything need me", "what needs my attention")
    if any(kw in lower for kw in ["anything need me", "what needs my attention",
                                   "need my decision", "what do i need to decide",
                                   "need me for anything", "decisions needed"]):
        return handle_decisions()

    # Goal progress (natural: "how are my goals", "am i on track")
    if any(kw in lower for kw in ["how are my goal", "am i on track",
                                   "goal progress", "how's the goal",
                                   "hows the goal", "goal status"]):
        return handle_goals("goal progress")

    # Health / system
    if any(kw in lower for kw in ["health", "system check", "system status",
                                   "is everything working", "how's the system",
                                   "hows the system"]):
        return handle_health()

    # Scripts
    if any(kw in lower for kw in ["call scripts", "all scripts", "show scripts",
                                   "give me scripts"]):
        return handle_call_scripts()

    # General status / update requests
    if any(kw in lower for kw in ["any updates", "update me", "whats going on",
                                   "what's going on", "hey whats going on",
                                   "what happened today", "anything new"]):
        return handle_away_status()

    # "send a proposal to X" (different from "send proposal X")
    if "send a proposal to " in lower or "send proposal to " in lower:
        for prefix in ["send a proposal to ", "send proposal to "]:
            if prefix in lower:
                company = lower.split(prefix, 1)[1].strip()
                if company:
                    return handle_send_proposal(f"send proposal {company}")

    # "how is X doing" — check a specific deal
    if lower.startswith("how is ") and " doing" in lower:
        company = lower.replace("how is ", "").replace(" doing", "").strip()
        if company:
            return handle_call_prep(f"prep {company}")

    # --- Conversational intent parser (last resort before giving up) ---
    result = _parse_conversational_intent(text)
    if result:
        return result

    return None  # Not a PA command -- let Clawdbot handle normally


def _parse_conversational_intent(text: str) -> str:
    """Parse natural conversational messages and extract intent + company.

    Handles messages like:
      "I just got off a call with Dolphin Cooling and they want a proposal"
      "Antimidators called back and said yes"
      "I met with Cloud 9 and they are interested but worried about cost"
      "Just finished a visit to PlumbingPro they want to think about it"
      "Did anyone respond to my emails today"

    Returns: response string, or empty string if no intent detected.
    """
    import importlib.util
    import re
    repo_root = _REPO_ROOT
    lower = text.lower().strip()

    # --- Pattern: Call/visit outcome reporting ---
    # "I just got off a call with [company] and [outcome description]"
    # "just finished a visit to [company] [outcome]"
    # "[company] called back and said [yes/no/etc]"
    outcome_patterns = [
        # "got off a call with X and they want a proposal"
        (r"(?:got off|finished|had|did|made)\s+(?:a\s+)?(?:call|visit|meeting)\s+(?:with|to|at)\s+(.+?)(?:\s+and\s+|\s+they\s+|\s*[,.])", None),
        # "X called back and said yes"
        (r"^(.+?)\s+(?:called back|responded|replied|got back|said)\s+", None),
        # "met with X and they are interested"
        (r"(?:met|spoke|talked)\s+(?:with|to)\s+(.+?)(?:\s+and\s+|\s+they\s+|\s*[,.])", None),
        # "visited X today" / "visit to X they want"
        (r"visit(?:ed)?\s+(?:to\s+)?(.+?)(?:\s+today|\s+and|\s+they\s+|\s*[,.])", None),
    ]

    for pattern, _ in outcome_patterns:
        match = re.search(pattern, lower)
        if match:
            company_guess = match.group(1).strip()
            # Clean up the company name
            company_guess = re.sub(r'\b(and|but|they|he|she|the|a|an)\b.*$', '', company_guess).strip()
            if len(company_guess) < 2:
                continue

            # Try to match to a real deal
            try:
                spec = importlib.util.spec_from_file_location(
                    "pipeline_db", repo_root / "execution" / "pipeline_db.py"
                )
                pdb = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(pdb)
                conn = pdb.get_db()
                deal = conn.execute(
                    "SELECT id, company FROM deals WHERE company LIKE ? ORDER BY updated_at DESC LIMIT 1",
                    (f"%{company_guess}%",)
                ).fetchone()
                conn.close()

                if not deal:
                    continue
                deal = dict(deal)
                company_name = deal["company"]
            except Exception:
                continue

            # Determine outcome from the rest of the message
            rest = lower[match.end():] if match.end() < len(lower) else lower[match.start():]

            if any(w in rest for w in ["said yes", "want to go", "sign", "let's do it", "onboard", "close"]):
                return handle_outcome(f"result {company_name}: client_won")
            elif any(w in rest for w in ["want a proposal", "send proposal", "wants pricing", "send them"]):
                # Generate and offer to send
                r = handle_proposal(f"proposal {company_name}")
                return f"{r}\n\nSend to client? Type: send proposal {company_name}"
            elif any(w in rest for w in ["interested", "want to learn", "curious", "intrigued"]):
                notes = text[match.end():].strip()[:100] if match.end() < len(text) else ""
                return handle_outcome(f"result {company_name}: interested - {notes}")
            elif any(w in rest for w in ["think about it", "not ready", "maybe later", "not now"]):
                return handle_outcome(f"result {company_name}: callback - {text[match.end():].strip()[:80]}")
            elif any(w in rest for w in ["not interested", "no thanks", "pass", "said no"]):
                return handle_outcome(f"result {company_name}: not_interested")
            elif any(w in rest for w in ["meeting", "booked", "scheduled", "calendly", "discovery"]):
                return handle_outcome(f"result {company_name}: meeting_booked")
            else:
                # Default: record as conversation
                notes = text[match.end():].strip()[:100] if match.end() < len(text) else ""
                return handle_outcome(f"result {company_name}: conversation - {notes}")

    # --- Pattern: Status questions ---
    if any(p in lower for p in ["anyone respond", "any responses", "any replies",
                                  "email response", "who responded", "any new leads"]):
        # Check recent responses
        try:
            spec = importlib.util.spec_from_file_location(
                "pipeline_db", repo_root / "execution" / "pipeline_db.py"
            )
            pdb = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pdb)
            conn = pdb.get_db()
            recent = conn.execute(
                "SELECT company, channel, response FROM outreach_log "
                "WHERE response IS NOT NULL AND response != '' "
                "AND created_at > datetime('now', '-2 days') "
                "ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
            conn.close()

            if recent:
                lines = [f"Recent responses ({len(recent)}):"]
                for r in recent:
                    d = dict(r)
                    lines.append(f"  {d['company']} [{d['channel']}]: {(d['response'] or '')[:60]}")
                return "\n".join(lines)
            return "No new responses in the last 2 days."
        except Exception:
            return "Could not check responses."

    # --- Pattern: "make/create/build a proposal for X" ---
    if any(p in lower for p in ["make me a proposal", "create a proposal", "build a proposal",
                                  "write a proposal", "draft a proposal"]):
        # Try to extract company from the rest
        for prefix in ["make me a proposal for ", "create a proposal for ",
                        "build a proposal for ", "write a proposal for ",
                        "draft a proposal for "]:
            if prefix in lower:
                company = lower.split(prefix, 1)[1].strip()
                if company:
                    return handle_proposal(f"proposal {company}")
        return "Which company? Just say: proposal [company name]"

    return ""


def _extract_company_from_natural(text: str, prefixes: list) -> str:
    """Extract company name from natural language by stripping known prefixes."""
    for prefix in prefixes:
        if prefix in text:
            return text.split(prefix, 1)[1].strip()
    return ""
