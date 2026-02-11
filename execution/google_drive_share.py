#!/usr/bin/env python3
"""
google_drive_share.py - Upload files to Google Drive and generate shareable links.

Reusable utility for sharing files with clients, collaborators, etc.
Uses existing OAuth credentials (credentials.json / token_sheets.json).

Usage:
    # Upload a single file and get a shareable link
    python execution/google_drive_share.py path/to/file.zip

    # Upload to a specific Drive folder
    python execution/google_drive_share.py path/to/file.zip --folder "Client Deliverables"

    # Upload multiple files
    python execution/google_drive_share.py file1.pdf file2.zip file3.jpg

    # Upload an entire directory (zips it first)
    python execution/google_drive_share.py path/to/folder/ --zip

    # As a Python module
    from execution.google_drive_share import upload_and_share
    link = upload_and_share("path/to/file.zip", folder_name="Client Sites")
"""

import argparse
import mimetypes
import os
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token_sheets.json"


def get_credentials():
    """Get or refresh OAuth credentials."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"ERROR: credentials.json not found at {CREDENTIALS_FILE}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def get_drive_service():
    """Build and return the Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def find_or_create_folder(service, folder_name, parent_id=None):
    """Find a folder by name or create it. Returns folder ID."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # Create the folder
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]

    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_file(service, file_path, folder_id=None):
    """Upload a file to Google Drive. Returns file ID and name."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type is None:
        mime_type = "application/octet-stream"

    metadata = {"name": file_path.name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)
    file = service.files().create(
        body=metadata, media_body=media, fields="id, name, webViewLink, size"
    ).execute()

    return file


def make_shareable(service, file_id):
    """Set 'anyone with link can view' permission. Returns shareable link."""
    permission = {
        "type": "anyone",
        "role": "reader",
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Get the shareable link
    file = service.files().get(fileId=file_id, fields="webViewLink").execute()
    return file.get("webViewLink")


def upload_and_share(file_path, folder_name=None):
    """Upload a file to Google Drive and return a shareable link.

    Args:
        file_path: Path to the file to upload
        folder_name: Optional Drive folder name (created if doesn't exist)

    Returns:
        dict with keys: id, name, link, size
    """
    service = get_drive_service()

    folder_id = None
    if folder_name:
        folder_id = find_or_create_folder(service, folder_name)

    print(f"Uploading {Path(file_path).name}...")
    file = upload_file(service, file_path, folder_id)

    print("Setting shareable permissions...")
    link = make_shareable(service, file["id"])

    size_mb = int(file.get("size", 0)) / (1024 * 1024)
    result = {
        "id": file["id"],
        "name": file["name"],
        "link": link,
        "size_mb": round(size_mb, 1),
    }

    print(f"\nUploaded: {result['name']} ({result['size_mb']} MB)")
    print(f"Shareable link: {result['link']}")
    return result


def zip_directory(dir_path, output_path=None):
    """Zip a directory. Returns path to the zip file."""
    dir_path = Path(dir_path)
    if output_path is None:
        output_path = dir_path.parent / f"{dir_path.name}.zip"
    else:
        output_path = Path(output_path)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in dir_path.rglob("*"):
            if file.name == ".DS_Store":
                continue
            zf.write(file, file.relative_to(dir_path.parent))

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Upload files to Google Drive and get shareable links."
    )
    parser.add_argument("files", nargs="+", help="File(s) or directory to upload")
    parser.add_argument("--folder", type=str, default=None, help="Drive folder name")
    parser.add_argument("--zip", action="store_true", help="Zip directory before uploading")
    args = parser.parse_args()

    results = []
    for file_path in args.files:
        path = Path(file_path)

        if path.is_dir():
            if args.zip:
                print(f"Zipping {path.name}...")
                path = zip_directory(path)
            else:
                print(f"ERROR: {path} is a directory. Use --zip to zip it first.")
                continue

        result = upload_and_share(str(path), folder_name=args.folder)
        results.append(result)

    if results:
        print("\n" + "=" * 50)
        print("  SHAREABLE LINKS")
        print("=" * 50)
        for r in results:
            print(f"  {r['name']} ({r['size_mb']} MB)")
            print(f"  {r['link']}")
            print()


if __name__ == "__main__":
    main()
