# CLI Commands Reference

> Single source of truth for all runnable commands in dev-sandbox.
> Last updated: 2026-03-06 | ~140 commands across 13 categories

---

## Quick Reference

```bash
# Start the day (health + revenue + digest + links)
./scripts/daily_standup.sh

# System health check
python scripts/health_check.py          # Full: EC2 services, n8n workflows, disk, clawdbot
python scripts/health_check.py --fast   # Local only (no SSH)

# Revenue snapshot
python scripts/revenue-report.py        # Last 7 days: Stripe, leads, SMS campaigns

# Search for a tool
python scripts/inventory.py search <keyword>

# Check API balances
python scripts/check_api_balances.py

# List all projects
python scripts/inventory.py list
```

---

## Inventory & Discovery

| Command | Path | Description |
|---------|------|-------------|
| `python scripts/inventory.py search <keyword>` | `scripts/inventory.py` | Search tool & project inventory |
| `python scripts/inventory.py list` | `scripts/inventory.py` | List all projects |
| `python scripts/inventory.py scripts` | `scripts/inventory.py` | List all scripts |

## Deployment

| Command | Path | Description |
|---------|------|-------------|
| `python deploy_to_skills.py --project <name> --version X.Y.Z` | `deploy_to_skills.py` | Deploy projects to production Skills workspaces |
| `python execution/manage_agent_skills.py` | `execution/manage_agent_skills.py` | Manage Claude Code Skills |
| `python execution/update_skill_docs.py` | `execution/update_skill_docs.py` | Update skill documentation |

## Personal Assistant

| Command | Path | Description |
|---------|------|-------------|
| `python -m src.morning_digest --preview` | `projects/shared/personal-assistant/src/morning_digest.py` | Generate and send morning digest emails |
| `python -m src.digest_aggregator` | `projects/shared/personal-assistant/src/digest_aggregator.py` | Combine data from Gmail, SMS, forms, calendar |
| `python -m src.smart_calendar` | `projects/shared/personal-assistant/src/smart_calendar.py` | AI-powered time block scheduling (Hormozi framework) |
| `python -m src.fitness_calendar` | `projects/shared/personal-assistant/src/fitness_calendar.py` | Workout schedule management |
| `python -m src.routine_scheduler` | `projects/shared/personal-assistant/src/routine_scheduler.py` | Create recurring Google Calendar events |
| `python -m src.ideas_queue` | `projects/shared/personal-assistant/src/ideas_queue.py` | Process ideas captured via Telegram |
| `python -m src.ai_news_digest` | `projects/shared/personal-assistant/src/ai_news_digest.py` | AI/tech news aggregation |
| `python -m src.restaurant_finder` | `projects/shared/personal-assistant/src/restaurant_finder.py` | Local restaurant recommendations |
| `python -m src.check_form_submissions` | `projects/shared/personal-assistant/src/check_form_submissions.py` | Check form submission data |
| `python -m src.create_time_blocks` | `projects/shared/personal-assistant/src/create_time_blocks.py` | Time blocking for focus work |

## Lead Scraper & SMS Campaigns

