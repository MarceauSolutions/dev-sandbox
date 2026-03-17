"""
Gmail API service layer for MailAssist.

Handles OAuth web flow (multi-user), email search, thread retrieval,
draft creation, and email sending via Gmail API.

Uses GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET from .env (same credentials
as the Fitness Influencer AI platform's user_oauth.py).
"""

import base64
import json
import os
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
]

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _get_oauth_config(redirect_uri: str) -> dict:
    """
    Build OAuth client config from env vars.
    Same pattern as fitness-influencer/backend/user_oauth.py.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in .env. "
            "These are the same Web Application credentials used by FitAI."
        )

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


class GmailService:
    """Per-user Gmail API wrapper for web app usage."""

    def __init__(self, redirect_uri: str):
        self.redirect_uri = redirect_uri
        self._sessions: dict[str, Credentials] = {}
        self._load_stored_sessions()

    def _session_file(self, session_id: str) -> Path:
        return DATA_DIR / f"session_{session_id}.json"

    def _load_stored_sessions(self):
        """Load any previously saved sessions from disk."""
        for f in DATA_DIR.glob("session_*.json"):
            session_id = f.stem.replace("session_", "")
            try:
                creds = Credentials.from_authorized_user_file(str(f), SCOPES)
                if creds and creds.valid:
                    self._sessions[session_id] = creds
                elif creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self._sessions[session_id] = creds
                    with open(f, "w") as fh:
                        fh.write(creds.to_json())
            except Exception:
                pass

    def get_auth_url(self, session_id: str) -> str:
        """Generate OAuth consent URL for a user session."""
        config = _get_oauth_config(self.redirect_uri)
        flow = Flow.from_client_config(
            config,
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=session_id,
        )
        return auth_url

    def handle_callback(self, session_id: str, code: str) -> dict:
        """Exchange auth code for credentials and store them."""
        config = _get_oauth_config(self.redirect_uri)
        flow = Flow.from_client_config(
            config,
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        self._sessions[session_id] = creds

        # Persist session
        with open(self._session_file(session_id), "w") as f:
            f.write(creds.to_json())

        # Get user profile
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        return {
            "email": profile.get("emailAddress", ""),
            "messages_total": profile.get("messagesTotal", 0),
        }

    def _get_service(self, session_id: str):
        """Get authenticated Gmail service for a session."""
        creds = self._sessions.get(session_id)
        if not creds:
            raise ValueError("Not authenticated. Please connect your Gmail first.")

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._sessions[session_id] = creds
            with open(self._session_file(session_id), "w") as f:
                f.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def is_authenticated(self, session_id: str) -> bool:
        creds = self._sessions.get(session_id)
        if not creds:
            return False
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._sessions[session_id] = creds
                return True
            except Exception:
                return False
        return creds.valid

    def get_profile(self, session_id: str) -> dict:
        service = self._get_service(session_id)
        profile = service.users().getProfile(userId="me").execute()
        return {"email": profile.get("emailAddress", "")}

    def search_emails(
        self, session_id: str, query: str, max_results: int = 20
    ) -> list[dict]:
        """Search Gmail using standard Gmail query syntax."""
        service = self._get_service(session_id)
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])
        output = []
        for msg_meta in messages:
            details = self._get_message_details(service, msg_meta["id"])
            if details:
                output.append(details)
        return output

    def get_thread(self, session_id: str, thread_id: str) -> list[dict]:
        """Get all messages in a thread, ordered chronologically."""
        service = self._get_service(session_id)
        thread = (
            service.users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )
        messages = []
        for msg in thread.get("messages", []):
            details = self._parse_message(msg)
            if details:
                messages.append(details)
        messages.sort(key=lambda m: m.get("timestamp", 0))
        return messages

    def send_email(
        self,
        session_id: str,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> dict:
        """Send an email (or reply to an existing thread)."""
        service = self._get_service(session_id)
        profile = service.users().getProfile(userId="me").execute()
        from_email = profile.get("emailAddress", "")

        msg = MIMEMultipart("alternative")
        msg["To"] = to
        msg["From"] = from_email
        msg["Subject"] = subject

        if reply_to_message_id:
            msg["In-Reply-To"] = reply_to_message_id
            msg["References"] = reply_to_message_id

        msg.attach(MIMEText(body, "plain"))

        html_body = body.replace("\n", "<br>")
        html = f"""<html><body style="font-family: -apple-system, sans-serif; line-height: 1.6; color: #333;">
        {html_body}
        </body></html>"""
        msg.attach(MIMEText(html, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        send_body = {"raw": raw}
        if thread_id:
            send_body["threadId"] = thread_id

        sent = (
            service.users()
            .messages()
            .send(userId="me", body=send_body)
            .execute()
        )
        return {"message_id": sent.get("id", ""), "thread_id": sent.get("threadId", "")}

    def create_draft(
        self,
        session_id: str,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> dict:
        """Create a draft in the user's Gmail."""
        service = self._get_service(session_id)
        profile = service.users().getProfile(userId="me").execute()
        from_email = profile.get("emailAddress", "")

        msg = MIMEMultipart("alternative")
        msg["To"] = to
        msg["From"] = from_email
        msg["Subject"] = subject

        if reply_to_message_id:
            msg["In-Reply-To"] = reply_to_message_id
            msg["References"] = reply_to_message_id

        msg.attach(MIMEText(body, "plain"))
        html_body = body.replace("\n", "<br>")
        html = f"""<html><body style="font-family: -apple-system, sans-serif; line-height: 1.6; color: #333;">
        {html_body}
        </body></html>"""
        msg.attach(MIMEText(html, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        draft_body = {"message": {"raw": raw}}
        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=draft_body)
            .execute()
        )
        return {"draft_id": draft.get("id", ""), "message_id": draft.get("message", {}).get("id", "")}

    def _get_message_details(self, service, message_id: str) -> dict | None:
        """Fetch and parse a single message by ID."""
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return self._parse_message(msg)
        except Exception:
            return None

    def _parse_message(self, msg: dict) -> dict | None:
        """Parse a Gmail API message object into a clean dict."""
        try:
            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            date_str = headers.get("date", "")
            timestamp = 0
            date_display = ""
            try:
                dt = parsedate_to_datetime(date_str)
                timestamp = dt.timestamp()
                date_display = dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                date_display = date_str

            body = self._extract_body(msg.get("payload", {}))
            from_raw = headers.get("from", "")
            from_name, from_email = self._parse_from(from_raw)

            return {
                "id": msg.get("id", ""),
                "thread_id": msg.get("threadId", ""),
                "from_name": from_name,
                "from_email": from_email,
                "to": headers.get("to", ""),
                "subject": headers.get("subject", "(No Subject)"),
                "snippet": msg.get("snippet", ""),
                "body": body,
                "date": date_display,
                "timestamp": timestamp,
                "labels": msg.get("labelIds", []),
                "message_id_header": headers.get("message-id", ""),
            }
        except Exception:
            return None

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text body from message payload."""
        mime_type = payload.get("mimeType", "")

        if payload.get("body", {}).get("data"):
            decoded = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )
            if mime_type == "text/plain":
                return decoded
            if mime_type == "text/html":
                return self._strip_html(decoded)

        parts = payload.get("parts", [])
        plain = ""
        html = ""
        for part in parts:
            pt = part.get("mimeType", "")
            if pt == "text/plain" and part.get("body", {}).get("data"):
                plain += base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="replace"
                )
            elif pt == "text/html" and part.get("body", {}).get("data"):
                html += base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="replace"
                )
            elif part.get("parts"):
                nested = self._extract_body(part)
                if nested:
                    plain += nested

        return plain if plain else self._strip_html(html) if html else ""

    @staticmethod
    def _strip_html(html: str) -> str:
        """Basic HTML to plain text."""
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        return text.strip()

    @staticmethod
    def _parse_from(from_header: str) -> tuple[str, str]:
        """Parse 'Name <email>' into (name, email)."""
        match = re.match(r'"?([^"<]+)"?\s*<([^>]+)>', from_header)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        match = re.match(r"([^\s<>]+@[^\s<>]+)", from_header)
        if match:
            return "", match.group(1)
        return "", from_header
