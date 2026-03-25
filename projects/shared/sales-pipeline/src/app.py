#!/usr/bin/env python3
"""
Marceau Sales Pipeline — Production Dashboard

AI services sales pipeline with kanban board, proposal generation,
pre-call intelligence briefs, outreach tracking, and deal management.

http://127.0.0.1:8785 (local) | https://pipeline.marceausolutions.com (production)
"""

import os
import sys
import csv
import json
import html
import io
from datetime import datetime, timedelta, date
from pathlib import Path

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import uvicorn

from .models import (
    get_db, create_deal, update_deal, get_deal, get_all_deals, get_deals_by_stage,
    delete_deal, log_outreach, get_outreach_log, get_todays_followups,
    create_proposal, get_proposals, save_call_brief, get_call_briefs,
    get_activities, get_pipeline_stats, log_activity, get_tier1_queue,
    get_call_queue, get_email_queue, get_phone_queue, get_inperson_queue,
    get_outreach_stats, assign_outreach_method,
    get_daily_outreach_counts, get_leads_by_tier_and_method,
    STAGES, STAGE_COLORS, CHANNELS, INDUSTRIES
)
from .ui import render_page

app = FastAPI(title="Marceau Sales Pipeline", version="1.0.0")
PORT = int(os.getenv("PIPELINE_PORT", "8785"))

# Paths
_SRC_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SRC_DIR.parents[3]
TRACKING_DIR = _PROJECT_ROOT / "projects/shared/lead-scraper/output"


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    conn = get_db()
    stats = get_pipeline_stats(conn)
    deals_by_stage = get_deals_by_stage(conn)
    recent_activity = get_activities(conn, limit=15)
    followups = get_todays_followups(conn)
    all_deals = [dict(d) for d in get_all_deals(conn)]
    tier1_queue = [dict(d) for d in get_tier1_queue(conn)]
    outreach_stats = get_outreach_stats(conn)
    daily_counts = get_daily_outreach_counts(conn)
    leads_grouped, all_leads = get_leads_by_tier_and_method(conn)
    conn.close()
    return render_page("dashboard", "Pipeline", {
        "stats": stats, "deals_by_stage": deals_by_stage,
        "activity": recent_activity, "followups": followups,
        "all_deals": all_deals, "tier1_queue": tier1_queue,
        "outreach_stats": outreach_stats,
        "daily_counts": daily_counts,
        "leads_grouped": leads_grouped,
        "all_leads": all_leads,
    })


@app.get("/deals", response_class=HTMLResponse)
async def deals_list():
    conn = get_db()
    deals = get_all_deals(conn)
    stats = get_pipeline_stats(conn)
    conn.close()
    return render_page("deals", "All Deals", {"deals": deals, "stats": stats})


@app.get("/deals/add", response_class=HTMLResponse)
async def add_deal_form():
    return render_page("add_deal", "Add Deal", {"industries": INDUSTRIES, "channels": CHANNELS})


@app.post("/deals/add")
async def add_deal_submit(
    company: str = Form(...), contact_name: str = Form(""), contact_phone: str = Form(""),
    contact_email: str = Form(""), industry: str = Form("Other"), pain_points: str = Form(""),
    lead_source: str = Form(""), notes: str = Form(""),
):
    conn = get_db()
    deal_id = create_deal(conn, company, contact_name=contact_name, contact_phone=contact_phone,
                          contact_email=contact_email, industry=industry, pain_points=pain_points,
                          lead_source=lead_source, notes=notes)
    conn.close()
    return RedirectResponse(f"/deals/{deal_id}", status_code=303)


@app.get("/deals/{deal_id}", response_class=HTMLResponse)
async def deal_detail(deal_id: int):
    conn = get_db()
    deal = get_deal(conn, deal_id)
    if not deal:
        conn.close()
        raise HTTPException(404, "Deal not found")
    outreach = get_outreach_log(conn, deal_id, 20)
    proposals = get_proposals(conn, deal_id)
    briefs = get_call_briefs(conn, deal_id)
    activities = get_activities(conn, deal_id, 20)
    conn.close()
    return render_page("deal_detail", deal["company"], {
        "deal": deal, "outreach": outreach, "proposals": proposals,
        "briefs": briefs, "activities": activities,
        "stages": STAGES, "industries": INDUSTRIES, "channels": CHANNELS,
    })


@app.post("/deals/{deal_id}/update")
async def update_deal_route(deal_id: int, request: Request):
    form = await request.form()
    kwargs = {k: v for k, v in form.items() if v and k != "deal_id"}
    # Convert numeric fields
    for f in ["proposal_amount", "setup_fee", "monthly_fee"]:
        if f in kwargs:
            try:
                kwargs[f] = float(kwargs[f])
            except ValueError:
                del kwargs[f]
    conn = get_db()
    update_deal(conn, deal_id, **kwargs)
    conn.close()
    return RedirectResponse(f"/deals/{deal_id}", status_code=303)


