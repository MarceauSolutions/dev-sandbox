"""
PDF Routes — Branded PDF Generation API

Generates professional, branded PDFs for client deliverables using the shared
branded_pdf_engine. Each endpoint accepts structured data and returns a PDF file.

Templates: workout, nutrition, progress, onboarding, peptide-guide, challenge, document
"""

import sys
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

# Add execution/ to path for shared engine
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "execution"))

from branded_pdf_engine import BrandedPDFEngine
from pdf_data_models import (
    WorkoutProgramData, NutritionGuideData, ProgressReportData,
    OnboardingPacketData, PeptideGuideData, ChallengeWorkoutData,
    GenericDocData,
)

router = APIRouter(prefix="/api/pdf", tags=["pdf"])

# Singleton engine instance
_engine = BrandedPDFEngine()


def _pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    """Wrap PDF bytes in a StreamingResponse with proper headers."""
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/templates")
async def list_templates():
    """List all available PDF templates."""
    return {"templates": _engine.list_templates()}


@router.post("/generate/workout")
async def generate_workout(data: WorkoutProgramData):
    """Generate a branded workout program PDF."""
    try:
        pdf = _engine.generate("workout_program", data.model_dump())
        name = data.client_name.replace(" ", "_")
        return _pdf_response(pdf, f"{name}_workout_program.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/generate/nutrition")
async def generate_nutrition(data: NutritionGuideData):
    """Generate a branded nutrition guide PDF."""
    try:
        pdf = _engine.generate("nutrition_guide", data.model_dump())
        name = data.client_name.replace(" ", "_")
        return _pdf_response(pdf, f"{name}_nutrition_guide.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/generate/progress")
async def generate_progress(data: ProgressReportData):
    """Generate a branded progress report PDF."""
    try:
        pdf = _engine.generate("progress_report", data.model_dump())
        name = data.client_name.replace(" ", "_")
        return _pdf_response(pdf, f"{name}_progress_report.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/generate/onboarding")
async def generate_onboarding(data: OnboardingPacketData):
    """Generate a branded onboarding packet PDF."""
    try:
        pdf = _engine.generate("onboarding_packet", data.model_dump())
        name = data.client_name.replace(" ", "_")
        return _pdf_response(pdf, f"{name}_onboarding_packet.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/generate/peptide-guide")
async def generate_peptide_guide(data: PeptideGuideData):
    """Generate a branded peptide guide PDF."""
    try:
        pdf = _engine.generate("peptide_guide", data.model_dump())
        filename = "peptide_guide.pdf"
        if data.client_name:
            filename = f"{data.client_name.replace(' ', '_')}_peptide_guide.pdf"
        return _pdf_response(pdf, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/generate/challenge")
async def generate_challenge(data: ChallengeWorkoutData):
    """Generate a branded challenge workout PDF."""
    try:
        pdf = _engine.generate("challenge_workout", data.model_dump())
        name = data.challenge_name.replace(" ", "_").replace("-", "_")
        return _pdf_response(pdf, f"{name}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.post("/generate/document")
async def generate_document(data: GenericDocData):
    """Generate a branded generic document PDF from markdown content."""
    try:
        pdf = _engine.generate("generic_document", data.model_dump())
        name = data.title.replace(" ", "_")[:40]
        return _pdf_response(pdf, f"{name}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
