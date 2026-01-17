#!/usr/bin/env python3
"""
client_db.py - Client Database for Elder Tech Concierge

WHAT: SQLite database for storing client configurations
WHY: Enable pre-configured deployment via unique setup URLs

TABLES:
- clients: Client profiles and subscription status
- contacts: Client contacts (emergency and family)
- preferences: Client preferences (speech rate, font size, etc.)
- activity_log: Track client interactions for monitoring

USAGE:
    from client_db import ClientDB

    db = ClientDB()

    # Create new client
    client_id = db.create_client(
        name="Dorothy Smith",
        email="dorothy@email.com",
        emergency_contacts=[{"name": "John Smith", "phone": "+1234567890", "relationship": "Son"}],
        family_contacts=[{"name": "Mary Smith", "phone": "+0987654321", "relationship": "Daughter"}]
    )

    # Get client by ID (for /setup/{client_id} endpoint)
    client = db.get_client(client_id)

    # Update client contacts
    db.update_contacts(client_id, family_contacts=[...])
"""

import sqlite3
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Contact:
    """Contact information."""
    name: str
    phone: str
    relationship: str
    email: Optional[str] = None
    is_emergency: bool = False


@dataclass
class ClientPreferences:
    """Client preferences for the app."""
    speech_rate: float = 1.0
    voice_volume: float = 1.0
    font_size: str = "large"  # small, medium, large, xlarge
    high_contrast: bool = False
    button_vibration: bool = True


@dataclass
class Client:
    """Client profile."""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    emergency_contacts: List[Contact]
    family_contacts: List[Contact]
    preferences: ClientPreferences
    subscription_status: str  # trial, active, expired, cancelled
    subscription_tier: str  # basic, standard, premium
    subscription_end: Optional[str]
    created_at: str
    updated_at: str
    last_active: Optional[str]
    setup_completed: bool
    notes: Optional[str]


# ============================================================================
# DATABASE CLASS
# ============================================================================

