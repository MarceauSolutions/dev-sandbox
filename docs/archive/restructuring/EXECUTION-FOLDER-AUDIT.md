# Execution Folder Audit - Migration Candidates

**Purpose**: Identify which `execution/` scripts should move to project-specific locations
**Created**: 2026-01-21

---

## Current State

**Total files in execution/**: 68 Python files
**Should remain in execution/**: ~5-10 (true shared utilities)
**Should migrate to projects/**: ~50-60 (project-specific)

---

## Migration Recommendations

### MIGRATE TO projects/shared/clickup-crm/
**Multi-tenant CRM tool**:
- `clickup_api.py` (8.9K)
- `clickup_oauth.py` (5.8K)

---

### MIGRATE TO projects/shared/lead-scraper/src/
**Already a project, but these might be missing**:
- `add_lead.py` (9.1K) - Add leads to database
- `lead_manager.py` (30K) - Lead management operations

**Action**: Check if these are duplicates or belong in lead-scraper project

---

### MIGRATE TO projects/marceau-solutions/amazon-seller/src/
**Amazon Seller Central integration**:
- `amazon_fee_calculator.py` (17K)
- `amazon_get_refresh_token.py` (5.6K)
- `amazon_inventory_optimizer.py` (16K)
- `amazon_oauth_server.py` (9.8K)
- `amazon_sp_api.py` (16K)
- `refresh_amazon_token.py` (2.2K)
- `setup_amazon_auth.py` (8.4K)
- `test_amazon_connection.py` (1.8K)
- `test_sp_api_simple.py` (1.8K)

**Total**: 9 files, ~94KB
**Status**: amazon-seller project exists, these should be in its src/

---

### MIGRATE TO projects/marceau-solutions/interview-prep/src/
**Interview prep PPTX generator**:
- `interview_prep_api.py` (27K)
- `interview_research.py` (16K)
- `pptx_editor.py` (29K)
- `pptx_generator.py` (26K)
- `apply_navy_theme.py` (7.2K)
- `download_pptx.py` (5.4K)
- `open_pptx.py` (2.4K)
- `enhance_experience_slides.py` (11K)
- `reformat_experience_slides.py` (7.5K)
- `standardize_experience_slides.py` (9.0K)
- `live_editor.py` (17K)
- `mock_interview.py` (23K)
- `educational_graphics.py` (14K)

**Total**: 13 files, ~194KB
**Status**: interview-prep project exists, these should be in its src/

---

### MIGRATE TO projects/marceau-solutions/fitness-influencer/backend/src/
**Fitness influencer content creation**:
- `fitness_assistant_api.py` (12K)
- `nutrition_guide_generator.py` (17K)
- `workout_plan_generator.py` (13K)
- `video_jumpcut.py` (14K)
- `video_analytics_dashboard.py` (9.3K)
- `intelligent_video_router.py` (21K)
- `intent_router.py` (15K)
- `video_ads.py` (12K)

**Total**: 8 files, ~113KB
**Status**: fitness-influencer/backend exists, these should be in its src/

---

### MIGRATE TO projects/shared/ai-customer-service/src/
**Email/SMS monitoring and responses**:
- `email_response_monitor.py` (21K)
- `gmail_api_monitor.py` (15K)
- `gmail_monitor.py` (13K)
- `twilio_inbox_monitor.py` (20K)
- `twilio_sms.py` (13K)

**Total**: 5 files, ~82KB
**Status**: ai-customer-service project exists, multi-tenant

---

### MIGRATE TO projects/shared/social-media-automation/src/
**Social media content creation**:
- `canva_integration.py` (9.8K)
- `creatomate_api.py` (16K)
- `creatomate_api_enhanced.py` (18K)
- `shotstack_api.py` (19K)
- `moviepy_video_generator.py` (5.3K)
- `moviepy_video_generator_old.py` (15K) ← Delete? (old version)
- `moviepy_video_generator_v2.py` (12K)
- `grok_image_gen.py` (7.2K)

**Total**: 8 files, ~102KB (7 files if deleting old version)
**Status**: social-media-automation project exists, multi-tenant

---

### MIGRATE TO projects/shared/personal-assistant/src/
**Calendar and scheduling**:
- `calendar_reminders.py` (10K)
- `calendly_monitor.py` (16K)

**Total**: 2 files, ~26KB
**Status**: personal-assistant project exists

---

### MIGRATE TO projects/marceau-solutions/naples-weather-report/src/
**Weather report generator** (OR create new project):
- `fetch_naples_weather.py` (3.9K)
- `generate_weather_report.py` (7.6K)

**Total**: 2 files, ~11KB
**Action**: Check if naples-weather-report project exists, if not create it

---

### MIGRATE TO projects/marceau-solutions/md-to-pdf/src/
**Markdown to PDF conversion**:
- `markdown_to_pdf.py` (10K)
- `pdf_outputs.py` (14K)

**Total**: 2 files, ~24KB
**Status**: md-to-pdf project exists as MCP

---

### KEEP IN execution/ (True Shared Utilities)
**These are deployment/infrastructure tools, not business logic**:
- `deploy_to_skills.py` (9.2K) ← **WAIT**, this is in root now, remove duplicate
- `session_manager.py` (6.1K) - Session management utility
- `google_auth_setup.py` (4.6K) - Google OAuth setup helper

**Total**: 2-3 files (check if deploy_to_skills.py is duplicate)

---

### DELETE (Obsolete or Duplicate)
- `moviepy_video_generator_old.py` (15K) - Old version, superseded by v2
- `deploy_to_skills.py` (9.2K) - Duplicate of root version
- Any other `_old` or `_v1` files

---

### UNCLEAR - NEED REVIEW
**Sales CRM setup scripts** (one-time setup?):
- `send_onboarding_email.py` (7.5K)
- `setup_sales_crm.py` (3.8K)
- `setup_custom_fields.py` (3.9K)
- `get_custom_fields.py` (1.1K)
- `custom_field_ids.json` (444B)
- `setup_wizard.py` (19K)

**Action**: Determine if these belong in clickup-crm or if they're one-time setup

**Template/Style management**:
- `template_manager.py` (14K)
- `update_skill_docs.py` (14K)
- `revenue_analytics.py` (13K)
- `monitor_capability_gaps.py` (12K)
- `manage_agent_skills.py` (11K)

**Action**: Determine project homes for these

**Form handling**:
- `form_handler/` (directory)

**Action**: Move to website projects or shared/

**Assets**:
- `assets/` (directory)
- `styles/` (directory)
- `webhooks.json` (21B)

**Action**: Move to appropriate project locations

---

## Migration Strategy

### Phase 1: Easy Wins (Clear Project Homes)
1. Amazon Seller scripts → `projects/marceau-solutions/amazon-seller/src/`
2. Interview Prep scripts → `projects/marceau-solutions/interview-prep/src/`
3. Fitness Influencer scripts → `projects/marceau-solutions/fitness-influencer/backend/src/`
4. ClickUp scripts → `projects/shared/clickup-crm/src/`

### Phase 2: Multi-Tenant Tools
5. Email/SMS monitoring → `projects/shared/ai-customer-service/src/`
6. Social media tools → `projects/shared/social-media-automation/src/`
7. Calendar tools → `projects/shared/personal-assistant/src/`

### Phase 3: Small Projects
8. MD to PDF → `projects/marceau-solutions/md-to-pdf/src/`
9. Weather report → `projects/marceau-solutions/naples-weather-report/src/` (create if needed)
10. Lead management → `projects/shared/lead-scraper/src/` (check for duplicates)

### Phase 4: Cleanup
11. Delete old/duplicate files
12. Review unclear items
13. Move assets/templates to appropriate locations

---

## Automated Migration Script

Create `scripts/migrate-execution-to-projects.sh`:

```bash
#!/bin/bash

# Migrate Amazon Seller scripts
git mv execution/amazon_*.py projects/marceau-solutions/amazon-seller/src/
git mv execution/setup_amazon_auth.py projects/marceau-solutions/amazon-seller/src/
git mv execution/refresh_amazon_token.py projects/marceau-solutions/amazon-seller/src/
git mv execution/test_*amazon*.py projects/marceau-solutions/amazon-seller/src/

# Migrate Interview Prep scripts
git mv execution/interview_*.py projects/marceau-solutions/interview-prep/src/
git mv execution/pptx_*.py projects/marceau-solutions/interview-prep/src/
git mv execution/*_slides.py projects/marceau-solutions/interview-prep/src/
git mv execution/apply_navy_theme.py projects/marceau-solutions/interview-prep/src/
git mv execution/download_pptx.py projects/marceau-solutions/interview-prep/src/
git mv execution/open_pptx.py projects/marceau-solutions/interview-prep/src/
git mv execution/live_editor.py projects/marceau-solutions/interview-prep/src/
git mv execution/mock_interview.py projects/marceau-solutions/interview-prep/src/
git mv execution/educational_graphics.py projects/marceau-solutions/interview-prep/src/

# Migrate Fitness Influencer scripts
git mv execution/fitness_*.py projects/marceau-solutions/fitness-influencer/backend/src/
git mv execution/*nutrition*.py projects/marceau-solutions/fitness-influencer/backend/src/
git mv execution/*workout*.py projects/marceau-solutions/fitness-influencer/backend/src/
git mv execution/video_*.py projects/marceau-solutions/fitness-influencer/backend/src/
git mv execution/*_video_*.py projects/marceau-solutions/fitness-influencer/backend/src/
git mv execution/intelligent_video_router.py projects/marceau-solutions/fitness-influencer/backend/src/
git mv execution/intent_router.py projects/marceau-solutions/fitness-influencer/backend/src/

# Migrate ClickUp scripts
mkdir -p projects/shared/clickup-crm/src
git mv execution/clickup_*.py projects/shared/clickup-crm/src/

# Migrate multi-tenant monitoring
git mv execution/*monitor*.py projects/shared/ai-customer-service/src/
git mv execution/gmail_*.py projects/shared/ai-customer-service/src/
git mv execution/twilio_*.py projects/shared/ai-customer-service/src/

# Migrate social media tools
git mv execution/canva_*.py projects/shared/social-media-automation/src/
git mv execution/creatomate_*.py projects/shared/social-media-automation/src/
git mv execution/shotstack_*.py projects/shared/social-media-automation/src/
git mv execution/moviepy_video_generator_v2.py projects/shared/social-media-automation/src/
git mv execution/grok_image_gen.py projects/shared/social-media-automation/src/

# Migrate calendar tools
git mv execution/calendar_*.py projects/shared/personal-assistant/src/
git mv execution/calendly_*.py projects/shared/personal-assistant/src/

# Migrate MD to PDF
git mv execution/markdown_to_pdf.py projects/marceau-solutions/md-to-pdf/src/
git mv execution/pdf_outputs.py projects/marceau-solutions/md-to-pdf/src/

# Delete old versions
rm execution/moviepy_video_generator_old.py
rm execution/deploy_to_skills.py  # Duplicate of root version

# Commit
git commit -m "refactor: Migrate execution/ scripts to project-specific locations

Moved 60+ scripts from execution/ to appropriate project folders:
- Amazon Seller (9 files) → marceau-solutions/amazon-seller/src/
- Interview Prep (13 files) → marceau-solutions/interview-prep/src/
- Fitness Influencer (8 files) → fitness-influencer/backend/src/
- ClickUp (2 files) → shared/clickup-crm/src/
- Monitoring (5 files) → shared/ai-customer-service/src/
- Social Media (7 files) → shared/social-media-automation/src/
- Calendar (2 files) → shared/personal-assistant/src/
- MD to PDF (2 files) → marceau-solutions/md-to-pdf/src/

Deleted obsolete:
- moviepy_video_generator_old.py
- deploy_to_skills.py (duplicate)

Follows company-centric architecture pattern.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Impact Assessment

### Files Remaining in execution/: ~5-10
- True shared utilities only
- Deployment/infrastructure tools
- OAuth helpers

### Files Migrated: ~60
- Project-specific business logic
- Multi-tenant tools in shared/
- Company-specific tools in company folders

### Benefits
- ✅ Clear project ownership
- ✅ Easier to find code (in project folders, not centralized)
- ✅ Matches company-centric architecture
- ✅ Projects can be deployed independently
- ✅ No more confusion about where to put new code

---

## Next Steps

1. **Review this audit** - Confirm migration recommendations
2. **Test in dev** - Run migration script on test data
3. **Update imports** - Fix all Python imports after migration
4. **Update directives** - Update all directive references to new paths
5. **Test each project** - Verify nothing broke
6. **Deploy** - Redeploy affected projects with new structure

---

## Questions for William

1. Should we migrate execution/ scripts now or defer?
2. Which phase should we start with (1-4)?
3. Are there any scripts in execution/ that should stay there?
4. Should we create naples-weather-report project or include in something else?

**Recommendation**: Start with Phase 1 (Easy Wins) - clear project homes for Amazon, Interview Prep, Fitness Influencer, and ClickUp.
