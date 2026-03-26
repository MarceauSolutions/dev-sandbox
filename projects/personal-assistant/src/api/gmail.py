#!/usr/bin/env python3
"""
Personal Assistant Gmail API
Handles email operations for the personal assistant tower.
"""

import os
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask import Blueprint, request, jsonify

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# Blueprint for Gmail API
gmail_bp = Blueprint('gmail', __name__, url_prefix='/api/gmail')

class GmailService:
    """Gmail service abstraction for personal assistant."""

    def __init__(self):
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Gmail API service."""
        creds = None
        token_path = os.path.join(os.path.dirname(__file__), '../../../token.json')
        creds_path = os.path.join(os.path.dirname(__file__), '../../../credentials.json')

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(creds_path):
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise Exception("Gmail credentials not found")

            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def list_emails(self, max_results: int = 10, query: str = '', label_ids: List[str] = None) -> Dict[str, Any]:
        """List emails with optional filtering."""
        try:
            params = {
                'userId': 'me',
                'maxResults': max_results,
                'q': query
            }
            if label_ids:
                params['labelIds'] = label_ids

            results = self.service.users().messages().list(**params).execute()
            messages = results.get('messages', [])

            emails = []
            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata'
                ).execute()

                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                emails.append({
                    'id': msg['id'],
                    'thread_id': msg_data.get('threadId'),
                    'snippet': msg_data.get('snippet', ''),
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'labels': msg_data.get('labelIds', [])
                })

            return {
                'success': True,
                'emails': emails,
                'count': len(emails)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def read_email(self, message_id: str) -> Dict[str, Any]:
        """Read a specific email."""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}

            # Extract body
            body = ''
            payload = msg.get('payload', {})
            if 'body' in payload and payload['body'].get('data'):
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            elif 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break

            return {
                'success': True,
                'email': {
                    'id': message_id,
                    'thread_id': msg.get('threadId'),
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'body': body,
                    'labels': msg.get('labelIds', [])
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def send_email(self, to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
        """Send an email."""
        try:
            from email.mime.text import MIMEText

            msg = MIMEText(body)
            msg['To'] = to
            msg['Subject'] = subject

            if 'from_addr' in kwargs:
                msg['From'] = kwargs['from_addr']

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            return {
                'success': True,
                'message_id': message['id']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
gmail_service = GmailService()

# API Routes
@gmail_bp.route('/list', methods=['POST'])
def list_emails():
    """List emails endpoint."""
    data = request.get_json() or {}
    max_results = data.get('max_results', 10)
    query = data.get('query', '')
    label_ids = data.get('label_ids')

    result = gmail_service.list_emails(max_results, query, label_ids)
    return jsonify(result)

@gmail_bp.route('/read/<message_id>', methods=['GET'])
def read_email(message_id):
    """Read email endpoint."""
    result = gmail_service.read_email(message_id)
    return jsonify(result)

@gmail_bp.route('/send', methods=['POST'])
def send_email():
    """Send email endpoint."""
    data = request.get_json() or {}
    to = data.get('to')
    subject = data.get('subject', '')
    body = data.get('body', '')

    if not to or not body:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: to, body'
        }), 400

    result = gmail_service.send_email(to, subject, body)
    return jsonify(result)

@gmail_bp.route('/health', methods=['GET'])
def health():
    """Health check for Gmail service."""
    try:
        # Quick test - list 1 message
        test = gmail_service.list_emails(1)
        return jsonify({
            'status': 'healthy',
            'service': 'gmail',
            'test_passed': test.get('success', False)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'gmail',
            'error': str(e)
        }), 500