| Command | Path | Description |
|---------|------|-------------|
| `python -m src.scraper` | `projects/shared/lead-scraper/src/scraper.py` | Main CLI for local business lead generation |
| `python -m src.campaign_analytics report` | `projects/shared/lead-scraper/src/campaign_analytics.py` | Campaign metrics tracking & reporting |
| `python -m src.follow_up_sequence` | `projects/shared/lead-scraper/src/follow_up_sequence.py` | 7-touch, 60-day follow-up sequences |
| `python -m src.sms_outreach` | `projects/shared/lead-scraper/src/sms_outreach.py` | SMS sending via Twilio |
| `python -m src.sms_scheduler` | `projects/shared/lead-scraper/src/sms_scheduler.py` | SMS scheduling with rate limiting |
| `python -m src.twilio_webhook` | `projects/shared/lead-scraper/src/twilio_webhook.py` | Inbound SMS reply webhook handler |
| `python -m src.apollo_pipeline` | `projects/shared/lead-scraper/src/apollo_pipeline.py` | Apollo.io integration pipeline |
| `python -m src.apollo_to_clickup` | `projects/shared/lead-scraper/src/apollo_to_clickup.py` | Sync Apollo leads to ClickUp CRM |
| `python -m src.campaign_runner` | `projects/shared/lead-scraper/src/campaign_runner.py` | Execute SMS campaigns |
| `python -m src.campaign_dashboard` | `projects/shared/lead-scraper/src/campaign_dashboard.py` | Campaign performance dashboard |
| `python -m src.campaign_optimizer` | `projects/shared/lead-scraper/src/campaign_optimizer.py` | Campaign optimization engine |
| `python -m src.lead_scoring` | `projects/shared/lead-scraper/src/lead_scoring.py` | Lead qualification scoring |
| `python -m src.ab_testing` | `projects/shared/lead-scraper/src/ab_testing.py` | A/B test framework for messages |
| `python -m src.opt_out_manager` | `projects/shared/lead-scraper/src/opt_out_manager.py` | TCPA compliance & STOP handling |
| `python -m src.weekly_report` | `projects/shared/lead-scraper/src/weekly_report.py` | Weekly campaign reports |
| `python -m src.weekly_monitor` | `projects/shared/lead-scraper/src/weekly_monitor.py` | Weekly monitoring tasks |
| `python -m src.cold_outreach` | `projects/shared/lead-scraper/src/cold_outreach.py` | Cold outreach strategy |
| `python -m src.outreach_optimizer` | `projects/shared/lead-scraper/src/outreach_optimizer.py` | Outreach message optimization |
| `python -m src.check_google_api_costs` | `projects/shared/lead-scraper/src/check_google_api_costs.py` | Monitor Google API costs |
| `python -m src.check_actual_costs` | `projects/shared/lead-scraper/src/check_actual_costs.py` | Track actual API spend |
| `python scripts/enroll_sms_in_followup.py` | `projects/shared/lead-scraper/scripts/enroll_sms_in_followup.py` | Enroll leads in follow-up sequences |

## Social Media Automation

| Command | Path | Description |
|---------|------|-------------|
| `python -m src.multi_platform_manager` | `projects/shared/social-media-automation/src/multi_platform_manager.py` | Cross-platform content distribution |
| `python -m src.x_api` | `projects/shared/social-media-automation/src/x_api.py` | X/Twitter API wrapper |
| `python -m src.x_scheduler` | `projects/shared/social-media-automation/src/x_scheduler.py` | X post scheduling |
| `python -m src.tiktok_scheduler` | `projects/shared/social-media-automation/src/tiktok_scheduler.py` | TikTok video scheduling & queue |
| `python -m src.tiktok_api` | `projects/shared/social-media-automation/src/tiktok_api.py` | TikTok API integration |
| `python -m src.youtube_uploader` | `projects/shared/social-media-automation/src/youtube_uploader.py` | YouTube video uploads |
| `python -m src.content_generator` | `projects/shared/social-media-automation/src/content_generator.py` | AI-powered content creation |
| `python -m src.peptide_content_generator` | `projects/shared/social-media-automation/src/peptide_content_generator.py` | Fitness/peptide niche content |
| `python -m src.business_content_generator` | `projects/shared/social-media-automation/src/business_content_generator.py` | Multi-business content generation |
| `python -m src.script_generator` | `projects/shared/social-media-automation/src/script_generator.py` | Video script generation |
| `python -m src.post_analytics` | `projects/shared/social-media-automation/src/post_analytics.py` | Post performance tracking |
| `python -m src.engagement_tracker` | `projects/shared/social-media-automation/src/engagement_tracker.py` | Engagement metrics tracking |
| `python -m src.business_scheduler` | `projects/shared/social-media-automation/src/business_scheduler.py` | Multi-business scheduling |

## Fitness Influencer

### Core Pipeline

