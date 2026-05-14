#!/usr/bin/env python3
"""
Drive Collector — Pull scanned documents from a Google Drive folder, extract text,
and return combined notes ready for SOP generation.

Workflow:
    1. William scans documents with the Google Drive app on his phone.
    2. Drive Scanner saves them as PDFs into a folder he chooses.
    3. William tells the SOP builder the folder name.
    4. This module:
       - Lists all files in the folder
       - Downloads PDFs / images / docs
       - Extracts text (Anthropic vision API for scanned PDFs, native export for Google Docs)
       - Returns combined text for sop_generator.py to structure into an SOP

Setup (one-time):
    1. The existing `token_sheets.json` only has `drive.file` scope (app-created files).
       To read files William uploaded manually, broader scope is required:
           https://www.googleapis.com/auth/drive.readonly
    2. First run will trigger a browser OAuth flow to grant Drive read access.
       This produces `token_drive_readonly.json` which is reused on subsequent runs.

Usage:
    from drive_collector import collect_notes_from_folder
    notes = collect_notes_from_folder("Front Desk SOP Notes")
"""

import base64
import io
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

CREDENTIALS_FILE = REPO_ROOT / "credentials.json"
TOKEN_FILE = REPO_ROOT / "token_drive_readonly.json"

# Mime types we know how to extract text from
SUPPORTED_TEXT_MIMES = {"text/plain", "text/markdown"}
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"
PDF_MIME = "application/pdf"
IMAGE_MIMES = {"image/jpeg", "image/png", "image/heic", "image/webp"}


def get_drive_service():
    """Get an authorized Google Drive v3 service handle."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                sys.exit(f"ERROR: {CREDENTIALS_FILE} not found. Place Google OAuth client JSON there.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            print("→ Opening browser for one-time Drive read authorization...")
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"→ Saved Drive token to {TOKEN_FILE.name}")

    return build("drive", "v3", credentials=creds)


def find_folder_id(service, folder_name: str) -> str:
    """Look up a Drive folder by name. Returns folder ID or raises."""
    query = (
        f"name='{folder_name}' and "
        f"mimeType='{GOOGLE_FOLDER_MIME}' and "
        f"trashed=false"
    )
    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, owners)",
        pageSize=10,
    ).execute()
    files = results.get("files", [])
    if not files:
        sys.exit(f"ERROR: No folder named '{folder_name}' found in your Drive.")
    if len(files) > 1:
        ids = ", ".join(f["id"] for f in files)
        print(f"WARNING: Multiple folders named '{folder_name}' found. Using first. IDs: {ids}")
    return files[0]["id"]


def list_files_in_folder(service, folder_id: str) -> list[dict]:
    """List non-folder files inside a folder. Returns list of {id, name, mimeType}."""
    query = (
        f"'{folder_id}' in parents and "
        f"trashed=false and "
        f"mimeType != '{GOOGLE_FOLDER_MIME}'"
    )
    files: list[dict] = []
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            spaces="drive",
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    files.sort(key=lambda f: f.get("modifiedTime", ""))
    return files


def download_file(service, file_id: str) -> bytes:
    """Download a non-Google-native file as bytes."""
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def export_google_doc_as_text(service, file_id: str) -> str:
    """Export a Google Doc as plain text."""
    data = service.files().export(fileId=file_id, mimeType="text/plain").execute()
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def extract_text_with_anthropic(file_bytes: bytes, mime_type: str, filename: str) -> str:
    """
    Use Claude vision to OCR a PDF or image. Returns extracted text.

    Strategy: For PDFs, send the entire PDF as a document content block (Claude reads it
    natively, including scanned pages). For images, send as image content block.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("ERROR: anthropic SDK not installed. Run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set in environment.")
    client = Anthropic(api_key=api_key)

    b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
    if mime_type == PDF_MIME:
        content_block = {
            "type": "document",
            "source": {"type": "base64", "media_type": PDF_MIME, "data": b64},
        }
    elif mime_type in IMAGE_MIMES:
        content_block = {
            "type": "image",
            "source": {"type": "base64", "media_type": mime_type, "data": b64},
        }
    else:
        return ""

    prompt = (
        f"This document/image is named '{filename}'. It contains process notes, "
        "instructions, or reference material for building a Standard Operating Procedure. "
        "Extract ALL readable text faithfully, preserving structure (headings, lists, tables). "
        "Do not summarize or interpret — output a verbatim transcription. "
        "If parts are unreadable, note them as [illegible]."
    )

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": [content_block, {"type": "text", "text": prompt}],
        }],
    )
    return message.content[0].text.strip()


def extract_text(service, file_meta: dict) -> str:
    """Dispatch text extraction based on mime type. Returns the file's text content."""
    file_id = file_meta["id"]
    name = file_meta["name"]
    mime = file_meta["mimeType"]

    if mime == GOOGLE_DOC_MIME:
        return export_google_doc_as_text(service, file_id)
    if mime in SUPPORTED_TEXT_MIMES:
        return download_file(service, file_id).decode("utf-8", errors="replace")
    if mime == PDF_MIME or mime in IMAGE_MIMES:
        data = download_file(service, file_id)
        return extract_text_with_anthropic(data, mime, name)
    print(f"  → Skipping unsupported mime type: {mime} ({name})")
    return ""


def collect_notes_from_folder(folder_name: str) -> str:
    """
    Main entry point. Returns combined text from all files in the folder,
    each preceded by a header showing the source filename.
    """
    service = get_drive_service()
    folder_id = find_folder_id(service, folder_name)
    files = list_files_in_folder(service, folder_id)
    if not files:
        sys.exit(f"ERROR: Folder '{folder_name}' is empty.")

    print(f"→ Found {len(files)} file(s) in '{folder_name}':")
    for f in files:
        print(f"   - {f['name']}  ({f['mimeType']})")

    chunks: list[str] = []
    for f in files:
        print(f"\n→ Extracting: {f['name']}")
        text = extract_text(service, f)
        if not text:
            continue
        chunks.append(f"=== Source: {f['name']} ===\n\n{text}\n")
        print(f"   ({len(text)} chars)")

    if not chunks:
        sys.exit("ERROR: No text could be extracted from any file in the folder.")

    return "\n".join(chunks)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pull and extract notes from a Drive folder.")
    parser.add_argument("--folder", required=True, help="Drive folder name")
    parser.add_argument("--output", help="Write combined notes to this file (default: stdout)")
    args = parser.parse_args()

    notes = collect_notes_from_folder(args.folder)
    if args.output:
        Path(args.output).write_text(notes, encoding="utf-8")
        print(f"\n→ Wrote {len(notes)} chars to {args.output}")
    else:
        print("\n" + notes)


if __name__ == "__main__":
    main()