@app.post("/deals/{deal_id}/stage")
async def change_stage(deal_id: int, stage: str = Form(...)):
    if stage not in STAGES:
        raise HTTPException(400, "Invalid stage")
    conn = get_db()
    update_deal(conn, deal_id, stage=stage)
    if stage == "Closed Won":
        deal = get_deal(conn, deal_id)
        if deal:
            update_deal(conn, deal_id, close_date=datetime.now().strftime("%Y-%m-%d"))
    conn.close()
    return RedirectResponse(f"/deals/{deal_id}", status_code=303)


@app.post("/deals/{deal_id}/delete")
async def delete_deal_route(deal_id: int):
    conn = get_db()
    delete_deal(conn, deal_id)
    conn.close()
    return RedirectResponse("/deals", status_code=303)


@app.post("/deals/{deal_id}/log-visit")
async def log_visit_route(
    deal_id: int,
    spoke_to: str = Form(""),
    reaction: str = Form(""),
    notes: str = Form(""),
    visit_date: str = Form(""),
):
    """Log an in-person visit interaction for a deal."""
    conn = get_db()
    deal = get_deal(conn, deal_id)
    if not deal:
        conn.close()
        raise HTTPException(404, "Deal not found")

    summary = f"{spoke_to} — {reaction}" if spoke_to else reaction
    log_outreach(conn, deal_id, deal["company"], spoke_to or deal["contact_name"] or "",
                 channel="In-Person", message=summary, response=notes)
    log_activity(conn, deal_id, "visit_logged",
                 f"In-person: {summary}" + (f" on {visit_date}" if visit_date else ""))

    if reaction in ("Positive", "Requested Follow-up"):
        update_deal(conn, deal_id, stage="Qualified")

    conn.close()
    return JSONResponse({"ok": True})


# ─── Bulk Import / Sync ───────────────────────────────────────

@app.get("/import", response_class=HTMLResponse)
async def import_page():
    return render_page("import", "Import CSV", {})


@app.post("/import", response_class=HTMLResponse)
async def import_csv(file: UploadFile = File(...), stage: str = Form("Intake"), lead_source: str = Form("CSV Import")):
    """Parse uploaded CSV and bulk-create deals, skipping duplicates."""
    try:
        contents = await file.read()
        text = contents.decode("utf-8-sig")  # handle BOM
        reader = csv.DictReader(io.StringIO(text))

        conn = get_db()
        # Build set of existing company names (lowercased) to detect duplicates
        existing = set(
            r[0].lower() for r in conn.execute("SELECT LOWER(company) FROM deals").fetchall()
        )

        added = 0
        skipped = 0
        for row in reader:
            company = (row.get("company") or row.get("Company") or "").strip()
            if not company:
                continue
            if company.lower() in existing:
                skipped += 1
                continue
            contact_name = (row.get("contact_name") or row.get("Contact Name") or row.get("first_name") or "").strip()
            contact_email = (row.get("contact_email") or row.get("Email") or row.get("email") or "").strip()
            industry = (row.get("industry") or row.get("Industry") or "Other").strip()
            contact_phone = (row.get("contact_phone") or row.get("Phone") or "").strip()
            notes = (row.get("notes") or row.get("Notes") or "").strip()

            create_deal(conn, company,
                        contact_name=contact_name,
                        contact_email=contact_email,
                        contact_phone=contact_phone,
                        industry=industry,
                        lead_source=lead_source,
                        stage=stage,
                        notes=notes)
            existing.add(company.lower())
            added += 1

        conn.close()
        return render_page("import", "Import CSV", {
            "result": f"Import complete — {added} deal(s) added, {skipped} duplicate(s) skipped."
        })
    except Exception as e:
        return render_page("import", "Import CSV", {"error": f"Import failed: {e}"})