| Command | Path | Description |
|---------|------|-------------|
| `python src/generate_viral_reel.py --recipe recipe.json` | `projects/marceau-solutions/fitness-influencer/src/generate_viral_reel.py` | Create viral fitness reels |
| `python src/process_peptide_video.py` | `projects/marceau-solutions/fitness-influencer/src/process_peptide_video.py` | Process peptide-focused videos |
| `python src/video_compositor.py` | `projects/marceau-solutions/fitness-influencer/src/video_compositor.py` | Video composition and assembly |
| `python src/video_polish.py` | `projects/marceau-solutions/fitness-influencer/src/video_polish.py` | Final video polishing |
| `python src/peptide_graphics_generator.py` | `projects/marceau-solutions/fitness-influencer/src/peptide_graphics_generator.py` | Generate peptide infographics |
| `python src/text_overlay_generator.py` | `projects/marceau-solutions/fitness-influencer/src/text_overlay_generator.py` | Text overlay generation |
| `python tests/battle_tests.py` | `projects/marceau-solutions/fitness-influencer/tests/battle_tests.py` | Comprehensive battle test suite |

### AI Tool Testing (9 scripts)

| Command | Path | Description |
|---------|------|-------------|
| `python tools/test_talking_head.py --image face.png --audio speech.mp3` | `tools/test_talking_head.py` | Talking head generation (SadTalker via Replicate) |
| `python tools/test_voice_elevenlabs.py` | `tools/test_voice_elevenlabs.py` | ElevenLabs voice synthesis & cloning |
| `python tools/test_voice_minimax.py` | `tools/test_voice_minimax.py` | Minimax voice synthesis (via fal.ai) |
| `python tools/test_voice_resemble.py` | `tools/test_voice_resemble.py` | Resemble AI voice cloning |
| `python tools/test_lipsync.py --video face.mp4 --audio speech.mp3` | `tools/test_lipsync.py` | Lip sync generation (4 models via fal.ai) |
| `python tools/test_image_to_video.py` | `tools/test_image_to_video.py` | Image-to-video animation |
| `python tools/test_face_restore.py` | `tools/test_face_restore.py` | Face restoration/enhancement (GFPGAN, CodeFormer) |
| `python tools/test_seed_bracketing.py` | `tools/test_seed_bracketing.py` | Seed bracketing for image consistency |
| `python tools/test_character_consistency.py` | `tools/test_character_consistency.py` | Character consistency across generations |

## Media Generation — Video

| Command | Path | Description |
|---------|------|-------------|
| `python execution/multi_provider_video_router.py` | `execution/multi_provider_video_router.py` | Multi-provider video routing (cost-optimized) |
| `python execution/intelligent_video_router.py` | `execution/intelligent_video_router.py` | Smart video provider selection |
| `python execution/moviepy_video_generator.py` | `execution/moviepy_video_generator.py` | Local video generation (FREE tier) |
| `python execution/grok_video_gen.py` | `execution/grok_video_gen.py` | xAI/Grok video generation |
| `python execution/creatomate_api.py` | `execution/creatomate_api.py` | Creatomate cloud video API |
| `python execution/creatomate_api_enhanced.py` | `execution/creatomate_api_enhanced.py` | Enhanced Creatomate wrapper |
| `python execution/video_ads.py` | `execution/video_ads.py` | Video ad generation |
| `python execution/video_jumpcut.py` | `execution/video_jumpcut.py` | Automated jumpcut editing |
| `python execution/video_analytics_dashboard.py` | `execution/video_analytics_dashboard.py` | Video performance analytics |

## Media Generation — Image

| Command | Path | Description |
|---------|------|-------------|
| `python execution/multi_provider_image_router.py` | `execution/multi_provider_image_router.py` | Multi-provider image routing (Grok, DALL-E, Replicate) |
| `python execution/grok_image_gen.py` | `execution/grok_image_gen.py` | xAI/Grok Aurora image generation |
| `python execution/educational_graphics.py` | `execution/educational_graphics.py` | Infographic generation |
| `python execution/canva_integration.py` | `execution/canva_integration.py` | Canva API wrapper |

## Amazon Seller

