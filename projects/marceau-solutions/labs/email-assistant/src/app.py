"""
MailAssist — AI-Powered Email Assistant

FastAPI web application for Gmail integration with AI-powered
email search, thread documentation, and response drafting.

Launch: ./scripts/email-assistant.sh → http://127.0.0.1:8791
"""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

from .gmail_service import GmailService
from . import ai_engine

# --- Config ---
APP_PORT = 8791
PROJECT_ROOT = Path(__file__).parent.parent
REDIRECT_URI = f"http://127.0.0.1:{APP_PORT}/auth/callback"

# --- App ---
app = FastAPI(title="MailAssist", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))

gmail = GmailService(redirect_uri=REDIRECT_URI)

SESSION_COOKIE = "mailassist_session"


def _get_session(request: Request) -> str:
    """Get or create a session ID from cookies."""
    return request.cookies.get(SESSION_COOKIE, "")


def _ensure_session(request: Request, response: Response) -> str:
    """Ensure a session cookie exists."""
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(SESSION_COOKIE, session_id, httponly=True, max_age=86400 * 30)
    return session_id


# ─── Pages ───


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    response = templates.TemplateResponse("index.html", {"request": request})
    session_id = _ensure_session(request, response)
    is_authed = gmail.is_authenticated(session_id)
    profile = gmail.get_profile(session_id) if is_authed else {}
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "authenticated": is_authed,
            "email": profile.get("email", ""),
        },
    )
    _ensure_session(request, response)
    return response


# ─── Auth ───


@app.get("/auth/connect")
async def auth_connect(request: Request):
    response = RedirectResponse(url="/")
    session_id = _ensure_session(request, response)
    auth_url = gmail.get_auth_url(session_id)
    return RedirectResponse(url=auth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = "", state: str = ""):
    session_id = state or _get_session(request)
    if not session_id or not code:
        raise HTTPException(400, "Missing auth code or session")

    result = gmail.handle_callback(session_id, code)
    response = RedirectResponse(url="/")
    response.set_cookie(SESSION_COOKIE, session_id, httponly=True, max_age=86400 * 30)
    return response


@app.get("/auth/status")
async def auth_status(request: Request):
    session_id = _get_session(request)
    if not session_id:
        return JSONResponse({"authenticated": False})
    is_authed = gmail.is_authenticated(session_id)
    if is_authed:
        profile = gmail.get_profile(session_id)
        return JSONResponse({"authenticated": True, "email": profile.get("email", "")})
    return JSONResponse({"authenticated": False})


@app.get("/auth/disconnect")
async def auth_disconnect(request: Request):
    session_id = _get_session(request)
    if session_id:
        session_file = gmail._session_file(session_id)
        if session_file.exists():
            session_file.unlink()
        gmail._sessions.pop(session_id, None)
    response = RedirectResponse(url="/")
    response.delete_cookie(SESSION_COOKIE)
    return response


# ─── Email Operations ───


@app.post("/api/search")
async def search_emails(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    query = data.get("query", "")
    use_ai = data.get("use_ai", False)
    max_results = data.get("max_results", 20)

    if use_ai and query:
        query = ai_engine.smart_search_query(query)

    results = gmail.search_emails(session_id, query, max_results=max_results)
    return JSONResponse({"emails": results, "query_used": query})


@app.post("/api/thread")
async def get_thread(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    thread_id = data.get("thread_id", "")
    if not thread_id:
        raise HTTPException(400, "thread_id required")

    messages = gmail.get_thread(session_id, thread_id)
    return JSONResponse({"messages": messages})


@app.post("/api/analyze")
async def analyze_thread(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    thread_id = data.get("thread_id", "")
    if not thread_id:
        raise HTTPException(400, "thread_id required")

    messages = gmail.get_thread(session_id, thread_id)
    analysis = ai_engine.analyze_email_thread(messages)
    return JSONResponse({"analysis": analysis, "message_count": len(messages)})


@app.post("/api/document")
async def generate_document(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    thread_id = data.get("thread_id", "")
    doc_type = data.get("doc_type", "summary")
    if not thread_id:
        raise HTTPException(400, "thread_id required")

    messages = gmail.get_thread(session_id, thread_id)
    document = ai_engine.generate_thread_document(messages, doc_type=doc_type)
    return JSONResponse({"document": document, "doc_type": doc_type})


@app.post("/api/draft")
async def draft_response(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    thread_id = data.get("thread_id", "")
    intent = data.get("intent", "")
    tone = data.get("tone", "professional")

    if not thread_id or not intent:
        raise HTTPException(400, "thread_id and intent required")

    messages = gmail.get_thread(session_id, thread_id)
    draft = ai_engine.draft_response(messages, user_intent=intent, tone=tone)
    return JSONResponse({"draft": draft})


@app.post("/api/send")
async def send_email(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    to = data.get("to", "")
    subject = data.get("subject", "")
    body = data.get("body", "")
    thread_id = data.get("thread_id")
    reply_to = data.get("reply_to_message_id")

    if not to or not subject or not body:
        raise HTTPException(400, "to, subject, and body required")

    result = gmail.send_email(
        session_id, to, subject, body,
        reply_to_message_id=reply_to,
        thread_id=thread_id,
    )
    return JSONResponse({"sent": True, **result})


@app.post("/api/save-draft")
async def save_draft(request: Request):
    session_id = _get_session(request)
    if not session_id or not gmail.is_authenticated(session_id):
        raise HTTPException(401, "Not authenticated")

    data = await request.json()
    to = data.get("to", "")
    subject = data.get("subject", "")
    body = data.get("body", "")
    thread_id = data.get("thread_id")
    reply_to = data.get("reply_to_message_id")

    if not to or not subject or not body:
        raise HTTPException(400, "to, subject, and body required")

    result = gmail.create_draft(
        session_id, to, subject, body,
        reply_to_message_id=reply_to,
        thread_id=thread_id,
    )
    return JSONResponse({"saved": True, **result})


# ─── Run ───

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=APP_PORT)