class ClientDB:
    """Client database operations."""

    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if db_path is None:
            # Default to data directory in project
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "clients.db")

        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                subscription_status TEXT DEFAULT 'trial',
                subscription_tier TEXT DEFAULT 'basic',
                subscription_end TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_active TEXT,
                setup_completed INTEGER DEFAULT 0,
                notes TEXT
            )
        """)

        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                relationship TEXT,
                is_emergency INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                client_id TEXT PRIMARY KEY,
                speech_rate REAL DEFAULT 1.0,
                voice_volume REAL DEFAULT 1.0,
                font_size TEXT DEFAULT 'large',
                high_contrast INTEGER DEFAULT 0,
                button_vibration INTEGER DEFAULT 1,
                custom_settings TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Activity log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_client ON contacts(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_client ON activity_log(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)")

        conn.commit()
        conn.close()

    # ========================================================================
    # CLIENT CRUD OPERATIONS
    # ========================================================================

    def create_client(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        emergency_contacts: Optional[List[Dict]] = None,
        family_contacts: Optional[List[Dict]] = None,
        preferences: Optional[Dict] = None,
        subscription_tier: str = "basic",
        notes: Optional[str] = None
    ) -> str:
        """
        Create a new client.

        Returns:
            client_id: Unique identifier for the client
        """
        client_id = str(uuid.uuid4())[:8]  # Short ID for easier URLs
        now = datetime.now().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert client
            cursor.execute("""
                INSERT INTO clients (id, name, email, phone, subscription_tier,
                                   created_at, updated_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (client_id, name, email, phone, subscription_tier, now, now, notes))

            # Insert emergency contacts
            if emergency_contacts:
                for contact in emergency_contacts:
                    cursor.execute("""
                        INSERT INTO contacts (client_id, name, phone, email,
                                            relationship, is_emergency)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (client_id, contact['name'], contact['phone'],
                          contact.get('email'), contact.get('relationship')))

            # Insert family contacts
            if family_contacts:
                for contact in family_contacts:
                    cursor.execute("""
                        INSERT INTO contacts (client_id, name, phone, email,
                                            relationship, is_emergency)
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (client_id, contact['name'], contact['phone'],
                          contact.get('email'), contact.get('relationship')))

            # Insert preferences
            prefs = preferences or {}
            cursor.execute("""
                INSERT INTO preferences (client_id, speech_rate, voice_volume,
                                       font_size, high_contrast, button_vibration)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (client_id,
                  prefs.get('speech_rate', 1.0),
                  prefs.get('voice_volume', 1.0),
                  prefs.get('font_size', 'large'),
                  prefs.get('high_contrast', False),
                  prefs.get('button_vibration', True)))

            # Log activity
            cursor.execute("""
                INSERT INTO activity_log (client_id, action, details)
                VALUES (?, 'client_created', ?)
            """, (client_id, json.dumps({'name': name, 'tier': subscription_tier})))

            conn.commit()
            return client_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_client(self, client_id: str) -> Optional[Client]:
        """
        Get client by ID.

        Returns:
            Client object or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get client
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Get contacts
        cursor.execute("""
            SELECT * FROM contacts WHERE client_id = ? ORDER BY is_emergency DESC, name
        """, (client_id,))
        contact_rows = cursor.fetchall()

        emergency_contacts = []
        family_contacts = []
        for c in contact_rows:
            contact = Contact(
                name=c['name'],
                phone=c['phone'],
                email=c['email'],
                relationship=c['relationship'],
                is_emergency=bool(c['is_emergency'])
            )
            if c['is_emergency']:
                emergency_contacts.append(contact)
            else:
                family_contacts.append(contact)

        # Get preferences
        cursor.execute("SELECT * FROM preferences WHERE client_id = ?", (client_id,))
        pref_row = cursor.fetchone()

        preferences = ClientPreferences(
            speech_rate=pref_row['speech_rate'] if pref_row else 1.0,
            voice_volume=pref_row['voice_volume'] if pref_row else 1.0,
            font_size=pref_row['font_size'] if pref_row else 'large',
            high_contrast=bool(pref_row['high_contrast']) if pref_row else False,
            button_vibration=bool(pref_row['button_vibration']) if pref_row else True
        )

        conn.close()

        return Client(
            id=row['id'],
            name=row['name'],
            email=row['email'],
            phone=row['phone'],
            emergency_contacts=emergency_contacts,
            family_contacts=family_contacts,
            preferences=preferences,
            subscription_status=row['subscription_status'],
            subscription_tier=row['subscription_tier'],
            subscription_end=row['subscription_end'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_active=row['last_active'],
            setup_completed=bool(row['setup_completed']),
            notes=row['notes']
        )

    def get_client_config(self, client_id: str) -> Optional[Dict]:
        """
        Get client configuration for the setup endpoint.

        Returns JSON-serializable dict for the app to consume.
        """
        client = self.get_client(client_id)
        if not client:
            return None

        return {
            'client_id': client.id,
            'client_name': client.name,
            'emergency_contacts': [asdict(c) for c in client.emergency_contacts],
            'family_contacts': [asdict(c) for c in client.family_contacts],
            'preferences': asdict(client.preferences),
            'subscription_tier': client.subscription_tier
        }

    def list_clients(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        List all clients (for admin dashboard).
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.*,
                   (SELECT COUNT(*) FROM contacts WHERE client_id = c.id AND is_emergency = 1) as emergency_count,
                   (SELECT COUNT(*) FROM contacts WHERE client_id = c.id AND is_emergency = 0) as family_count
            FROM clients c
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_client(self, client_id: str, **kwargs) -> bool:
        """
        Update client fields.

        Valid kwargs: name, email, phone, subscription_status, subscription_tier,
                     subscription_end, setup_completed, notes
        """
        valid_fields = {'name', 'email', 'phone', 'subscription_status',
                       'subscription_tier', 'subscription_end', 'setup_completed', 'notes'}

        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return False

        updates['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [client_id]

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(f"UPDATE clients SET {set_clause} WHERE id = ?", values)

        # Log activity
        cursor.execute("""
            INSERT INTO activity_log (client_id, action, details)
            VALUES (?, 'client_updated', ?)
        """, (client_id, json.dumps(kwargs)))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def update_contacts(
        self,
        client_id: str,
        emergency_contacts: Optional[List[Dict]] = None,
        family_contacts: Optional[List[Dict]] = None
    ) -> bool:
        """
        Update client contacts (replaces existing).
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if emergency_contacts is not None:
                # Remove existing emergency contacts
                cursor.execute("""
                    DELETE FROM contacts WHERE client_id = ? AND is_emergency = 1
                """, (client_id,))

                # Add new emergency contacts
                for contact in emergency_contacts:
                    cursor.execute("""
                        INSERT INTO contacts (client_id, name, phone, email,
                                            relationship, is_emergency)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (client_id, contact['name'], contact['phone'],
                          contact.get('email'), contact.get('relationship')))

            if family_contacts is not None:
                # Remove existing family contacts
                cursor.execute("""
                    DELETE FROM contacts WHERE client_id = ? AND is_emergency = 0
                """, (client_id,))

                # Add new family contacts
                for contact in family_contacts:
                    cursor.execute("""
                        INSERT INTO contacts (client_id, name, phone, email,
                                            relationship, is_emergency)
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (client_id, contact['name'], contact['phone'],
                          contact.get('email'), contact.get('relationship')))

            # Update timestamp
            cursor.execute("""
                UPDATE clients SET updated_at = ? WHERE id = ?
            """, (datetime.now().isoformat(), client_id))

            # Log activity
            cursor.execute("""
                INSERT INTO activity_log (client_id, action, details)
                VALUES (?, 'contacts_updated', ?)
            """, (client_id, json.dumps({
                'emergency_count': len(emergency_contacts) if emergency_contacts else 0,
                'family_count': len(family_contacts) if family_contacts else 0
            })))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def update_preferences(self, client_id: str, **kwargs) -> bool:
        """
        Update client preferences.
        """
        valid_fields = {'speech_rate', 'voice_volume', 'font_size',
                       'high_contrast', 'button_vibration'}

        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if preferences exist
        cursor.execute("SELECT 1 FROM preferences WHERE client_id = ?", (client_id,))
        exists = cursor.fetchone()

        if exists:
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [client_id]
            cursor.execute(f"UPDATE preferences SET {set_clause} WHERE client_id = ?", values)
        else:
            columns = ['client_id'] + list(updates.keys())
            placeholders = ', '.join(['?'] * len(columns))
            values = [client_id] + list(updates.values())
            cursor.execute(f"""
                INSERT INTO preferences ({', '.join(columns)}) VALUES ({placeholders})
            """, values)

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_client(self, client_id: str) -> bool:
        """
        Delete a client and all associated data.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM activity_log WHERE client_id = ?", (client_id,))
            cursor.execute("DELETE FROM preferences WHERE client_id = ?", (client_id,))
            cursor.execute("DELETE FROM contacts WHERE client_id = ?", (client_id,))
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ========================================================================
    # ACTIVITY TRACKING
    # ========================================================================

    def log_activity(self, client_id: str, action: str, details: Optional[Dict] = None):
        """Log client activity."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO activity_log (client_id, action, details)
            VALUES (?, ?, ?)
        """, (client_id, action, json.dumps(details) if details else None))

        # Update last_active
        cursor.execute("""
            UPDATE clients SET last_active = ? WHERE id = ?
        """, (datetime.now().isoformat(), client_id))

        conn.commit()
        conn.close()

    def get_activity(self, client_id: str, limit: int = 50) -> List[Dict]:
        """Get recent activity for a client."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM activity_log
            WHERE client_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (client_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get database statistics for admin dashboard."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total clients
        cursor.execute("SELECT COUNT(*) as count FROM clients")
        stats['total_clients'] = cursor.fetchone()['count']

        # By subscription status
        cursor.execute("""
            SELECT subscription_status, COUNT(*) as count
            FROM clients
            GROUP BY subscription_status
        """)
        stats['by_status'] = {row['subscription_status']: row['count']
                             for row in cursor.fetchall()}

        # By tier
        cursor.execute("""
            SELECT subscription_tier, COUNT(*) as count
            FROM clients
            GROUP BY subscription_tier
        """)
        stats['by_tier'] = {row['subscription_tier']: row['count']
                          for row in cursor.fetchall()}

        # Active in last 24h
        cursor.execute("""
            SELECT COUNT(*) as count FROM clients
            WHERE last_active > datetime('now', '-1 day')
        """)
        stats['active_24h'] = cursor.fetchone()['count']

        # Setup completion rate
        cursor.execute("""
            SELECT
                SUM(CASE WHEN setup_completed = 1 THEN 1 ELSE 0 END) as completed,
                COUNT(*) as total
            FROM clients
        """)
        row = cursor.fetchone()
        stats['setup_completion'] = {
            'completed': row['completed'],
            'total': row['total'],
            'rate': round(row['completed'] / row['total'] * 100, 1) if row['total'] > 0 else 0
        }

        conn.close()
        return stats


# ============================================================================
# CLI for testing
# ============================================================================

if __name__ == '__main__':
    import sys

    db = ClientDB()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'create-test':
            # Create a test client
            client_id = db.create_client(
                name="Dorothy Smith",
                email="dorothy@example.com",
                phone="+15551234567",
                emergency_contacts=[
                    {"name": "John Smith", "phone": "+15559876543", "relationship": "Son"},
                ],
                family_contacts=[
                    {"name": "Mary Smith", "phone": "+15555555555", "relationship": "Daughter"},
                    {"name": "Bob Smith", "phone": "+15556666666", "relationship": "Grandson"},
                ],
                preferences={"font_size": "xlarge", "high_contrast": True},
                subscription_tier="standard",
                notes="Test client for development"
            )
            print(f"Created test client: {client_id}")
            print(f"Setup URL: /setup/{client_id}")

        elif command == 'list':
            clients = db.list_clients()
            print(f"\nFound {len(clients)} clients:\n")
            for c in clients:
                print(f"  [{c['id']}] {c['name']} - {c['subscription_tier']} ({c['subscription_status']})")
                print(f"           Contacts: {c['emergency_count']} emergency, {c['family_count']} family")

        elif command == 'stats':
            stats = db.get_stats()
            print("\nDatabase Statistics:")
            print(f"  Total clients: {stats['total_clients']}")
            print(f"  Active (24h): {stats['active_24h']}")
            print(f"  By status: {stats['by_status']}")
            print(f"  By tier: {stats['by_tier']}")
            print(f"  Setup completion: {stats['setup_completion']['rate']}%")

        elif command == 'get' and len(sys.argv) > 2:
            client_id = sys.argv[2]
            client = db.get_client(client_id)
            if client:
                print(f"\nClient: {client.name}")
                print(f"  ID: {client.id}")
                print(f"  Email: {client.email}")
                print(f"  Tier: {client.subscription_tier}")
                print(f"  Status: {client.subscription_status}")
                print(f"  Emergency contacts: {len(client.emergency_contacts)}")
                for c in client.emergency_contacts:
                    print(f"    - {c.name} ({c.relationship}): {c.phone}")
                print(f"  Family contacts: {len(client.family_contacts)}")
                for c in client.family_contacts:
                    print(f"    - {c.name} ({c.relationship}): {c.phone}")
            else:
                print(f"Client {client_id} not found")

        else:
            print("Usage: python client_db.py [create-test|list|stats|get <id>]")
    else:
        print("Elder Tech Client Database")
        print("Usage: python client_db.py [create-test|list|stats|get <id>]")