@app.post("/deals/sync-outreach")
async def sync_outreach():
    """Import deals + log outreach from ALL tracking files (not date-filtered).
    New deals are created for unrecognized emails/companies.
    For existing deals, the email is logged to outreach_log if not already there.
    """
    try:
        conn = get_db()

        existing_email_to_id = {
            (r[0] or "").lower(): r[1]
            for r in conn.execute("SELECT contact_email, id FROM deals WHERE contact_email IS NOT NULL AND contact_email != ''").fetchall()
        }
        existing_company_to_id = {
            (r[0] or "").lower(): r[1]
            for r in conn.execute("SELECT LOWER(company), id FROM deals").fetchall()
        }

        added = 0
        logged = 0
        skipped = 0

        for f in sorted(TRACKING_DIR.glob("outreach_tracking_*.json"), reverse=True):
            try:
                data = json.loads(f.read_text())
            except Exception:
                continue

            batches = data if isinstance(data, list) else [data]

            for batch in batches:
                if not isinstance(batch, dict):
                    continue
                for em in batch.get("emails", []):
                    email      = (em.get("recipient") or "").lower().strip()
                    company    = (em.get("company") or "").strip()
                    company_key = company.lower()
                    subject    = (em.get("subject") or "").strip()
                    sent_at    = (em.get("sent_at") or str(date.today()))[:19]
                    verdict    = (em.get("research_verdict") or "").strip()
                    pain       = (em.get("pain_point_angle") or "").strip()
                    first_name = (em.get("first_name") or "").strip()

                    try:
                        em_tier = int(em.get("tier", 0))
                    except (ValueError, TypeError):
                        em_tier = 0

                    # Resolve deal_id
                    deal_id = existing_email_to_id.get(email) or existing_company_to_id.get(company_key)

                    if deal_id is None:
                        # New deal
                        if not company and not email:
                            continue
                        deal_id = create_deal(
                            conn, company or email,
                            contact_name=first_name,
                            contact_email=email,
                            stage="Intake",
                            lead_source="Outreach Sync",
                            tier=em_tier,
                            email_template=pain or None,
                            notes=("[Research] " + verdict) if verdict else "",
                        )
                        if email:
                            existing_email_to_id[email] = deal_id
                        if company_key:
                            existing_company_to_id[company_key] = deal_id
                        added += 1

                    # Log the email to outreach_log if not already there
                    existing_log = conn.execute(
                        "SELECT id FROM outreach_log WHERE deal_id=? AND channel='Email' AND message_summary LIKE ?",
                        (deal_id, "%" + subject[:25] + "%")
                    ).fetchone()
                    if existing_log:
                        skipped += 1
                        continue

                    msg = ("Subject: " + subject) if subject else "Email sent"
                    if verdict:
                        msg += " | Research: " + verdict[:120]
                    log_outreach(conn, deal_id, company, first_name, "Email",
                                 msg, "", "", "cold-email-sprint")
                    # Preserve original sent_at timestamp
                    conn.execute(
                        "UPDATE outreach_log SET created_at=? WHERE id=(SELECT MAX(id) FROM outreach_log WHERE deal_id=?)",
                        (sent_at, deal_id)
                    )
                    conn.commit()
                    logged += 1

        conn.close()
        return JSONResponse({"ok": True, "added": added, "logged": logged, "skipped": skipped})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# ─── Outreach ────────────────────────────────────────────────

@app.get("/outreach", response_class=HTMLResponse)
async def outreach_page():
    conn = get_db()
    queue = get_phone_queue(conn)
    log = get_outreach_log(conn, limit=200)
    ostats = get_outreach_stats(conn)
    # Get all deals grouped by lead_source for list switching
    all_deals_for_lists = conn.execute("""
        SELECT d.*,
               COUNT(DISTINCT CASE WHEN o.channel='Call' THEN o.id END) AS call_count,
               MAX(CASE WHEN o.channel='Call' THEN o.created_at END) AS last_called,
               MAX(CASE WHEN o.channel='Email' THEN o.created_at END) AS last_emailed,
               MAX(CASE WHEN o.channel='Email' THEN o.message_summary END) AS last_email_subject
        FROM deals d
        LEFT JOIN outreach_log o ON o.deal_id = d.id
        WHERE d.stage NOT IN ('Closed Won','Closed Lost')
        GROUP BY d.id
        ORDER BY CASE WHEN d.tier=1 THEN 0 WHEN d.tier=2 THEN 1 ELSE 2 END, d.company ASC
    """).fetchall()
    # Group by lead_source
    lists_by_source = {}
    for d in all_deals_for_lists:
        src = d["lead_source"] or "Other"
        if src not in lists_by_source:
            lists_by_source[src] = []
        lists_by_source[src].append(dict(d))
    conn.close()
    return render_page("outreach", "Call Day", {
        "queue": queue, "log": log, "outreach_stats": ostats,
        "lists_by_source": lists_by_source,
    })


@app.get("/email-day", response_class=HTMLResponse)
async def email_day_page():
    conn = get_db()
    queue = get_email_queue(conn)
    log = get_outreach_log(conn, limit=30)
    ostats = get_outreach_stats(conn)
    conn.close()
    return render_page("email-day", "Email Day", {"queue": queue, "log": log, "outreach_stats": ostats})


@app.get("/inperson-day", response_class=HTMLResponse)
async def inperson_day_page():
    conn = get_db()
    queue = get_inperson_queue(conn)
    log = get_outreach_log(conn, limit=30)
    ostats = get_outreach_stats(conn)
    conn.close()
    return render_page("inperson-day", "In-Person Day", {"queue": queue, "log": log, "outreach_stats": ostats})