| Command | Path | Description |
|---------|------|-------------|
| `python execution/amazon_sp_api.py` | `execution/amazon_sp_api.py` | Amazon SP-API wrapper |
| `python execution/amazon_fee_calculator.py` | `execution/amazon_fee_calculator.py` | Calculate Amazon FBA/referral fees |
| `python execution/amazon_inventory_optimizer.py` | `execution/amazon_inventory_optimizer.py` | Inventory optimization |
| `python execution/amazon_oauth_server.py` | `execution/amazon_oauth_server.py` | OAuth flow server |
| `python execution/amazon_get_refresh_token.py` | `execution/amazon_get_refresh_token.py` | Get OAuth refresh token |
| `python execution/refresh_amazon_token.py` | `execution/refresh_amazon_token.py` | Refresh Amazon API token |
| `python execution/setup_amazon_auth.py` | `execution/setup_amazon_auth.py` | Setup Amazon authentication |
| `python execution/test_amazon_connection.py` | `execution/test_amazon_connection.py` | Test SP-API connection |
| `python execution/test_sp_api_simple.py` | `execution/test_sp_api_simple.py` | Simple SP-API test |

## CRM & Communication

### ClickUp CRM

| Command | Path | Description |
|---------|------|-------------|
| `python execution/clickup_oauth.py` | `execution/clickup_oauth.py` | ClickUp OAuth flow |
| `python execution/setup_sales_crm.py` | `execution/setup_sales_crm.py` | Setup sales CRM in ClickUp |
| `python execution/setup_custom_fields.py` | `execution/setup_custom_fields.py` | Setup custom fields |
| `python execution/get_custom_fields.py` | `execution/get_custom_fields.py` | Get custom field definitions |
| `python execution/add_lead.py` | `execution/add_lead.py` | Add lead to CRM |
| `python execution/lead_manager.py` | `execution/lead_manager.py` | Lead management operations |

### Communication

| Command | Path | Description |
|---------|------|-------------|
| `python execution/twilio_sms.py` | `execution/twilio_sms.py` | SMS sending via Twilio |
| `python execution/twilio_inbox_monitor.py` | `execution/twilio_inbox_monitor.py` | Inbound SMS monitoring |
| `python execution/gmail_monitor.py` | `execution/gmail_monitor.py` | Gmail inbox monitoring |
| `python execution/gmail_api_monitor.py` | `execution/gmail_api_monitor.py` | Gmail API monitoring |
| `python execution/email_response_monitor.py` | `execution/email_response_monitor.py` | Track email responses |
| `python execution/send_onboarding_email.py` | `execution/send_onboarding_email.py` | Email onboarding sequences |
| `python execution/calendly_monitor.py` | `execution/calendly_monitor.py` | Calendly event monitoring |

## Documents & Presentations

| Command | Path | Description |
|---------|------|-------------|
| `python execution/markdown_to_pdf.py` | `execution/markdown_to_pdf.py` | Convert Markdown to PDF |
| `python execution/pptx_generator.py` | `execution/pptx_generator.py` | PowerPoint generation |
| `python execution/pptx_editor.py` | `execution/pptx_editor.py` | PowerPoint editing |
| `python execution/pdf_outputs.py` | `execution/pdf_outputs.py` | PDF generation utilities |
| `python execution/apply_navy_theme.py` | `execution/apply_navy_theme.py` | Apply navy theme to slides |
| `python execution/standardize_experience_slides.py` | `execution/standardize_experience_slides.py` | Standardize slide formatting |
| `python execution/download_pptx.py` | `execution/download_pptx.py` | Download PowerPoint files |
| `python execution/open_pptx.py` | `execution/open_pptx.py` | Open PowerPoint files |

## AI Customer Service

| Command | Path | Description |
|---------|------|-------------|
| `python src/cli.py` | `projects/shared/ai-customer-service/src/cli.py` | Main CLI for AI customer service |
| `python src/auto_lead_detector.py` | `projects/shared/ai-customer-service/src/auto_lead_detector.py` | Detect leads from conversations |
| `python scripts/outreach_call.py` | `projects/shared/ai-customer-service/scripts/outreach_call.py` | Make outbound AI calls |
| `python scripts/batch_outreach.py` | `projects/shared/ai-customer-service/scripts/batch_outreach.py` | Batch outbound calling |
| `python scripts/make_test_call.py` | `projects/shared/ai-customer-service/scripts/make_test_call.py` | Test voice AI calls |
| `python scripts/check_call_logs.py` | `projects/shared/ai-customer-service/scripts/check_call_logs.py` | Check Twilio call logs |
| `python scripts/configure_twilio.py` | `projects/shared/ai-customer-service/scripts/configure_twilio.py` | Configure Twilio settings |

