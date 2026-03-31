#!/usr/bin/env python3
"""
UNIFIED OUTREACH LOGGER

This is the ONLY way to log outreach. All steps happen together or none happen.

Usage:
    from execution.log_outreach import log_outreach
    
    result = log_outreach(
        company="ABC Company",
        channel="Call",
        outcome="Spoke with owner, interested in demo",
        stage="Qualified",  # optional - auto-determines if not provided
        contact_name="John Smith",  # optional
        follow_up_days=3,  # optional, default based on outcome
    )
    
    print(result['proof'])  # Human-readable proof for Telegram

CLI:
    python -m execution.log_outreach --company "ABC Company" --channel Call --outcome "Left voicemail"
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Paths
DB_PATH = '/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/pipeline.db'
SHEET_ID_FILE = '/home/clawdbot/dev-sandbox/config/pipeline_sheet_id.txt'
TOKEN_PATH = '/home/clawdbot/dev-sandbox/token_sheets.json'


def determine_stage(outcome: str, current_stage: str) -> str:
    """Determine the appropriate stage based on outcome text."""
    outcome_lower = outcome.lower()
    
    # Hard no indicators → Closed Lost
    if any(x in outcome_lower for x in ['hung up', 'hard no', 'not interested', 'no solicitation', 'don\'t call', 'do not contact']):
        return 'Closed Lost'
    
    # Interest indicators → Qualified
    if any(x in outcome_lower for x in ['interested', 'wants demo', 'scheduled', 'booked', 'send proposal']):
        return 'Qualified'
    
    # Meeting booked
    if any(x in outcome_lower for x in ['meeting booked', 'demo scheduled', 'call scheduled']):
        return 'Meeting Booked'
    
    # Keep current stage if contacted, otherwise move to Contacted
    if current_stage in ['Qualified', 'Meeting Booked', 'Proposal Sent', 'Trial Active', 'Closed Won']:
        return current_stage
    
    return 'Contacted'


def determine_follow_up_days(outcome: str, stage: str) -> Optional[int]:
    """Determine follow-up days based on outcome."""
    outcome_lower = outcome.lower()
    
    # No follow-up for closed
    if stage == 'Closed Lost':
        return None
    
    # Voicemail → 3 days
    if 'voicemail' in outcome_lower:
        return 3
    
    # Took number/will pass along → 4-5 days
    if any(x in outcome_lower for x in ['took number', 'pass along', 'will forward', 'leave a message']):
        return 4
    
    # Interested but not ready → 30 days
    if 'not ready' in outcome_lower or 'nurture' in outcome_lower:
        return 30
    
    # Soft no → 60 days
    if 'soft no' in outcome_lower:
        return 60
    
    # Default for contacted → 3 days
    if stage == 'Contacted':
        return 3
    
    # Qualified → 2 days (hot lead)
    if stage == 'Qualified':
        return 2
    
    return 3


def sync_to_sheet(deal_id: int) -> bool:
    """Sync a single deal to Google Sheet."""
    try:
        # Import here to avoid dependency issues
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        if not os.path.exists(SHEET_ID_FILE) or not os.path.exists(TOKEN_PATH):
            return False
        
        with open(SHEET_ID_FILE, 'r') as f:
            sheet_id = f.read().strip()
        
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, ['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=creds)
        
        # Get deal data
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                d.id, d.company, d.contact_name, d.contact_phone, d.contact_email,
                d.industry, d.city, d.state, d.stage, d.tier, d.lead_score,
                d.next_action, d.next_action_date, d.notes, d.created_at, d.updated_at,
                (SELECT channel FROM outreach_log WHERE deal_id = d.id ORDER BY created_at DESC LIMIT 1) as last_channel,
                (SELECT created_at FROM outreach_log WHERE deal_id = d.id ORDER BY created_at DESC LIMIT 1) as last_contact,
                (SELECT response FROM outreach_log WHERE deal_id = d.id ORDER BY created_at DESC LIMIT 1) as last_response
            FROM deals d WHERE d.id = ?
        """, (deal_id,))
        
        r = cur.fetchone()
        conn.close()
        
        if not r:
            return False
        
        response_status = 'No Response'
        if r['last_response']:
            response_status = 'Responded'
        elif r['stage'] == 'Qualified':
            response_status = 'Interested'
        elif r['stage'] == 'Closed Lost':
            response_status = 'Closed'
        
        row_data = [[
            r['id'], r['company'] or '', r['contact_name'] or '', r['contact_phone'] or '',
            r['contact_email'] or '', r['industry'] or '', r['city'] or '', r['state'] or '',
            r['stage'] or '', r['tier'] or '', r['lead_score'] or '', r['last_channel'] or '',
            r['last_contact'] or '', response_status, r['next_action'] or '',
            r['next_action_date'] or '', (r['notes'] or '')[:500], r['created_at'] or '', r['updated_at'] or ''
        ]]
        
        # Find row in sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range='All Leads!A:A'
        ).execute()
        
        values = result.get('values', [])
        row_num = None
        for i, row in enumerate(values):
            if row and str(row[0]) == str(deal_id):
                row_num = i + 1
                break
        
        if row_num:
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'All Leads!A{row_num}:S{row_num}',
                valueInputOption='RAW',
                body={'values': row_data}
            ).execute()
        else:
            service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range='All Leads!A:S',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': row_data}
            ).execute()
        
        return True
    except Exception as e:
        print(f"Sheet sync warning: {e}", file=sys.stderr)
        return False