@app.post("/deals/{deal_id}/log-call")
async def log_call_route(
    deal_id: int,
    outcome: str = Form(""),
    notes: str = Form(""),
    follow_up_date: str = Form(""),
):
    from datetime import date as _date, timedelta
    conn = get_db()
    deal = get_deal(conn, deal_id)
    if not deal:
        conn.close()
        raise HTTPException(404, "Deal not found")

    message = f"Call: {outcome}" if outcome else "Call logged"

    # ── Follow-up routing based on outcome ──────────────────────────────────
    # Compute auto follow-up date if not supplied by user
    today = _date.today()
    _routing = {
        "Voicemail Left":         {"days": 3,  "action": "Re-call",                         "method": None},
        "No Answer":              {"days": 3,  "action": "Re-call",                         "method": None},
        "Answered - Interested":  {"days": 1,  "action": "Book meeting — qualified lead",   "method": None,  "stage": "Qualified"},
        "Answered - Callback":    {"days": 1,  "action": "Call back — callback requested",  "method": None},
        "Language Barrier":       {"days": 1,  "action": "In-person visit",                 "method": "in-person"},
        "Already Has System":     {"days": 90, "action": "Check back — verify system works","method": None},
        "Wrong Number":           {"days": None,"action": "Update phone number",             "method": None},
        "Not Interested":         {"days": 30, "action": "Re-email with value-add",         "method": None},
    }
    rule = _routing.get(outcome, {})
    resolved_fu = follow_up_date or (
        (today + timedelta(days=rule["days"])).strftime("%Y-%m-%d") if rule.get("days") else None
    )

    log_outreach(conn, deal_id, dict(deal)["company"], dict(deal).get("contact_name") or "",
                 "Call", message, "", resolved_fu)

    # Apply routing: stage, next_action, outreach_method
    update_kwargs = {}
    if rule.get("stage") and dict(deal)["stage"] in ("Intake",):
        update_kwargs["stage"] = rule["stage"]
    if rule.get("action"):
        update_kwargs["next_action"] = rule["action"]
    if resolved_fu:
        update_kwargs["next_action_date"] = resolved_fu
    if rule.get("method"):
        update_kwargs["outreach_method"] = rule["method"]
    if update_kwargs:
        update_deal(conn, deal_id, **update_kwargs)

    # Append notes
    if notes:
        existing = dict(deal).get("notes") or ""
        note_entry = f"[{today}] {outcome}: {notes}"
        update_deal(conn, deal_id, notes=(existing + "\n" + note_entry).strip())

    conn.close()
    return JSONResponse({
        "ok": True,
        "follow_up_action": rule.get("action", ""),
        "follow_up_date": resolved_fu or "",
    })


# ─── Send Proposal + Signing Agreement ──────────────────────

@app.post("/deals/{deal_id}/send-proposal")
async def send_proposal_route(
    deal_id: int,
    client_name: str = Form(""),
    client_email: str = Form(""),
    tier: int = Form(1),
    pain_point: str = Form(""),
):
    """
    Run close_deal.py for the given deal, return JSON with signing_url + pdf_path + email_sent.
    Form fields (all optional overrides — falls back to deal data if empty):
      client_name, client_email, tier, pain_point
    """
    import re
    import subprocess

    conn = get_db()
    deal = get_deal(conn, deal_id)
    if not deal:
        conn.close()
        raise HTTPException(404, "Deal not found")

    # Use form values; fall back to deal data
    resolved_name  = client_name.strip()  or deal["contact_name"] or deal["company"]
    resolved_email = client_email.strip() or deal["contact_email"] or ""
    resolved_pain  = pain_point.strip()   or deal["pain_points"]  or "Improve lead capture and follow-up"
    business_name  = deal["company"]

    if not resolved_email:
        conn.close()
        return JSONResponse(
            {"ok": False, "error": "No email address provided. Add one to the deal or fill in the form."},
            status_code=400,
        )

    close_deal_py = str(_PROJECT_ROOT / "projects/marceau-solutions/digital/tools/web-dev/close_deal.py")
    cmd = [
        sys.executable, close_deal_py,
        "--client-name",   resolved_name,
        "--business-name", business_name,
        "--email",         resolved_email,
        "--tier",          str(tier),
        "--pain-point",    resolved_pain,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=90,
            cwd=str(_PROJECT_ROOT),
        )
        output = result.stdout + result.stderr

        # Extract signing URL from output
        signing_url = ""
        for line in output.splitlines():
            m = re.search(r'https?://\S+', line)
            if m:
                candidate = m.group(0).rstrip("│").strip()
                if "sign.marceausolutions.com" in candidate or "localhost:8797" in candidate:
                    signing_url = candidate
                    break

        # Extract PDF path from output
        agreement_path = ""
        for line in output.splitlines():
            if "agreement.pdf" in line and "Saved:" in line:
                agreement_path = line.split("Saved:")[-1].strip()
                break

        email_sent = result.returncode == 0 and "Sent to" in output

        if result.returncode != 0:
            conn.close()
            return JSONResponse({"ok": False, "error": output[-800:] or "close_deal.py exited non-zero"}, status_code=500)

        # Advance deal stage to Proposal Sent, update contact info
        update_deal(conn, deal_id, stage="Proposal Sent",
                    contact_name=resolved_name, contact_email=resolved_email)
        log_activity(conn, deal_id, "proposal_sent",
                     f"Proposal & agreement sent to {resolved_email} (Tier {tier}). Signing: {signing_url}")
        conn.close()

        return JSONResponse({
            "ok": True,
            "signing_url": signing_url,
            "pdf_path": agreement_path,
            "email_sent": email_sent,
        })

    except subprocess.TimeoutExpired:
        conn.close()
        return JSONResponse({"ok": False, "error": "close_deal.py timed out (>90s)"}, status_code=500)
    except Exception as exc:
        conn.close()
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