## Legal Case Manager

| Command | Path | Description |
|---------|------|-------------|
| `python src/communication_logger.py` | `projects/marceau-solutions/legal-case-manager/src/communication_logger.py` | Log legal communications |
| `python src/document_generator.py` | `projects/marceau-solutions/legal-case-manager/src/document_generator.py` | Generate legal documents |
| `python src/timeline_builder.py` | `projects/marceau-solutions/legal-case-manager/src/timeline_builder.py` | Build case timelines |
| `python src/evidence_catalog.py` | `projects/marceau-solutions/legal-case-manager/src/evidence_catalog.py` | Catalog case evidence |
| `python src/deadline_tracker.py` | `projects/marceau-solutions/legal-case-manager/src/deadline_tracker.py` | Track legal deadlines |

## Infrastructure & Utilities

| Command | Path | Description |
|---------|------|-------------|
| `python execution/agent_bridge_api.py` | `execution/agent_bridge_api.py` | Python Bridge API for n8n (EC2 localhost:5010) |
| `python execution/security_scanner.py` | `execution/security_scanner.py` | Security vulnerability scanning |
| `python execution/secrets_manager.py` | `execution/secrets_manager.py` | Secrets management utilities |
| `python execution/mcp_security.py` | `execution/mcp_security.py` | MCP security utilities |
| `python execution/setup_wizard.py` | `execution/setup_wizard.py` | Interactive setup wizard |
| `python execution/monitor_capability_gaps.py` | `execution/monitor_capability_gaps.py` | Monitor capability gaps |
| `python execution/session_manager.py` | `execution/session_manager.py` | Claude session state management |
| `python execution/intent_router.py` | `execution/intent_router.py` | Route requests by intent |
| `python execution/template_manager.py` | `execution/template_manager.py` | Template management |
| `python execution/live_editor.py` | `execution/live_editor.py` | Live document editing |
| `python execution/google_auth_setup.py` | `execution/google_auth_setup.py` | Google OAuth setup |
| `python execution/google_drive_share.py` | `execution/google_drive_share.py` | Google Drive sharing automation |
| `python execution/stripe_payments.py` | `execution/stripe_payments.py` | Stripe payment processing |
| `python execution/stripe_webhook_server.py` | `execution/stripe_webhook_server.py` | Stripe webhook handler |

## Fitness & Health Utilities

| Command | Path | Description |
|---------|------|-------------|
| `python execution/workout_plan_generator.py` | `execution/workout_plan_generator.py` | Generate structured workout plans |
| `python execution/nutrition_guide_generator.py` | `execution/nutrition_guide_generator.py` | Generate nutrition guides |
| `python execution/fitness_assistant_api.py` | `execution/fitness_assistant_api.py` | Fitness API wrapper |
| `python execution/calendar_reminders.py` | `execution/calendar_reminders.py` | Fitness calendar reminders |
| `python execution/revenue_analytics.py` | `execution/revenue_analytics.py` | Cross-project revenue tracking |

## Interview Prep

| Command | Path | Description |
|---------|------|-------------|
| `python execution/interview_research.py` | `execution/interview_research.py` | Interview research automation |
| `python execution/interview_prep_api.py` | `execution/interview_prep_api.py` | Interview prep API |
| `python execution/mock_interview.py` | `execution/mock_interview.py` | Mock interview simulator |

## Weather

| Command | Path | Description |
|---------|------|-------------|
| `python execution/fetch_naples_weather.py` | `execution/fetch_naples_weather.py` | Fetch Naples weather data |
| `python execution/generate_weather_report.py` | `execution/generate_weather_report.py` | Generate weather report PDF |

## MCP Tools