def log_outreach(
    company: str,
    channel: str,
    outcome: str,
    stage: Optional[str] = None,
    contact_name: Optional[str] = None,
    follow_up_days: Optional[int] = None,
    response_type: Optional[str] = None,
) -> dict:
    """
    Log outreach with ALL required steps. Returns proof or raises exception.
    
    Args:
        company: Company name (partial match OK)
        channel: Call, Email, SMS, In-Person, etc.
        outcome: What happened (e.g., "Left voicemail", "Spoke with owner, interested")
        stage: Optional override for stage (auto-determined if not provided)
        contact_name: Optional contact name update
        follow_up_days: Optional override for follow-up (auto-determined if not provided)
        response_type: Optional response categorization (interested, rejected, voicemail, etc.)
    
    Returns:
        dict with: deal_id, company, stage, follow_up, outreach_id, sheet_synced, proof
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    try:
        # 1. Find the deal
        cur.execute("SELECT * FROM deals WHERE company LIKE ?", (f"%{company}%",))
        deal = cur.fetchone()
        
        if not deal:
            raise ValueError(f"Company not found: {company}")
        
        deal_id = deal['id']
        current_stage = deal['stage']
        
        # 2. Determine stage and follow-up
        new_stage = stage or determine_stage(outcome, current_stage)
        
        if follow_up_days is None:
            follow_up_days = determine_follow_up_days(outcome, new_stage)
        
        follow_up_date = None
        if follow_up_days and new_stage != 'Closed Lost':
            follow_up_date = (datetime.now() + timedelta(days=follow_up_days)).strftime('%Y-%m-%d')
        
        # 3. Determine response type for outreach_log
        if not response_type:
            outcome_lower = outcome.lower()
            if 'voicemail' in outcome_lower:
                response_type = 'voicemail'
            elif any(x in outcome_lower for x in ['hung up', 'hard no', 'not interested']):
                response_type = 'rejected'
            elif any(x in outcome_lower for x in ['interested', 'warm', 'demo']):
                response_type = 'interested'
            elif any(x in outcome_lower for x in ['took number', 'pass along', 'forward']):
                response_type = 'gatekeeper_positive'
            elif 'not ready' in outcome_lower:
                response_type = 'nurture'
        
        # 4. Update deals table
        note_entry = f"[{timestamp}] {channel.upper()}: {outcome}"
        
        update_fields = {
            'notes': (deal['notes'] or '') + ' | ' + note_entry if deal['notes'] else note_entry,
            'stage': new_stage,
            'updated_at': datetime.now().isoformat(),
        }
        
        if contact_name:
            update_fields['contact_name'] = contact_name
        
        if new_stage == 'Closed Lost':
            update_fields['next_action'] = 'DO NOT CONTACT'
            update_fields['next_action_date'] = None
        elif follow_up_date:
            update_fields['next_action'] = 'Follow up'
            update_fields['next_action_date'] = follow_up_date
        
        set_clause = ', '.join(f"{k} = ?" for k in update_fields.keys())
        cur.execute(
            f"UPDATE deals SET {set_clause} WHERE id = ?",
            list(update_fields.values()) + [deal_id]
        )
        
        # 5. Insert into outreach_log
        cur.execute("""
            INSERT INTO outreach_log (deal_id, company, contact, channel, message_summary, response, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (deal_id, deal['company'], contact_name or deal['contact_name'], channel, outcome[:500], response_type, datetime.now().isoformat()))
        
        outreach_id = cur.lastrowid
        
        # 6. Commit transaction
        conn.commit()
        
        # 7. Sync to Google Sheet (non-blocking)
        sheet_synced = sync_to_sheet(deal_id)
        
        # 8. Build proof
        proof = f"""{'='*50}
✅ LOGGED — {deal['company']}
{'='*50}
Record ID:    {deal_id}
Outreach ID:  {outreach_id}
Channel:      {channel}
Stage:        {current_stage} → {new_stage}
Follow-up:    {follow_up_date or 'None'}
Sheet Synced: {'Yes' if sheet_synced else 'No'}
{'='*50}"""
        
        return {
            'deal_id': deal_id,
            'outreach_id': outreach_id,
            'company': deal['company'],
            'stage': new_stage,
            'previous_stage': current_stage,
            'follow_up': follow_up_date,
            'sheet_synced': sheet_synced,
            'proof': proof,
        }
        
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_call(company: str, outcome: str, contact_name: Optional[str] = None, **kwargs) -> dict:
    """Convenience wrapper for logging calls."""
    return log_outreach(company=company, channel='Call', outcome=outcome, contact_name=contact_name, **kwargs)