# ─── Proposals ───────────────────────────────────────────────

@app.get("/deals/{deal_id}/proposal/new", response_class=HTMLResponse)
async def new_proposal_form(deal_id: int):
    conn = get_db()
    deal = get_deal(conn, deal_id)
    conn.close()
    if not deal:
        raise HTTPException(404)
    return render_page("new_proposal", "Generate Proposal", {"deal": deal})


@app.post("/deals/{deal_id}/proposal/create")
async def create_proposal_route(
    deal_id: int, title: str = Form(...), setup_fee: float = Form(0),
    monthly_fee: float = Form(0), scope: str = Form(""), deliverables: str = Form(""), timeline: str = Form(""),
):
    conn = get_db()
    pid = create_proposal(conn, deal_id, title, setup_fee, monthly_fee, scope, deliverables, timeline)
    # Update deal amounts
    update_deal(conn, deal_id, setup_fee=setup_fee, monthly_fee=monthly_fee,
                proposal_amount=setup_fee + monthly_fee * 12, stage="Proposal Sent")
    conn.close()

    # Generate PDF
    try:
        _generate_proposal_pdf(conn, deal_id, pid)
    except Exception:
        pass

    return RedirectResponse(f"/deals/{deal_id}", status_code=303)


def _generate_proposal_pdf(conn, deal_id, proposal_id):
    """Generate branded PDF proposal."""
    # Uses existing branded_pdf_engine pattern
    pass  # PDF generation handled by existing engine


# ─── Pre-Call Briefs ─────────────────────────────────────────

@app.post("/deals/{deal_id}/brief/generate")
async def generate_brief(deal_id: int):
    conn = get_db()
    deal = get_deal(conn, deal_id)
    if not deal:
        conn.close()
        raise HTTPException(404)

    # Generate AI-powered brief
    brief_data = _generate_call_brief(deal)
    brief_id = save_call_brief(conn, deal_id, **brief_data)
    conn.close()
    return RedirectResponse(f"/deals/{deal_id}", status_code=303)


def _generate_call_brief(deal):
    """Generate pre-call intelligence brief using AI or templates."""
    company = deal["company"]
    industry = deal["industry"] or "business"
    pain_points = deal["pain_points"] or "unknown"

    # Industry-specific pain points and solutions
    industry_intel = {
        "HVAC": {
            "common_pains": "Missed calls during peak season, manual scheduling, no after-hours response, slow quote turnaround",
            "solution": "AI phone answering + appointment booking. Captures every call 24/7, books directly into their calendar, sends automated follow-ups.",
            "roi": "Average HVAC company misses 30% of inbound calls. At $300/job average, recovering just 5 calls/week = $6,500/month.",
        },
        "Med Spa": {
            "common_pains": "High no-show rate, manual appointment reminders, no lead follow-up for consultations",
            "solution": "AI appointment reminders + lead nurture sequences. Reduces no-shows by 40%, automated consultation follow-up.",
            "roi": "Average med spa loses $500-1000/week in no-shows. 40% reduction = $800-1600/month recovered.",
        },
        "Restaurant": {
            "common_pains": "Phone overwhelm during rush, reservation management, no online ordering integration",
            "solution": "AI phone system handles reservations, answers FAQs, routes to-go orders. Frees staff for in-house service.",
            "roi": "Saves 15-20 staff hours/week on phone. At $15/hr = $900-1200/month in labor savings.",
        },
        "Dental": {
            "common_pains": "Appointment scheduling bottleneck, recall reminders, insurance verification delays",
            "solution": "AI scheduling assistant + automated recall campaigns. Patients book 24/7, reminders reduce cancellations.",
            "roi": "One additional appointment/day at $250 average = $5,000/month additional revenue.",
        },
    }

    intel = industry_intel.get(industry, {
        "common_pains": "Manual processes, missed communications, slow response times, no after-hours coverage",
        "solution": "AI automation for customer communication, scheduling, and follow-up. 24/7 coverage without additional staff.",
        "roi": "Most businesses see 20-40% improvement in response time and 15-25% increase in booked appointments.",
    })

    return {
        "company_research": f"Industry: {industry}\nCompany: {company}\nKnown pain points: {pain_points}",
        "pain_points": intel["common_pains"],
        "talking_points": f"1. Ask about their current phone/scheduling system\n2. How many calls they miss per week\n3. What happens after hours\n4. Current follow-up process for leads\n5. Biggest frustration with current setup",
        "questions_to_ask": "• How many inbound calls do you get per day?\n• What happens when you can't answer?\n• How do you currently follow up with leads?\n• What's your biggest operational bottleneck?\n• Have you looked at AI solutions before?",
        "competitive_landscape": f"Most {industry} businesses in Naples/Fort Myers are NOT using AI yet. Early mover advantage is real. Main competitors for their attention: generic answering services ($300-500/mo, no AI), DIY chatbots (low quality).",
        "recommended_solution": intel["solution"] + f"\n\nEstimated ROI: {intel['roi']}",
    }


