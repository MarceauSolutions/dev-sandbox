"""
Fitness-Influencer Tower — Lead Routes
Extracted from main.py monolith. 9 routes.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

router = APIRouter()


# ============================================================================
# Lead Capture & Opt-In Endpoints
# ============================================================================

class LeadSubmission(BaseModel):
    firstName: str
    lastName: str
    businessName: str
    email: str
    phone: str
    projectDescription: str
    smsOptIn: bool
    emailOptIn: bool
    termsAgreement: bool
    timestamp: str
    source: str

class SMSOptIn(BaseModel):
    phone: str
    firstName: str
    lastName: str
    timestamp: str

class EmailOptIn(BaseModel):
    email: str
    firstName: str
    lastName: str
    businessName: str
    timestamp: str

@router.post("/api/leads/submit")
async def submit_lead(lead: LeadSubmission):
    """
    Submit lead capture form data to Google Sheets.
    This endpoint stores form submissions for follow-up.

    Supports credentials via:
    1. GOOGLE_TOKEN_JSON environment variable (base64 encoded token.json content)
    2. Local token.json file
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import json
        import base64

        creds = None

        # Method 1: Try loading from environment variable (for Railway deployment)
        token_json_env = os.getenv('GOOGLE_TOKEN_JSON')
        if token_json_env:
            try:
                # Decode base64 if it looks encoded, otherwise use as-is
                if not token_json_env.startswith('{'):
                    token_data = base64.b64decode(token_json_env).decode('utf-8')
                else:
                    token_data = token_json_env
                token_dict = json.loads(token_data)
                creds = Credentials.from_authorized_user_info(token_dict)
            except Exception as e:
                print(f"Failed to load credentials from env: {e}")

        # Method 2: Fall back to local file
        if not creds:
            token_path = SCRIPTS_PATH / "token.json"
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path))

        if not creds:
            return {
                "success": False,
                "error": "Google OAuth not configured. Please set up credentials first.",
                "data": lead.dict()
            }

        service = build('sheets', 'v4', credentials=creds)

        # TODO: Replace with your actual Google Sheets ID
        # For now, return success with data
        spreadsheet_id = os.getenv('LEADS_SHEET_ID', 'CONFIGURE_ME')

        if spreadsheet_id == 'CONFIGURE_ME':
            # Store locally for now
            print(f"📝 Lead Captured: {lead.firstName} {lead.lastName} - {lead.businessName}")
            print(f"   Email: {lead.email} | Phone: {lead.phone}")
            print(f"   SMS Opt-In: {lead.smsOptIn} | Email Opt-In: {lead.emailOptIn}")

            return {
                "success": True,
                "message": "Lead captured (Google Sheets pending configuration)",
                "data": lead.dict()
            }

        # Prepare row data
        row_data = [
            lead.timestamp,
            lead.firstName,
            lead.lastName,
            lead.businessName,
            lead.email,
            lead.phone,
            lead.projectDescription,
            "Yes" if lead.smsOptIn else "No",
            "Yes" if lead.emailOptIn else "No",
            lead.source
        ]

        # Append to sheet (use LEADS_SHEET_NAME env var or default to Sheet1)
        sheet_name = os.getenv('LEADS_SHEET_NAME', 'Sheet1')
        body = {'values': [row_data]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A:J',
            valueInputOption='RAW',
            body=body
        ).execute()

        return {
            "success": True,
            "message": "Lead submitted to Google Sheets",
            "data": lead.dict()
        }

    except Exception as e:
        print(f"Error submitting lead: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": lead.dict()
        }

# NOTE: /api/sms/optin is now handled by sms_routes.py (hybrid n8n + Python)
# Migrated 2026-02-10: SMS sending goes through n8n on EC2 instead of direct Twilio calls

