#!/usr/bin/env python3
"""
Portfolio Builder — Auto-generates portfolio pages from completed projects.

Runs two ways:
  1. SCHEDULED: Cron checks pipeline.db for newly won deals → adds to portfolio.json → regenerates
  2. MANUAL: Add a project to portfolio.json → run generate

The portfolio page at marceausolutions.com/portfolio/ updates automatically as you close deals.

Usage:
    python3 -m projects.shared.portfolio.portfolio_builder generate    # Build pages from portfolio.json
    python3 -m projects.shared.portfolio.portfolio_builder check       # Check pipeline for new wins to add
    python3 -m projects.shared.portfolio.portfolio_builder add         # Interactive add
    python3 -m projects.shared.portfolio.portfolio_builder list        # Show all portfolio projects
"""

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

if os.environ.get("REPO_ROOT"):
    _REPO_ROOT = Path(os.environ["REPO_ROOT"])
else:
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_PORTFOLIO_JSON = Path(__file__).resolve().parent / "portfolio.json"
_DB_PATH = _REPO_ROOT / "projects" / "lead-generation" / "sales-pipeline" / "data" / "pipeline.db"
_OUTPUT_DIR = _REPO_ROOT / "client-sites" / "portfolio"

TOWER_SERVICES = {
    "digital-web-dev": ["Website Design", "Landing Page", "SEO", "Mobile Optimization"],
    "digital-ai-services": ["AI Phone Receptionist", "Lead Generation", "Automation", "CRM Integration"],
    "fitness-coaching": ["Coaching Platform", "Program Delivery", "Stripe Billing", "Client Portal"],
    "fitness-influencer": ["Video Production", "Social Media", "Content Strategy", "Brand Building"],
}


def _load_portfolio() -> dict:
    with open(_PORTFOLIO_JSON) as f:
        return json.load(f)


def _save_portfolio(data: dict):
    with open(_PORTFOLIO_JSON, "w") as f:
        json.dump(data, f, indent=2)


def list_projects():
    """List all portfolio projects."""
    portfolio = _load_portfolio()
    print(f"\nPORTFOLIO — {len(portfolio['projects'])} projects:")
    print("-" * 60)
    for p in portfolio["projects"]:
        tower = portfolio["towers"].get(p["tower"], {}).get("name", p["tower"])
        featured = " [FEATURED]" if p.get("featured") else ""
        print(f"  {p['date_completed']}  {p['client']}{featured}")
        print(f"              {p['title']} ({tower})")
        if p.get("url"):
            print(f"              {p['url']}")
        print()


def check_pipeline():
    """Check pipeline.db for newly won deals not yet in portfolio."""
    if not _DB_PATH.exists():
        print("Pipeline.db not found")
        return

    portfolio = _load_portfolio()
    existing_companies = {p["client"].lower() for p in portfolio["projects"]}

    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find won deals not in portfolio
    cursor.execute("""
        SELECT id, company, contact_name, industry, tower, monthly_fee, close_date
        FROM deals
        WHERE stage IN ('Won', 'Client Won', 'Active', 'Trial')
        ORDER BY close_date DESC
    """)

    new_wins = []
    for row in cursor.fetchall():
        if row["company"].lower() not in existing_companies:
            new_wins.append(dict(row))

    conn.close()

    if not new_wins:
        print("No new wins to add to portfolio")
        return

    print(f"\nFOUND {len(new_wins)} new wins not in portfolio:")
    for deal in new_wins:
        print(f"  #{deal['id']} {deal['company']} — {deal['industry']} ({deal.get('tower', 'digital-ai-services')})")

    # Auto-add them
    for deal in new_wins:
        tower = deal.get("tower") or _guess_tower(deal.get("industry", ""))
        project = {
            "id": deal["company"].lower().replace(" ", "-").replace(",", "")[:40],
            "tower": tower,
            "client": deal["company"],
            "title": _generate_title(deal),
            "description": _generate_description(deal),
            "services": TOWER_SERVICES.get(tower, ["AI Services"])[:3],
            "result": "Project delivered — details coming soon",
            "url": "",
            "industry": deal.get("industry", ""),
            "date_completed": deal.get("close_date") or datetime.now().strftime("%Y-%m-%d"),
            "featured": False,
        }
        portfolio["projects"].append(project)
        print(f"  Added: {deal['company']}")

    _save_portfolio(portfolio)
    print(f"\nPortfolio updated — now {len(portfolio['projects'])} projects")
    return len(new_wins)


