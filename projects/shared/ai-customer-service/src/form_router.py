"""
FastAPI router for multi-business form handling.

This integrates the form handler into the main API at:
- POST /api/form/submit - Receive form submissions
- GET  /api/form/health - Health check
- GET  /api/form/businesses - List configured businesses
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, List
import re

# Add execution to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from execution.form_handler import (
    MultiBusinessFormHandler,
    get_business_config,
    get_all_businesses
)

router = APIRouter(prefix="/api/form", tags=["forms"])

# Initialize handler
handler = MultiBusinessFormHandler()


class FormSubmissionRequest(BaseModel):
    """Form submission request body."""
    email: str  # Simple string, validated below
    name: Optional[str] = ""
    phone: Optional[str] = ""
    message: Optional[str] = ""
    source: Optional[str] = ""
    business_id: Optional[str] = ""
    interest: Optional[str] = ""
    email_opt_in: Optional[bool] = True
    sms_opt_in: Optional[bool] = False
    social_handle: Optional[str] = ""
    followers: Optional[str] = ""
    utm_source: Optional[str] = ""
    utm_medium: Optional[str] = ""
    utm_campaign: Optional[str] = ""

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if not v or '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower().strip()


class FormSubmissionResponse(BaseModel):
    """Form submission response."""
    status: str
    message: str
    submission_id: str
    business_id: str
    task_url: Optional[str] = None
    auto_responses: List[str] = []
    errors: List[str] = []


@router.post("/submit", response_model=FormSubmissionResponse)
async def submit_form(
    submission: FormSubmissionRequest,
    request: Request
):
    """
    Handle form submission from any website.

    Automatically routes to correct business based on:
    1. Explicit business_id field
    2. Source field
    3. Referrer/Origin headers
    """
    try:
        # Build data dict from request
        data = submission.model_dump()

        # Add metadata from request
        data['ip_address'] = request.client.host if request.client else ""
        data['user_agent'] = request.headers.get('User-Agent', '')
        data['referrer'] = request.headers.get('Referer', '')
        data['origin'] = request.headers.get('Origin', '')

        # Process submission
        result = handler.process_submission(data)

        if result['success']:
            return FormSubmissionResponse(
                status="success",
                message="Form submitted successfully",
                submission_id=result['submission_id'],
                business_id=result.get('business_id', 'unknown'),
                task_url=f"https://app.clickup.com/t/{result['clickup_task_id']}" if result.get('clickup_task_id') else None,
                auto_responses=result.get('auto_responses_sent', []),
                errors=[]
            )
        else:
            return FormSubmissionResponse(
                status="partial",
                message="Form received with some integration errors",
                submission_id=result['submission_id'],
                business_id=result.get('business_id', 'unknown'),
                errors=result.get('errors', [])
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def form_health():
    """Health check for form handling system."""
    businesses = get_all_businesses()
    return {
        "status": "healthy",
        "service": "multi-business-form-handler",
        "businesses_configured": len(businesses),
        "business_ids": list(businesses.keys()),
        "integrations": {
            "clickup": bool(handler.clickup_token),
            "google_sheets": bool(handler.sheets_spreadsheet_id),
            "email": bool(handler.smtp_username),
            "sms": bool(handler.twilio_sid)
        }
    }


@router.get("/businesses")
async def list_businesses():
    """List all configured businesses."""
    businesses = get_all_businesses()
    return {
        "count": len(businesses),
        "businesses": [
            {
                "id": config.business_id,
                "name": config.business_name,
                "domain": config.domain,
                "clickup_configured": bool(config.clickup_list_id),
                "sheets_configured": bool(config.google_sheet_id),
                "auto_response_enabled": config.auto_response_enabled,
            }
            for config in businesses.values()
        ]
    }
