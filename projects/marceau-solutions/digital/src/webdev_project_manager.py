#!/usr/bin/env python3
"""
webdev_project_manager.py - Web Development Tower Project Lifecycle Manager

Manages the full website project lifecycle: proposal → build → deploy → maintain

LIFECYCLE STAGES:
  proposal   → Client interested, preparing proposal
  approved   → Deal closed, project kicked off
  research   → Gathering business info and brand personality
  content    → Generating website copy with AI
  build      → Building static site from templates
  review     → Client reviewing staging site
  revision   → Making client-requested changes
  deploy     → Pushing to production hosting
  live       → Site launched and operational
  maintenance → Ongoing monthly maintenance
  archived   → Project completed or cancelled

INTEGRATION:
  - Uses website-builder modules (research_engine, content_generator, site_builder)
  - Triggers n8n workflows for notifications
  - Stores artifacts in pipeline.db
  - Outputs sites to /home/clawdbot/dev-sandbox/client-sites/

USAGE:
  from execution.webdev_project_manager import WebDevProjectManager

  mgr = WebDevProjectManager()
  project = mgr.create_project(deal_id=123, project_name="acme-corp")
  mgr.run_research(project['id'])
  mgr.generate_content(project['id'])
  mgr.build_site(project['id'])
  mgr.deploy_to_github_pages(project['id'])
"""

import os
import sys
import json
import sqlite3
import subprocess
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Add project paths
sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[1] / "projects/ai-systems/src/website-builder/src"))

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────

DB_PATH = Path("/home/clawdbot/data/pipeline.db")
CLIENT_SITES_DIR = Path("/home/clawdbot/dev-sandbox/client-sites")
WEBSITE_BUILDER_SRC = Path("/home/clawdbot/dev-sandbox/projects/ai-systems/src/website-builder/src")

# n8n webhook URLs (configured in n8n)
N8N_BASE = os.getenv("N8N_WEBHOOK_URL", "https://n8n.marceausolutions.com/webhook")
N8N_WEBHOOKS = {
    "payment_welcome": f"{N8N_BASE}/webdev-payment-welcome",
    "deploy_notification": f"{N8N_BASE}/webdev-deploy-notification", 
    "monthly_checkin": f"{N8N_BASE}/webdev-monthly-checkin",
}

# Project lifecycle stages
STAGES = [
    "proposal", "approved", "research", "content", "build",
    "review", "revision", "deploy", "live", "maintenance", "archived"
]