| Command | Path | Description |
|---------|------|-------------|
| `python -m src.md_to_pdf` | `projects/shared/md-to-pdf/src/md_to_pdf.py` | Markdown to PDF converter (published to MCP Registry) |

## Scripts (Maintenance & Setup)

### Python Scripts

| Command | Path | Description |
|---------|------|-------------|
| `./scripts/daily_standup.sh` | `scripts/daily_standup.sh` | Morning routine: health + revenue + digest + quick links |
| `python scripts/health_check.py` | `scripts/health_check.py` | Full system health check (EC2, n8n, disk, clawdbot, .env). Exit 1 on failure. |
| `python scripts/health_check.py --fast` | `scripts/health_check.py` | Local-only health check (skips SSH) |
| `python scripts/backup-n8n.py` | `scripts/backup-n8n.py` | Export ALL n8n workflows to dated JSON — run weekly + commit |
| `python scripts/backup-n8n.py --list` | `scripts/backup-n8n.py` | List all n8n workflows with IDs (no backup written) |
| `python scripts/check_api_balances.py` | `scripts/check_api_balances.py` | API provider balance dashboard |
| `python scripts/revenue-report.py` | `scripts/revenue-report.py` | Weekly revenue dashboard (Stripe + leads + SMS) |
| `python scripts/create-coaching-tracker-sheet.py` | `scripts/create-coaching-tracker-sheet.py` | Create coaching tracker Google Sheet |
| `python scripts/create-coaching-drive-folders.py` | `scripts/create-coaching-drive-folders.py` | Create coaching Google Drive folders |
| `python scripts/create-social-media-sheet.py` | `scripts/create-social-media-sheet.py` | Create social media content sheet |
| `python scripts/update-social-media-sheets.py` | `scripts/update-social-media-sheets.py` | Update social media sheets |
| `python scripts/clawdbot-action-router.py` | `scripts/clawdbot-action-router.py` | Route Clawdbot actions |
| `python scripts/route-clawdbot-contribution.py` | `scripts/route-clawdbot-contribution.py` | Route Clawdbot contributions |

### Shell Scripts

| Command | Path | Description |
|---------|------|-------------|
| `bash scripts/add-company-project.sh` | `scripts/add-company-project.sh` | Add new company project |
| `bash scripts/auto_save.sh` | `scripts/auto_save.sh` | Automated git backup |
| `bash scripts/create-company-folder.sh` | `scripts/create-company-folder.sh` | Create company folder structure |
| `bash scripts/daily-backup.sh` | `scripts/daily-backup.sh` | Daily backup to EC2 |
| `bash scripts/ec2-hardening.sh` | `scripts/ec2-hardening.sh` | EC2 security hardening |
| `bash scripts/ec2-tunnel.sh` | `scripts/ec2-tunnel.sh` | SSH tunnel to EC2 |
| `bash scripts/fix-website-submodules.sh` | `scripts/fix-website-submodules.sh` | Fix git submodules |
| `bash scripts/invoke-claude-code.sh` | `scripts/invoke-claude-code.sh` | Invoke Claude Code CLI |
| `bash scripts/mac-sync.sh` | `scripts/mac-sync.sh` | Sync Mac to EC2 |
| `bash scripts/quick_test.sh` | `scripts/quick_test.sh` | Quick testing script |
| `bash scripts/restore-hybrid-architecture.sh` | `scripts/restore-hybrid-architecture.sh` | Restore hybrid architecture |
| `bash scripts/restructure_client_folders.sh` | `scripts/restructure_client_folders.sh` | Restructure client folders |
| `bash scripts/setup-git-remotes.sh` | `scripts/setup-git-remotes.sh` | Setup git remotes |
| `bash scripts/sync-clawdbot-outputs.sh` | `scripts/sync-clawdbot-outputs.sh` | Sync Clawdbot outputs |
| `bash scripts/sync-handoffs.sh` | `scripts/sync-handoffs.sh` | Sync agent handoffs |
| `bash scripts/verify-automation-tools.sh` | `scripts/verify-automation-tools.sh` | Verify automation tools |
| `bash scripts/verify-git-remotes.sh` | `scripts/verify-git-remotes.sh` | Verify git remotes |
