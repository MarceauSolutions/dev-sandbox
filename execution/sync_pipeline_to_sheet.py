#!/usr/bin/env python3
"""
Pipeline to Google Sheet Sync

Syncs the pipeline.db database to the master Google Sheet.
Run after any pipeline changes or on a schedule.

Usage:
    python sync_pipeline_to_sheet.py           # Full sync
    python sync_pipeline_to_sheet.py --deal 42 # Sync single deal
"""

import sqlite3
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Config
DB_PATH = '/home/clawdbot/dev-sandbox/projects/shared/sales-pipeline/data/pipeline.db'
SHEET_ID_FILE = '/home/clawdbot/dev-sandbox/config/pipeline_sheet_id.txt'
TOKEN_PATH = '/home/clawdbot/dev-sandbox/token_sheets.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheet_service():
    """Initialize Google Sheets service."""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build('sheets', 'v4', credentials=creds)


def get_sheet_id():
    """Get the sheet ID from config."""
    with open(SHEET_ID_FILE, 'r') as f:
        return f.read().strip()


def get_all_deals():
    """Get all deals from database with outreach info."""
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
        FROM deals d
        ORDER BY 
            CASE d.stage 
                WHEN 'Qualified' THEN 1
                WHEN 'Meeting Booked' THEN 2
                WHEN 'Proposal Sent' THEN 3
                WHEN 'Contacted' THEN 4
                WHEN 'Intake' THEN 5
                ELSE 6
            END,
            d.lead_score DESC NULLS LAST
    """)
    
    rows = []
    for r in cur.fetchall():
        response_status = 'No Response'
        if r['last_response']:
            response_status = 'Responded'
        elif r['stage'] == 'Qualified':
            response_status = 'Interested'
        elif r['stage'] == 'Closed Lost':
            response_status = 'Closed'
        
        rows.append([
            r['id'],
            r['company'] or '',
            r['contact_name'] or '',
            r['contact_phone'] or '',
            r['contact_email'] or '',
            r['industry'] or '',
            r['city'] or '',
            r['state'] or '',
            r['stage'] or '',
            r['tier'] or '',
            r['lead_score'] or '',
            r['last_channel'] or '',
            r['last_contact'] or '',
            response_status,
            r['next_action'] or '',
            r['next_action_date'] or '',
            (r['notes'] or '')[:500],
            r['created_at'] or '',
            r['updated_at'] or ''
        ])
    
    conn.close()
    return rows


def full_sync():
    """Full sync of all deals to sheet."""
    print("🔄 Starting full sync...")
    
    service = get_sheet_service()
    sheet_id = get_sheet_id()
    
    # Get all deals
    rows = get_all_deals()
    print(f"   Found {len(rows)} deals in database")
    
    # Clear existing data (except header)
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range='All Leads!A2:S1000'
    ).execute()
    
    # Write new data
    if rows:
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f'All Leads!A2:S{len(rows)+1}',
            valueInputOption='RAW',
            body={'values': rows}
        ).execute()
    
    print(f"✅ Synced {len(rows)} deals to Google Sheet")
    return len(rows)


def sync_single_deal(deal_id: int):
    """Update a single deal in the sheet (finds and updates the row)."""
    print(f"🔄 Syncing deal {deal_id}...")
    
    service = get_sheet_service()
    sheet_id = get_sheet_id()
    
    # Get current sheet data to find the row
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='All Leads!A:A'
    ).execute()
    
    values = result.get('values', [])
    row_num = None
    for i, row in enumerate(values):
        if row and str(row[0]) == str(deal_id):
            row_num = i + 1
            break
    
    # Get the deal data
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
        FROM deals d
        WHERE d.id = ?
    """, (deal_id,))
    
    r = cur.fetchone()
    conn.close()
    
    if not r:
        print(f"   Deal {deal_id} not found in database")
        return False
    
    response_status = 'No Response'
    if r['last_response']:
        response_status = 'Responded'
    elif r['stage'] == 'Qualified':
        response_status = 'Interested'
    elif r['stage'] == 'Closed Lost':
        response_status = 'Closed'
    
    row_data = [[
        r['id'],
        r['company'] or '',
        r['contact_name'] or '',
        r['contact_phone'] or '',
        r['contact_email'] or '',
        r['industry'] or '',
        r['city'] or '',
        r['state'] or '',
        r['stage'] or '',
        r['tier'] or '',
        r['lead_score'] or '',
        r['last_channel'] or '',
        r['last_contact'] or '',
        response_status,
        r['next_action'] or '',
        r['next_action_date'] or '',
        (r['notes'] or '')[:500],
        r['created_at'] or '',
        r['updated_at'] or ''
    ]]
    
    if row_num:
        # Update existing row
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f'All Leads!A{row_num}:S{row_num}',
            valueInputOption='RAW',
            body={'values': row_data}
        ).execute()
        print(f"✅ Updated deal {deal_id} at row {row_num}")
    else:
        # Append new row
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range='All Leads!A:S',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': row_data}
        ).execute()
        print(f"✅ Added deal {deal_id} as new row")
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync pipeline to Google Sheet")
    parser.add_argument("--deal", "-d", type=int, help="Sync single deal by ID")
    args = parser.parse_args()
    
    if args.deal:
        sync_single_deal(args.deal)
    else:
        full_sync()
