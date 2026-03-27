"""
Personal Assistant Google Sheets API - Tower-specific Sheets operations.

Extracted from monolithic agent_bridge_api.py to restore tower independence.
Provides Google Sheets read/write/append for personal-assistant tower.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_sheets_service = None


def get_sheets_service():
    """Get or create Google Sheets API service."""
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_path = Path(__file__).resolve().parent.parent.parent.parent / "token.json"
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path))
            _sheets_service = build('sheets', 'v4', credentials=creds)
            logger.info("Sheets service initialized for personal-assistant tower")
            return _sheets_service
    except Exception as e:
        logger.error(f"Sheets service initialization failed: {e}")
    return None


def read_sheet(spreadsheet_id: Optional[str] = None, range_name: str = "Sheet1!A1:Z100") -> Dict[str, Any]:
    """
    Read data from a Google Sheet.

    Args:
        spreadsheet_id: Google Sheet ID (falls back to GOOGLE_SHEETS_SPREADSHEET_ID env var)
        range_name: Sheet range in A1 notation

    Returns:
        Dict with sheet values
    """
    spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        return {"success": False, "error": "spreadsheet_id is required"}

    service = get_sheets_service()
    if not service:
        return {"success": False, "error": "Sheets service not available"}

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name
        ).execute()
        values = result.get('values', [])
        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "range": range_name,
            "values": values,
            "row_count": len(values)
        }
    except Exception as e:
        logger.error(f"Failed to read sheet: {e}")
        return {"success": False, "error": str(e)}


def write_sheet(values: List[List], spreadsheet_id: Optional[str] = None, range_name: str = "Sheet1!A1") -> Dict[str, Any]:
    """
    Write data to a Google Sheet.

    Args:
        values: 2D array of values to write
        spreadsheet_id: Google Sheet ID
        range_name: Starting cell in A1 notation

    Returns:
        Dict with update status
    """
    spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        return {"success": False, "error": "spreadsheet_id is required"}
    if not values:
        return {"success": False, "error": "values is required"}

    service = get_sheets_service()
    if not service:
        return {"success": False, "error": "Sheets service not available"}

    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        return {"success": True, "updated_cells": result.get('updatedCells', 0)}
    except Exception as e:
        logger.error(f"Failed to write sheet: {e}")
        return {"success": False, "error": str(e)}


def append_sheet(values: List[List], spreadsheet_id: Optional[str] = None, range_name: str = "Sheet1!A1") -> Dict[str, Any]:
    """
    Append rows to a Google Sheet.

    Args:
        values: 2D array of rows to append
        spreadsheet_id: Google Sheet ID
        range_name: Target range in A1 notation

    Returns:
        Dict with append status
    """
    spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        return {"success": False, "error": "spreadsheet_id is required"}

    service = get_sheets_service()
    if not service:
        return {"success": False, "error": "Sheets service not available"}

    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        return {
            "success": True,
            "updated_range": result.get('updates', {}).get('updatedRange', '')
        }
    except Exception as e:
        logger.error(f"Failed to append to sheet: {e}")
        return {"success": False, "error": str(e)}


def get_tower_capabilities() -> Dict[str, Any]:
    """Return tower capabilities for Sheets operations."""
    return {
        "name": "personal-assistant-sheets",
        "description": "Google Sheets integration for personal assistant automation",
        "functions": ["read_sheet", "write_sheet", "append_sheet"],
        "protocols": ["direct_import", "mcp_server"]
    }