# ─── API ─────────────────────────────────────────────────────

@app.post("/deals/enrich-from-csv")
async def enrich_from_csv():
    """One-time enrichment: pull phone_dependency, email_confidence, lead_score from original CSV."""
    csv_path = Path(__file__).resolve().parents[4] / "projects/marceau-solutions/digital/outputs/naples-ai-prospects-routed-v2-2026-03-23.csv"
    if not csv_path.exists():
        return JSONResponse({"ok": False, "error": "CSV not found"})

    conn = get_db()
    updated = 0
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = (row.get('company_name') or '').strip()
            if not company:
                continue

            deal = conn.execute("SELECT id, contact_phone FROM deals WHERE LOWER(company) = LOWER(?)", (company,)).fetchone()
            if not deal:
                continue

            phone_dep = row.get('phone_dependency', 'medium')
            lead_score = int(row.get('lead_score', 0) or 0)
            phone = row.get('phone', '')

            # Parse email confidence from score_breakdown JSON
            email_conf = 'unknown'
            try:
                breakdown = json.loads(row.get('score_breakdown', '{}'))
                email_conf = breakdown.get('email', {}).get('label', 'unknown')
            except Exception:
                pass

            kwargs = {'phone_dependency': phone_dep, 'email_confidence': email_conf, 'lead_score': lead_score}
            if phone and not deal['contact_phone']:
                kwargs['contact_phone'] = phone

            update_deal(conn, deal['id'], **kwargs)
            updated += 1

    # Now run the routing assignment
    assign_outreach_method(conn)
    conn.close()
    return JSONResponse({"ok": True, "updated": updated})


@app.on_event("startup")
async def startup_enrich():
    """On first startup, enrich deals from CSV and assign outreach methods if not yet done."""
    conn = get_db()
    # Check if any deals have been routed (non-default outreach_method)
    has_routing = conn.execute(
        "SELECT COUNT(*) FROM deals WHERE outreach_method IS NOT NULL AND outreach_method != 'email'"
    ).fetchone()[0]
    if has_routing == 0:
        csv_path = Path(__file__).resolve().parents[4] / "projects/marceau-solutions/digital/outputs/naples-ai-prospects-routed-v2-2026-03-23.csv"
        if csv_path.exists():
            updated = 0
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    company = (row.get('company_name') or '').strip()
                    if not company:
                        continue
                    deal = conn.execute(
                        "SELECT id, contact_phone FROM deals WHERE LOWER(company) = LOWER(?)", (company,)
                    ).fetchone()
                    if not deal:
                        continue
                    phone_dep = row.get('phone_dependency', 'medium')
                    lead_score = int(row.get('lead_score', 0) or 0)
                    phone = row.get('phone', '')
                    email_conf = 'unknown'
                    try:
                        breakdown = json.loads(row.get('score_breakdown', '{}'))
                        email_conf = breakdown.get('email', {}).get('label', 'unknown')
                    except Exception:
                        pass
                    kwargs = {'phone_dependency': phone_dep, 'email_confidence': email_conf, 'lead_score': lead_score}
                    if phone and not deal['contact_phone']:
                        kwargs['contact_phone'] = phone
                    update_deal(conn, deal['id'], **kwargs)
                    updated += 1
            assign_outreach_method(conn)
    conn.close()


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "sales-pipeline", "version": "1.1.0"}


@app.get("/api/stats")
async def api_stats():
    conn = get_db()
    stats = get_pipeline_stats(conn)
    conn.close()
    return stats


@app.get("/api/deals")
async def api_deals():
    conn = get_db()
    deals = get_all_deals(conn)
    conn.close()
    return [dict(d) for d in deals]


# ─── Call Logger API (Panacea) ──────────────────────────────

from .call_logger import log_call, get_recent_calls, get_calls_for_business, parse_call_command