def log_voicemail(company: str, contact_name: Optional[str] = None) -> dict:
    """Convenience wrapper for logging voicemails."""
    return log_outreach(
        company=company, 
        channel='Call', 
        outcome='Left voicemail',
        contact_name=contact_name,
        response_type='voicemail',
        follow_up_days=3
    )


def log_email(company: str, outcome: str, contact_name: Optional[str] = None, **kwargs) -> dict:
    """Convenience wrapper for logging emails."""
    return log_outreach(company=company, channel='Email', outcome=outcome, contact_name=contact_name, **kwargs)


def log_visit(company: str, outcome: str, contact_name: Optional[str] = None, **kwargs) -> dict:
    """Convenience wrapper for logging in-person visits."""
    return log_outreach(company=company, channel='In-Person', outcome=outcome, contact_name=contact_name, **kwargs)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Log outreach (unified)")
    parser.add_argument("--company", "-c", required=True, help="Company name")
    parser.add_argument("--channel", default="Call", help="Channel: Call, Email, SMS, In-Person")
    parser.add_argument("--outcome", "-o", required=True, help="What happened")
    parser.add_argument("--contact", help="Contact name")
    parser.add_argument("--stage", help="Override stage")
    parser.add_argument("--follow-up", type=int, help="Follow-up days")
    
    args = parser.parse_args()
    
    try:
        result = log_outreach(
            company=args.company,
            channel=args.channel,
            outcome=args.outcome,
            contact_name=args.contact,
            stage=args.stage,
            follow_up_days=args.follow_up,
        )
        print(result['proof'])
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