def _guess_tower(industry: str) -> str:
    industry = industry.lower()
    if any(k in industry for k in ["hvac", "plumbing", "roofing", "auto"]):
        return "digital-ai-services"
    if any(k in industry for k in ["med spa", "dental", "health"]):
        return "digital-ai-services"
    if any(k in industry for k in ["gym", "fitness", "training"]):
        return "fitness-coaching"
    if any(k in industry for k in ["entertainment", "event", "music"]):
        return "digital-web-dev"
    return "digital-ai-services"


def _generate_title(deal: dict) -> str:
    industry = deal.get("industry", "")
    tower = deal.get("tower", "")
    if "ai" in tower or not tower:
        return f"AI Automation for {industry} Business"
    elif "web" in tower:
        return f"{industry} Business Website"
    elif "fitness" in tower:
        return f"Fitness Coaching Platform"
    return f"Custom Solution for {deal['company']}"


def _generate_description(deal: dict) -> str:
    fee = deal.get("monthly_fee", 0)
    industry = deal.get("industry", "business")
    if fee:
        return f"AI automation solution for a {industry.lower()} company. Ongoing monthly service delivering measurable ROI."
    return f"Custom solution delivered for a {industry.lower()} company in Southwest Florida."


def generate_pages():
    """Generate the portfolio HTML page."""
    portfolio = _load_portfolio()
    projects = portfolio["projects"]
    towers = portfolio["towers"]

    # Sort: featured first, then by date descending
    projects.sort(key=lambda p: (0 if p.get("featured") else 1, p.get("date_completed", "")), reverse=False)
    projects.sort(key=lambda p: (0 if p.get("featured") else 1))

    # Group by tower
    tower_groups = {}
    for p in projects:
        t = p["tower"]
        if t not in tower_groups:
            tower_groups[t] = []
        tower_groups[t].append(p)

    html = _build_portfolio_html(projects, tower_groups, towers)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUT_DIR / "index.html"
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Portfolio page generated: {output_path}")
    print(f"  {len(projects)} projects across {len(tower_groups)} towers")

    # Deploy to website repo
    for repo_path in [Path("/tmp/marceausolutions-check"), Path("/home/clawdbot/marceausolutions.com")]:
        if repo_path.exists():
            dest_dir = repo_path / "portfolio"
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(output_path), str(dest_dir / "index.html"))
            try:
                subprocess.run(["git", "add", "portfolio/"], capture_output=True, cwd=str(repo_path))
                subprocess.run(["git", "commit", "-m", "auto: portfolio page updated"],
                             capture_output=True, cwd=str(repo_path))
                subprocess.run(["git", "push", "origin", "main"],
                             capture_output=True, timeout=30, cwd=str(repo_path))
                print(f"  Deployed to {repo_path}")
            except Exception:
                pass

    return len(projects)


