#!/usr/bin/env python3
"""
Document Serving Routes — Serve business docs (PDFs, Markdown) via API.

Serves files from the pt-business directory with allowlisted paths.
Markdown files can be returned as rendered HTML.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/api/docs", tags=["Documents"])

# Base directory for business documents
DOCS_BASE = Path(__file__).parent.parent.parent / "pt-business"

# Allowlisted directory prefixes (relative to DOCS_BASE)
ALLOWED_DIRS = {"legal", "ops", "content", "business-planning", "research", "data", "intake"}


def _validate_path(path: str) -> Path:
    """Validate and resolve a document path, preventing directory traversal."""
    # Normalize and resolve
    clean = path.replace("..", "").lstrip("/")
    full_path = (DOCS_BASE / clean).resolve()

    # Must be under DOCS_BASE
    if not str(full_path).startswith(str(DOCS_BASE.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    # Must be in an allowlisted directory
    rel = full_path.relative_to(DOCS_BASE.resolve())
    top_dir = str(rel).split("/")[0] if "/" in str(rel) else ""
    if top_dir and top_dir not in ALLOWED_DIRS:
        raise HTTPException(status_code=403, detail=f"Directory '{top_dir}' not accessible")

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    return full_path


@router.get("/list")
async def list_documents():
    """List all available documents organized by directory."""
    docs = {}
    for allowed_dir in ALLOWED_DIRS:
        dir_path = DOCS_BASE / allowed_dir
        if not dir_path.exists():
            continue
        files = []
        for f in sorted(dir_path.rglob("*")):
            if f.is_file() and f.suffix in {".pdf", ".md", ".json", ".txt"}:
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(DOCS_BASE)),
                    "type": f.suffix[1:],
                    "size": f.stat().st_size
                })
        if files:
            docs[allowed_dir] = files
    return {"documents": docs}


@router.get("/{path:path}")
async def serve_document(path: str, format: Optional[str] = None):
    """
    Serve a document file.

    For PDFs: returns the file directly.
    For Markdown: returns raw text, or HTML if format=html.
    """
    full_path = _validate_path(path)

    # PDF files
    if full_path.suffix == ".pdf":
        return FileResponse(
            full_path,
            media_type="application/pdf",
            filename=full_path.name
        )

    # Markdown files
    if full_path.suffix == ".md":
        content = full_path.read_text(encoding="utf-8")

        if format == "html":
            # Render markdown to styled HTML
            try:
                import markdown
                html_body = markdown.markdown(
                    content,
                    extensions=["tables", "fenced_code", "toc"]
                )
            except ImportError:
                # Fallback: basic conversion
                html_body = f"<pre>{content}</pre>"

            html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  body {{ font-family: Inter, -apple-system, sans-serif; background: #1a1a1a; color: #f0f4f8;
         max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }}
  h1, h2, h3 {{ color: #C9963C; border-bottom: 1px solid #333; padding-bottom: 0.3em; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ border: 1px solid #444; padding: 8px 12px; text-align: left; }}
  th {{ background: #2D2D2D; color: #C9963C; }}
  tr:nth-child(even) {{ background: #252525; }}
  code {{ background: #2D2D2D; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  pre {{ background: #2D2D2D; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
  a {{ color: #D4AF37; }}
  ul, ol {{ padding-left: 1.5em; }}
  li {{ margin: 0.3em 0; }}
  input[type="checkbox"] {{ margin-right: 0.5em; }}
</style>
</head><body>{html_body}</body></html>"""
            return HTMLResponse(content=html)

        return HTMLResponse(content=content, media_type="text/plain")

    # JSON files
    if full_path.suffix == ".json":
        return FileResponse(full_path, media_type="application/json")

    # Text files
    if full_path.suffix == ".txt":
        return FileResponse(full_path, media_type="text/plain")

    raise HTTPException(status_code=400, detail=f"Unsupported file type: {full_path.suffix}")