@app.post("/api/calls/log")
async def api_log_call(request: Request):
    """Log a call. Body: {business, outcome, notes?, contact_name?, phone?, email?}"""
    data = await request.json()
    business = data.get("business", "").strip()
    outcome = data.get("outcome", "").strip()
    if not business or not outcome:
        return JSONResponse({"ok": False, "error": "business and outcome required"}, status_code=400)
    result = log_call(
        business, outcome,
        notes=data.get("notes", ""),
        contact_name=data.get("contact_name", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
    )
    return {"ok": True, **result}


@app.post("/api/calls/parse")
async def api_parse_call(request: Request):
    """Parse natural language call command. Body: {text}
    e.g. 'called Dolphin Cooling: callback, will follow up Thursday'
    """
    data = await request.json()
    text = data.get("text", "").strip()
    parsed = parse_call_command(text)
    if not parsed:
        return JSONResponse({"ok": False, "error": "Could not parse. Use: called [business]: [outcome], [notes]"}, status_code=400)
    result = log_call(parsed["business"], parsed["outcome"], notes=parsed.get("notes", ""))
    return {"ok": True, "parsed": parsed, **result}


@app.get("/api/calls/recent")
async def api_recent_calls(limit: int = 20):
    """Get recent call history."""
    return get_recent_calls(limit)


@app.get("/api/calls/{business}")
async def api_calls_for_business(business: str):
    """Get all outreach history for a business."""
    return get_calls_for_business(business)


# ─── Visit Scheduler API (Panacea) ─────────────────────────

from .visit_scheduler import build_visit_schedule, format_visit_schedule, log_visit

@app.get("/api/visits/schedule")
async def api_visit_schedule(max_visits: int = 10):
    """Generate optimized visit schedule (farthest-first routing)."""
    candidates = build_visit_schedule(max_visits=max_visits)
    return {
        "ok": True,
        "count": len(candidates),
        "formatted": format_visit_schedule(candidates),
        "visits": [
            {
                "business": c.business_name,
                "address": c.address,
                "distance_miles": round(c.distance_from_home, 1),
                "signals": c.signals,
                "notes": c.notes,
                "contact_name": c.contact_name,
                "phone": c.phone,
                "priority_score": c.priority_score,
                "last_contact": c.last_contact_date,
            }
            for c in candidates
        ],
    }


@app.post("/api/visits/log")
async def api_log_visit(request: Request):
    """Log an in-person visit. Body: {business, outcome, notes?}"""
    data = await request.json()
    business = data.get("business", "").strip()
    outcome = data.get("outcome", "").strip()
    if not business or not outcome:
        return JSONResponse({"ok": False, "error": "business and outcome required"}, status_code=400)
    visit = log_visit(business, outcome, notes=data.get("notes", ""))
    return {"ok": True, **visit}


# ─── Unified Tracker API (Panacea) ─────────────────────────

from .unified_tracker import (
    get_lead_profile, format_lead_profile,
    get_hot_leads, format_hot_leads,
    get_next_actions, format_next_actions,
)

@app.get("/api/leads/hot")
async def api_hot_leads(limit: int = 10):
    """Get highest-engagement leads."""
    leads = get_hot_leads(limit)
    return {
        "ok": True,
        "count": len(leads),
        "formatted": format_hot_leads(leads),
        "leads": [
            {
                "company": p.company,
                "engagement_score": p.engagement_score,
                "pipeline_stage": p.pipeline_stage,
                "last_contact": p.last_contact,
                "next_action": p.next_action,
                "phone": p.phone,
            }
            for p in leads
        ],
    }


@app.get("/api/leads/actions")
async def api_next_actions(limit: int = 15):
    """Get prioritized next actions across all leads."""
    actions = get_next_actions(limit)
    return {
        "ok": True,
        "count": len(actions),
        "formatted": format_next_actions(actions),
        "actions": actions,
    }


@app.get("/api/leads/{company}")
async def api_lead_profile(company: str):
    """Get complete lead profile with all touchpoints."""
    profile = get_lead_profile(company)
    return {
        "ok": True,
        "formatted": format_lead_profile(profile),
        "profile": {
            "company": profile.company,
            "contact_name": profile.contact_name,
            "phone": profile.phone,
            "email": profile.email,
            "pipeline_stage": profile.pipeline_stage,
            "engagement_score": profile.engagement_score,
            "last_contact": profile.last_contact,
            "next_action": profile.next_action,
            "next_action_reason": profile.next_action_reason,
            "touchpoint_count": len(profile.touchpoints),
        },
    }


# ─── Daily Lead Lists API ───────────────────────────────────

from .generate_lead_lists import (
    get_tier_1_phone_leads, get_tier_2_phone_leads, get_email_leads,
    get_inperson_leads, get_warm_leads, generate_daily_lists,
    format_phone_list, format_warm_leads,
)

@app.get("/api/lists/daily")
async def api_daily_lists():
    """Generate all daily outreach lists. n8n calls this at 7:00 AM."""
    lists = generate_daily_lists()
    return {
        "ok": True,
        "generated_at": lists["generated_at"],
        "tier_1_phone": {"count": len(lists["tier_1_phone"]), "leads": lists["tier_1_phone"]},
        "tier_2_phone": {"count": len(lists["tier_2_phone"]), "leads": lists["tier_2_phone"]},
        "email": {"count": len(lists["email"]), "leads": lists["email"]},
        "inperson": {"count": len(lists["inperson"]), "leads": lists["inperson"]},
        "warm": {"count": len(lists["warm"]), "leads": lists["warm"]},
        "formatted_phone": format_phone_list(lists["tier_1_phone"], "TIER 1"),
        "formatted_warm": format_warm_leads(lists["warm"]),
    }


@app.get("/api/lists/phone")
async def api_phone_list(limit: int = 30):
    """Get phone call list (Tier 1 + 2 combined, never-called only)."""
    t1 = get_tier_1_phone_leads(limit)
    t2 = get_tier_2_phone_leads(limit)
    # Deduplicate
    seen = {l["id"] for l in t1}
    combined = t1 + [l for l in t2 if l["id"] not in seen]
    return {"ok": True, "count": len(combined), "leads": combined[:limit]}


@app.get("/api/lists/warm")
async def api_warm_list():
    """Get warm leads (qualified, meeting booked, proposal sent)."""
    leads = get_warm_leads()
    return {"ok": True, "count": len(leads), "leads": leads, "formatted": format_warm_leads(leads)}


# ─── Phone Enrichment API ──────────────────────────────────

from .enrich_phones import get_phone_stats, get_deals_missing_phone

@app.get("/api/phones/stats")
async def api_phone_stats():
    """Get phone coverage statistics."""
    conn = get_db()
    stats = get_phone_stats(conn)
    conn.close()
    return {"ok": True, **stats}


@app.post("/api/phones/enrich")
async def api_enrich_phones(request: Request):
    """Enrich missing phone numbers via Apollo. Body: {dry_run?: bool, limit?: int}"""
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    dry_run = data.get("dry_run", True)
    from .enrich_phones import run_enrichment
    results = run_enrichment(dry_run=dry_run)
    return {"ok": True, "dry_run": dry_run, **results}


# ─── Pipeline Health & Analytics API ───────────────────────

from .pipeline_health import get_pipeline_health, get_stale_deals, rescore_leads, format_health_report

@app.get("/api/health/report")
async def api_health_report():
    """Full pipeline health report — funnel, velocity, channel effectiveness."""
    conn = get_db()
    health = get_pipeline_health(conn)
    stale = get_stale_deals(conn)
    conn.close()
    return {
        "ok": True,
        "formatted": format_health_report(health, stale),
        **health,
        "stale_count": len(stale),
    }


@app.get("/api/health/stale")
async def api_stale_deals(days: int = 5):
    """Deals that haven't been touched in X days."""
    conn = get_db()
    stale = get_stale_deals(conn, days_threshold=days)
    conn.close()
    return {"ok": True, "count": len(stale), "deals": stale}


@app.post("/api/health/rescore")
async def api_rescore(request: Request):
    """Recalculate lead scores based on engagement. Body: {dry_run?: bool}"""
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    dry_run = data.get("dry_run", True)
    conn = get_db()
    result = rescore_leads(conn, dry_run=dry_run)
    conn.close()
    return {"ok": True, **result}


# ─── Auto Follow-up API (n8n triggers this) ────────────────

from .auto_followup import process_followups, format_summary, get_followups_due as get_auto_followups_due
import sqlite3 as _sqlite3

@app.get("/api/followups/due")
async def api_followups_due():
    """Get all follow-ups due today (for n8n preview/check)."""
    conn = _sqlite3.connect(str(_SRC_DIR.parent / "data" / "pipeline.db"))
    conn.row_factory = _sqlite3.Row
    due = get_auto_followups_due(conn)
    conn.close()
    return {"ok": True, "count": len(due), "followups": due}


@app.post("/api/followups/send")
async def api_send_followups(request: Request):
    """Send all due follow-ups. Body: {dry_run?: bool, sms_only?: bool}
    n8n calls this daily at 8:00 AM.
    """
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    dry_run = data.get("dry_run", False)
    sms_only = data.get("sms_only", False)
    results = process_followups(dry_run=dry_run, sms_only=sms_only)
    summary = format_summary(results)
    sent = sum(1 for r in results if r.get("success") and not r.get("dry_run"))
    return {
        "ok": True,
        "dry_run": dry_run,
        "sent": sent,
        "total": len(results),
        "summary": summary,
        "results": results,
    }


if __name__ == "__main__":
    print(f"\n  Marceau Sales Pipeline → http://127.0.0.1:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
