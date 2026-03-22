#!/usr/bin/env python3
"""
KeyVault SaaS — Seed William's organization with all known credentials.

Run: python -m projects.shared.api-key-manager.src.seed
"""

import os
from pathlib import Path
from dotenv import dotenv_values

from .models import (
    get_db, create_org, create_user, upsert_service, upsert_api_key,
    add_consumer, add_deprecation_notice, log_audit
)

MAC_ENV_PATH = Path(__file__).parents[4] / ".env"


def seed():
    conn = get_db()

    # Check if already seeded
    existing = conn.execute("SELECT id FROM organizations WHERE slug = 'marceau-solutions'").fetchone()
    if existing:
        print("Already seeded. Use --force to re-seed.")
        conn.close()
        return

    # Load actual key values from .env for encrypted storage
    env = dotenv_values(str(MAC_ENV_PATH)) if MAC_ENV_PATH.exists() else {}

    # Create org + owner
    org_id = create_org(conn, "Marceau Solutions", "marceau-solutions", "pro")
    user_id = create_user(conn, "wmarceau@marceausolutions.com", "keyvault2026!", "William Marceau", org_id, "owner")

    # Environments
    conn.execute("INSERT INTO environments (org_id, name, env_file_path, ssh_command, notes) VALUES (?, ?, ?, ?, ?)",
                 (org_id, "Mac Local", "~/dev-sandbox/.env", None, "Primary dev machine — source of truth"))
    conn.execute("INSERT INTO environments (org_id, name, env_file_path, ssh_command, notes) VALUES (?, ?, ?, ?, ?)",
                 (org_id, "EC2 Clawdbot", "/home/clawdbot/.clawdbot/.env", "ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97", "Clawdbot service env"))
    conn.execute("INSERT INTO environments (org_id, name, env_file_path, ssh_command, notes) VALUES (?, ?, ?, ?, ?)",
                 (org_id, "EC2 Dev-Sandbox", "/home/clawdbot/dev-sandbox/.env", "ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97", "EC2 copy of dev-sandbox"))
    conn.execute("INSERT INTO environments (org_id, name, env_file_path, ssh_command, notes) VALUES (?, ?, ?, ?, ?)",
                 (org_id, "n8n Credentials", "n8n credential store", None, "Encrypted credential store on EC2"))
    conn.commit()

    def _add(service_name, category, env_vars, dashboard_url=None, notes=None, consumers=None, **svc_kwargs):
        """Helper to add a service with multiple keys."""
        kw = {}
        if dashboard_url:
            kw["dashboard_url"] = dashboard_url
        if notes:
            kw["notes"] = notes
        sid = upsert_service(conn, org_id, service_name, category, **kw)
        key_ids = []
        for var_info in env_vars:
            if isinstance(var_info, str):
                var_name = var_info
                var_kwargs = {}
            else:
                var_name = var_info[0]
                var_kwargs = var_info[1] if len(var_info) > 1 else {}
            value = env.get(var_name)
            kid = upsert_api_key(conn, org_id, sid, var_name, value=value, **var_kwargs)
            key_ids.append(kid)
        if consumers:
            for c in consumers:
                add_consumer(conn, key_ids[0], *c)
        return sid, key_ids

    # ─── AI & Content ────────────────────────────────────────
    _add("Anthropic", "ai",
         [("ANTHROPIC_API_KEY", {"key_type": "api_key"}), ("Anthropic_Longlived_Token", {"key_type": "long_lived_token"})],
         "https://console.anthropic.com", "Claude API — primary AI",
         [("script", "execution/ scripts", "execution/"), ("bot", "Clawdbot"), ("workflow", "n8n AI workflows")])

    _add("xAI / Grok", "ai",
         [("XAI_API_KEY", {"key_type": "api_key", "notes": "Renewed 2026-03-06"})],
         "https://console.x.ai", "Image/video via Aurora",
         [("script", "grok_image_gen.py", "execution/grok_image_gen.py"), ("workflow", "X-Batch-Image-Generator")])

    _add("Replicate", "ai",
         [("REPLICATE_API_TOKEN", {"key_type": "api_token"})],
         "https://replicate.com/account", "SD, OmniHuman, Kling, Veo 3",
         [("script", "multi_provider_image_router.py"), ("script", "multi_provider_video_router.py")])

    _add("Creatomate", "ai",
         [("CREATOMATE_API_KEY", {"key_type": "api_key"}), ("CREATOMATE_TEMPLATE_ID", {"key_type": "config"})],
         "https://creatomate.com/dashboard")

    _add("Shotstack", "ai",
         [("SHOTSTACK_API_KEY", {"key_type": "api_key"}), ("SHOTSTACK_ENV", {"key_type": "config"})],
         "https://dashboard.shotstack.io", "Legacy video backup")

    _add("ElevenLabs", "ai",
         [("ELEVENLABS_API_KEY", {"key_type": "api_key"})],
         "https://elevenlabs.io/app/settings", "Only TTS provider",
         [("script", "Voice API"), ("workflow", "Voice workflows")])

    _add("OpenAI", "ai",
         [("OPENAI_API_KEY", {"key_type": "api_key", "notes": "Check if still needed — mem0 embeddings?"})],
         "https://platform.openai.com")

    _add("Google Gemini", "ai",
         [("GOOGLE_GEMINI_API_KEY", {"key_type": "api_key"})],
         "https://aistudio.google.com")

    _add("fal.ai", "ai",
         [("FAL_API_KEY", {"key_type": "api_key", "status": "retired", "notes": "Balance exhausted"})],
         "https://fal.ai/dashboard")

    _add("Resemble AI", "ai",
         [("RESEMBLE_API_KEY", {"key_type": "api_key", "status": "retired"})],
         notes="Test-only, never production")

    # ─── Communication ───────────────────────────────────────
    _add("Gmail SMTP", "communication",
         [("SMTP_USERNAME", {"key_type": "username"}), ("SMTP_PASSWORD", {"key_type": "app_password"}), ("SMTP_HOST", {"key_type": "config"})],
         notes="Workspace app password — wmarceau@marceausolutions.com",
         consumers=[("script", "send_onboarding_email.py", "execution/send_onboarding_email.py")])

    _add("Google OAuth", "communication",
         [("GOOGLE_CLIENT_ID", {"key_type": "oauth_client_id"}), ("GOOGLE_CLIENT_SECRET", {"key_type": "oauth_client_secret"}), ("GOOGLE_PROJECT_ID", {"key_type": "config"})],
         "https://console.cloud.google.com", "Project: fitness-influencer-assistant")

    _add("Twilio", "communication",
         [("TWILIO_ACCOUNT_SID", {"key_type": "account_sid"}), ("TWILIO_AUTH_TOKEN", {"key_type": "auth_token"}),
          ("TWILIO_PHONE_NUMBER", {"key_type": "config", "notes": "+1 855-239-9364 (A2P)"}),
          ("TWILIO_PHONE_NUMBER_LOCAL", {"key_type": "config", "notes": "+1 239-880-3365 (inactive)"})],
         "https://console.twilio.com", "A2P registered toll-free",
         [("script", "twilio_sms.py", "execution/twilio_sms.py"), ("workflow", "SMS workflows")])

    _add("Telegram", "communication",
         [("TELEGRAM_BOT_TOKEN", {"key_type": "bot_token", "notes": "Goes stale — patch via health_check.py"}),
          ("TELEGRAM_CHAT_ID", {"key_type": "config"})],
         notes="Clawdbot @w_marceaubot",
         consumers=[("bot", "Clawdbot"), ("workflow", "GitHub→Telegram")])

    _add("n8n", "communication",
         [("N8N_API_KEY", {"key_type": "api_key"})],
         "https://n8n.marceausolutions.com",
         consumers=[("script", "health_check.py"), ("script", "agent_bridge_api.py")])

    # ─── Business ────────────────────────────────────────────
    _add("Stripe", "business",
         [("STRIPE_SECRET_KEY", {"key_type": "secret_key"}), ("STRIPE_WEBHOOK_SECRET", {"key_type": "webhook_secret"})],
         "https://dashboard.stripe.com", "Live keys, 6 webhooks",
         [("script", "stripe_payments.py"), ("script", "revenue_analytics.py"), ("workflow", "Stripe webhooks")])

    sid, _ = _add("Apollo.io", "business",
         [("APOLLO_API_KEY", {"key_type": "api_key", "notes": "Auth moved to X-Api-Key header"})],
         "https://app.apollo.io", "Lead enrichment — endpoints deprecated Feb 2026, FIXED",
         [("mcp", "apollo-mcp"), ("script", "apollo.py (lead-scraper)"), ("script", "build-naples-prospect-list.py")])
    add_deprecation_notice(conn, org_id, sid,
        "Endpoints deprecated: mixed_people/search → api_search, auth → header",
        notice_date="2026-02-01", effective_date="2026-02-28",
        migration_notes="Fixed in commit bd8086b6")
    conn.execute("UPDATE deprecation_notices SET status = 'resolved', resolved_at = '2026-03-22' WHERE org_id = ? AND status = 'active'", (org_id,))
    conn.commit()

    _add("Hunter.io", "business",
         [("HUNTER_API_KEY", {"key_type": "api_key", "status": "empty"})],
         notes="Not configured")

    _add("Amazon SP-API", "business",
         [("AMAZON_REFRESH_TOKEN", {"key_type": "refresh_token"}), ("AMAZON_LWA_APP_ID", {"key_type": "app_id"}),
          ("AMAZON_LWA_CLIENT_SECRET", {"key_type": "client_secret"}), ("AMAZON_AWS_ACCESS_KEY", {"key_type": "access_key"}),
          ("AMAZON_AWS_SECRET_KEY", {"key_type": "secret_key"}), ("AMAZON_ROLE_ARN", {"key_type": "config"}),
          ("AMAZON_MARKETPLACE_ID", {"key_type": "config"})],
         "https://sellercentral.amazon.com", "7 credentials for SP-API",
         [("script", "amazon_sp_api.py")])

    # ─── Social ──────────────────────────────────────────────
    _add("X / Twitter", "social",
         [("X_API_KEY", {"key_type": "consumer_key", "auth_protocol": "oauth1", "monthly_cost": 8.0}),
          ("X_API_SECRET", {"key_type": "consumer_secret", "auth_protocol": "oauth1"}),
          ("X_ACCESS_TOKEN", {"key_type": "access_token", "auth_protocol": "oauth1", "notes": "Permanent — no expiry"}),
          ("X_ACCESS_TOKEN_SECRET", {"key_type": "access_token_secret", "auth_protocol": "oauth1"}),
          ("X_BEARER_TOKEN", {"key_type": "bearer_token", "auth_protocol": "oauth2"})],
         "https://developer.twitter.com/en/portal/dashboard", "OAuth 1.0a — tokens never expire. Premium $8/mo",
         [("script", "x_api.py"), ("workflow", "X-Social-Post-Scheduler-v2"), ("bot", "Clawdbot")])

    _add("YouTube", "social",
         [("YOUTUBE_CLIENT_ID", {"key_type": "oauth_client_id"}), ("YOUTUBE_CLIENT_SECRET", {"key_type": "oauth_client_secret"}),
          ("YOUTUBE_REFRESH_TOKEN", {"key_type": "refresh_token"})],
         "https://console.cloud.google.com")

    _add("TikTok", "social",
         [("TIKTOK_CLIENT_KEY", {"key_type": "client_key"}), ("TIKTOK_CLIENT_SECRET", {"key_type": "client_secret"})],
         "https://developers.tiktok.com", "Sandbox mode")

    _add("LinkedIn (Personal)", "social",
         [("LINKEDIN_CLIENT_ID", {"key_type": "client_id"}), ("LINKEDIN_CLIENT_SECRET", {"key_type": "client_secret"}),
          ("LINKEDIN_ACCESS_TOKEN", {"key_type": "access_token", "expires_at": "2026-05-21", "notes": "60-day tokens"})],
         "https://www.linkedin.com/developers")

    _add("LinkedIn (Company)", "social",
         [("LINKEDIN_COMPANY_CLIENT_ID", {"key_type": "client_id", "status": "empty"}),
          ("LINKEDIN_COMPANY_CLIENT_SECRET", {"key_type": "client_secret", "status": "empty"}),
          ("LINKEDIN_COMPANY_ACCESS_TOKEN", {"key_type": "access_token", "status": "empty"})],
         notes="EMPTY — not configured")

    # ─── Monitoring ──────────────────────────────────────────
    _add("Langfuse", "monitoring",
         [("LANGFUSE_SECRET_KEY", {"key_type": "secret_key"}), ("LANGFUSE_PUBLIC_KEY", {"key_type": "public_key"}),
          ("LANGFUSE_BASE_URL", {"key_type": "config"})],
         "https://cloud.langfuse.com")

    _add("Helicone", "monitoring",
         [("HELICONE_API_KEY", {"key_type": "api_key"})],
         "https://www.helicone.ai/dashboard")

    # ─── Infrastructure ─────────────────────────────────────
    _add("Google Places", "infrastructure",
         [("GOOGLE_PLACES_API_KEY", {"key_type": "api_key"})],
         "https://console.cloud.google.com")

    _add("Yelp", "infrastructure",
         [("YELP_CLIENT_ID", {"key_type": "client_id"}), ("YELP_API_KEY", {"key_type": "api_key"})],
         "https://www.yelp.com/developers")

    _add("PyPI", "infrastructure",
         [("PYPI_TOKEN", {"key_type": "api_token"})],
         "https://pypi.org/manage/account/", "MCP package publishing")

    # Google Sheets (config values)
    _add("Google Sheets", "infrastructure",
         [("GOOGLE_SHEETS_SPREADSHEET_ID", {"key_type": "config"}), ("SOCIAL_MEDIA_SPREADSHEET_ID", {"key_type": "config"}),
          ("COACHING_TRACKER_SPREADSHEET_ID", {"key_type": "config"}), ("HVAC_LEADS_SHEET_ID", {"key_type": "config"}),
          ("SQUAREFOOT_LEADS_SHEET_ID", {"key_type": "config"}), ("SCORECARD_SPREADSHEET_ID", {"key_type": "config"})],
         notes="6 spreadsheets tracked")

    log_audit(conn, org_id, "database_seeded", details="Initial seed with all known credentials", user_id=user_id)

    total_services = conn.execute("SELECT COUNT(*) FROM services WHERE org_id = ?", (org_id,)).fetchone()[0]
    total_keys = conn.execute("SELECT COUNT(*) FROM api_keys WHERE org_id = ?", (org_id,)).fetchone()[0]
    total_consumers = conn.execute("SELECT COUNT(*) FROM key_consumers").fetchone()[0]
    total_encrypted = conn.execute("SELECT COUNT(*) FROM api_keys WHERE org_id = ? AND encrypted_value IS NOT NULL", (org_id,)).fetchone()[0]

    print(f"Seeded: {total_services} services, {total_keys} keys ({total_encrypted} encrypted), {total_consumers} consumers")
    print(f"Login: wmarceau@marceausolutions.com / keyvault2026!")
    conn.close()


if __name__ == "__main__":
    import sys
    if "--force" in sys.argv:
        import os
        db_path = Path(__file__).parent.parent / "data" / "keyvault.db"
        if db_path.exists():
            os.remove(str(db_path))
            print("Database deleted.")
    seed()