@router.post("/api/email/optin")
async def email_optin(opt_in: EmailOptIn):
    """
    Handle email opt-in webhook.
    Sends welcome email and adds to email list.

    Supports:
    - SendGrid API (preferred, set SENDGRID_API_KEY)
    - SMTP (fallback, set SMTP_USERNAME and SMTP_PASSWORD)
    """
    try:
        import os

        sendgrid_api_key = os.getenv('SENDGRID_API_KEY', '').strip()
        sender_name = os.getenv('SENDER_NAME', 'Marceau Solutions')
        sender_email = os.getenv('SENDER_EMAIL', 'wmarceau@marceausolutions.com')

        # Build email HTML content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #FFD700;">Welcome, {opt_in.firstName}!</h1>
                <p>Thank you for joining Marceau Solutions.</p>
                <p>We're excited to help <strong>{opt_in.businessName}</strong> scale with AI automation.</p>

                <h2 style="color: #000;">What's Next?</h2>
                <ul>
                    <li>Schedule your free consultation call</li>
                    <li>Get access to our AI tools dashboard</li>
                    <li>Receive exclusive tips and strategies</li>
                </ul>

                <p>Stay tuned for updates, special offers, and fitness industry insights!</p>

                <p style="margin-top: 30px;">
                    Best,<br>
                    <strong>The Marceau Solutions Team</strong>
                </p>
            </div>
        </body>
        </html>
        """

        # Try SendGrid first (preferred for cloud environments)
        if sendgrid_api_key:
            import httpx

            print(f"📧 Sending via SendGrid to: {opt_in.email}")

            response = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {sendgrid_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": opt_in.email}]}],
                    "from": {"email": sender_email, "name": sender_name},
                    "subject": f"Welcome to Marceau Solutions, {opt_in.firstName}!",
                    "content": [{"type": "text/html", "value": html_content}]
                },
                timeout=30.0
            )

            if response.status_code in [200, 201, 202]:
                print(f"📧 Email Opt-In Success (SendGrid): {opt_in.firstName} {opt_in.lastName} - {opt_in.email}")
                return {
                    "success": True,
                    "message": "Welcome email sent via SendGrid",
                    "data": opt_in.dict()
                }
            else:
                print(f"SendGrid error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"SendGrid API error: {response.status_code}",
                    "data": opt_in.dict()
                }

        # Fallback to SMTP
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com').strip()
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USERNAME', '').strip()
        smtp_pass = os.getenv('SMTP_PASSWORD', '').strip()

        if not smtp_user or not smtp_pass:
            print(f"📧 Email Opt-In (no email provider configured): {opt_in.firstName} {opt_in.lastName} - {opt_in.email}")
            return {
                "success": False,
                "message": "No email provider configured. Set SENDGRID_API_KEY or SMTP credentials.",
                "data": opt_in.dict()
            }

        # Debug: log SMTP config (without password)
        print(f"📧 Connecting to SMTP: host={repr(smtp_host)}, port={smtp_port}, user={smtp_user}")

        # Create welcome email using the html_content defined above
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Welcome to Marceau Solutions, {opt_in.firstName}!"
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = opt_in.email
        msg.attach(MIMEText(html_content, 'html'))

        # Send email with timeout and better error handling
        import socket
        socket.setdefaulttimeout(30)  # 30 second timeout

        try:
            # Use SMTP_SSL for port 465, STARTTLS for port 587
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
        except smtplib.SMTPAuthenticationError as auth_err:
            print(f"SMTP Authentication failed: {auth_err}")
            return {
                "success": False,
                "error": "SMTP authentication failed. Please use a Gmail App Password.",
                "data": opt_in.dict()
            }
        except socket.gaierror as dns_err:
            print(f"DNS resolution failed for {smtp_host}: {dns_err}")
            return {
                "success": False,
                "error": f"Could not resolve SMTP server: {smtp_host}",
                "data": opt_in.dict()
            }
        except OSError as net_err:
            print(f"Network error connecting to SMTP: {net_err}")
            return {
                "success": False,
                "error": f"Network error: {net_err}. Try using an email service like SendGrid instead of SMTP.",
                "data": opt_in.dict()
            }

        print(f"📧 Email Opt-In Success: {opt_in.firstName} {opt_in.lastName} - {opt_in.email}")

        return {
            "success": True,
            "message": "Welcome email sent",
            "data": opt_in.dict()
        }

    except Exception as e:
        print(f"Error sending email: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": opt_in.dict()
        }


# ============================================================================
# User OAuth Endpoints (Gmail/Sheets/Calendar Access)
# ============================================================================

class OAuthStartRequest(BaseModel):
    """Request to start OAuth flow."""
    email: str

class UserDataRequest(BaseModel):
    """Request for user-specific data."""
    user_id: str

class UserSheetsRequest(BaseModel):
    """Request for user's spreadsheet data."""
    user_id: str
    spreadsheet_id: str
    range_name: Optional[str] = "Sheet1!A:Z"