class WebDevProjectManager:
    """
    Manages web development projects from proposal to maintenance.
    Wires together website-builder modules for automated site generation.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.client_sites_dir = CLIENT_SITES_DIR
        self.client_sites_dir.mkdir(parents=True, exist_ok=True)
        
        # Lazy-load website builder modules
        self._research_engine = None
        self._content_generator = None
        self._site_builder = None

    def _get_db(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _load_website_builder(self):
        """Lazy-load website builder modules."""
        if self._research_engine is None:
            try:
                # Add website-builder to path and import as package
                import importlib.util
                
                wb_path = WEBSITE_BUILDER_SRC
                
                # Load modules individually handling relative imports
                def load_module(name):
                    spec = importlib.util.spec_from_file_location(
                        name, wb_path / f"{name}.py"
                    )
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    return module
                
                # Import directly - these don't have relative imports
                content_mod = load_module("content_generator")
                site_mod = load_module("site_builder")
                
                self._content_generator = content_mod.ContentGenerator()
                self._site_builder = site_mod.SiteBuilder()
                
                # Research engine has relative imports, try package import
                try:
                    # Ensure the src directory is a package
                    init_path = wb_path / "__init__.py"
                    if not init_path.exists():
                        init_path.touch()
                    
                    # Add parent to path for package import
                    parent_path = str(wb_path.parent)
                    if parent_path not in sys.path:
                        sys.path.insert(0, parent_path)
                    
                    from src.research_engine import ResearchEngine
                    self._research_engine = ResearchEngine()
                except ImportError:
                    # Fallback: create minimal research engine
                    logger.warning("Using fallback research engine")
                    self._research_engine = self._create_fallback_research_engine()
                
                logger.info("Website builder modules loaded successfully")
            except ImportError as e:
                logger.warning(f"Could not import website-builder: {e}")
                raise
    
    def _create_fallback_research_engine(self):
        """Create a minimal fallback research engine."""
        class FallbackResearchEngine:
            def research_company(self, company_name, owner_name=None):
                return {
                    "company": {
                        "name": company_name,
                        "industry": "General",
                        "location": "",
                        "description": f"{company_name} is a local business.",
                        "services": ["Professional Services"],
                        "target_audience": "Local customers",
                        "unique_selling_points": ["Quality service", "Local expertise"]
                    },
                    "owner": {
                        "name": owner_name or "Owner",
                        "title": "Owner",
                        "background": "",
                        "expertise": []
                    },
                    "tone": "professional",
                    "color_scheme": {
                        "primary": "#1a1a2e",
                        "secondary": "#667eea",
                        "accent": "#4ade80"
                    }
                }
            
            def research_with_social(self, company_name, owner_name=None, social_profiles=None):
                return self.research_company(company_name, owner_name)
        
        return FallbackResearchEngine()

    # ── Project CRUD ─────────────────────────────────────────────────────────

    def create_project(
        self,
        deal_id: int,
        project_name: str,
        project_type: str = "new_site",
        domain: str = None,
        setup_fee: float = 0,
        monthly_fee: float = 0,
        target_launch: str = None,
    ) -> Dict[str, Any]:
        """
        Create a new web development project.
        
        Args:
            deal_id: Associated deal ID from pipeline
            project_name: Slug-friendly project name (e.g., "acme-corp")
            project_type: new_site | redesign | landing_page | maintenance
            domain: Target domain (e.g., "acmecorp.com")
            setup_fee: One-time setup fee
            monthly_fee: Monthly maintenance fee
            target_launch: Target launch date (YYYY-MM-DD)
            
        Returns:
            Created project dict with ID
        """
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Set default target launch to 2 weeks from now
        if not target_launch:
            target_launch = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO webdev_projects 
            (deal_id, project_name, project_type, domain, setup_fee, monthly_fee, 
             target_launch, proposal_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'proposal')
        """, (deal_id, project_name, project_type, domain, setup_fee, monthly_fee, target_launch))
        
        project_id = cursor.lastrowid
        conn.commit()
        
        # Create output directory
        output_dir = self.client_sites_dir / project_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Update with output dir
        cursor.execute("""
            UPDATE webdev_projects SET output_dir = ? WHERE id = ?
        """, (str(output_dir), project_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Created project {project_id}: {project_name}")
        return self.get_project(project_id)

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM webdev_projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_project_by_deal(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """Get project by deal ID."""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM webdev_projects WHERE deal_id = ?", (deal_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_projects(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List projects, optionally filtered by status."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT wp.*, d.company, d.contact_name, d.contact_email
                FROM webdev_projects wp
                LEFT JOIN deals d ON wp.deal_id = d.id
                WHERE wp.status = ?
                ORDER BY wp.updated_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT wp.*, d.company, d.contact_name, d.contact_email
                FROM webdev_projects wp
                LEFT JOIN deals d ON wp.deal_id = d.id
                ORDER BY wp.updated_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_status(
        self,
        project_id: int,
        new_status: str,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Update project status with automatic timestamp tracking.
        """
        if new_status not in STAGES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {STAGES}")
        
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Update status and timestamp
        cursor.execute("""
            UPDATE webdev_projects 
            SET status = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (new_status, project_id))
        
        # Track stage-specific timestamps
        if new_status == "approved":
            cursor.execute("UPDATE webdev_projects SET approved_date = datetime('now') WHERE id = ?", (project_id,))
        elif new_status == "live":
            cursor.execute("UPDATE webdev_projects SET launched_at = datetime('now') WHERE id = ?", (project_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Project {project_id} status → {new_status}")
        return self.get_project(project_id)

    # ── Research Phase ───────────────────────────────────────────────────────

    def run_research(
        self,
        project_id: int,
        company_name: str = None,
        owner_name: str = None,
        social_profiles: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """
        Run research phase using website-builder research engine.
        
        Args:
            project_id: Project ID
            company_name: Override company name (defaults to deal company)
            owner_name: Owner/founder name
            social_profiles: Dict of social URLs {platform: url}
            
        Returns:
            Research results dict
        """
        self._load_website_builder()
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get deal info for defaults
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deals WHERE id = ?", (project['deal_id'],))
        row = cursor.fetchone()
        deal = dict(row) if row else {}
        conn.close()
        
        company_name = company_name or deal.get('company', project['project_name'])
        
        # Run research
        logger.info(f"Running research for project {project_id}: {company_name}")
        
        if social_profiles:
            research = self._research_engine.research_with_social(
                company_name=company_name,
                owner_name=owner_name,
                social_profiles=social_profiles
            )
        else:
            research = self._research_engine.research_company(
                company_name=company_name,
                owner_name=owner_name
            )
        
        # Store research JSON
        if hasattr(research, 'to_dict'):
            research_dict = research.to_dict()
        elif hasattr(research, '__dataclass_fields__'):
            # Convert dataclass to dict recursively
            from dataclasses import asdict
            research_dict = asdict(research)
        else:
            research_dict = research
        
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE webdev_projects 
            SET research_json = ?, status = 'research', updated_at = datetime('now')
            WHERE id = ?
        """, (json.dumps(research_dict), project_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Research complete for project {project_id}")
        return research_dict

    # ── Content Generation ───────────────────────────────────────────────────

    def generate_content(self, project_id: int) -> Dict[str, Any]:
        """
        Generate website content from research data.
        
        Uses ContentGenerator with personality-driven copy if brand_personality exists.
        """
        self._load_website_builder()
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        if not project.get('research_json'):
            raise ValueError(f"Project {project_id} has no research data. Run research first.")
        
        research = json.loads(project['research_json'])
        
        logger.info(f"Generating content for project {project_id}")
        
        # Use personality content if available
        if research.get('brand_personality'):
            content = self._content_generator.generate_personality_content(research)
        else:
            content = self._content_generator.generate_content(research)
        
        content_dict = self._content_generator.to_dict(content)
        
        # Store content JSON
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE webdev_projects 
            SET content_json = ?, status = 'content', updated_at = datetime('now')
            WHERE id = ?
        """, (json.dumps(content_dict), project_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Content generation complete for project {project_id}")
        return content_dict

    # ── Site Building ────────────────────────────────────────────────────────

    def build_site(self, project_id: int) -> Dict[str, str]:
        """
        Build static website from research and content data.
        
        Returns:
            Dict of generated file paths
        """
        self._load_website_builder()
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        if not project.get('content_json'):
            raise ValueError(f"Project {project_id} has no content. Generate content first.")
        
        research = json.loads(project.get('research_json', '{}'))
        content = json.loads(project['content_json'])
        output_dir = project.get('output_dir') or str(self.client_sites_dir / project['project_name'])
        
        logger.info(f"Building site for project {project_id} → {output_dir}")
        
        # Use personality site builder if brand_personality exists
        if research.get('brand_personality'):
            files = self._site_builder.build_personality_site(research, content, output_dir)
        else:
            files = self._site_builder.build_site(research, content, output_dir)
        
        # Update status
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE webdev_projects 
            SET status = 'build', updated_at = datetime('now')
            WHERE id = ?
        """, (project_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Site build complete: {len(files)} files generated")
        return files

    # ── Deployment ───────────────────────────────────────────────────────────

    def deploy_to_github_pages(
        self,
        project_id: int,
        repo_name: str = None,
        commit_message: str = None
    ) -> Dict[str, Any]:
        """
        Deploy site to GitHub Pages.
        
        Args:
            project_id: Project ID
            repo_name: GitHub repo name (defaults to project_name)
            commit_message: Commit message
            
        Returns:
            Deployment result dict
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        output_dir = Path(project.get('output_dir', ''))
        if not output_dir.exists():
            raise ValueError(f"Output directory does not exist: {output_dir}")
        
        repo_name = repo_name or project['project_name']
        commit_message = commit_message or f"Deploy {project['project_name']} - {datetime.now().isoformat()}"
        
        logger.info(f"Deploying project {project_id} to GitHub Pages: {repo_name}")
        
        # Initialize git if needed
        git_dir = output_dir / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=output_dir, check=True)
            subprocess.run(["git", "checkout", "-b", "main"], cwd=output_dir, check=True)
        
        # Add and commit
        subprocess.run(["git", "add", "."], cwd=output_dir, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=output_dir,
            capture_output=True,
            text=True
        )
        
        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=output_dir,
            capture_output=True,
            text=True
        )
        commit_sha = sha_result.stdout.strip()[:7] if sha_result.returncode == 0 else None
        
        # Check if remote exists, add if not
        remote_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=output_dir,
            capture_output=True
        )
        
        if remote_result.returncode != 0:
            # Add remote (assumes repo exists on GitHub)
            github_url = f"git@github.com:marceaupatu/{repo_name}.git"
            subprocess.run(["git", "remote", "add", "origin", github_url], cwd=output_dir, check=True)
        
        # Push to GitHub
        push_result = subprocess.run(
            ["git", "push", "-u", "origin", "main", "--force"],
            cwd=output_dir,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            logger.warning(f"Push may have failed: {push_result.stderr}")
        
        # Construct live URL
        live_url = f"https://marceaupatu.github.io/{repo_name}/"
        
        # Record deployment
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO webdev_deployments 
            (project_id, version, deploy_type, commit_sha, deployed_to, notes)
            VALUES (?, '1.0.0', 'initial', ?, 'github_pages', ?)
        """, (project_id, commit_sha, commit_message))
        
        cursor.execute("""
            UPDATE webdev_projects 
            SET github_repo = ?, live_url = ?, status = 'deploy', 
                hosting_provider = 'github_pages', updated_at = datetime('now')
            WHERE id = ?
        """, (repo_name, live_url, project_id))
        
        conn.commit()
        conn.close()
        
        # Trigger n8n notification
        self._trigger_webhook("deploy_notification", {
            "project_id": project_id,
            "project_name": project['project_name'],
            "live_url": live_url,
            "deployed_at": datetime.now().isoformat()
        })
        
        logger.info(f"Deployment complete: {live_url}")
        return {
            "project_id": project_id,
            "repo_name": repo_name,
            "live_url": live_url,
            "commit_sha": commit_sha,
            "success": push_result.returncode == 0
        }

    def mark_live(self, project_id: int) -> Dict[str, Any]:
        """Mark project as live after client approval."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE webdev_projects 
            SET status = 'live', launched_at = datetime('now'),
                next_checkin = date('now', '+30 days'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (project_id,))
        
        conn.commit()
        conn.close()
        
        project = self.get_project(project_id)
        
        # Trigger welcome webhook
        self._trigger_webhook("payment_welcome", {
            "project_id": project_id,
            "project_name": project['project_name'],
            "live_url": project.get('live_url'),
            "launched_at": project.get('launched_at')
        })
        
        logger.info(f"Project {project_id} marked as live")
        return project

    # ── Maintenance ──────────────────────────────────────────────────────────

    def get_projects_due_checkin(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get projects due for monthly check-in within N days."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT wp.*, d.company, d.contact_name, d.contact_email
            FROM webdev_projects wp
            LEFT JOIN deals d ON wp.deal_id = d.id
            WHERE wp.status IN ('live', 'maintenance')
            AND (wp.next_checkin IS NULL OR wp.next_checkin <= date('now', '+' || ? || ' days'))
            ORDER BY wp.next_checkin ASC
        """, (days_ahead,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def record_checkin(
        self,
        project_id: int,
        notes: str = None,
        next_checkin_days: int = 30
    ) -> Dict[str, Any]:
        """Record a maintenance check-in."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE webdev_projects 
            SET last_checkin = datetime('now'),
                next_checkin = date('now', '+' || ? || ' days'),
                maintenance_notes = COALESCE(maintenance_notes || char(10), '') || 
                    datetime('now') || ': ' || ?,
                status = 'maintenance',
                updated_at = datetime('now')
            WHERE id = ?
        """, (next_checkin_days, notes or "Monthly check-in", project_id))
        
        conn.commit()
        conn.close()
        
        project = self.get_project(project_id)
        
        # Trigger check-in webhook
        self._trigger_webhook("monthly_checkin", {
            "project_id": project_id,
            "project_name": project['project_name'],
            "live_url": project.get('live_url'),
            "notes": notes,
            "next_checkin": project.get('next_checkin')
        })
        
        logger.info(f"Check-in recorded for project {project_id}")
        return project

    # ── Statistics ───────────────────────────────────────────────────────────

    def get_tower_stats(self) -> Dict[str, Any]:
        """Get web-dev tower statistics."""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # Projects by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM webdev_projects
            GROUP BY status
        """)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total revenue
        cursor.execute("""
            SELECT 
                SUM(setup_fee) as total_setup,
                SUM(monthly_fee) as total_monthly,
                COUNT(*) as total_projects
            FROM webdev_projects
            WHERE status NOT IN ('archived', 'proposal')
        """)
        revenue = dict(cursor.fetchone())
        
        # Active projects (not archived)
        cursor.execute("""
            SELECT COUNT(*) FROM webdev_projects WHERE status != 'archived'
        """)
        active = cursor.fetchone()[0]
        
        # Due for check-in
        cursor.execute("""
            SELECT COUNT(*) FROM webdev_projects 
            WHERE status IN ('live', 'maintenance')
            AND next_checkin <= date('now', '+7 days')
        """)
        due_checkin = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "by_status": by_status,
            "revenue": revenue,
            "active_projects": active,
            "due_for_checkin": due_checkin,
            "timestamp": datetime.now().isoformat()
        }

    # ── Webhooks ─────────────────────────────────────────────────────────────

    def _trigger_webhook(self, webhook_name: str, payload: Dict[str, Any]) -> bool:
        """Trigger n8n webhook."""
        url = N8N_WEBHOOKS.get(webhook_name)
        if not url:
            logger.warning(f"Unknown webhook: {webhook_name}")
            return False
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Webhook {webhook_name} triggered successfully")
            return True
        except requests.RequestException as e:
            logger.warning(f"Webhook {webhook_name} failed: {e}")
            return False

    # ── Full Pipeline ────────────────────────────────────────────────────────

    def run_full_pipeline(
        self,
        deal_id: int,
        project_name: str,
        company_name: str = None,
        owner_name: str = None,
        social_profiles: Dict[str, str] = None,
        auto_deploy: bool = False
    ) -> Dict[str, Any]:
        """
        Run the full website generation pipeline.
        
        Stages: create → research → content → build → (deploy)
        
        Args:
            deal_id: Deal ID from pipeline
            project_name: Slug-friendly project name
            company_name: Company name (defaults to deal company)
            owner_name: Owner name for research
            social_profiles: Social profile URLs
            auto_deploy: If True, auto-deploy to GitHub Pages
            
        Returns:
            Final project dict with all artifacts
        """
        logger.info(f"Starting full pipeline for {project_name}")
        
        # 1. Create project
        project = self.create_project(deal_id=deal_id, project_name=project_name)
        project_id = project['id']
        
        # 2. Research
        self.run_research(
            project_id=project_id,
            company_name=company_name,
            owner_name=owner_name,
            social_profiles=social_profiles
        )
        
        # 3. Content
        self.generate_content(project_id)
        
        # 4. Build
        files = self.build_site(project_id)
        
        # 5. Deploy (if requested)
        if auto_deploy:
            self.deploy_to_github_pages(project_id)
        
        project = self.get_project(project_id)
        project['generated_files'] = files
        
        logger.info(f"Full pipeline complete for {project_name}")
        return project


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """CLI for webdev project management."""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Web Development Project Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create
    create_parser = subparsers.add_parser("create", help="Create new project")
    create_parser.add_argument("--deal-id", type=int, required=True)
    create_parser.add_argument("--name", required=True, help="Project name (slug)")
    create_parser.add_argument("--type", default="new_site", choices=["new_site", "redesign", "landing_page"])
    create_parser.add_argument("--domain", help="Target domain")
    
    # list
    list_parser = subparsers.add_parser("list", help="List projects")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=20)
    
    # research
    research_parser = subparsers.add_parser("research", help="Run research phase")
    research_parser.add_argument("project_id", type=int)
    research_parser.add_argument("--company", help="Company name override")
    research_parser.add_argument("--owner", help="Owner name")
    
    # build
    build_parser = subparsers.add_parser("build", help="Build site")
    build_parser.add_argument("project_id", type=int)
    
    # deploy
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to GitHub Pages")
    deploy_parser.add_argument("project_id", type=int)
    
    # stats
    subparsers.add_parser("stats", help="Show tower statistics")
    
    # checkin
    checkin_parser = subparsers.add_parser("checkin", help="Record maintenance check-in")
    checkin_parser.add_argument("project_id", type=int)
    checkin_parser.add_argument("--notes", help="Check-in notes")
    
    # due
    subparsers.add_parser("due", help="Show projects due for check-in")
    
    # pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Run full pipeline")
    pipeline_parser.add_argument("--deal-id", type=int, required=True)
    pipeline_parser.add_argument("--name", required=True)
    pipeline_parser.add_argument("--company", help="Company name")
    pipeline_parser.add_argument("--owner", help="Owner name")
    pipeline_parser.add_argument("--deploy", action="store_true", help="Auto-deploy")
    
    args = parser.parse_args()
    mgr = WebDevProjectManager()
    
    if args.command == "create":
        result = mgr.create_project(
            deal_id=args.deal_id,
            project_name=args.name,
            project_type=args.type,
            domain=args.domain
        )
        print(json.dumps(result, indent=2, default=str))
    
    elif args.command == "list":
        projects = mgr.list_projects(status=args.status, limit=args.limit)
        for p in projects:
            print(f"[{p['id']}] {p['project_name']} | {p['status']} | {p.get('company', 'N/A')}")
    
    elif args.command == "research":
        result = mgr.run_research(
            project_id=args.project_id,
            company_name=args.company,
            owner_name=args.owner
        )
        print(json.dumps(result, indent=2, default=str))
    
    elif args.command == "build":
        files = mgr.build_site(args.project_id)
        print(f"Generated {len(files)} files:")
        for name, path in files.items():
            print(f"  {name}: {path}")
    
    elif args.command == "deploy":
        result = mgr.deploy_to_github_pages(args.project_id)
        print(json.dumps(result, indent=2, default=str))
    
    elif args.command == "stats":
        stats = mgr.get_tower_stats()
        print(json.dumps(stats, indent=2, default=str))
    
    elif args.command == "checkin":
        result = mgr.record_checkin(args.project_id, notes=args.notes)
        print(f"Check-in recorded. Next check-in: {result.get('next_checkin')}")
    
    elif args.command == "due":
        due = mgr.get_projects_due_checkin()
        if due:
            print(f"Projects due for check-in ({len(due)}):")
            for p in due:
                print(f"  [{p['id']}] {p['project_name']} | Due: {p.get('next_checkin', 'ASAP')} | {p.get('contact_email', 'N/A')}")
        else:
            print("No projects due for check-in")
    
    elif args.command == "pipeline":
        result = mgr.run_full_pipeline(
            deal_id=args.deal_id,
            project_name=args.name,
            company_name=args.company,
            owner_name=args.owner,
            auto_deploy=args.deploy
        )
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
