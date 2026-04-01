#!/usr/bin/env python3
"""BoabFit Lead Database - SQLite storage for lead nurturing"""
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "leads.db"

def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            phone TEXT,
            committed TEXT,
            source TEXT DEFAULT '6week-landing',
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Email sequence tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            template TEXT NOT NULL,
            scheduled_for TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    
    # Sent emails log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            template TEXT NOT NULL,
            subject TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent',
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def add_lead(email, name=None, phone=None, committed=None, source='6week-landing'):
    """Add a new lead and schedule their email sequence"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Insert lead
        cursor.execute('''
            INSERT INTO leads (email, name, phone, committed, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, name, phone, committed, source))
        lead_id = cursor.lastrowid
        
        # Schedule email sequence
        now = datetime.now()
        sequence = [
            ('day1_getting_started', 24),   # 24 hours
            ('day3_checkin', 72),            # 72 hours  
            ('day7_motivation', 168),        # 7 days
            ('day14_halfway', 336),          # 14 days
        ]
        
        for template, hours in sequence:
            scheduled = now + timedelta(hours=hours)
            cursor.execute('''
                INSERT INTO email_queue (lead_id, template, scheduled_for)
                VALUES (?, ?, ?)
            ''', (lead_id, template, scheduled))
        
        conn.commit()
        print(f"Added lead {lead_id}: {email} with {len(sequence)} scheduled emails")
        return lead_id
        
    except sqlite3.IntegrityError:
        print(f"Lead already exists: {email}")
        return None
    finally:
        conn.close()

def get_due_emails():
    """Get emails that are due to be sent"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT eq.id, eq.lead_id, eq.template, eq.scheduled_for,
               l.email, l.name
        FROM email_queue eq
        JOIN leads l ON eq.lead_id = l.id
        WHERE eq.status = 'pending'
        AND eq.scheduled_for <= datetime('now')
        ORDER BY eq.scheduled_for
    ''')
    
    emails = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return emails

def mark_email_sent(queue_id, subject=''):
    """Mark an email as sent"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get email details
    cursor.execute('SELECT lead_id, template FROM email_queue WHERE id = ?', (queue_id,))
    row = cursor.fetchone()
    if row:
        # Update queue status
        cursor.execute('''
            UPDATE email_queue 
            SET status = 'sent', sent_at = datetime('now')
            WHERE id = ?
        ''', (queue_id,))
        
        # Log sent email
        cursor.execute('''
            INSERT INTO sent_emails (lead_id, template, subject)
            VALUES (?, ?, ?)
        ''', (row['lead_id'], row['template'], subject))
        
        conn.commit()
    conn.close()

def get_lead_stats():
    """Get lead statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM leads')
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as pending FROM email_queue WHERE status = 'pending'")
    pending = cursor.fetchone()['pending']
    
    cursor.execute("SELECT COUNT(*) as sent FROM sent_emails")
    sent = cursor.fetchone()['sent']
    
    conn.close()
    return {'total_leads': total, 'pending_emails': pending, 'sent_emails': sent}

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_db()
    elif len(sys.argv) > 1 and sys.argv[1] == 'stats':
        stats = get_lead_stats()
        print(f"Total leads: {stats['total_leads']}")
        print(f"Pending emails: {stats['pending_emails']}")
        print(f"Sent emails: {stats['sent_emails']}")
    else:
        print("Usage: lead_db.py [init|stats]")