def _build_portfolio_html(projects: list, tower_groups: dict, towers: dict) -> str:
    now = datetime.now().strftime("%B %Y")

    project_cards = ""
    for p in projects:
        tower_info = towers.get(p["tower"], {})
        tower_name = tower_info.get("name", p["tower"])
        featured_class = "featured" if p.get("featured") else ""
        featured_badge = '<span class="featured-badge">FEATURED</span>' if p.get("featured") else ""
        services_html = " ".join(f'<span class="service-tag">{s}</span>' for s in p.get("services", []))
        url_html = f'<a href="{p["url"]}" class="project-link" target="_blank" rel="noopener">View Project &rarr;</a>' if p.get("url") else ""

        project_cards += f"""
        <div class="project-card {featured_class}">
            {featured_badge}
            <div class="project-tower">{tower_name}</div>
            <h3 class="project-title">{p['title']}</h3>
            <div class="project-client">{p['client']}</div>
            <p class="project-desc">{p['description']}</p>
            <div class="project-services">{services_html}</div>
            <div class="project-result">{p.get('result', '')}</div>
            {url_html}
        </div>"""

    stats_towers = len(tower_groups)
    stats_projects = len(projects)
    stats_industries = len(set(p.get("industry", "") for p in projects if p.get("industry")))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Our Work — Marceau Solutions Portfolio</title>
    <meta name="description" content="See what Marceau Solutions has built. AI automation, websites, and coaching platforms for businesses in Southwest Florida.">
    <meta property="og:title" content="Marceau Solutions — Portfolio">
    <meta property="og:description" content="AI automation, websites, and coaching platforms for small businesses.">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root {{ --gold:#C9963C; --dark:#111; --card:#1a1a1a; --border:#2a2a2a; --text:#fff; --muted:#999; }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Inter',sans-serif; background:var(--dark); color:var(--text); }}
        .container {{ max-width:900px; margin:0 auto; padding:2rem 1.5rem; }}
        .header {{ text-align:center; padding:3rem 0; border-bottom:2px solid var(--gold); margin-bottom:3rem; }}
        .header h1 {{ font-size:2rem; font-weight:800; color:var(--gold); margin-bottom:0.5rem; }}
        .header p {{ color:var(--muted); font-size:1rem; margin-bottom:1.5rem; }}
        .stats {{ display:flex; gap:2rem; justify-content:center; flex-wrap:wrap; }}
        .stat {{ text-align:center; }}
        .stat-num {{ font-size:2rem; font-weight:800; color:var(--gold); }}
        .stat-label {{ font-size:0.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.1em; }}
        .project-card {{ background:var(--card); border:1px solid var(--border); border-radius:16px; padding:2rem; margin-bottom:1.5rem; position:relative; transition:all 0.3s; }}
        .project-card:hover {{ border-color:var(--gold); transform:translateY(-2px); }}
        .project-card.featured {{ border-color:var(--gold); background:linear-gradient(135deg, rgba(201,150,60,0.08), rgba(201,150,60,0.02)); }}
        .featured-badge {{ position:absolute; top:1rem; right:1rem; background:var(--gold); color:var(--dark); font-size:0.65rem; font-weight:700; padding:3px 10px; border-radius:10px; text-transform:uppercase; letter-spacing:0.05em; }}
        .project-tower {{ font-size:0.75rem; color:var(--gold); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem; }}
        .project-title {{ font-size:1.2rem; font-weight:700; margin-bottom:0.25rem; }}
        .project-client {{ font-size:0.9rem; color:var(--muted); margin-bottom:0.75rem; }}
        .project-desc {{ font-size:0.9rem; color:#bbb; line-height:1.6; margin-bottom:1rem; }}
        .project-services {{ display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.75rem; }}
        .service-tag {{ background:rgba(59,130,246,0.1); color:#60a5fa; padding:3px 10px; border-radius:12px; font-size:0.75rem; }}
        .project-result {{ font-size:0.85rem; color:var(--gold); font-style:italic; margin-bottom:0.75rem; }}
        .project-link {{ color:var(--gold); text-decoration:none; font-size:0.9rem; font-weight:600; }}
        .project-link:hover {{ text-decoration:underline; }}
        .cta {{ text-align:center; padding:3rem 2rem; background:var(--card); border:2px solid var(--gold); border-radius:16px; margin-top:3rem; }}
        .cta h2 {{ font-size:1.3rem; color:var(--gold); margin-bottom:0.5rem; }}
        .cta p {{ color:var(--muted); margin-bottom:1.5rem; }}
        .cta a {{ display:inline-block; background:var(--gold); color:var(--dark); font-weight:700; padding:0.8rem 2rem; border-radius:50px; text-decoration:none; }}
        .footer {{ text-align:center; padding:2rem; color:#444; font-size:0.75rem; margin-top:2rem; }}
        .footer a {{ color:var(--gold); text-decoration:none; }}
        @media (max-width:600px) {{ .container {{ padding:1rem; }} .project-card {{ padding:1.25rem; }} .stats {{ gap:1rem; }} }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Our Work</h1>
        <p>AI automation, websites, and coaching platforms for businesses in Southwest Florida.</p>
        <div class="stats">
            <div class="stat"><div class="stat-num">{stats_projects}</div><div class="stat-label">Projects</div></div>
            <div class="stat"><div class="stat-num">{stats_industries}</div><div class="stat-label">Industries</div></div>
            <div class="stat"><div class="stat-num">{stats_towers}</div><div class="stat-label">Service Lines</div></div>
        </div>
    </div>

    {project_cards}

    <div class="cta">
        <h2>Ready to Build Something?</h2>
        <p>Book a free 15-minute discovery call and let's talk about what AI can do for your business.</p>
        <a href="https://calendly.com/wmarceau/ai-services-discovery-call" target="_blank" rel="noopener">Book a Discovery Call</a>
    </div>

    <div class="footer">
        <p>Marceau Solutions &mdash; <a href="https://marceausolutions.com">marceausolutions.com</a> &mdash; Naples, FL</p>
        <p style="margin-top:0.5rem;">Portfolio auto-updated {now}</p>
    </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Portfolio Builder")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("list", help="List all portfolio projects")
    sub.add_parser("check", help="Check pipeline for new wins")
    sub.add_parser("generate", help="Generate portfolio page")
    args = parser.parse_args()

    if args.command == "list":
        list_projects()
    elif args.command == "check":
        added = check_pipeline()
        if added:
            generate_pages()
    elif args.command == "generate":
        generate_pages()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
