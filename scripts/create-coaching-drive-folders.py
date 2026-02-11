#!/usr/bin/env python3
"""
create-coaching-drive-folders.py - Create Google Drive folder structure for coaching clients.

Creates:
  Coaching Clients/
  └── _TEMPLATE (Client Name)/
      ├── Program/
      ├── Progress/
      └── Resources/   ← uploads 3 PDFs here

Usage:
    python scripts/create-coaching-drive-folders.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"

# PDFs to upload to Resources folder
DOCS_DIR = PROJECT_ROOT / "projects" / "marceau-solutions" / "fitness-influencer" / "docs"
PDFS_TO_UPLOAD = [
    DOCS_DIR / "working-together.pdf",
    DOCS_DIR / "liability-waiver.pdf",
    DOCS_DIR / "cancellation-policy.pdf",
]


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}")
                sys.exit(1)
            print("Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {TOKEN_FILE}")

    return creds


def find_or_create_folder(service, name, parent_id=None):
    """Find or create a folder in Google Drive."""
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        print(f"  Found existing: {name} ({folders[0]['id']})")
        return folders[0]['id']

    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    folder = service.files().create(body=metadata, fields='id').execute()
    print(f"  Created: {name} ({folder['id']})")
    return folder['id']


def upload_pdf(service, file_path, parent_id):
    """Upload a PDF to a Google Drive folder."""
    file_metadata = {
        'name': file_path.name,
        'parents': [parent_id],
    }
    media = MediaFileUpload(str(file_path), mimetype='application/pdf')
    uploaded = service.files().create(
        body=file_metadata, media_body=media, fields='id, name'
    ).execute()
    print(f"  Uploaded: {uploaded['name']} ({uploaded['id']})")
    return uploaded['id']


def main():
    print("=== Creating Coaching Client Drive Folders ===\n")

    creds = get_credentials()
    drive = build('drive', 'v3', credentials=creds)

    # 1. Top-level folder
    print("Creating folder structure...")
    coaching_id = find_or_create_folder(drive, "Coaching Clients")

    # 2. Template client folder
    template_id = find_or_create_folder(drive, "_TEMPLATE (Client Name)", coaching_id)

    # 3. Subfolders
    program_id = find_or_create_folder(drive, "Program", template_id)
    progress_id = find_or_create_folder(drive, "Progress", template_id)
    resources_id = find_or_create_folder(drive, "Resources", template_id)

    # 4. Upload PDFs to Resources
    print("\nUploading documents to Resources/...")
    for pdf_path in PDFS_TO_UPLOAD:
        if pdf_path.exists():
            upload_pdf(drive, pdf_path, resources_id)
        else:
            print(f"  SKIPPED (not found): {pdf_path.name}")

    print("\nDone! Folder structure:")
    print(f"  Coaching Clients/")
    print(f"  └── _TEMPLATE (Client Name)/")
    print(f"      ├── Program/")
    print(f"      ├── Progress/")
    print(f"      └── Resources/  (3 PDFs uploaded)")
    print(f"\nOpen Google Drive to see your folders.")


if __name__ == "__main__":
    main()