@router.post("/api/oauth/start")
async def start_oauth(request: OAuthStartRequest):
    """
    Start OAuth flow for a user to connect their Google account.

    Returns an authorization URL that the user should visit to grant access.
    After granting access, they'll be redirected back to /api/oauth/callback.
    """
    try:
        from user_oauth import create_authorization_url

        result = create_authorization_url(request.email)

        return {
            "success": True,
            "authorization_url": result['url'],
            "user_id": result['user_id'],
            "message": "Redirect user to authorization_url to connect their Google account"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/api/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    Handle OAuth callback from Google.

    This endpoint receives the authorization code after user grants access.
    It exchanges the code for tokens and stores them securely.
    """
    from fastapi.responses import HTMLResponse

    try:
        from user_oauth import handle_oauth_callback

        result = handle_oauth_callback(code, state)

        # Return a nice HTML page for the user
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connected Successfully</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       display: flex; justify-content: center; align-items: center; height: 100vh;
                       margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .card {{ background: white; padding: 40px; border-radius: 16px; text-align: center;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; }}
                h1 {{ color: #22c55e; margin-bottom: 10px; }}
                p {{ color: #6b7280; }}
                .user-id {{ background: #f3f4f6; padding: 10px; border-radius: 8px;
                           font-family: monospace; margin: 20px 0; }}
                .close-btn {{ background: #667eea; color: white; padding: 12px 24px;
                             border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Connected!</h1>
                <p>Your Google account has been successfully connected.</p>
                <p><strong>Email:</strong> {result['email']}</p>
                <div class="user-id">User ID: {result['user_id']}</div>
                <p>You can now use the AI assistant to access your Gmail and Google Sheets.</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connection Failed</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       display: flex; justify-content: center; align-items: center; height: 100vh;
                       margin: 0; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }}
                .card {{ background: white; padding: 40px; border-radius: 16px; text-align: center;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; }}
                h1 {{ color: #ef4444; margin-bottom: 10px; }}
                p {{ color: #6b7280; }}
                .error {{ background: #fef2f2; color: #dc2626; padding: 10px; border-radius: 8px;
                         font-family: monospace; margin: 20px 0; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>❌ Connection Failed</h1>
                <p>There was an error connecting your Google account.</p>
                <div class="error">{str(e)}</div>
                <p>Please try again or contact support.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=400)

@router.get("/api/oauth/status/{user_id}")
async def oauth_status(user_id: str):
    """Check if a user has connected their Google account."""
    try:
        from user_oauth import is_user_connected, get_token_path
        import json

        connected = is_user_connected(user_id)

        result = {
            "user_id": user_id,
            "connected": connected
        }

        if connected:
            token_path = get_token_path(user_id)
            with open(token_path, 'r') as f:
                data = json.load(f)
            result["email"] = data.get("user_email")
            result["connected_at"] = data.get("connected_at")
            result["scopes"] = data.get("scopes", [])

        return result

    except Exception as e:
        return {"user_id": user_id, "connected": False, "error": str(e)}

@router.delete("/api/oauth/disconnect/{user_id}")
async def oauth_disconnect(user_id: str):
    """Disconnect a user's Google account."""
    try:
        from user_oauth import disconnect_user

        disconnected = disconnect_user(user_id)

        return {
            "success": True,
            "user_id": user_id,
            "disconnected": disconnected,
            "message": "Account disconnected" if disconnected else "Account was not connected"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/api/oauth/users")
async def list_oauth_users():
    """List all connected users (admin endpoint)."""
    try:
        from user_oauth import list_connected_users

        users = list_connected_users()

        return {
            "success": True,
            "count": len(users),
            "users": users
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/user/email-digest")
async def user_email_digest(request: UserDataRequest):
    """
    Get email digest for a connected user.

    Requires the user to have connected their Google account first.
    """
    try:
        from user_oauth import get_user_email_digest, is_user_connected

        if not is_user_connected(request.user_id):
            return {
                "success": False,
                "error": "User not connected. Please connect Google account first.",
                "connect_url": "/api/oauth/start"
            }

        digest = get_user_email_digest(request.user_id, hours_back=24)

        return {
            "success": True,
            "user_id": request.user_id,
            "digest": digest
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/user/sheets-data")
async def user_sheets_data(request: UserSheetsRequest):
    """
    Get spreadsheet data for a connected user.

    Requires the user to have connected their Google account first.
    """
    try:
        from user_oauth import get_user_sheets_data, is_user_connected

        if not is_user_connected(request.user_id):
            return {
                "success": False,
                "error": "User not connected. Please connect Google account first.",
                "connect_url": "/api/oauth/start"
            }

        data = get_user_sheets_data(
            request.user_id,
            request.spreadsheet_id,
            request.range_name
        )

        return {
            "success": True,
            "user_id": request.user_id,
            "data": data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


