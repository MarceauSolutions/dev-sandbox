"""Dystonia Research Digest — FastAPI Web Application."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent  # dev-sandbox root
sys.path.insert(0, str(ROOT))

from src.database import (
    add_category,
    delete_category,
    get_categories,
    get_digest,
    get_digest_count,
    get_digests,
    get_paper,
    get_papers_by_category,
    get_papers_for_digest,
    get_stats,
    get_total_paper_count,
    init_db,
    search_papers,
    seed_categories,
    toggle_category,
)

from execution.dystonia_research_digest import SEARCH_QUERIES

APP_PORT = 8792
PROJECT_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=str(PROJECT_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_categories(SEARCH_QUERIES)
    yield


app = FastAPI(
    title="Dystonia Research Digest",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(PROJECT_DIR / "static")), name="static")


# ── Helper ───────────────────────────────────────────────────────────────────

def _format_date(iso_str: str) -> str:
    if not iso_str:
        return "Unknown"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return iso_str


templates.env.filters["format_date"] = _format_date


# ── Pages ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = get_stats()
    recent = get_digests(limit=5)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_digests": recent,
    })


@app.get("/digests", response_class=HTMLResponse)
async def digest_list(request: Request, page: int = 1):
    per_page = 20
    offset = (page - 1) * per_page
    digests = get_digests(limit=per_page, offset=offset)
    total = get_digest_count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    return templates.TemplateResponse("digest_list.html", {
        "request": request,
        "digests": digests,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    })


@app.get("/digests/{digest_id}", response_class=HTMLResponse)
async def digest_detail(request: Request, digest_id: int):
    digest = get_digest(digest_id)
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    papers_by_cat = get_papers_by_category(digest_id)
    total_papers = sum(len(v) for v in papers_by_cat.values())
    return templates.TemplateResponse("digest_detail.html", {
        "request": request,
        "digest": digest,
        "papers_by_category": papers_by_cat,
        "total_papers": total_papers,
    })


@app.get("/digests/{digest_id}/pdf")
async def digest_pdf(digest_id: int):
    digest = get_digest(digest_id)
    if not digest or not digest.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF not available")
    pdf_path = Path(digest["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )


@app.get("/papers/{paper_id}", response_class=HTMLResponse)
async def paper_detail(request: Request, paper_id: int):
    paper = get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return templates.TemplateResponse("paper_detail.html", {
        "request": request,
        "paper": paper,
    })


@app.get("/papers", response_class=HTMLResponse)
async def paper_search(request: Request, q: str = ""):
    results = []
    if q:
        results = search_papers(q, limit=50)
    return templates.TemplateResponse("paper_search.html", {
        "request": request,
        "query": q,
        "results": results,
    })


@app.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request):
    cats = get_categories()
    return templates.TemplateResponse("categories.html", {
        "request": request,
        "categories": cats,
    })


@app.post("/categories")
async def create_category(query: str = Form(...), label: str = Form(...)):
    add_category(query, label)
    return RedirectResponse("/categories", status_code=303)


@app.post("/categories/{cat_id}/toggle")
async def toggle_cat(cat_id: int):
    toggle_category(cat_id)
    return RedirectResponse("/categories", status_code=303)


@app.post("/categories/{cat_id}/delete")
async def delete_cat(cat_id: int):
    delete_category(cat_id)
    return RedirectResponse("/categories", status_code=303)


# ── API Endpoints ────────────────────────────────────────────────────────────

def _run_digest_background(days_back: int):
    """Background task to run the digest."""
    from src.digest_runner import run_digest_with_persistence
    run_digest_with_persistence(days_back=days_back, send_emails=True)


@app.post("/api/run-digest")
async def api_run_digest(background_tasks: BackgroundTasks, days_back: int = 7):
    background_tasks.add_task(_run_digest_background, days_back)
    return JSONResponse({
        "status": "started",
        "message": f"Digest run started (looking back {days_back} days). Check /api/status for progress.",
    })


@app.get("/api/status")
async def api_status():
    stats = get_stats()
    last = stats.get("last_run")
    return JSONResponse({
        "last_run": {
            "id": last["id"] if last else None,
            "date": last["run_date"] if last else None,
            "status": last["status"] if last else None,
            "total_papers": last["total_papers"] if last else 0,
            "email_sent": last["email_sent"] if last else False,
        } if last else None,
        "total_digests": stats["total_digests"],
        "total_papers": stats["total_papers"],
        "unique_papers": stats["unique_papers"],
    })


@app.get("/api/digest/{digest_id}")
async def api_digest_json(digest_id: int):
    digest = get_digest(digest_id)
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    papers = get_papers_for_digest(digest_id)
    return JSONResponse({
        "digest": digest,
        "papers": papers,
    })


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "service": "dystonia-research-digest", "port": APP_PORT})


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=APP_PORT)
